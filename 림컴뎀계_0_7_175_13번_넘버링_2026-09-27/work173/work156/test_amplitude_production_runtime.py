from limbus_damage_engine_v29 import BattleState, EnemyState, FighterState, Status
from passive_compiler_v29 import compile_one
from passive_runtime_v29_base import PassiveRuntime, PassiveTrigger, PassiveEvent
from amplitude_runtime_v1 import AmplitudeRuntime


def _state():
    enemy = EnemyState(100, 100, statuses={'Tremor': Status(potency=20, count=5)})
    state = BattleState(enemy=enemy, fighters={'i': FighterState()}, runtime={})
    return state, enemy


def test_amplitude_presence_modifier_runs_on_real_passive_runtime_path():
    state, enemy = _state()
    AmplitudeRuntime().set_state(state, enemy, '붕괴', 'conversion', owner_id='i')
    rules, _, unsupported = compile_one({'id': 's', 'name': 'skill', 'effect': '대상이 진폭 변환이나 진폭 얽힘 상태면, 이 코인 피해량 +48%'}, 'i', 0)
    assert not unsupported and len(rules) == 1
    rule = rules[0]
    assert rule.trigger == PassiveTrigger.COIN_START

    rt = PassiveRuntime()
    rt.register(rule)
    ctx = {'target': enemy, 'skill': object()}
    rt.emit(PassiveTrigger.COIN_START, ctx, state)
    assert abs(float(ctx.get('dynamic_damage_bonus', 0.0)) - 0.48) < 1e-9


def test_amplitude_presence_modifier_does_not_fire_without_amplitude_status():
    state, enemy = _state()
    rules, _, unsupported = compile_one({'id': 's', 'name': 'skill', 'effect': '대상이 진폭 변환이나 진폭 얽힘 상태면, 이 코인 피해량 +60%'}, 'i', 0)
    assert not unsupported and len(rules) == 1
    rt = PassiveRuntime()
    rt.register(rules[0])
    ctx = {'target': enemy, 'skill': object()}
    rt.emit(PassiveTrigger.COIN_START, ctx, state)
    assert float(ctx.get('dynamic_damage_bonus', 0.0)) == 0.0


def test_amplitude_conversion_then_modifier_uses_same_target_status():
    state, enemy = _state()
    conversion_rules, _, unsupported = compile_one({'id': 's', 'name': 'skill', 'effect': '[적중시] 진동 - 붕괴로 진폭 변환'}, 'i', 0)
    modifier_rules, _, unsupported2 = compile_one({'id': 's2', 'name': 'skill', 'effect': '대상이 진폭 변환이나 진폭 얽힘 상태면, 피해량 +30%'}, 'i', 1)
    assert not unsupported and not unsupported2

    rt = PassiveRuntime()
    rt.register(conversion_rules[0])
    rt.register(modifier_rules[0])
    ctx = {'target': enemy, 'skill': object()}
    rt.emit(PassiveTrigger.HIT, ctx, state)
    assert AmplitudeRuntime().has_state(enemy, '붕괴', 'conversion')

    ctx2 = {'target': enemy, 'skill': object()}
    rt.emit(PassiveTrigger.COIN_START, ctx2, state)
    assert abs(float(ctx2.get('dynamic_damage_bonus', 0.0)) - 0.30) < 1e-9
