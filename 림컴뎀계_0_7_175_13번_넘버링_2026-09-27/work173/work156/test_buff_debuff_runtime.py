"""병합 테스트: buff_debuff_runtime

원본 파일 (내용은 AST 병합기로 합쳤고 테스트 본문은 바꾸지 않음):
  - test_v113_buff_debuff_runtime.py
  - test_v118_buff_debuff_damage_integration.py
  - test_v119_buff_debuff_timing.py
  - test_v120_buff_debuff_aggregation.py
  - test_v121_buff_debuff_lifecycle.py
  - test_v122_buff_debuff_event_bridge.py
이름 충돌 helper 는 `이름__vNN` 으로 분리했다. 매핑은 tools/MERGE_MAP.json 참고.
"""
from limbus_damage_engine_v29 import BattleState, EnemyState, FighterState, DamageEngine
from buff_debuff_runtime_v1 import BuffDebuffRuntime
from effect_runtime_v1 import EffectRuntime
from effect_executor_v1 import EffectExecutor
from rule_ir_v1 import EffectIR, ConditionIR
from condition_runtime_v1 import ConditionRuntime
from one_turn_solver_v29 import IdentityData, SkillData, CoinData
from damage_modifier_runtime_v1 import DamageModifierRuntime
from types import SimpleNamespace
from buff_debuff_event_bridge_v1 import BuffDebuffEventBridge



# ======================================================================
# 원본: test_v113_buff_debuff_runtime.py
# ======================================================================

def state():
    return BattleState(enemy=EnemyState(hp=100,max_hp=100), fighters={"A": FighterState()})

def test_buff_debuff_lifecycle_and_branch_clone():
    s=state(); BuffDebuffRuntime.apply(s,target_id="A",name="Power",kind="buff",potency=2,duration=2)
    assert BuffDebuffRuntime.has(s,target_id="A",name="Power",kind="buff")
    branch=s.clone(); BuffDebuffRuntime.remove(branch,target_id="A",name="Power",kind="buff")
    assert BuffDebuffRuntime.has(s,target_id="A",name="Power",kind="buff")
    assert not BuffDebuffRuntime.has(branch,target_id="A",name="Power",kind="buff")
    assert BuffDebuffRuntime.end_turn(s)==[]
    assert BuffDebuffRuntime.has(s,target_id="A",name="Power",kind="buff")
    expired=BuffDebuffRuntime.end_turn(s); assert len(expired)==1
    assert not BuffDebuffRuntime.has(s,target_id="A",name="Power",kind="buff")

def test_effect_and_condition_common_runtime():
    s=state(); er=EffectRuntime(); ex=EffectExecutor()
    cmd=er.resolve(EffectIR(kind="buff_apply",params={"target_id":"A","name":"Guard","potency":1,"duration":1}),rule_id="r1")
    result=ex.execute(cmd,{"state":s,"identity_id":"A"})
    assert result["applied"]
    ctx={"state":s,"identity_id":"A","buff_debuff_runtime":BuffDebuffRuntime}
    assert ConditionRuntime.evaluate(ConditionIR(op="has_buff",args={"value":"Guard"}),ctx)


# ======================================================================
# 원본: test_v118_buff_debuff_damage_integration.py
# ======================================================================

def _case():
    state = BattleState(enemy=EnemyState(1000, 1000), fighters={"a": FighterState()})
    ident = IdentityData("a", "A", 0, {})
    skill = SkillData("s", "S", 10, [CoinData(0, "slash", "pride")], "slash", "pride")
    return state, ident, skill, skill.coins[0]

def test_buff_damage_percent_flows_into_damage_engine():
    base_state, ident, skill, coin = _case()
    base = DamageEngine().calculate_coin_damage(base_state, ident, skill, coin, "H", False, coin_index=0)[0]
    BuffDebuffRuntime.apply(base_state, target_id="a", name="Power Up", kind="buff",
                            modifiers={"damage_percent": 0.20})
    boosted = DamageEngine().calculate_coin_damage(base_state, ident, skill, coin, "H", False, coin_index=0)[0]
    assert boosted > base
    assert DamageModifierRuntime.resolve(base_state, ident, skill, coin, False)["damage_percent"] >= 0.20

def test_buff_power_modifiers_change_skill_and_coin_power():
    state, ident, skill, coin = _case()
    BuffDebuffRuntime.apply(state, target_id="a", name="Skill Power", kind="buff",
                            modifiers={"skill_power": 2})
    BuffDebuffRuntime.apply(state, target_id="a", name="Coin Power", kind="buff",
                            modifiers={"coin_power": 3})
    roll = DamageEngine().coin_roll(state, ident, skill, coin, "H", prior_heads=0)
    assert roll == 15

def test_enemy_vulnerability_and_defense_debuff_flow_through_common_runtime():
    state, ident, skill, coin = _case()
    base = DamageEngine().calculate_coin_damage(state, ident, skill, coin, "H", False, coin_index=0)[0]
    BuffDebuffRuntime.apply(state, target_id="enemy", name="Vulnerable", kind="debuff",
                            modifiers={"vulnerability": 0.20})
    vulnerable = DamageEngine().calculate_coin_damage(state, ident, skill, coin, "H", False, coin_index=0)[0]
    assert vulnerable > base
    BuffDebuffRuntime.apply(state, target_id="enemy", name="Defense Down", kind="debuff",
                            modifiers={"defense_level_down": 5})
    assert DamageModifierRuntime.resolve(state, ident, skill, coin, False)["defense_level_bonus"] == -5


# ======================================================================
# 원본: test_v119_buff_debuff_timing.py
# ======================================================================

def _case__v119_buff():
    s = BattleState(enemy=EnemyState(1000, 1000), fighters={'a': FighterState()})
    i = IdentityData('a', 'A', 0, {})
    sk = SkillData('s', 'S', 10, [CoinData(0, 'slash', 'pride')], 'slash', 'pride')
    return (s, i, sk, sk.coins[0])

def test_timing_filters_before_coin_vs_damage():
    s, i, sk, c = _case__v119_buff()
    BuffDebuffRuntime.apply(s, target_id='a', name='Power', modifiers={'skill_power': 2}, timing='before_coin')
    BuffDebuffRuntime.apply(s, target_id='a', name='Damage', modifiers={'damage_percent': 0.25}, timing='damage')
    before = DamageModifierRuntime.resolve(s, i, sk, c, False, timing='before_coin')
    damage = DamageModifierRuntime.resolve(s, i, sk, c, False, timing='damage')
    assert before['skill_power'] == 2 and before['damage_percent'] == 0
    assert damage['damage_percent'] == 0.25 and damage['skill_power'] == 0

def test_timing_condition_uses_current_coin_context():
    s, i, sk, c = _case__v119_buff()
    BuffDebuffRuntime.apply(s, target_id='a', name='SecondCoin', modifiers={'damage_percent': 0.3}, timing='damage', conditions={'coin_index_gte': 1})
    first = DamageModifierRuntime.resolve(s, i, sk, c, False, timing='damage', context={'coin_index': 0})
    second = DamageModifierRuntime.resolve(s, i, sk, c, False, timing='damage', context={'coin_index': 1})
    assert first['damage_percent'] == 0
    assert second['damage_percent'] == 0.3


# ======================================================================
# 원본: test_v120_buff_debuff_aggregation.py
# ======================================================================

def test_default_modifier_stacking_is_additive_and_item_stack_modes_are_explicit():
    s = state()
    BuffDebuffRuntime.apply(s, target_id="A", name="Power", potency=2, modifiers={"damage_percent": .10})
    BuffDebuffRuntime.apply(s, target_id="A", name="Power", potency=3, modifiers={"damage_percent": .20}, stack_mode="add")
    assert BuffDebuffRuntime.snapshot(s, target_id="A")["buff:Power"]["potency"] == 5
    assert abs(BuffDebuffRuntime.resolve(s, target_id="A")["damage_percent"] - .30) < 1e-9

def test_modifier_max_min_and_replace_priority_are_deterministic():
    s = state()
    BuffDebuffRuntime.apply(s, target_id="A", name="MaxA", modifiers={"damage_percent": .10}, modifier_policy={"damage_percent": "max"})
    BuffDebuffRuntime.apply(s, target_id="A", name="MaxB", modifiers={"damage_percent": .30}, modifier_policy={"damage_percent": "max"})
    assert abs(BuffDebuffRuntime.resolve(s, target_id="A")["damage_percent"] - .30) < 1e-9

    s = state()
    BuffDebuffRuntime.apply(s, target_id="A", name="ReplaceLow", modifiers={"skill_power": 2}, priority=1, modifier_policy={"skill_power": "replace"})
    BuffDebuffRuntime.apply(s, target_id="A", name="ReplaceHigh", modifiers={"skill_power": 5}, priority=2, modifier_policy={"skill_power": "replace"})
    BuffDebuffRuntime.apply(s, target_id="A", name="ReplaceIgnored", modifiers={"skill_power": 9}, priority=1, modifier_policy={"skill_power": "replace"})
    assert BuffDebuffRuntime.resolve(s, target_id="A")["skill_power"] == 5

def test_multiplicative_scale_is_opt_in_and_default_remains_additive():
    s = state()
    BuffDebuffRuntime.apply(s, target_id="A", name="M1", modifiers={"damage_percent": .20}, modifier_policy={"damage_percent": "multiply_scale"})
    BuffDebuffRuntime.apply(s, target_id="A", name="M2", modifiers={"damage_percent": .30}, modifier_policy={"damage_percent": "multiply_scale"})
    # (1.20 * 1.30) - 1 = 0.56
    assert abs(BuffDebuffRuntime.resolve(s, target_id="A")["damage_percent"] - .56) < 1e-9


# ======================================================================
# 원본: test_v121_buff_debuff_lifecycle.py
# ======================================================================

def state__v121_buff():
    return SimpleNamespace(runtime={}, event_log=[], fighters={}, enemy=SimpleNamespace(staggered=False, hp=100, max_hp=100))

def test_event_consumption_is_opt_in_and_count_based():
    s = state__v121_buff()
    BuffDebuffRuntime.apply(s, target_id='A', name='NextHit', count=2, consume_on='after_coin')
    rec = BuffDebuffRuntime.consume_on_event(s, event='after_coin', target_id='A')
    assert rec[0]['after'] == 1
    assert BuffDebuffRuntime.snapshot(s, target_id='A')['buff:NextHit']['count'] == 1
    BuffDebuffRuntime.consume_on_event(s, event='after_skill', target_id='A')
    assert BuffDebuffRuntime.snapshot(s, target_id='A')['buff:NextHit']['count'] == 1
    rec = BuffDebuffRuntime.consume_on_event(s, event='after_coin', target_id='A')
    assert rec[0]['after'] == 0
    assert not BuffDebuffRuntime.has(s, target_id='A', name='NextHit')

def test_effect_executor_preserves_consume_on_declaration():
    s = state__v121_buff()
    er = EffectRuntime()
    ex = EffectExecutor()
    cmd = er.resolve(EffectIR(kind='buff_apply', params={'target_id': 'A', 'name': 'Guard', 'count': 1, 'consume_on': 'after_skill'}), rule_id='r1')
    result = ex.execute(cmd, {'state': s, 'identity_id': 'A'})
    assert result['applied'] is True
    assert BuffDebuffRuntime.snapshot(s, target_id='A')['buff:Guard']['consume_on'] == 'after_skill'


# ======================================================================
# 원본: test_v122_buff_debuff_event_bridge.py
# ======================================================================

def state__v122_buff():
    return SimpleNamespace(runtime={}, event_log=[], fighters={}, enemy=SimpleNamespace(staggered=False, hp=100, max_hp=100))

def test_bridge_consumes_same_lifecycle_contract():
    s = state__v122_buff()
    BuffDebuffRuntime.apply(s, target_id='A', name='NextHit', count=1, consume_on='after_coin')
    out = BuffDebuffEventBridge.dispatch(s, event='after_coin', target_id='A', context={'coin_index': 1})
    assert out['count'] == 1
    assert not BuffDebuffRuntime.has(s, target_id='A', name='NextHit')
    assert any((x.get('event') == 'buff_debuff_consumed' for x in s.event_log))

def test_bridge_turn_end_records_expiry():
    s = state__v122_buff()
    BuffDebuffRuntime.apply(s, target_id='A', name='OneTurn', duration=1)
    out = BuffDebuffEventBridge.end_turn(s)
    assert out['count'] == 1
    assert not BuffDebuffRuntime.has(s, target_id='A', name='OneTurn')
    assert any((x.get('event') == 'buff_debuff_expired' for x in s.event_log))
