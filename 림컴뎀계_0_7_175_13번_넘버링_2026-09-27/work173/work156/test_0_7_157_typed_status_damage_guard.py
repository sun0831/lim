from passive_compiler_v29 import compile_clause_template
from passive_runtime_v29_base import AttackTypeIs, ModifyContext
from passive_compiler_v29 import Clamp, BinaryValue, FloorValue, StatusField


def test_0_7_157_typed_status_damage_scaling_is_now_explicitly_typed_and_count_based():
    text='대상의 화상 횟수 3 당 타격 피해량 +10% (최대 30%)'
    rule, reasons, unsupported = compile_clause_template(text)
    assert rule is not None
    assert isinstance(rule.condition, AttackTypeIs)
    assert rule.condition.value == 'blunt'
    assert '화상_per_stack_capped' in reasons
    assert not unsupported
    effect = rule.effects[0]
    assert effect.field == 'dynamic_damage_bonus'
    assert isinstance(effect.amount, Clamp)
    assert isinstance(effect.amount.inner, BinaryValue)
    assert isinstance(effect.amount.inner.left, FloorValue)
    assert isinstance(effect.amount.inner.left.inner, BinaryValue)
    assert isinstance(effect.amount.inner.left.inner.left, StatusField)
    assert effect.amount.inner.left.inner.left.name == 'Burn'
    assert effect.amount.inner.left.inner.left.field == 'count'
    assert effect.amount.inner.left.inner.left.target == 'enemy'


def test_0_7_157_plain_damage_percent_remains_supported():
    text='출혈이 부여된 적 공격 시 피해량 +10 %'
    rule, reasons, unsupported = compile_clause_template(text)
    assert rule is not None
    assert 'damage_percent' in reasons
    assert not unsupported
