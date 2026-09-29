import json
from passive_compiler_v29 import compile_one
from passive_runtime_v29_base import Not, TargetHasSP, ModifyContext


def _rules():
    cat=json.load(open('identity_catalog_v2.json',encoding='utf-8'))
    ident=next(x for x in cat['identities'] if x['id']=='identity-10313')
    p=next(x for x in ident['passives'] if x.get('name')=='발파각쇄' and '정신력이 0 미만' not in x.get('effect',''))
    return compile_one(p, ident['id'], 0)


def test_target_no_sp_doubles_rupture_sinking_damage_modifier():
    rules, reasons, unsupported = _rules()
    base=[r for r in rules if r.source_text.startswith('대상의 파열과 침잠의 합')]
    assert len(base)==1
    extra=[r for r in rules if '정신력이 없는 대상이면' in r.source_text]
    assert len(extra)==1
    assert any(isinstance(c, Not) and isinstance(c.condition, TargetHasSP) for c in extra[0].conditions)
    assert any(isinstance(e, ModifyContext) and e.field=='dynamic_damage_bonus' for e in extra[0].effects)
    assert 'status_sum_damage_modifier_double_without_target_sp' in reasons
