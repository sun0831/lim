from passive_compiler_v29 import compile_passive_v29
from passive_runtime_v29_base import BasicAttackSkillCondition, ModifyContext


def _compile(text):
    return compile_passive_v29(
        {'effect': text, 'condition': '', 'type': '전투', 'name': 'cross-sum'},
        'identity-10716', 0,
    )


def test_10716_cross_resource_status_sum_is_conditional_basic_skill_damage():
    text = (
        '자신의 완성되어가는 교본과 메인 타겟 적의 결투 고조 수치 합에 따라 다음 효과 전부 얻음\n'
        '- 수치 1당, 기본 스킬로 가하는 피해량 +3% (최대 15%)'
    )
    rules = _compile(text).rules
    assert len(rules) == 1
    rule = rules[0]
    assert rule.conditions == [BasicAttackSkillCondition()]
    effect = rule.effects[0]
    assert isinstance(effect, ModifyContext)
    assert effect.field == 'dynamic_damage_bonus'
    assert effect.amount.hi == 0.15
    assert effect.amount.inner.left.inner.left.name == '완성되어가는 교본'
    assert effect.amount.inner.left.inner.right.name == '결투 고조'


def test_10716_cross_sum_caps_at_15_percent():
    text = (
        '자신의 완성되어가는 교본과 메인 타겟 적의 결투 고조 수치 합에 따라 다음 효과 전부 얻음\n'
        '- 수치 1당, 기본 스킬로 가하는 피해량 +3% (최대 15%)'
    )
    rule = _compile(text).rules[0]
    assert rule.effects[0].amount.hi == 0.15
