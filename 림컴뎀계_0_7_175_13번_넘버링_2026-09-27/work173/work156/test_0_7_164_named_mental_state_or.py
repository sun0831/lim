import json, sys
sys.path.insert(0, '.')
from passive_compiler_v29 import compile_passive_v29
from passive_runtime_v29_base import Or, HasStatus

def test_10813_morale_or_panic_is_conditioned():
    cat=json.load(open('identity_catalog_v2.json',encoding='utf-8'))
    ident=next(x for x in cat['identities'] if x['id']=='identity-10813')
    p=next(x for x in ident['passives'] if x['name']=='낱장치기')
    c=compile_passive_v29(p, ident['id'], 0)
    rules=[r for r in c.rules if '사기 저하 또는 패닉' in r.source_text]
    assert rules
    cond=rules[0].conditions[0]
    assert isinstance(cond, Or)
    assert any(isinstance(x, HasStatus) and x.name=='사기저하' and x.target=='enemy' for x in cond.conditions)
    assert any(isinstance(x, HasStatus) and x.name=='패닉' and x.target=='enemy' for x in cond.conditions)
