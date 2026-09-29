import json
from passive_compiler_v29 import compile_passive_v29


def _get(identity_id, idx):
    D=json.load(open('identity_catalog_v2.json',encoding='utf-8'))
    i=next(x for x in D['identities'] if x['id']==identity_id)
    return compile_passive_v29(i['passives'][idx], identity_id, idx)


def test_10707_support_lost_hp_keeps_parent_pierce_scope():
    c=_get('identity-10707',2)
    assert c.rules
    r=c.rules[0]
    assert any(type(x).__name__=='AttackTypeIs' and getattr(x,'value',None)=='pierce' for x in r.conditions[0].conditions)
    assert any(e.field=='dynamic_damage_bonus' for e in r.effects)


def test_10707_second_support_variant_also_keeps_pierce_scope():
    c=_get('identity-10707',3)
    assert c.rules
    r=c.rules[0]
    assert any(type(x).__name__=='AttackTypeIs' and getattr(x,'value',None)=='pierce' for x in r.conditions[0].conditions)
