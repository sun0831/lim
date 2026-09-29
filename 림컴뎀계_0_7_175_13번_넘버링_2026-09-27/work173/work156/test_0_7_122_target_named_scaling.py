from passive_compiler_v29 import parse_effects


def _resource_target(text):
    out = parse_effects(text)
    e = next(x.effect for x in out if x.reason == 'named_resource_damage_scaling')
    # Clamp(Floor(ResourceField(...)/per)*amount)
    return e.amount.inner.left.inner.left.target


def test_named_target_damage_scaling_reads_enemy_resource():
    assert _resource_target('대상의 잔향 1당 피해량 +1% (최대 20%)') == 'enemy'


def test_named_self_damage_scaling_keeps_self_resource():
    assert _resource_target('자신의 잔향 1당 피해량 +1% (최대 20%)') == 'self'
