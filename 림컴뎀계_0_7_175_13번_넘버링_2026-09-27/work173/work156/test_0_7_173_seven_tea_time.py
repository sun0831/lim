import json
from passive_compiler_v29 import compile_one
from passive_runtime_v29_base import AllySelectorTarget, TargetWeakToAttackType

def test_10206_support_damage_rule_merges_parent_and_numeric_continuation():
    d=json.load(open('identity_catalog_v2.json',encoding='utf8'))
    ident=next(x for x in d['identities'] if x['id']=='identity-10206')
    passive=next(p for p in ident['passives'] if p['type']=='서포트' and '내성 1.5 초과' in p['effect'])
    rules, _, unsupported=compile_one(passive,'identity-10206')
    assert not unsupported
    assert len(rules)==1
    r=rules[0]
    assert isinstance(r.target, AllySelectorTarget)
    assert r.target.policy=='speed_max'
    assert any(isinstance(c,TargetWeakToAttackType) and c.threshold==1.5 for c in r.conditions[0].conditions)
    eff=r.effects[0]
    assert eff.field=='dynamic_damage_bonus'
    assert 'Rupture' in repr(eff.amount)
