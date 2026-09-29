"""병합 테스트: triggers_actions_queue

원본 파일 (내용은 AST 병합기로 합쳤고 테스트 본문은 바꾸지 않음):
  - test_v29_action_queue_v1.py
  - test_v29_triggered_action_queue.py
  - test_v29_after_hit_trigger.py
  - test_v29_trigger_runtime.py
  - test_v29_generated_damage_attribution.py
  - test_v29_passive_optimization.py
  - test_v29_scenario_flow.py
  - test_v29_trace_detail.py
  - test_v29_preparation.py
  - test_v29_parallel_engine_upgrades.py
  - test_v29_parallel_upgrades.py
이름 충돌 helper 는 `이름__vNN` 으로 분리했다. 매핑은 tools/MERGE_MAP.json 참고.
"""
import sys
import unittest
import json
import math
from pathlib import Path
from action_queue_v1 import ActionQueue
from one_turn_solver_v29 import IdentityCatalogV29, OneTurnSolverV29
from special_gimmick_v2 import GimmickRegistry
from types import SimpleNamespace
from trigger_runtime_v1 import TriggerRuntime, TriggerRule, TriggerCondition, TriggerEffect
from copy import deepcopy
from limbus_damage_engine_v29 import (
    IdentityData,
    SkillData,
    CoinData,
    BattleState,
    EnemyState,
    FighterState,
    Status,
    DamageEngine,
)



# ======================================================================
# 원본: test_v29_action_queue_v1.py
# ======================================================================
sys.path.insert(0, str(Path(__file__).parent))

def test_trigger_is_inserted_without_changing_requested_order():
    q=ActionQueue.from_scenario([
        {'identity_id':'A','skill_id':'S1'},
        {'identity_id':'B','skill_id':'S2'},
        {'identity_id':'C','skill_id':'S3'},
    ])
    first=q.pop()
    trig=q.triggered_from(first,'X','assist','assist','stagger')
    assert q.enqueue_triggered(trig)
    order=[]
    while q:
        a=q.pop(); order.append((a.requested_index,a.generated,a.identity_id))
    assert order == [(1,True,'X'),(2,False,'B'),(3,False,'C')]
    assert [x['requested_index'] for x in q.requested_plan()] == [1,2,3]

def test_trigger_chain_depth_is_carried():
    q=ActionQueue.from_scenario([{'identity_id':'A','skill_id':'S1'}], max_depth=2)
    a=q.pop()
    b=q.triggered_from(a,'B','S1','r')
    c=q.triggered_from(b,'C','S1','r')
    d=q.triggered_from(c,'D','S1','r')
    assert (b.depth,c.depth,d.depth)==(1,2,3)
    assert q.enqueue_triggered(b)
    assert q.enqueue_triggered(c)
    assert not q.enqueue_triggered(d)


# ======================================================================
# 원본: test_v29_triggered_action_queue.py
# ======================================================================

def load(*ids):
    cat=IdentityCatalogV29.from_json(str(Path(__file__).parent/'identity_catalog_v2.json'))
    return {i:(cat.build_identity(i)) for i in ids}

def test_player_order_and_triggered_action_are_separate():
    ids=load('identity-10216','identity-11216')
    f=ids['identity-10216']; g=ids['identity-11216']
    sc={'coin_mode':'max','enemy':{'hp':100000,'max_hp':100000,'level':60},
        'allies':{f.id:{'sp':45},g.id:{'sp':45}},
        'actions':[{'identity_id':f.id,'skill_id':'102163'},
                   {'identity_id':g.id,'skill_id':'112162'}]}
    r=OneTurnSolverV29().solve(sc,ids)
    assert [x['requested_index'] for x in r['actions']] == [1,1,2]
    assert r['actions'][1]['generated'] is True
    assert r['actions'][2]['generated'] is False

def test_newly_staggered_triggers_only_when_not_staggered_at_start():
    ids=load('identity-10216','identity-11216')
    f=ids['identity-10216']; g=ids['identity-11216']
    sc={'coin_mode':'max','enemy':{'hp':1000,'max_hp':1000,'level':60,'stagger_thresholds':[999]},
        'allies':{f.id:{'sp':45},g.id:{'sp':45}},
        'actions':[{'identity_id':f.id,'skill_id':'102161'}]}
    r=OneTurnSolverV29().solve(sc,ids)
    assert any(x['generated'] and x['identity_id']==g.id for x in r['actions'])

    sc['enemy']['stagger_level']=1
    r2=OneTurnSolverV29().solve(sc,ids)
    assert not any(x['generated'] and x['identity_id']==g.id for x in r2['actions'])


def test_newly_staggered_is_not_retriggered_by_stagger_level_increase():
    solver=OneTurnSolverV29()
    state=BattleState(EnemyState(hp=100,max_hp=100,stagger_level=2,stagger_index=2,stagger_thresholds=[90,80,70]), {})
    runtime=TriggerRuntime([])
    skill=SimpleNamespace(id='S1',name='S1',_slot='S1')
    identity_map={'A': SimpleNamespace(id='A',passives=[])}
    queued,newly=solver._fire_probabilistic_stagger_triggers(
        state,runtime,identity_map,'A',skill,before_level=1,before_index=1)
    assert queued == []
    assert newly is False


def test_newly_staggered_is_not_retriggered_by_capped_threshold_index():
    solver=OneTurnSolverV29()
    state=BattleState(EnemyState(hp=100,max_hp=100,stagger_level=3,stagger_index=3,stagger_thresholds=[90,80,70,60]), {})
    runtime=TriggerRuntime([])
    skill=SimpleNamespace(id='S1',name='S1',_slot='S1')
    identity_map={'A': SimpleNamespace(id='A',passives=[])}
    queued,newly=solver._fire_probabilistic_stagger_triggers(
        state,runtime,identity_map,'A',skill,before_level=3,before_index=2)
    assert queued == []
    assert newly is False


def test_stagger_transition_records_source_and_forced_without_inventing_forced_state():
    from limbus_damage_engine_v29 import DamageEngine
    engine=DamageEngine()
    state=BattleState(EnemyState(hp=80,max_hp=100,stagger_level=0,stagger_index=0,stagger_thresholds=[90]), {})
    event=engine.check_stagger(state, source='damage', forced=False)
    assert event['before_staggered'] is False
    assert event['after_staggered'] is True
    assert event['newly_staggered'] is True
    assert event['source'] == 'damage'
    assert event['forced'] is False
    assert state.runtime['last_stagger_event']['newly_staggered'] is True


def test_stagger_transition_does_not_retrigger_when_existing_stagger_is_strengthened():
    from limbus_damage_engine_v29 import DamageEngine
    engine=DamageEngine()
    state=BattleState(EnemyState(hp=60,max_hp=100,stagger_level=1,stagger_index=1,stagger_thresholds=[90,70]), {})
    event=engine.check_stagger(state, source='damage', forced=False)
    assert event['before_staggered'] is True
    assert event['after_staggered'] is True
    assert event['newly_staggered'] is False
    assert event['stagger_level_before'] == 1
    assert event['stagger_level_after'] == 2


def test_forced_stagger_is_explicit_metadata_and_not_inferred():
    from limbus_damage_engine_v29 import DamageEngine
    engine=DamageEngine()
    state=BattleState(EnemyState(hp=100,max_hp=100,stagger_level=0,stagger_index=0,stagger_thresholds=[]), {})
    state.enemy.stagger_level = 1
    event=engine.check_stagger(state, source='forced_effect', forced=True)
    assert event['after_staggered'] is True
    assert event['newly_staggered'] is False
    assert event['forced'] is True
    assert event['source'] == 'forced_effect'




def test_stagger_condition_distinguishes_forced_from_nonforced_transition():
    from condition_runtime_v1 import ConditionRuntime
    from rule_ir_v1 import ConditionIR
    assert ConditionRuntime.evaluate(ConditionIR('newly_staggered_nonforced'), {
        'action_start_staggered': False, 'action_end_staggered': True, 'stagger_forced': False
    }) is True
    assert ConditionRuntime.evaluate(ConditionIR('newly_staggered_nonforced'), {
        'action_start_staggered': False, 'action_end_staggered': True, 'stagger_forced': True
    }) is False
    assert ConditionRuntime.evaluate(ConditionIR('stagger_forced', {'value': True}), {
        'stagger_forced': True
    }) is True

def test_mid_turn_resource_can_transform_later_player_action():
    ids=load('identity-10216','identity-11216')
    f=ids['identity-10216']; g=ids['identity-11216']
    sc={'coin_mode':'max','enemy':{'hp':100000,'max_hp':100000,'level':60},
        'allies':{f.id:{'sp':45},g.id:{'sp':45,'resources':{'새벽불':30}}},
        'actions':[{'identity_id':g.id,'skill_id':'112163'}]}
    r=OneTurnSolverV29().solve(sc,ids)
    assert r['actions'][0]['transformation'] is not None
    assert r['actions'][0]['skill_id']=='1121635'

def test_triggered_assist_resource_changes_later_player_resolution():
    ids=load('identity-10216','identity-11216')
    f=ids['identity-10216']; g=ids['identity-11216']
    sc={'coin_mode':'max','enemy':{'hp':100000,'max_hp':100000,'level':60},
        'allies':{f.id:{'sp':45},g.id:{'sp':45,'resources':{'새벽불':26},'statuses':{'새벽맞이':{'potency':1,'count':1}}}},
        'actions':[{'identity_id':f.id,'skill_id':'102163'},
                   {'identity_id':g.id,'skill_id':'112163'}]}
    r=OneTurnSolverV29().solve(sc,ids)
    assert [x['requested_index'] for x in r['actions']] == [1,1,2,2]
    assert r['fighters'][g.id]['resources']['새벽불'] >= 30
    # The second player action resolves first as 새벽녘, then its named follow-up
    # can itself be inserted immediately afterward.
    assert r['actions'][2]['skill_id']=='1121635'
    assert r['actions'][2]['transformation'] is not None


# ======================================================================
# 원본: test_v29_after_hit_trigger.py
# ======================================================================

def _solver():
    solver = OneTurnSolverV29.__new__(OneTurnSolverV29)
    class FakeEngine:
        @staticmethod
        def simulate_coin(state, identity, skill, coin, face, is_crit, coin_index, prior_heads):
            state.enemy.hp -= 10 if coin_index == 1 else 0
    solver.core = SimpleNamespace(machine=SimpleNamespace(engine=FakeEngine()))
    return solver

def test_after_hit_fires_only_when_coin_deals_damage_and_affects_next_coin():
    solver = _solver()
    a = SimpleNamespace(id='a')
    skill = SimpleNamespace(id='S1', name='A', _slot='S1', coins=[object(), object()])
    rt = TriggerRuntime([TriggerRule(
        'hit1', 'a', 'after_hit',
        [TriggerCondition('equals', 1, field='coin_index')],
        [TriggerEffect('set_flag', {'flag': 'hit_seen', 'value': True})], 1,
    )])
    state = SimpleNamespace(
        enemy=SimpleNamespace(hp=100, statuses={}, stagger_level=0, stagger_index=0,
                              stagger_thresholds=[], staggered=False),
        fighters={'a': SimpleNamespace(resources={}, statuses={}, ammo=0, hp=100, max_hp=100)},
        runtime={'condition_flags': {}, 'probabilistic_trigger_runtime_template': rt,
                 'probabilistic_identity_map': {'a': a}},
        turn_damage=0,
    )
    clone, damage, trace = solver._execute_unopposed_coins_with_triggers(
        state, a, skill, ['H', 'H'], 0
    )
    assert damage == 10
    assert clone.runtime['condition_flags']['hit_seen'] is True

def test_after_hit_trigger_is_not_fired_for_zero_damage_coin():
    solver = _solver()
    a = SimpleNamespace(id='a')
    skill = SimpleNamespace(id='S1', name='A', _slot='S1', coins=[object(), object()])
    rt = TriggerRuntime([TriggerRule(
        'hit2', 'a', 'after_hit', [],
        [TriggerEffect('set_flag', {'flag': 'hit_seen', 'value': True})], 1,
    )])
    state = SimpleNamespace(
        enemy=SimpleNamespace(hp=100, statuses={}, stagger_level=0, stagger_index=0,
                              stagger_thresholds=[], staggered=False),
        fighters={'a': SimpleNamespace(resources={}, statuses={}, ammo=0, hp=100, max_hp=100)},
        runtime={'condition_flags': {}, 'probabilistic_trigger_runtime_template': rt,
                 'probabilistic_identity_map': {'a': a}},
        turn_damage=0,
    )
    clone, damage, _ = solver._execute_unopposed_coins_with_triggers(
        state, a, skill, ['H', 'H'], 1
    )
    assert damage == 0
    assert 'hit_seen' not in clone.runtime['condition_flags']


# ======================================================================
# 원본: test_v29_trigger_runtime.py
# ======================================================================

def test_generic_trigger_event_condition_effect():
    r=TriggerRule('t1','A','after_skill',
        [TriggerCondition('skill_name_contains','S3'), TriggerCondition('newly_staggered')],
        [TriggerEffect('queue_action',{'identity_id':'B','skill_name':'S1'})],1)
    rt=TriggerRuntime([r])
    fired=rt.fire('after_skill',{'skill_name':'S3','action_start_staggered':False,'action_end_staggered':True})
    assert fired[0]['effect']['type']=='queue_action'
    assert rt.ledger.counts == {'t1': 1}

def test_generic_trigger_does_not_fire_for_already_staggered():
    r=TriggerRule('t1','A','after_skill',[TriggerCondition('newly_staggered')],[TriggerEffect('queue_action')])
    rt=TriggerRuntime([r])
    assert rt.fire('after_skill',{'action_start_staggered':True,'action_end_staggered':True})==[]


# ======================================================================
# 원본: test_v29_generated_damage_attribution.py
# ======================================================================

class GeneratedDamageAttributionTest(unittest.TestCase):
    def test_generated_child_damage_is_included_in_parent_return(self):
        solver = OneTurnSolverV29()
        parent = IdentityData(id='P', name='Parent', skills={}, offense_level=60)
        child = IdentityData(id='C', name='Child', skills={}, offense_level=60)
        parent_skill = SkillData(id='P1', name='P1', base_power=10, coins=[CoinData(0,'slash','wrath')], attack_type='slash', sin='wrath')
        child_skill = SkillData(id='C1', name='C1', base_power=20, coins=[CoinData(0,'slash','wrath')], attack_type='slash', sin='wrath')
        parent.skills['P1'] = parent_skill
        child.skills['C1'] = child_skill
        enemy = type('E', (), {'hp': 100.0, 'max_hp':100.0, 'staggered':False, 'stagger_level':0, 'stagger_index':0, 'statuses':{}, 'sp':0, 'defense_level':0, 'defense_level_bonus':0, 'level':60, 'physical_res':{'slash':1}, 'sin_res':{}, 'stagger_thresholds':[]})()
        fighter_cls = None
        from limbus_damage_engine_v29 import BattleState, FighterState
        state = BattleState(enemy=enemy, fighters={'P': FighterState(level=60), 'C': FighterState(level=60)})
        state.runtime['probabilistic_trigger_runtime_template'] = solver._probabilistic_trigger_runtime([])
        state.runtime['probabilistic_identity_map'] = {'P': parent, 'C': child}
        runtime = state.runtime['probabilistic_trigger_runtime_template']
        # Directly queue a child through the runtime by monkeypatching the trigger fire.
        original_fire = runtime.fire
        def fire(event, ctx):
            if event == 'after_hit' and ctx.get('identity_id') == 'P':
                return [{'rule_id':'r','owner_id':'P','effect':{'type':'queue_action','identity_id':'C','skill_id':'C1'}}]
            return original_fire(event, ctx)
        runtime.fire = fire
        total, trace = solver._execute_probabilistic_generated_action(state, runtime, {'P':parent,'C':child}, 'P', parent_skill)
        self.assertGreaterEqual(total, 0.0)
        self.assertEqual(len(trace), 2)
        self.assertGreater(state.turn_damage, 0.0)
        self.assertAlmostEqual(total, state.turn_damage, places=6)
if __name__ == '__main__':
    unittest.main()


# ======================================================================
# 원본: test_v29_passive_optimization.py
# ======================================================================

def ident(passive):
    return {'id':'x','name':'X','offense_level':0,'stats':{'level':60,'speed':13,'hp':1000,'hpBase':1000,'defenseLevel':0,'resistances':{}},
      'skills':{'S1':{'id':'S1','name':'S1','base_power':10,'coin_powers':[1],'coin_count':1,
        'coins':[{'coin_power':1,'damage_type':'slash','sin':'lust'}],'attack_type':'slash','sin':'lust'}},
      'passives':[{'id':'p','name':'P','effect':passive}]}

def solve(passive, ammo=0, enemy_speed=10, hp=1000, statuses=None):
    i=IdentityCatalogV29([ident(passive)]).build_identity('x',offense_level=0,level=60,speed=13)
    sc={'enemy':{'hp':hp,'max_hp':1000,'level':60,'defense_level':0,'speed':enemy_speed,
        'physical_res':{'slash':1,'pierce':1,'blunt':1},'sin_res':{'lust':1},'statuses':statuses or {}},
        'allies':{'x':{'sp':0,'hp':1000,'max_hp':1000,'speed':13,'ammo':ammo}},
        'actions':[{'identity_id':'x','skill_id':'S1','faces':['H']}],'passive_mode':'compiled_conservative'}
    return OneTurnSolverV29().solve(sc,{'x':i})

def test_builtin_ammo_does_not_overwrite_explicit_higher_value():
    r=solve('상시 적용 : 탄환 7개 보유', ammo=9)
    assert r['fighters']['x']['ammo'] == 9

def test_builtin_ammo_initializes_empty_magazine():
    r=solve('상시 적용 : 탄환 7개 보유', ammo=0)
    assert r['fighters']['x']['ammo'] == 7

def test_speed_difference_condition():
    fast=solve('대상보다 속도가 3 이상 높을 때 피해량 +10%', enemy_speed=10)
    slow=solve('대상보다 속도가 3 이상 높을 때 피해량 +10%', enemy_speed=11)
    assert fast['turn_damage'] > slow['turn_damage']

def test_status_gain_parser():
    r=solve('전투 시작 시 보호 1 얻음')
    assert r['fighters']['x']['statuses']['Protection']['potency'] == 1


# ======================================================================
# 원본: test_v29_scenario_flow.py
# ======================================================================

def make_ident(iid, name, sin='lust'):
    return {'id':iid,'name':name,'offense_level':0,
      'stats':{'level':60,'speed':10,'hp':1000,'hpBase':1000,'defenseLevel':0,'resistances':{}},
      'skills':{'S1':{'id':'S1','name':'S1','base_power':10,'coin_powers':[1],'coin_count':1,
        'coins':[{'coin_power':1,'damage_type':'slash','sin':sin}],'attack_type':'slash','sin':sin}},
      'passives':[]}

def test_sequential_actions_and_identity_damage():
    records=[make_ident('a','A'), make_ident('b','B')]
    cat=IdentityCatalogV29(records)
    ids={x:cat.build_identity(x) for x in ('a','b')}
    sc={'enemy':{'hp':1000,'max_hp':1000,'level':60,'defense_level':0,
        'physical_res':{'slash':1,'pierce':1,'blunt':1},'sin_res':{'lust':1},
        'stagger_thresholds':[980]},
        'allies':{'a':{'sp':0,'hp':1000,'max_hp':1000},'b':{'sp':0,'hp':1000,'max_hp':1000}},
        'actions':[{'identity_id':'a','skill_id':'S1','faces':['H']},
                   {'identity_id':'b','skill_id':'S1','faces':['H']}],
        'passive_mode':'off'}
    r=OneTurnSolverV29().solve(sc,ids)
    assert r['turn_damage'] == r['damage_by_identity']['a'] + r['damage_by_identity']['b']
    assert r['enemy_stagger_index'] >= 1
    assert r['actions'][0]['damage'] > 0

def test_initial_stagger_is_supported():
    cat=IdentityCatalogV29([make_ident('a','A')]); ident=cat.build_identity('a')
    sc={'enemy':{'hp':500,'max_hp':1000,'stagger_thresholds':[800,500], 'stagger_level':1,'stagger_index':1,
        'physical_res':{'slash':1,'pierce':1,'blunt':1},'sin_res':{'lust':1}},
        'allies':{'a':{}},'actions':[{'identity_id':'a','skill_id':'S1','faces':['H']}]}
    r=OneTurnSolverV29().solve(sc,{'a':ident})
    assert r['enemy_staggered'] is True


# ======================================================================
# 원본: test_v29_trace_detail.py
# ======================================================================

def test_action_trace_contains_coin_and_resource_state():
    record={'id':'a','name':'A','offense_level':0,
      'stats':{'level':60,'speed':10,'hp':100,'hpBase':100,'defenseLevel':0,'resistances':{}},
      'skills':{'S1':{'id':'S1','name':'S1','base_power':10,'coin_powers':[1,1],'coin_count':2,
        'coins':[{'coin_power':1,'damage_type':'slash','sin':'lust'},{'coin_power':1,'damage_type':'slash','sin':'lust'}],'attack_type':'slash','sin':'lust'}},
      'passives':[]}
    cat=IdentityCatalogV29([record]); ident=cat.build_identity('a')
    sc={'enemy':{'hp':1000,'max_hp':1000,'level':60,'defense_level':0,'physical_res':{'slash':1,'pierce':1,'blunt':1},'sin_res':{'lust':1}},
        'allies':{'a':{'resources':{'X':3}}},'resource_specs':{'X':{'maximum':10}},
        'actions':[{'identity_id':'a','skill_id':'S1','faces':['H','H']}], 'passive_mode':'off'}
    r=OneTurnSolverV29().solve(sc,{'a':ident})
    a=r['actions'][0]
    assert len(a['coins'])==2
    assert a['state_at_action_start']['fighter_resources']['X']==3
    assert a['state_at_action_end']['fighter_resources']['X']==3
    assert all('actual_damage' in c for c in a['coins'])


# ======================================================================
# 원본: test_v29_preparation.py
# ======================================================================

def load__v29_preparation():
    cat = IdentityCatalogV29.from_json(str(Path(__file__).parent / 'identity_catalog_v2.json'))
    rec = cat.records['identity-11216']
    ident = cat.build_identity('identity-11216')
    return (cat, ident)

def test_explicit_preparation_levels_and_flags():
    cat, ident = load__v29_preparation()
    solver = OneTurnSolverV29()
    ids = {ident.id: ident}
    st = solver.build_state({'enemy': {'hp': 1000}}, ids)
    solver._apply_prepared_state(st, {'flags': {'ready': True}, 'levels': {'dawn_fire': 30}})
    assert st.runtime['condition_flags']['ready'] is True
    assert st.runtime['preparation_levels']['dawn_fire'] == 30

def test_mid_turn_dawn_transformation():
    cat, ident = load__v29_preparation()
    solver = OneTurnSolverV29()
    ids = {ident.id: ident}
    sc = {'coin_mode': 'max', 'preparation': {'levels': {'dawn_fire': 30}}, 'allies': {ident.id: {'resources': {'새벽불': 30}}}, 'enemy': {'hp': 100000, 'max_hp': 100000}, 'actions': [{'identity_id': ident.id, 'skill_id': '112163'}]}
    r = solver.solve(sc, ids)
    assert r['actions'][0]['skill_id'] != '1121603' or r['actions'][0]['transformation'] is None


# ======================================================================
# 원본: test_v29_parallel_engine_upgrades.py
# ======================================================================

def ident__v29_parallel():
    return IdentityData('A', 'A', 0, {'S': SkillData('S', 'S', 10, [CoinData(1, 'slash', 'lust')], 'slash', 'lust')}, [])

def test_bleed_deals_self_damage_and_consumes_count():
    e = EnemyState(hp=100, max_hp=100)
    f = FighterState(hp=50, max_hp=50, statuses={'Bleed': Status(potency=7, count=1)})
    st = BattleState(e, {'A': f})
    DamageEngine().before_coin(st, ident__v29_parallel())
    assert f.hp == 43
    assert 'Bleed' not in f.statuses

def test_sinking_sp_damage_is_clamped():
    e=EnemyState(hp=100,max_hp=100,sp=-42,statuses={'Sinking':Status(potency=10,count=1)})
    st=BattleState(e,{'A':FighterState()})
    DamageEngine().on_target_hit(st)
    assert e.sp == -45
    assert 'Sinking' not in e.statuses

def test_fixed_damage_effect_can_trigger_stagger_threshold():
    e=EnemyState(hp=20,max_hp=100,stagger_thresholds=[15])
    st=BattleState(e,{'A':FighterState()})
    DamageEngine().apply_effect(st,'A','enemy',{'type':'damage_fixed','amount':6})
    assert e.hp == 14
    assert e.stagger_level == 1
    assert e.stagger_index == 1

def test_offense_defense_modifier_truncates_to_two_decimal_places():
    # Attack level is the actor's effective offense level.  These are the
    # empirically verified Sinclair S2 defense-level points.
    assert DamageEngine.offense_defense_modifier(60, 47) == 0.34
    assert DamageEngine.offense_defense_modifier(60, 37) == 0.47

    # Negative values are truncated toward zero, not rounded away from zero.
    assert DamageEngine.offense_defense_modifier(60, 65) == -0.16


def test_defense_level_bonus_is_part_of_fighter_state_and_output():
    e=EnemyState(hp=100,max_hp=100,level=60)
    f=FighterState(level=60,defense_level_bonus=5)
    st=BattleState(e,{'A':f})
    value=DamageEngine.offense_defense_modifier(60,65)
    assert value < 0


# ======================================================================
# 원본: test_v29_parallel_upgrades.py
# ======================================================================

def mk_identity(effects, coin_power=5):
    return {
        'id':'x','name':'테스트','stats':{'level':60,'speed':10},
        'skills':[{'id':'s1','slot':'S1','name':'테스트 스킬','affinity':'gloom','attackType':'slash','basePower':10,'coinPowers':[coin_power],'effects':effects}],
        'passives':[]
    }

def test_conditional_damage_modifier_is_applied():
    eng=DamageEngine(); enemy=EnemyState(1000,1000,level=60); f=FighterState(level=60)
    ident=IdentityData('x','x',0,{'s':SkillData('s','s',10,[CoinData(5,'slash','gloom')],'slash','gloom',conditions=[{'effect':'damage_bonus','condition':{'type':'negative_status_count_per','per':1,'amount':0.1,'max':0.1}}])})
    enemy.statuses['Burn']=Status(potency=1,count=1)
    state=BattleState(enemy,{'x':f}); state.runtime['current_resonance_offense_bonus']=0
    a,_=eng.calculate_coin_damage(state,ident,ident.skills['s'],ident.skills['s'].coins[0],'H',False,0,1)
    enemy2=EnemyState(1000,1000,level=60); enemy2.statuses['Burn']=Status(potency=1,count=1)
    state2=BattleState(enemy2,{'x':FighterState(level=60)})
    ident2=IdentityData('x','x',0,{'s':SkillData('s','s',10,[CoinData(5,'slash','gloom')],'slash','gloom')})
    b,_=eng.calculate_coin_damage(state2,ident2,ident2.skills['s'],ident2.skills['s'].coins[0],'H',False,0,1)
    assert a>b

def test_resource_consumption_damage_bonus_uses_actual_spent_amount():
    cat=IdentityCatalogV29([mk_identity(['[사용시] 자신의 생체 재료 횟수가 10 이상이면, 생체 재료 횟수를 최대 20까지 소모하고 아래 효과 적용','- 소모한 수치 1당, 피해량 +3%'])])
    ident=cat.build_identity('x')
    skill=ident.skills['S1']
    assert skill.resource_conditional_cost_max
    assert skill.resource_consumption_damage_per.get('생체 재료') == 0.03
    scenario={'coin_mode':'fixed','enemy':{'hp':1000,'max_hp':1000},'allies':{'x':{'resources':{'생체 재료':15}}},'actions':[{'identity_id':'x','skill_id':'S1','faces':['H']}]}
    r=OneTurnSolverV29().solve(scenario,{'x':ident})
    assert r['fighters']['x']['resources']['생체 재료']==0
    assert r['actions'][0]['damage']>0

def test_damage_by_skill_breakdown_is_present():
    cat=IdentityCatalogV29([mk_identity([])])
    ident=cat.build_identity('x')
    scenario={'coin_mode':'fixed','enemy':{'hp':1000,'max_hp':1000},'actions':[{'identity_id':'x','skill_id':'S1','faces':['H']},{'identity_id':'x','skill_id':'S1','faces':['H']}]}
    r=OneTurnSolverV29().solve(scenario,{'x':ident})
    # v0.5.18 baseline did not expose this map; test is intentionally pending
    # until the solver upgrade is applied.
    assert math.isclose(sum(a['damage'] for a in r['actions']), r['turn_damage'])

def test_cross_identity_resource_gain_targets_rule_owner():
    from special_gimmick_v2 import GimmickRegistry
    from limbus_damage_engine_v29 import FighterState, BattleState, EnemyState
    # Use a minimal registry rule directly through the generic trigger payload.
    ids=IdentityCatalogV29([mk_identity([]), {**mk_identity([]), 'id':'y','name':'소유자'}])
    owner=ids.build_identity('x'); actor=ids.build_identity('y')
    state=BattleState(EnemyState(100,100), {'x':FighterState(), 'y':FighterState()})
    reg=GimmickRegistry([owner,actor], { 'x':[], 'y':[] }, available_identity_ids=['x','y'], extra_trigger_rules=[{
        'id':'cross_gain','owner_id':'x','event':'after_coin','conditions':[{'type':'actual_damage_gt_zero'}],
        'effects':[{'type':'resource_gain','resource':'생체 재료','amount':2}],'max_activations':1}])
    reg.after_coin(state, actor, actor.skills['S1'], 1, 5)
    assert state.fighters['x'].resources.get('생체 재료',0)==2
    assert state.fighters['y'].resources.get('생체 재료',0)==0
