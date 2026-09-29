import json
from passive_compiler_v29 import compile_passive_v29

def test_reverse_named_status_conditions_for_10909():
    cat=json.load(open('identity_catalog_v2.json',encoding='utf-8'))
    ident=next(x for x in cat['identities'] if x['id']=='identity-10909')
    p=next(x for x in ident['passives'] if x['name']=='황금 시간 - 맞서기')
    r=compile_passive_v29({**p,'identity_id':ident['id']},ident['id'])
    assert len(r.rules) >= 2
    assert any('시간 유예를 보유한 대상' in x.source_text and any(type(c).__name__=='HasStatus' and c.name=='시간 유예' and c.target=='enemy' for c in x.conditions) for x in r.rules)
    assert any('시간 유예를 보유한 적' in x.source_text and any(type(c).__name__=='HasStatus' and c.name=='시간 유예' and c.target=='enemy' for c in x.conditions) for x in r.rules)

def test_reverse_named_status_does_not_capture_numeric_resources():
    cat=json.load(open('identity_catalog_v2.json',encoding='utf-8'))
    ident=next(x for x in cat['identities'] if x['id']=='identity-10909')
    r=compile_passive_v29({'identity_id':ident['id'],'name':'x','type':'전투','effect':'탄환을 보유한 대상에게 피해량 +10%'},ident['id'])
    assert not any(any(type(c).__name__=='HasStatus' and c.name=='탄환' for c in x.conditions) for x in r.rules)
