from passive_compiler_v29 import compile_clause_template, StatusField
from passive_runtime_v29_base import AttackTypeIs, ModifyContext


def _compiled(text):
    rule, reasons, unsupported = compile_clause_template(text)
    assert rule is not None, (text, reasons, unsupported)
    return rule


def _status_field(effect):
    # Clamp(BinaryValue(FloorValue(BinaryValue(StatusField / per)) * pct), ...)
    return effect.amount.inner.left.inner.left


def test_burn_count_typed_blunt_damage_is_count_and_attack_type():
    r = _compiled('대상의 화상 횟수 3 당 타격 피해량 +10% (최대 30%)')
    assert isinstance(r.condition, AttackTypeIs) and r.condition.value == 'blunt'
    vals = [x for x in r.effects if isinstance(x, ModifyContext)]
    assert vals
    field = _status_field(vals[0])
    assert isinstance(field, StatusField)
    assert field.name == 'Burn' and field.field == 'count'


def test_burn_potency_typed_pierce_damage_uses_potency():
    r = _compiled('대상의 화상 위력 6 당 관통 피해량 +5% (최대 15%)')
    assert isinstance(r.condition, AttackTypeIs) and r.condition.value == 'pierce'
    field = _status_field(r.effects[0])
    assert field.name == 'Burn' and field.field == 'potency'


def test_untyped_status_damage_has_no_attack_type_gate():
    r = _compiled('대상의 화상 위력 6 당 피해량 +5% (최대 15%)')
    assert not isinstance(r.condition, AttackTypeIs)


def test_next_turn_typed_damage_up_is_not_gated_by_current_attack_type():
    r = _compiled('다음 턴에 타격 피해량 증가 1 얻음')
    assert not isinstance(r.condition, AttackTypeIs)
