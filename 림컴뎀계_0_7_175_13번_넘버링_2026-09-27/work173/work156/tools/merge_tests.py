#!/usr/bin/env python3
"""AST 기반 안전 테스트 병합기 (림컴뎀계).

원본 test_*.py 여러 개를 하나로 합치되
  - 이름 충돌은 정의와 모든 참조를 함께 rename (지역변수 shadow 는 건드리지 않음)
  - decorator / 클래스 / 함수 본문은 AST 그대로 보존 (rename 이 필요 없는 문장은 원문 그대로)
  - 똑같은 helper 는 1개로 합치고, 다른 helper 는 접미사(__vNN)로 분리
  - 병합 후 "각 함수가 참조하는 모듈 수준 이름이 원래 자기 파일 것인지" 정적 검증
사용:  python tools/merge_tests.py groups.json OUT_DIR
"""
import ast, copy, json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


# ───────────────────────── scope-aware renamer ─────────────────────────
def _stores_in(nodes):
    """함수/클래스 본문에서 (중첩 스코프 안쪽은 제외하고) 지역으로 바인딩되는 이름."""
    out = set()
    def visit(n):
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            out.add(n.name); return
        if isinstance(n, ast.Lambda): return
        if isinstance(n, ast.Name) and isinstance(n.ctx, (ast.Store, ast.Del)):
            out.add(n.id)
        elif isinstance(n, (ast.Import, ast.ImportFrom)):
            for a in n.names:
                out.add((a.asname or a.name).split('.')[0])
        elif isinstance(n, ast.ExceptHandler) and n.name:
            out.add(n.name)
        elif isinstance(n, (ast.MatchAs, ast.MatchStar)) and getattr(n, 'name', None):
            out.add(n.name)
        elif isinstance(n, ast.MatchMapping) and n.rest:
            out.add(n.rest)
        for c in ast.iter_child_nodes(n):
            visit(c)
    for n in nodes: visit(n)
    return out

def _declared_global(nodes):
    g = set()
    for n in ast.walk(ast.Module(body=list(nodes), type_ignores=[])):
        if isinstance(n, (ast.Global, ast.Nonlocal)): g.update(n.names)
    return g

def _args_names(args):
    names = [a.arg for a in args.posonlyargs + args.args + args.kwonlyargs]
    if args.vararg: names.append(args.vararg.arg)
    if args.kwarg: names.append(args.kwarg.arg)
    return set(names)

class Renamer(ast.NodeTransformer):
    def __init__(self, mapping):
        self.map = mapping; self.scopes = []; self.changed = 0
    def shadowed(self, name):
        for i in range(len(self.scopes) - 1, -1, -1):
            kind, s = self.scopes[i]
            if kind == 'class' and i != len(self.scopes) - 1: continue
            if name in s: return True
        return False
    def visit_Name(self, n):
        if n.id in self.map and not self.shadowed(n.id):
            self.changed += 1; n.id = self.map[n.id]
        return n
    def _func(self, n):
        top = not self.scopes
        n.decorator_list = [self.visit(d) for d in n.decorator_list]
        # defaults / annotations 는 바깥 스코프에서 평가
        for d in n.args.defaults + [x for x in n.args.kw_defaults if x is not None]:
            self.visit(d)
        for a in n.args.posonlyargs + n.args.args + n.args.kwonlyargs + [x for x in (n.args.vararg, n.args.kwarg) if x]:
            if a.annotation is not None: a.annotation = self.visit(a.annotation)
        if n.returns is not None: n.returns = self.visit(n.returns)
        if top and n.name in self.map:
            self.changed += 1; n.name = self.map[n.name]
        loc = (_args_names(n.args) | _stores_in(n.body)) - _declared_global(n.body)
        self.scopes.append(('func', loc))
        n.body = [self.visit(s) for s in n.body]
        self.scopes.pop()
        return n
    visit_FunctionDef = _func
    visit_AsyncFunctionDef = _func
    def visit_Lambda(self, n):
        for d in n.args.defaults + [x for x in n.args.kw_defaults if x is not None]:
            self.visit(d)
        self.scopes.append(('func', _args_names(n.args)))
        n.body = self.visit(n.body)
        self.scopes.pop(); return n
    def visit_ClassDef(self, n):
        top = not self.scopes
        n.decorator_list = [self.visit(d) for d in n.decorator_list]
        n.bases = [self.visit(b) for b in n.bases]
        n.keywords = [self.visit(k) for k in n.keywords]
        if top and n.name in self.map:
            self.changed += 1; n.name = self.map[n.name]
        self.scopes.append(('class', _stores_in(n.body)))
        n.body = [self.visit(s) for s in n.body]
        self.scopes.pop(); return n
    def _comp(self, n):
        tg = set()
        for g in n.generators:
            for t in ast.walk(g.target):
                if isinstance(t, ast.Name): tg.add(t.id)
        # 첫 iter 는 바깥 스코프, 나머지는 comp 스코프
        n.generators[0].iter = self.visit(n.generators[0].iter)
        self.scopes.append(('func', tg))
        for i, g in enumerate(n.generators):
            g.target = self.visit(g.target)
            if i: g.iter = self.visit(g.iter)
            g.ifs = [self.visit(x) for x in g.ifs]
        if isinstance(n, ast.DictComp):
            n.key = self.visit(n.key); n.value = self.visit(n.value)
        else:
            n.elt = self.visit(n.elt)
        self.scopes.pop(); return n
    visit_ListComp = visit_SetComp = visit_GeneratorExp = visit_DictComp = _comp
    def visit_Global(self, n):
        n.names = [self.map.get(x, x) for x in n.names]; return n


# ───────────────────────── module analysis ─────────────────────────
def _immutable_expr(e):
    """중복 제거해도 안전한(변경 불가능) 값인지: 상수 / Path 계산식 / 상수 튜플"""
    for n in ast.walk(e):
        if isinstance(n, (ast.List, ast.Dict, ast.Set, ast.ListComp, ast.DictComp, ast.SetComp,
                          ast.GeneratorExp, ast.Lambda)):
            return False
        if isinstance(n, ast.Call):
            f = n.func
            ok = (isinstance(f, ast.Name) and f.id in ('Path', 'str')) or \
                 (isinstance(f, ast.Attribute) and f.attr in ('resolve', 'with_name', 'joinpath'))
            if not ok: return False
    return True

def dump(n):
    return ast.dump(n, annotate_fields=True, include_attributes=False)

class Mod:
    pass

def analyze(path: Path):
    m = Mod()
    m.path = path; m.stem = path.stem
    m.src = path.read_text(encoding='utf-8'); m.lines = m.src.splitlines()
    tree = ast.parse(m.src); m.tree = tree
    m.tag = '_'.join(m.stem[5:].split('_')[:2])
    m.items = []          # (kind, node, text_prefix_lines_start)
    m.doc = None
    prev_end = 0
    body = list(tree.body)
    if body and isinstance(body[0], ast.Expr) and isinstance(getattr(body[0], 'value', None), ast.Constant) \
            and isinstance(body[0].value.value, str):
        m.doc = body[0].value.value; prev_end = body[0].end_lineno; body = body[1:]
    for n in body:
        start = min([n.lineno] + [d.lineno for d in getattr(n, 'decorator_list', [])])
        seg_start = prev_end + 1
        prev_end = n.end_lineno
        n._seg = (seg_start, n.end_lineno)   # 앞쪽 주석/빈줄 포함
        m.items.append(n)
    return m

def seg_text(m, n):
    a, b = n._seg
    lines = m.lines[a - 1:b]
    # 앞쪽 빈 줄 제거
    while lines and not lines[0].strip(): lines.pop(0)
    return "\n".join(lines)

def bindings(n):
    """stmt → [(name, kind)]"""
    if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)): return [(n.name, 'def')]
    if isinstance(n, ast.ClassDef): return [(n.name, 'class')]
    if isinstance(n, ast.Assign):
        out = []
        for t in n.targets:
            for x in ast.walk(t):
                if isinstance(x, ast.Name) and isinstance(x.ctx, ast.Store): out.append((x.id, 'assign'))
        return out
    if isinstance(n, ast.AnnAssign) and isinstance(n.target, ast.Name):
        return [(n.target.id, 'assign')]
    return []


# ───────────────────────── merger ─────────────────────────
class Merger:
    def __init__(self, name, files):
        self.name = name
        self.mods = [analyze(f) for f in files]
        for m in self.mods:
            for n in m.items:
                if isinstance(n, ast.ImportFrom) and any(a.name == '*' for a in n.names):
                    raise ValueError(f"{m.stem}: star import — 병합 불가")
                if isinstance(n, ast.ImportFrom) and n.module == '__future__':
                    raise ValueError(f"{m.stem}: __future__ import — 병합 불가")
                if isinstance(n, (ast.ImportFrom, ast.Import)):
                    names = [a.name for a in n.names] + ([n.module] if isinstance(n, ast.ImportFrom) else [])
                    if any(str(x).startswith('test_') for x in names if x):
                        raise ValueError(f"{m.stem}: 다른 테스트 파일 import — 병합 불가")
        self.registry = {}       # name -> dict(kind, sig, prov:set)
        self.imports = []        # (kind, module/level, name, asname)
        self.imp_seen = {}       # key -> True
        self.out_items = []      # (text or node-source, src stem)
        self.renames = {}        # stem -> {old:new}
        self.dups = []           # (stem, name)
        self.testmap = []        # (orig_stem, orig_name, new_name)
        self.setup_seen = set()

    @staticmethod
    def _sig_import(n, a):
        if isinstance(n, ast.Import):
            if a.asname: return ('import', a.name)
            return ('pkg', a.name.split('.')[0])
        return ('from', n.level, n.module, a.name)

    def _fresh(self, name, tag):
        base = f"{name}__{tag}"; c = base; i = 2
        while c in self.registry or c in self.taken:
            c = f"{base}_{i}"; i += 1
        return c

    def merge(self):
        self.taken = set()
        all_names = set()
        for m in self.mods:
            for n in m.items:
                for b, _ in bindings(n): all_names.add(b)
        self.taken = all_names
        for m in self.mods:
            self._merge_one(m)
        return self.render()

    def _merge_one(self, m):
        # 이 파일의 바인딩 목록
        binds = []   # (name, kind, node, alias)
        for n in m.items:
            if isinstance(n, ast.Import):
                for a in n.names:
                    binds.append(((a.asname or a.name.split('.')[0]), 'import', n, a))
            elif isinstance(n, ast.ImportFrom):
                for a in n.names:
                    binds.append(((a.asname or a.name), 'import', n, a))
            else:
                for b, k in bindings(n):
                    binds.append((b, k, n, None))
        rename = {}
        # fixpoint
        for _ in range(50):
            changed = False
            for name, kind, node, alias in binds:
                if name in rename: continue
                if name not in self.registry: continue
                reg = self.registry[name]
                same = False
                if kind == 'import':
                    same = (reg['kind'] == 'import' and reg['sig'] == self._sig_import(node, alias))
                elif kind in ('def', 'class'):
                    if name.startswith('test') or name.startswith('Test'):
                        same = False
                    elif reg['kind'] == kind:
                        cp = copy.deepcopy(node)
                        r = Renamer({k: v for k, v in rename.items()}); r.visit(cp)
                        same = (dump(cp) == reg['sig'])
                elif kind == 'assign':
                    if reg['kind'] == 'assign' and isinstance(node, ast.Assign):
                        cp = copy.deepcopy(node)
                        r = Renamer(dict(rename)); r.visit(cp)
                        same = (dump(cp) == reg['sig']) and _immutable_expr(cp.value)
                if not same:
                    tag = m.tag
                    rename[name] = self._fresh(name, tag); self.taken.add(rename[name]); changed = True
            if not changed: break
        self.renames[m.stem] = rename
        # 등록 + 출력
        emitted_imp_in_this = set()
        for n in m.items:
            if isinstance(n, (ast.Import, ast.ImportFrom)):
                for a in n.names:
                    nm = (a.asname or a.name.split('.')[0]) if isinstance(n, ast.Import) else (a.asname or a.name)
                    newnm = rename.get(nm, nm)
                    sig = self._sig_import(n, a)
                    if newnm != nm and isinstance(n, ast.Import) and not a.asname and '.' in a.name:
                        raise ValueError(f"{m.stem}: 점 있는 import({a.name}) 이름 충돌 — 병합 불가")
                    self.registry.setdefault(newnm, dict(kind='import', sig=sig, prov=set()))
                    self.registry[newnm]['prov'].add(m.stem)
                    if isinstance(n, ast.Import):
                        key = ('import', a.name, newnm if (a.asname or newnm != nm) else None)
                        emit = ('import', a.name, key[2])
                    else:
                        key = ('from', n.level, n.module, a.name, newnm if newnm != a.name else None)
                        emit = ('from', (n.level, n.module), a.name, key[4])
                    if key in self.imp_seen: continue
                    self.imp_seen[key] = True
                    self.imports.append(emit)
            else:
                cp = copy.deepcopy(n)
                r = Renamer(dict(rename))
                cp = r.visit(cp)
                ast.fix_missing_locations(cp)
                bs = bindings(n)
                # 중복 def/class/assign → 생략
                if bs and all(nm not in rename and nm in self.registry and self.registry[nm]['kind'] != 'import'
                              and not nm.startswith(('test', 'Test'))
                              and self.registry[nm]['sig'] == dump(cp) for nm, _ in bs):
                    for nm, _ in bs: self.registry[nm]['prov'].add(m.stem)
                    self.dups.append((m.stem, [nm for nm, _ in bs]))
                    continue
                for nm, kd in bs:
                    fin = rename.get(nm, nm)
                    self.registry[fin] = dict(kind=kd, sig=dump(cp), prov={m.stem})
                # 기타 문장(Expr/If): 동일 문장 중복 제거
                if not bs:
                    key = dump(cp)
                    if key in self.setup_seen: continue
                    self.setup_seen.add(key)
                # test 이름 기록
                if isinstance(cp, (ast.FunctionDef, ast.ClassDef)):
                    orig = n.name
                    if orig.startswith(('test', 'Test')):
                        self.testmap.append((m.stem, orig, cp.name))
                text = seg_text(m, n) if r.changed == 0 else self._unparse_with_lead(m, n, cp)
                self.out_items.append((m.stem, text, cp))

    def _unparse_with_lead(self, m, n, cp):
        # 앞쪽 주석은 살리고 본문은 unparse
        a, _ = n._seg
        start = min([n.lineno] + [d.lineno for d in getattr(n, 'decorator_list', [])])
        lead = [l for l in m.lines[a - 1:start - 1] if l.strip()]
        return ("\n".join(lead) + "\n" if lead else "") + ast.unparse(cp)

    def render(self):
        out = []
        out.append(f'"""병합 테스트: {self.name}\n')
        out.append("원본 파일 (내용은 AST 병합기로 합쳤고 테스트 본문은 바꾸지 않음):")
        for m in self.mods: out.append(f"  - {m.path.name}")
        out.append("이름 충돌 helper 는 `이름__vNN` 으로 분리했다. 매핑은 tools/MERGE_MAP.json 참고.\n\"\"\"")
        # imports
        plain = [i for i in self.imports if i[0] == 'import']
        frm = [i for i in self.imports if i[0] == 'from']
        for _, mod, asn in plain:
            out.append(f"import {mod}" + (f" as {asn}" if asn else ""))
        bymod = {}
        for _, key, name, asn in frm:
            bymod.setdefault(key, []).append((name, asn))
        for (lvl, mod), names in bymod.items():
            parts = [f"{a} as {b}" if b else a for a, b in names]
            head = "from " + "." * lvl + (mod or "") + " import "
            line = head + ", ".join(parts)
            if len(line) > 110:
                line = head + "(\n    " + ",\n    ".join(parts) + ",\n)"
            out.append(line)
        out.append("")
        last = None
        for stem, text, cp in self.out_items:
            if stem != last:
                out.append("\n\n# " + "=" * 70)
                out.append(f"# 원본: {stem}.py")
                out.append("# " + "=" * 70)
                last = stem
            out.append("\n" + text if isinstance(cp, (ast.FunctionDef, ast.ClassDef)) else text)
        return "\n".join(out) + "\n"

    # 정적 검증: 각 원본 파일의 코드가 참조하는 모듈 수준 이름이 자기 파일 소유인가
    def verify_provenance(self, merged_src):
        prov = {n: v['prov'] for n, v in self.registry.items()}
        class Collector(Renamer):
            def visit_Name(self, n):
                if n.id in self.map and not self.shadowed(n.id) and isinstance(n.ctx, ast.Load):
                    self.found.add(n.id)
                return n
        problems = []
        for stem, text, cp in self.out_items:
            c = Collector({k: k for k in prov}); c.found = set()
            c.visit(copy.deepcopy(cp))
            for nm in sorted(c.found):
                if stem not in prov[nm]:
                    problems.append((stem, getattr(cp, 'name', '<stmt>'), nm, sorted(prov[nm])))
        return problems


def main():
    cfg = json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
    outdir = Path(sys.argv[2]); outdir.mkdir(parents=True, exist_ok=True)
    manifest = {}
    for name, stems in cfg['groups'].items():
        files = [ROOT / f"test_{s}.py" for s in stems]
        mg = Merger(name, files)
        src = mg.merge()
        probs = mg.verify_provenance(src)
        (outdir / f"test_{name}.py").write_text(src, encoding='utf-8')
        manifest[f"test_{name}.py"] = dict(
            sources=[f"test_{s}.py" for s in stems],
            renames={k: v for k, v in mg.renames.items() if v},
            deduped=[(a, b) for a, b in mg.dups],
            tests=[dict(source=a, original=b, merged=c) for a, b, c in mg.testmap],
            provenance_problems=probs)
        print(f"{name}: {len(stems)} files → 1 | tests {len(mg.testmap)} | renames {sum(len(v) for v in mg.renames.values())} "
              f"| deduped {sum(len(b) for _, b in mg.dups)} | 출처검증문제 {len(probs)}")
    (outdir / "MERGE_MAP.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=1), encoding='utf-8')

if __name__ == '__main__':
    main()
