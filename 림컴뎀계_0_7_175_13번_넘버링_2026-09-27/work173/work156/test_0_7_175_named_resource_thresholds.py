import json
from passive_compiler_v29 import compile_passive_v29
from passive_runtime_v29_base import ResourceAtLeast, Not, And


def _passive():
    cat=json.load(open('identity_catalog_v2.json',encoding='utf8'))
    ident=next(x for x in cat['identities'] if x['id']=='identity-10913')
    return ident, next(x for x in ident['passives'] if x['name']=='정의의 마법소녀 / 절망의 기사' and '지키는 검이 3 이상' in x['effect'])


def test_named_resource_thresholds_compile():
    ident,p=_passive()
    c=compile_passive_v29(p, ident['id'])
    starts=[r for r in c.rules if '전투 시작 시 지키는 검' in r.source_text]
    assert len(starts)==2
    r3=next(r for r in starts if '3 이상' in r.source_text)
    r5=next(r for r in starts if '5일 경우' in r.source_text)
    assert any(isinstance(x, ResourceAtLeast) and x.name=='지키는 검' and x.value==3 for x in r3.conditions)
    assert any(isinstance(x, Not) and isinstance(x.condition, ResourceAtLeast) and x.condition.name=='지키는 검' and x.condition.value==5 for x in r3.conditions)
    assert any(isinstance(x, And) and any(isinstance(y, ResourceAtLeast) and y.name=='지키는 검' and y.value==5 for y in x.conditions) for x in r5.conditions)


def test_exact_named_resource_value_is_not_broader_than_exact_value():
    ident,p=_passive()
    c=compile_passive_v29(p, ident['id'])
    r5=next(r for r in c.rules if '지키는 검이 5일 경우' in r.source_text)
    exact=next(x for x in r5.conditions if isinstance(x, And))
    assert any(isinstance(x, Not) and isinstance(x.condition, ResourceAtLeast) and x.condition.value==6 for x in exact.conditions)
