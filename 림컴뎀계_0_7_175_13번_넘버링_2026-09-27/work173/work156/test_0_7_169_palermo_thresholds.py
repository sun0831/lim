import json
from passive_compiler_v29 import compile_one
from passive_runtime_v29_base import CrossResourceStatusSumThreshold, BasicAttackSkillCondition

def _p():
    d=json.load(open('identity_catalog_v2.json',encoding='utf8'))['identities']
    return next(x for x in d if x['id']=='identity-10716')['passives'][3]

def test_palermo_threshold_child_effects_are_conditioned():
    rules,reasons,uns=compile_one(_p(),'identity-10716',3)
    by={r.source_text.strip().split('\n')[0]:r for r in rules}
    r1=next(r for r in rules if r.source_text.startswith('1 : 합 위력'))
    r2=next(r for r in rules if r.source_text.startswith('2 : 기본 스킬'))
    r4=next(r for r in rules if r.source_text.startswith('4 : 기본 스킬'))
    r5=next(r for r in rules if r.source_text.startswith('5 : 기본 스킬'))
    for r,n in ((r1,1),(r2,2),(r4,4),(r5,5)):
        assert any(isinstance(c,CrossResourceStatusSumThreshold) and c.value==n for c in r.conditions)
    assert any(isinstance(c,BasicAttackSkillCondition) for c in r2.conditions)
    assert any(isinstance(c,BasicAttackSkillCondition) for c in r4.conditions)
    assert any(isinstance(c,BasicAttackSkillCondition) for c in r5.conditions)
