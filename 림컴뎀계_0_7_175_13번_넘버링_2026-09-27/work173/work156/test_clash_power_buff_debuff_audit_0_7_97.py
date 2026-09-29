from types import SimpleNamespace
from status_effect_runtime_v1 import StatusEffectRuntime
from buff_debuff_runtime_v1 import BuffDebuffRuntime
from damage_modifier_runtime_v1 import DamageModifierRuntime

def state():
    return SimpleNamespace(runtime={})

def test_clash_power_maps_to_clash_channel_not_skill_power():
    st=state()
    StatusEffectRuntime.apply_catalog_effect(st,target_id='A',name='Clash Power Up',count=2)
    r=BuffDebuffRuntime.resolve(st,target_id='A')
    assert r['clash_power'] == 2
    assert r.get('skill_power', 0) == 0

def test_clash_power_down_is_negative_clash_channel():
    st=state()
    StatusEffectRuntime.apply_catalog_effect(st,target_id='A',name='Clash Power Down',potency=3)
    r=BuffDebuffRuntime.resolve(st,target_id='A')
    assert r['clash_power'] == -3
    assert r.get('skill_power', 0) == 0

def test_damage_modifier_does_not_treat_clash_power_as_damage_skill_power():
    st=state()
    StatusEffectRuntime.apply_catalog_effect(st,target_id='A',name='Clash Power Up',count=2)
    assert DamageModifierRuntime.resolve(st, SimpleNamespace(id='A'), SimpleNamespace(), SimpleNamespace(damage_type='slash'), False)['skill_power'] == 0
