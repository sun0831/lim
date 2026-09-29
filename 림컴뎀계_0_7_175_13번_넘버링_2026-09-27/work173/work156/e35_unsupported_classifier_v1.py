"""E35-3 classifier for unsupported clauses.

Conservative: classifies why a clause is currently unsupported without claiming
that the clause is executable. Categories are planning labels, not coverage.
"""
from __future__ import annotations
import json,re
from collections import Counter,defaultdict
from pathlib import Path
from passive_compiler_v29 import split_clauses
from rule_ir_compiler_v1 import compile_record

CATS=("existing_primitive_parser_gap","compound_clause_decomposition","data_or_parameter_gap","true_runtime_gap","unresolved")

def classify(text:str, unsupported:list[str])->str:
    t=text.strip()
    # Existing frozen contracts can express these semantics; current parser simply
    # does not lower the prose into a PassiveDefinition yet.
    if re.search(r"(?:가장\s*(?:높|낮)|가장\s*(?:빠르|느리)|무작위|랜덤|특정\s*인격|소속|자신을\s*제외)",t) and re.search(r"(?:아군|적|대상)",t):
        return "existing_primitive_parser_gap"
    if re.search(r"(?:스킬|사용할 수 없|변경|전환|교체).*(?:다시|다른|다음 턴|사용)",t):
        return "compound_clause_decomposition"
    if re.search(r"(?:확률|확률로|경우|동전|코인).*(?:적용|발동|추가|부여|재사용)",t):
        return "data_or_parameter_gap"
    if re.search(r"(?:사용함|사용한다|발동함|발동한다|공격함|공격한다|추가 공격|원호|처형|피해를 전가|전가)",t):
        return "compound_clause_decomposition"
    if re.search(r"(?:BGM|전투 BGM|애니메이션|연출|대사)",t):
        return "true_runtime_gap"
    if re.search(r"(?:체력이 0|체력.*1 미만|사망|부활|대기 해제|복귀)",t):
        return "data_or_parameter_gap"
    if unsupported and all(x in {"trigger","effect"} for x in unsupported):
        return "existing_primitive_parser_gap"
    return "unresolved"

def run(path="GIMMICK_GAP_REPORT_v4.json"):
    d=json.loads(Path(path).read_text(encoding="utf-8")); counts=Counter(); rows=[]
    for i,g in enumerate(d.get('gaps',[])):
        for j,c in enumerate(split_clauses(str(g.get('source_text','')))):
            rs,reasons,uns=compile_record({'id':f'e35:{i}:{j}','name':'e35','effect':c},str(g.get('identity_id','unknown')),j)
            if rs: continue
            cat=classify(c,uns); counts[cat]+=1
            rows.append({'identity_id':g.get('identity_id'),'identity_name':g.get('identity_name'),'categories':g.get('categories',[]),'clause':c,'unsupported':uns,'classification':cat})
    return {'version':'E35-3','total_unsupported':len(rows),'classification_counts':dict(counts),'rows':rows}

if __name__=='__main__':
    r=run(); Path('E35_UNSUPPORTED_CLAUSE_CLASSIFICATION.json').write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf-8')
    md=['# E35-3 Unsupported Clause Classification','',f"- Unsupported clauses: **{r['total_unsupported']}**",'','| Classification | Count |','|---|---:|']
    for k,v in sorted(r['classification_counts'].items(),key=lambda x:-x[1]): md.append(f'| {k} | {v} |')
    md += ['', '## Interpretation', '- `existing_primitive_parser_gap`: existing E34 primitives appear sufficient; parser/lowering is missing.', '- `compound_clause_decomposition`: clause likely needs decomposition into multiple existing primitives.', '- `data_or_parameter_gap`: semantic primitive exists but a required parameter/data contract is missing.', '- `true_runtime_gap`: current primitive/runtime vocabulary does not safely represent the behavior.', '- `unresolved`: insufficient evidence; do not guess.']
    Path('E35_UNSUPPORTED_CLAUSE_CLASSIFICATION.md').write_text('\n'.join(md),encoding='utf-8')
    print(json.dumps(r['classification_counts'],ensure_ascii=False))
