"""Safely merged test file (AST-aware, whole-file rename incl. call sites, decorators preserved via line-removal import stripping).
Originals: test_actual_speed_charge_scaling_audit_0_7_101.py, test_charge_potency_passive_runtime.py, test_charge_potency_shield_runtime.py, test_tremor_burst_actor_rank.py, test_tremor_burst_charge_to_rupture.py, test_tremor_burst_count_runtime.py, test_tremor_burst_extra_high_point.py, test_tremor_burst_extra_toggle.py, test_tremor_burst_flower_resource.py, test_tremor_burst_followup_runtime.py, test_tremor_burst_no_implicit_count_v1.py, test_tremor_burst_secondary_damage.py
"""
from __future__ import annotations

from passive_compiler_v29 import compile_passive_v29
from passive_runtime_v29_base import PassiveRuntime, PassiveTrigger
from limbus_damage_engine_v29 import BattleState, FighterState, EnemyState
from passive_runtime_v29_base import PassiveRuntime, PassiveTrigger, PassiveEvent
from passive_compiler_v29 import compile_clause_template
from passive_runtime_v29_base import PassiveTrigger, PassiveRuntime, PassiveDefinition, Always, ModifyBurstContext
from limbus_damage_engine_v29 import DamageEngine, EnemyState, FighterState, BattleState, Status
from passive_runtime_v29_base import PassiveTrigger, PassiveRuntime, PassiveDefinition, Always, SelfTarget, EventTarget, ConsumeChargeUpTo, AddStatus
from passive_runtime_v29_base import PassiveTrigger, PassiveRuntime, PassiveDefinition, Always, SelfTarget
from passive_runtime_v29_base import PassiveTrigger, PassiveRuntime, PassiveDefinition, SelfTarget
from limbus_damage_engine_v29 import FighterState, EnemyState, BattleState
from passive_runtime_v29_base import PassiveRuntime, PassiveDefinition, PassiveTrigger, Always, SelfTarget
from passive_compiler_v29 import compile_one
from limbus_damage_engine_v29 import DamageEngine
from passive_runtime_v29_base import PassiveTrigger
from passive_runtime_v29_base import PassiveTrigger, PassiveRuntime, PassiveDefinition, Always, SelfTarget, AddBurstSecondaryDamage, Const


# ---- merged from test_actual_speed_charge_scaling_audit_0_7_101.py ----

def _state(speed=10, enemy_speed=5, charge=0):
    return BattleState(fighters={'identity-10116': FighterState(speed=speed, charge=0, charge_potency=charge, hp=100, max_hp=100)}, enemy=EnemyState(hp=1000, max_hp=1000, speed=enemy_speed, defense_level_bonus=0))

def _run(text, speed=10, enemy_speed=5, charge=0):
    record={'id':'p','name':'audit','effect':text}
    rules=list(compile_passive_v29(record,'identity-10116',0).rules); assert rules
    rule=rules[0]; st=_state(speed,enemy_speed,charge); ctx={'state':st,'target':st.enemy}
    rt=PassiveRuntime(); rt.register(rule); rt.emit(PassiveTrigger.COIN_START,ctx,st); return ctx

def test_charge_scaling_uses_declared_cap_not_coefficient():
    ctx=_run('자신의 속도가 대상보다 빠르면, (대상과의 속도 차이 × 자신의 충전 위력)%만큼 피해량이 증가 (최대 20%)', speed=10, enemy_speed=5, charge=25)
    assert abs(ctx['dynamic_damage_bonus']-0.20)<1e-9


# ---- merged from test_charge_potency_passive_runtime.py ----


def _state__test_charge_potency_passive_runtime():
    return BattleState(
        fighters={'identity-10116': FighterState(speed=10, charge_potency=3, hp=100, max_hp=100),
                  'identity-10713': FighterState(speed=5, charge_potency=4, hp=100, max_hp=100)},
        enemy=EnemyState(hp=1000, max_hp=1000, speed=5, defense_level_bonus=0),
    )


def _rules(record, owner):
    return list(compile_passive_v29(record, owner, 0).rules)


def test_10116_speed_difference_uses_charge_potency():
    record={'id':'p','name':'speed','effect':'자신의 속도가 대상보다 빠르면, (대상과의 속도 차이 × 자신의 충전 위력)%만큼 피해량이 증가 (최대 20%)'}
    rule=_rules(record, 'identity-10116')[0]
    assert rule.trigger == PassiveTrigger.COIN_START
    st=_state__test_charge_potency_passive_runtime(); rt=PassiveRuntime(); rt.register(rule)
    ctx={'state':st, 'target':st.enemy}
    rt.emit(PassiveTrigger.COIN_START, ctx, st)
    assert abs(ctx['dynamic_damage_bonus'] - 0.15) < 1e-9


def test_10713_turn_start_defense_level_uses_charge_potency():
    record={'id':'p','name':'def','effect':'턴 시작시, 자신의 충전 위력만큼 방어 레벨 증가 얻음 (최대 6)'}
    rule=_rules(record, 'identity-10713')[0]
    assert rule.trigger == PassiveTrigger.TURN_START
    st=_state__test_charge_potency_passive_runtime(); rt=PassiveRuntime(); rt.register(rule)
    rt.emit(PassiveTrigger.TURN_START, {'state':st}, st)
    assert st.fighters['identity-10713'].defense_level_bonus == 4


def test_10116_turn_end_haste_is_queued_to_next_turn_state():
    record={'id':'p','name':'haste','effect':'턴 종료 시, (자신의 충전 위력 / 2)만큼 다음 턴에 신속 얻음 (최대 2, 소수점 버림)'}
    rule=_rules(record, 'identity-10116')[0]
    assert rule.trigger == PassiveTrigger.TURN_END
    st=_state__test_charge_potency_passive_runtime(); st.fighters['identity-10116'].charge_potency=5
    rt=PassiveRuntime(); rt.register(rule)
    rt.emit(PassiveTrigger.TURN_END, {'state':st}, st)
    assert st.fighters['identity-10116'].statuses.get('Haste') is None
    assert st.runtime['next_turn_state']['fighters']['identity-10116']['statuses']['Haste']['count'] == 2


# ---- merged from test_charge_potency_shield_runtime.py ----

def test_charge_potency_start_shield():
    rec={'id':'p','name':'shield','effect':'전투 시작시 자신의 체력이 50% 미만이면, (충전 위력 x 5)만큼 보호막 얻음 (최대 25)'}
    rule=compile_passive_v29(rec,'identity-10713',0).rules[0]
    assert rule.trigger == PassiveTrigger.COMBAT_START
    st=BattleState(fighters={'identity-10713':FighterState(hp=40,max_hp=100,charge_potency=4)}, enemy=EnemyState(hp=100,max_hp=100))
    rt=PassiveRuntime(); rt.register(rule); rt.emit(PassiveTrigger.COMBAT_START,{'state':st},st)
    assert st.fighters['identity-10713'].shield == 20

def test_charge_potency_start_shield_cap():
    rec={'id':'p','name':'shield','effect':'전투 시작시 자신의 체력이 50% 미만이면, (충전 위력 x 5)만큼 보호막 얻음 (최대 25)'}
    rule=compile_passive_v29(rec,'identity-10713',0).rules[0]
    st=BattleState(fighters={'identity-10713':FighterState(hp=40,max_hp=100,charge_potency=8)}, enemy=EnemyState(hp=100,max_hp=100))
    rt=PassiveRuntime(); rt.register(rule); rt.emit(PassiveTrigger.COMBAT_START,{'state':st},st)
    assert st.fighters['identity-10713'].shield == 25

def test_charge_potency_before_hit_shield_is_capped_and_limited():
    rec={'id':'p','name':'shield','effect':'피격 직전, (자신의 충전 위력)만큼 보호막 얻음 (최대 5, 턴 당 최대 3회)'}
    rule=compile_passive_v29(rec,'identity-10713',0).rules[0]
    assert rule.trigger == PassiveTrigger.COIN_HIT
    assert rule.max_activations == 3
    st=BattleState(fighters={'identity-10713':FighterState(hp=100,max_hp=100,charge_potency=8)}, enemy=EnemyState(hp=100,max_hp=100))
    rt=PassiveRuntime(); rt.register(rule)
    for _ in range(3): rt.emit(PassiveTrigger.COIN_HIT,{'state':st,'target':st.enemy},st)
    assert st.fighters['identity-10713'].shield == 15


# ---- merged from test_tremor_burst_actor_rank.py ----


def test_slowest_ally_burst_modifier_is_actor_scoped():
    text='속도가 가장 느린 아군 1명이 진동 폭발로 입히는 흐트러짐 피해량 +20%'
    rule, reasons, unsupported = compile_clause_template(text)
    assert not unsupported
    assert rule.trigger == PassiveTrigger.TREMOR_BURST
    assert any(isinstance(e, ModifyBurstContext) for e in rule.effects)


def test_slowest_ally_only_gets_burst_bonus():
    e=DamageEngine()
    enemy=EnemyState(100,100,stagger_thresholds=[70],statuses={'Tremor':Status(potency=10,count=2)})
    slow=FighterState('slow',45,45); fast=FighterState('fast',45,45)
    slow.speed=10; fast.speed=20
    state=BattleState(enemy=enemy,fighters={'slow':slow,'fast':fast},runtime={})
    pr=PassiveRuntime(); e.passive_runtime=pr
    rule,_,_=compile_clause_template('속도가 가장 느린 아군 1명이 진동 폭발로 입히는 흐트러짐 피해량 +20%')
    pr.register(PassiveDefinition('p','p','passive_owner',rule.trigger,[rule.condition],__import__('passive_runtime_v29_base').SelfTarget(),list(rule.effects)))
    # Passive owner is deliberately neither slow nor fast: only event actor rank
    # should determine activation.
    state.fighters['passive_owner']=FighterState('passive_owner',45,45)
    state.fighters['passive_owner'].speed=15
    e.apply_effect(state,'fast','enemy',{'type':'tremor_burst','name':'Tremor','count_cost':1})
    assert enemy.stagger_thresholds == [80]
    e.apply_effect(state,'slow','enemy',{'type':'tremor_burst','name':'Tremor','count_cost':1})
    assert enemy.stagger_thresholds == [92]


# ---- merged from test_tremor_burst_charge_to_rupture.py ----

def test_burst_charge_cap_converts_actual_consumed_amount_to_rupture_count():
    t, reasons, unsupported = compile_clause_template('진동 폭발. 진동 폭발 시 진동 횟수가 2 감소하고, 충전 횟수를 최대 4 소모하여 소모한 충전 횟수만큼 파열 횟수 증가')
    assert not unsupported
    assert any(isinstance(e, ConsumeChargeUpTo) for e in t.effects)
    assert any(isinstance(e, AddStatus) and r=='tremor_burst_rupture_count_from_charge' for e,r in zip(t.effects,reasons))

def test_charge_to_rupture_uses_partial_available_charge():
    e=DamageEngine(); enemy=EnemyState(100,100,statuses={'Tremor':Status(potency=10,count=2)})
    f=FighterState('i',45,45); f.charge=2
    state=BattleState(enemy=enemy,fighters={'i':f},runtime={}); state.runtime['damage_engine']=e
    t,_,_=compile_clause_template('진동 폭발 시 충전 횟수를 최대 4 소모하여 소모한 충전 횟수만큼 파열 횟수 증가')
    pr=PassiveRuntime(); e.passive_runtime=pr
    pr.register(PassiveDefinition('p','p','i',PassiveTrigger.TREMOR_BURST,[Always()],EventTarget('target'),t.effects))
    e.apply_effect(state,'i','enemy',{'type':'tremor_burst','name':'Tremor'})
    assert f.charge==0
    assert enemy.statuses['Rupture'].count==2


def test_explicit_burst_count_cost_two_is_not_double_burst():
    from passive_runtime_v29_base import TriggerTremorBurst
    t, _, unsupported = compile_clause_template('진동 폭발. 진동 폭발 시 진동 횟수가 2 감소')
    assert not unsupported
    burst = next(e for e in t.effects if isinstance(e, TriggerTremorBurst))
    assert burst.count == 1
    assert burst.count_cost == 2


# ---- merged from test_tremor_burst_count_runtime.py ----


def test_tremor_burst_count_passive_compiles_to_next_turn_damage_up():
    text='턴 종료 시 이번 턴에 자신이 진동 폭발을 시킨 횟수만큼 다음 턴에 피해량 증가를 얻음 (최대 3)'
    rule, reasons, unsupported = compile_clause_template(text)
    assert not unsupported
    assert rule.trigger == PassiveTrigger.TURN_END
    assert rule.effects[0].name == 'Damage Up'
    assert rule.effects[0].potency.resolve(None, type('S', (), {'runtime': {'tremor_burst_counts': {'i': 2}}})(), 'i') == 20
    assert rule.deferred_turns == 0


def test_tremor_burst_count_tracks_per_source_identity():
    e=DamageEngine()
    enemy=EnemyState(100,100,stagger_thresholds=[70],statuses={'Tremor':Status(potency=10,count=5)})
    a=FighterState('a',45,45); b=FighterState('b',45,45)
    state=BattleState(enemy=enemy,fighters={'a':a,'b':b},runtime={})
    e.apply_effect(state,'a','enemy',{'type':'tremor_burst','name':'Tremor','count_cost':1})
    e.apply_effect(state,'b','enemy',{'type':'tremor_burst','name':'Tremor','count_cost':1})
    e.apply_effect(state,'a','enemy',{'type':'tremor_burst','name':'Tremor','count_cost':1})
    assert state.runtime['tremor_burst_counts'] == {'a':2,'b':1}


def test_tremor_burst_count_max_three_next_turn():
    text='턴 종료 시 이번 턴에 자신이 진동 폭발을 시킨 횟수만큼 다음 턴에 피해량 증가를 얻음 (최대 3)'
    rule, _, unsupported = compile_clause_template(text)
    assert not unsupported
    f=FighterState('i',45,45); state=BattleState(enemy=EnemyState(100,100),fighters={'i':f},runtime={'tremor_burst_counts':{'i':5}})
    pr=PassiveRuntime(); pr.register(PassiveDefinition('p','p','i',PassiveTrigger.TURN_END,[Always()],SelfTarget(),list(rule.effects)))
    pr.emit(PassiveTrigger.TURN_END, {'state':state}, state)
    assert state.runtime['next_turn_state']['fighters']['i']['statuses']['Damage Up']['potency'] == 30


# ---- merged from test_tremor_burst_extra_high_point.py ----


def test_extra_burst_clause_is_conditional_not_unconditional_burst():
    text='편성 순서 1번인 아군의 스킬, 코인 효과로 진동 폭발 시 25% 확률로 진동 폭발이 1회 추가로 발동 (턴 당 1회)'
    rule, reasons, unsupported = compile_clause_template(text)
    assert not unsupported
    assert rule.trigger == PassiveTrigger.TREMOR_BURST
    assert rule.max_activations == 1
    assert 'tremor_burst_extra_high_point:25%' in reasons
    assert type(rule.effects[0]).__name__ == 'TriggerTremorBurst'
    assert type(rule.condition).__name__ == 'RosterPositionCondition'


def test_extra_burst_high_point_fires_once_for_first_roster_owner_without_recursive_loop():
    e=DamageEngine()
    enemy=EnemyState(100,100,stagger_thresholds=[70],statuses={'Tremor':Status(potency=10,count=5)})
    a=FighterState('a',45,45); b=FighterState('b',45,45)
    state=BattleState(enemy=enemy,fighters={'a':a,'b':b},runtime={'roster_order':['a','b']})
    pr=PassiveRuntime(); e.passive_runtime=pr; state.runtime['damage_engine']=e
    rule,_,_=compile_clause_template('편성 순서 1번인 아군의 스킬, 코인 효과로 진동 폭발 시 25% 확률로 진동 폭발이 1회 추가로 발동 (턴 당 1회)')
    pr.register(PassiveDefinition('extra','extra','a',rule.trigger,[rule.condition],SelfTarget(),list(rule.effects),max_activations=rule.max_activations))
    e.apply_effect(state,'a','enemy',{'type':'tremor_burst','name':'Tremor','count_cost':1})
    # Initial burst + one high-point additional burst. The nested burst must not
    # recursively invoke the same passive, and the turn cap prevents a second.
    assert state.runtime['tremor_burst_counts']['a'] == 2
    assert enemy.statuses['Tremor'].count == 3
    assert sum(1 for x in state.event_log if x.get('event')=='tremor_burst') == 2
    assert pr.passives[0].activations == 1


def test_extra_burst_does_not_fire_for_non_first_roster_owner():
    e=DamageEngine(); enemy=EnemyState(100,100,stagger_thresholds=[70],statuses={'Tremor':Status(potency=10,count=3)})
    a=FighterState('a',45,45); b=FighterState('b',45,45)
    state=BattleState(enemy=enemy,fighters={'a':a,'b':b},runtime={'roster_order':['a','b']})
    pr=PassiveRuntime(); e.passive_runtime=pr; state.runtime['damage_engine']=e
    rule,_,_=compile_clause_template('편성 순서 1번인 아군의 스킬, 코인 효과로 진동 폭발 시 25% 확률로 진동 폭발이 1회 추가로 발동 (턴 당 1회)')
    pr.register(PassiveDefinition('extra','extra','b',rule.trigger,[rule.condition],SelfTarget(),list(rule.effects),max_activations=rule.max_activations))
    e.apply_effect(state,'b','enemy',{'type':'tremor_burst','name':'Tremor','count_cost':1})
    assert state.runtime['tremor_burst_counts']['b'] == 1
    assert enemy.statuses['Tremor'].count == 2


# ---- merged from test_tremor_burst_extra_toggle.py ----

TEXT='편성 순서 1번인 아군의 스킬, 코인 효과로 진동 폭발 시 25% 확률로 진동 폭발이 1회 추가로 발동 (턴 당 1회)'

def make_state(enabled):
    e=DamageEngine()
    enemy=EnemyState(100,100,stagger_thresholds=[70],statuses={'Tremor':Status(potency=10,count=5)})
    a=FighterState('a',45,45); b=FighterState('b',45,45)
    state=BattleState(enemy=enemy,fighters={'a':a,'b':b},runtime={'roster_order':['a','b'], 'calculation_options': {'enable_extra_tremor_burst': enabled}})
    pr=PassiveRuntime(); e.passive_runtime=pr; state.runtime['damage_engine']=e
    rule,_,_=compile_clause_template(TEXT)
    pr.register(PassiveDefinition('extra','extra','a',rule.trigger,[rule.condition],SelfTarget(),list(rule.effects),max_activations=rule.max_activations))
    return e,state,pr

def test_extra_burst_option_off_disables_only_optional_branch():
    e,state,pr=make_state(False)
    e.apply_effect(state,'a','enemy',{'type':'tremor_burst','name':'Tremor','count_cost':1})
    assert state.runtime['tremor_burst_counts']['a'] == 1
    assert state.enemy.statuses['Tremor'].count == 4
    assert pr.passives[0].activations == 0

def test_extra_burst_option_on_preserves_high_point_behavior():
    e,state,pr=make_state(True)
    e.apply_effect(state,'a','enemy',{'type':'tremor_burst','name':'Tremor','count_cost':1})
    assert state.runtime['tremor_burst_counts']['a'] == 2
    assert state.enemy.statuses['Tremor'].count == 3
    assert pr.passives[0].activations == 1

def test_extra_burst_option_omitted_defaults_on_for_backward_compatibility():
    e,state,pr=make_state(True)
    state.runtime.pop('calculation_options')
    e.apply_effect(state,'a','enemy',{'type':'tremor_burst','name':'Tremor','count_cost':1})
    assert state.runtime['tremor_burst_counts']['a'] == 2


# ---- merged from test_tremor_burst_flower_resource.py ----


def test_tremor_burst_flower_compiles_as_generic_resource_gain():
    rec={'id':'p','name':'시들지 않는 꽃','effect':'진동 폭발 발생 시, 꽃잎 2 얻음'}
    rules,_,_=compile_one(rec,'10414',0)
    assert rules and rules[0].trigger == PassiveTrigger.TREMOR_BURST
    assert rules[0].effects[0].name == '꽃잎'


def test_tremor_burst_flower_resource_runtime_gain():
    f=FighterState(); state=BattleState(enemy=EnemyState(100,100,statuses={'Tremor':__import__('limbus_damage_engine_v29').Status(potency=10,count=1)}), fighters={'i':f}, runtime={})
    pr=PassiveRuntime(); rules,_,_=compile_one({'id':'p','name':'p','effect':'진동 폭발 발생 시, 꽃잎 2 얻음'},'i',0)
    pr.register_many(rules)
    e=DamageEngine(); e.passive_runtime=pr
    e.apply_effect(state,'i','enemy',{'type':'tremor_burst','name':'Tremor','count_cost':1})
    assert f.resources['꽃잎']==2
    assert any(x.get('event')=='resource_gain' and x.get('resource')=='꽃잎' for x in state.event_log)


# ---- merged from test_tremor_burst_followup_runtime.py ----


def test_burst_stagger_damage_to_defense_level_down_compiles_resolved_trigger():
    t, reasons, unsupported = compile_clause_template('적에게 진동 폭발 시 입히는 흐트러짐 손상 4 당 방어 레벨 1 감소 부여 (턴마다 적 1명당 최대 5)')
    assert not unsupported
    assert t.trigger == PassiveTrigger.TREMOR_BURST_RESOLVED
    assert t.max_activations == 5


def test_burst_resolved_defense_down_uses_final_damage():
    e=DamageEngine()
    enemy=EnemyState(100,100,stagger_thresholds=[70],statuses={'Tremor':Status(potency=10,count=1)})
    f=FighterState('i',45,45); f.charge=3
    state=BattleState(enemy=enemy,fighters={'i':f},runtime={})
    from passive_runtime_v29_base import PassiveRuntime, PassiveDefinition, Always, SelfTarget, AddStatus, ContextValue, Const
    from passive_compiler_v29 import Clamp, div
    pr=PassiveRuntime(); e.passive_runtime=pr
    pr.register(PassiveDefinition('p','p','i',PassiveTrigger.TREMOR_BURST_RESOLVED,[Always()],__import__('passive_runtime_v29_base').EventTarget('target'),[
        AddStatus('Defense Level Down', potency=Clamp(div(ContextValue('burst_stagger_damage'),Const(4)),0,5))
    ],max_activations=5))
    e.apply_effect(state,'i','enemy',{'type':'tremor_burst','name':'Tremor','count_cost':1})
    assert enemy.statuses['Defense Level Down'].potency == 2


def test_burst_rupture_and_next_turn_attack_level_parse():
    from passive_compiler_v29 import compile_clause_template
    t, reasons, unsupported = compile_clause_template('진동 폭발 시 진동 횟수 4 감소. 파열 5 부여')
    assert not unsupported
    assert t.trigger == PassiveTrigger.TREMOR_BURST
    assert any(r=='tremor_burst_rupture_5' for r in reasons)
    t2, reasons2, unsupported2 = compile_clause_template('속도가 가장 빠른 아군 1명이 적에게 진동 폭발 시, 다음 턴에 공격 레벨 증가 2 얻음 (턴당 1회)')
    assert not unsupported2
    assert any(r=='next_turn_status:tremor_burst_attack_level_up' for r in reasons2)

def test_burst_resolved_defense_down_can_be_queued_for_target_next_turn():
    t, reasons, unsupported = compile_clause_template('최대 체력이 가장 낮은 아군 1명이 적에게 진동 폭발 시 입히는 흐트러짐 손상 4 당 다음 턴에 방어 레벨 1 감소 부여 (턴마다 적 1명당 최대 3)')
    assert not unsupported
    assert t.trigger == PassiveTrigger.TREMOR_BURST_RESOLVED
    assert t.target_kind == 'event'
    assert t.max_activations == 3
    assert 'next_turn_status_target:tremor_burst_stagger_to_defense_down' in reasons


# ---- merged from test_tremor_burst_no_implicit_count_v1.py ----

def test_burst_trigger_clause_does_not_create_burst_effect():
    rule, reasons, unsupported = compile_clause_template('진동 폭발 발생 시, 꽃잎 2 얻음')
    assert not unsupported
    assert rule.trigger == PassiveTrigger.TREMOR_BURST
    assert rule.effects[0].name == '꽃잎'

def test_explicit_passive_burst_count_cost_is_preserved():
    rule, reasons, unsupported = compile_clause_template('진동 폭발. 대상의 진동 횟수 1 감소')
    assert not unsupported
    assert rule.effects[0].count_cost == 1

def test_plain_burst_keeps_count_in_engine():
    e=DamageEngine(); enemy=EnemyState(100,100,statuses={'Tremor':Status(potency=10,count=2)})
    f=FighterState('i',45,45); state=BattleState(enemy=enemy,fighters={'i':f},runtime={})
    e.apply_effect(state,'i','enemy',{'type':'tremor_burst','name':'Tremor'})
    assert state.enemy.statuses['Tremor'].count == 2

def test_explicit_burst_cost_consumes_count():
    e=DamageEngine(); enemy=EnemyState(100,100,statuses={'Tremor':Status(potency=10,count=2)})
    f=FighterState('i',45,45); state=BattleState(enemy=enemy,fighters={'i':f},runtime={})
    e.apply_effect(state,'i','enemy',{'type':'tremor_burst','name':'Tremor','count_cost':1})
    assert state.enemy.statuses['Tremor'].count == 1


# ---- merged from test_tremor_burst_secondary_damage.py ----


def test_burst_secondary_damage_compiles():
    t, reasons, unsupported = compile_clause_template('진동 폭발 시 최종 흐트러짐 손상의 30%만큼 분노 피해를 줌.(최대 20)')
    assert not unsupported
    assert t.trigger == PassiveTrigger.TREMOR_BURST
    assert any(isinstance(e, AddBurstSecondaryDamage) for e in t.effects)


def test_burst_secondary_damage_uses_final_burst_damage_and_cap():
    e=DamageEngine()
    enemy=EnemyState(100,100,stagger_thresholds=[70],statuses={'Tremor':Status(potency=10,count=1)},sin_res={'wrath':1.0})
    f=FighterState('i',45,45)
    state=BattleState(enemy=enemy,fighters={'i':f},runtime={})
    pr=PassiveRuntime(); e.passive_runtime=pr
    pr.register(PassiveDefinition('p','p','i',PassiveTrigger.TREMOR_BURST,[Always()],SelfTarget(),[AddBurstSecondaryDamage('wrath',Const(.3),Const(20))]))
    e.apply_effect(state,'i','enemy',{'type':'tremor_burst','name':'Tremor','count_cost':1})
    assert enemy.stagger_thresholds == [80]
    assert enemy.hp == 97
    assert state.turn_damage == 3


def test_burst_secondary_damage_applies_sin_resistance():
    e=DamageEngine()
    enemy=EnemyState(100,100,stagger_thresholds=[70],statuses={'Tremor':Status(potency=10,count=1)},sin_res={'wrath':0.5})
    f=FighterState('i',45,45)
    state=BattleState(enemy=enemy,fighters={'i':f},runtime={})
    pr=PassiveRuntime(); e.passive_runtime=pr
    pr.register(PassiveDefinition('p','p','i',PassiveTrigger.TREMOR_BURST,[Always()],SelfTarget(),[AddBurstSecondaryDamage('wrath',Const(.3),Const(20))]))
    e.apply_effect(state,'i','enemy',{'type':'tremor_burst','name':'Tremor','count_cost':1})
    assert enemy.hp == 98
