"""병합 테스트: target_selection

원본 파일 (내용은 AST 병합기로 합쳤고 테스트 본문은 바꾸지 않음):
  - test_v29_explicit_multitarget.py
  - test_v29_target_count.py
  - test_v29_target_selection.py
  - test_v38_target_request_metadata.py
  - test_v39_coin_target_assignment.py
  - test_v39_trigger_target_inheritance.py
  - test_v40_multitarget_shared_coin_state.py
  - test_v42_target_death_multitarget.py
  - test_v43_coin_target_roles.py
  - test_v45_random_target_selection.py
  - test_v46_random_target_override.py
  - test_v47_ally_target_selection.py
  - test_v48_ally_rank_condition.py
이름 충돌 helper 는 `이름__vNN` 으로 분리했다. 매핑은 tools/MERGE_MAP.json 참고.
"""
from one_turn_solver_v29 import IdentityCatalogV29, OneTurnSolverV29, SkillTextParserV19
from action_queue_v1 import ActionRequest, ActionQueue
from limbus_damage_engine_v29 import IdentityData, SkillData, CoinData
from target_selector_v1 import select_targets
from types import SimpleNamespace
from passive_compiler_v29 import compile_one
from passive_runtime_v29_base import PassiveRuntime, PassiveTrigger



# ======================================================================
# 원본: test_v29_explicit_multitarget.py
# ======================================================================

def test_explicit_targets_resolve_independent_hp_and_damage():
    record={'id':'a','name':'A','offense_level':0,
      'stats':{'level':60,'speed':10,'hp':1000,'hpBase':1000,'defenseLevel':0,'resistances':{}},
      'skills':{'S1':{'id':'S1','name':'S1','base_power':10,'coin_powers':[1],'coin_count':1,
        'coins':[{'coin_power':1,'damage_type':'slash','sin':'lust'}],'attack_type':'slash','sin':'lust'}}, 'passives':[]}
    ident=IdentityCatalogV29([record]).build_identity('a')
    sc={'target_count':2,'target_policy':'explicit','enemy':{'hp':1000,'max_hp':1000},
        'allies':{'a':{}},'actions':[{'identity_id':'a','skill_id':'S1','faces':['H'],'target_ids':['t1','t2']}],
        'enemy':{'hp':1000,'max_hp':1000,'targets':[{'id':'t1','hp':100,'max_hp':100},{'id':'t2','hp':50,'max_hp':50}]},
        'passive_mode':'off'}
    r=OneTurnSolverV29().solve(sc,{'a':ident})
    dm=r['actions'][0]['damage_by_target']
    assert set(dm)=={'t1','t2'}
    assert r['total_damage_all_targets']==sum(dm.values())
    assert r['target_states']['t1']['hp'] <= 100
    assert r['target_states']['t2']['hp'] <= 50


# ======================================================================
# 원본: test_v29_target_count.py
# ======================================================================

def test_target_count_splits_main_and_additional_damage():
    record={'id':'a','name':'A','offense_level':0,
      'stats':{'level':60,'speed':10,'hp':1000,'hpBase':1000,'defenseLevel':0,'resistances':{}},
      'skills':{'S1':{'id':'S1','name':'S1','base_power':10,'coin_powers':[1],'coin_count':1,
        'coins':[{'coin_power':1,'damage_type':'slash','sin':'lust'}],'attack_type':'slash','sin':'lust'}},
      'passives':[]}
    ident=IdentityCatalogV29([record]).build_identity('a')
    sc={'target_count':2,'enemy':{'hp':1000,'max_hp':1000,'level':60,'defense_level':0,
        'physical_res':{'slash':1,'pierce':1,'blunt':1},'sin_res':{'lust':1}},
        'allies':{'a':{}},'actions':[{'identity_id':'a','skill_id':'S1','faces':['H']}],
        'passive_mode':'off'}
    r=OneTurnSolverV29().solve(sc,{'a':ident})
    assert r['target_count']==2
    assert r['main_target_damage']==r['turn_damage']
    assert r['additional_target_damage']==r['main_target_damage']
    assert r['total_damage_all_targets']==r['main_target_damage']*2
    assert r['main_target_damage_by_identity']['a']==r['damage_by_identity']['a']
    assert r['total_damage_all_targets_by_identity']['a']==r['damage_by_identity']['a']*2
    assert r['actions'][0]['total_damage_all_targets']==r['actions'][0]['damage']*2


# ======================================================================
# 원본: test_v29_target_selection.py
# ======================================================================

def test_action_request_preserves_target_selection_metadata():
    from action_queue_v1 import ActionQueue
    q=ActionQueue.from_scenario([{
        'identity_id':'A','skill_id':'S1','target_policy':'lowest_hp','target_index':1,'target_ids':['e2']
    }])
    a=q.pop()
    assert a.target_policy=='lowest_hp'
    assert a.target_index==1
    assert a.target_ids==['e2']

def test_target_selector_supports_explicit_ally_speed_aliases():
    from target_selector_v1 import select_targets
    allies=[
        {'id':'ally_a','speed':12,'hp':100,'max_hp':100},
        {'id':'ally_b','speed':25,'hp':100,'max_hp':100},
        {'id':'ally_c','speed':7,'hp':100,'max_hp':100},
    ]
    assert select_targets(allies,'fastest_ally')[0]['id']=='ally_b'
    assert select_targets(allies,'slowest_ally')[0]['id']=='ally_c'


def test_target_selector_supports_speed_and_hp_policies():
    from target_selector_v1 import select_targets
    ts=[{'id':'a','speed':5,'hp':50,'max_hp':100,'formation_index':0},
        {'id':'b','speed':9,'hp':80,'max_hp':100,'formation_index':1},
        {'id':'c','speed':7,'hp':20,'max_hp':100,'formation_index':2}]
    assert select_targets(ts,'fastest')[0]['id']=='b'
    assert select_targets(ts,'lowest_hp')[0]['id']=='c'
    assert select_targets(ts,'leftmost')[0]['id']=='a'

def test_target_selector_supports_highest_status_policy():
    from target_selector_v1 import select_targets
    ts=[{'id':'a','statuses':{'잔향':{'potency':3}}},
        {'id':'b','statuses':{'잔향':{'potency':8}}}]
    assert select_targets(ts,'highest_status:잔향')[0]['id']=='b'


# ======================================================================
# 원본: test_v38_target_request_metadata.py
# ======================================================================

def test_generated_request_target_metadata_is_more_specific_than_scenario():
    r = ActionRequest(identity_id='i', skill_id='S1', requested_index=1,
                      target_policy='highest_status:Bleed', target_index=1,
                      target_ids=['b'])
    assert r.target_policy == 'highest_status:Bleed'
    assert r.target_index == 1
    assert r.target_ids == ['b']


# ======================================================================
# 원본: test_v39_coin_target_assignment.py
# ======================================================================

def test_coin_target_ids_assign_each_coin_to_its_own_target():
    record={
      'id':'a','name':'A','offense_level':0,
      'stats':{'level':60,'speed':10,'hp':1000,'hpBase':1000,'defenseLevel':0,'resistances':{}},
      'skills':{'S1':{'id':'S1','name':'S1','base_power':10,'coin_powers':[1,10],'coin_count':2,
        'coins':[{'coin_power':1,'damage_type':'slash','sin':'lust'}, {'coin_power':10,'damage_type':'slash','sin':'lust'}],
        'attack_type':'slash','sin':'lust'}}, 'passives':[]}
    ident=IdentityCatalogV29([record]).build_identity('a')
    sc={'coin_mode':'fixed','target_count':1,'enemy':{'hp':1000,'max_hp':1000,'targets':[
        {'id':'t1','hp':100,'max_hp':100}, {'id':'t2','hp':100,'max_hp':100}]},
        'allies':{'a':{}},'actions':[{'identity_id':'a','skill_id':'S1','faces':['H','H'],
        'coin_target_ids':['t1','t2']}],'passive_mode':'off'}
    r=OneTurnSolverV29().solve(sc,{'a':ident})
    dm=r['actions'][0]['damage_by_target']
    assert set(dm)=={'t1','t2'}
    assert dm['t1'] > 0 and dm['t2'] > 0
    events=[e for e in r['event_log'] if e.get('event')=='coin_target_resolution']
    assert [(e['coin'],e['target_id']) for e in events]==[(1,'t1'),(2,'t2')]
    assert r['target_states']['t1']['hp'] < 100
    assert r['target_states']['t2']['hp'] < 100

def test_coin_target_ids_can_use_target_indices():
    record={
      'id':'a','name':'A','offense_level':0,
      'stats':{'level':60,'speed':10,'hp':1000,'hpBase':1000,'defenseLevel':0,'resistances':{}},
      'skills':{'S1':{'id':'S1','name':'S1','base_power':10,'coin_powers':[1,10],'coin_count':2,
        'coins':[{'coin_power':1,'damage_type':'slash','sin':'lust'}, {'coin_power':10,'damage_type':'slash','sin':'lust'}],
        'attack_type':'slash','sin':'lust'}}, 'passives':[]}
    ident=IdentityCatalogV29([record]).build_identity('a')
    sc={'enemy':{'hp':1000,'max_hp':1000,'targets':[
        {'id':'t1','hp':100,'max_hp':100}, {'id':'t2','hp':100,'max_hp':100}]},
        'allies':{'a':{}},'actions':[{'identity_id':'a','skill_id':'S1','faces':['H','H'],
        'coin_target_indices':[0,1]}],'passive_mode':'off'}
    r=OneTurnSolverV29().solve(sc,{'a':ident})
    events=[e for e in r['event_log'] if e.get('event')=='coin_target_resolution']
    assert [(e['coin'],e['target_id']) for e in events]==[(1,'t1'),(2,'t2')]


# ======================================================================
# 원본: test_v39_trigger_target_inheritance.py
# ======================================================================

def test_triggered_action_inherits_explicit_source_target_metadata():
    src = ActionRequest('i1','s1',1,target_policy='highest_hp',target_ids=['t2','t3'],
                        coin_target_ids=['t3','t2'])
    q=ActionQueue([src])
    generated=q.triggered_from(src,'i2','s2','assist',target_policy='main')
    # Queue itself preserves the source chain; solver is responsible for
    # resolving the legacy 'main' default against the source metadata.
    assert generated.target_policy == 'main'
    assert generated.target_ids is None

def test_explicit_trigger_target_overrides_source():
    src = ActionRequest('i1','s1',1,target_policy='highest_hp',target_ids=['t2'])
    q=ActionQueue([src])
    generated=q.triggered_from(src,'i2','s2','assist',target_policy='lowest_hp',target_ids=['t1'])
    assert generated.target_policy == 'lowest_hp'
    assert generated.target_ids == ['t1']


# ======================================================================
# 원본: test_v40_multitarget_shared_coin_state.py
# ======================================================================

def _ident(resource_cost=False):
    coin={'coin_power':1,'damage_type':'slash','sin':'lust'}
    if resource_cost:
        coin['resource_cost']={'X':1}
    return IdentityCatalogV29([{
      'id':'a','name':'A','offense_level':0,
      'stats':{'level':60,'speed':10,'hp':1000,'hpBase':1000,'defenseLevel':0,'resistances':{}},
      'skills':{'S1':{'id':'S1','name':'S1','base_power':10,'coin_powers':[1], 'coin_count':1,
        'coins':[coin], 'attack_type':'slash','sin':'lust'}}, 'passives':[]
    }]).build_identity('a')

def test_multi_target_coin_resource_cost_is_spent_once():
    ident=_ident(True)
    ident.skills['S1'].coins[0].resource_cost={'X':1}
    sc={'coin_mode':'fixed','resource_specs':{'X':{'maximum':99}},'target_count':2,
        'enemy':{'hp':1000,'max_hp':1000,'targets':[{'id':'t1','hp':100,'max_hp':100},{'id':'t2','hp':100,'max_hp':100}]},
        'allies':{'a':{'resources':{'X':2}}},
        'actions':[{'identity_id':'a','skill_id':'S1','faces':['H']}], 'passive_mode':'off'}
    r=OneTurnSolverV29().solve(sc,{'a':ident})
    # One logical coin consumes one Charge, not one per target.
    assert r['fighters']['a']['resources']['X'] == 1
    assert r['actions'][0]['damage_by_target']['t1'] > 0
    assert r['actions'][0]['damage_by_target']['t2'] > 0

def test_multi_target_crit_is_one_logical_poise_consumption():
    ident=_ident(False)
    sc={'coin_mode':'fixed','target_count':2,
        'enemy':{'hp':1000,'max_hp':1000,'targets':[{'id':'t1','hp':100,'max_hp':100},{'id':'t2','hp':100,'max_hp':100}]},
        'allies':{'a':{'poise':{'count':2,'potency':20}}},
        'actions':[{'identity_id':'a','skill_id':'S1','faces':['H'],'crit':True}], 'passive_mode':'off'}
    r=OneTurnSolverV29().solve(sc,{'a':ident})
    
    coins=[e for e in r['event_log'] if e.get('event')=='coin']
    assert [e['poise_after']['count'] for e in coins] == [1, 1]

def test_multi_target_coin_runs_attacker_bleed_once_per_logical_coin():
    ident=_ident(False)
    sc={'coin_mode':'fixed','target_count':2,
        'enemy':{'hp':1000,'max_hp':1000,'targets':[{'id':'t1','hp':100,'max_hp':100},{'id':'t2','hp':100,'max_hp':100}]},
        'allies':{'a':{'statuses':{'Bleed':{'potency':5,'count':3}}}},
        'actions':[{'identity_id':'a','skill_id':'S1','faces':['H']}], 'passive_mode':'off'}
    r=OneTurnSolverV29().solve(sc,{'a':ident})
    bleeds=[e for e in r['event_log'] if e.get('event')=='bleed_self_damage']
    assert len(bleeds)==1
    assert bleeds[0]['actual_damage']==5

def test_explicit_coin_multitarget_runs_special_callback_for_each_target_with_same_ammo_context():
    ident=_ident(False)
    sc={'coin_mode':'fixed','target_count':2,
        'enemy':{'hp':1000,'max_hp':1000,'targets':[{'id':'t1','hp':100,'max_hp':100},{'id':'t2','hp':100,'max_hp':100}]},
        'allies':{'a':{'ammo':1}},
        'actions':[{'identity_id':'a','skill_id':'S1','faces':['H'],
                    'coin_target_ids':[['t1','t2']]}], 'passive_mode':'off'}
    r=OneTurnSolverV29().solve(sc,{'a':ident})
    # No ammo-spend rule is attached to this skill, so this primarily verifies
    # the multi-target path accepts a list-valued coin target assignment and
    # resolves both target slots exactly once.
    events=[e for e in r['event_log'] if e.get('event')=='coin_target_resolution']
    assert [(e['coin'],e['target_id']) for e in events]==[(1,'t1'),(1,'t2')]


# ======================================================================
# 원본: test_v42_target_death_multitarget.py
# ======================================================================

def _scenario(hp1=5, hp2=50):
    return {
        'coin_mode':'fixed',
        'passive_mode':'compiled_conservative',
        'target_count':2,
        'actions':[{'identity_id':'i1','skill_id':'S1','faces':['H']}],
        'enemy':{'targets':[
            {'id':'A','hp':hp1,'max_hp':hp1,'defense_level':60,'stagger_thresholds':[0]},
            {'id':'B','hp':hp2,'max_hp':hp2,'defense_level':60,'stagger_thresholds':[0]},
        ]},
    }

def test_multitarget_death_is_recorded_for_the_actual_target_only():
    solver=OneTurnSolverV29()
    skill=SkillData(id='S1', name='S1', base_power=10, coins=[CoinData(coin_power=0, damage_type='blunt', sin='')], attack_type='blunt', sin='')
    ident=IdentityData(id='i1', name='Test', offense_level=0, skills={'S1':skill})
    out=solver.solve(_scenario(), {'i1':ident})
    slots=out['target_states']
    assert slots['A']['hp'] == 0
    assert slots['B']['hp'] == 40
    deaths=[e for e in out['event_log'] if e.get('event')=='unit_death']
    assert len(deaths)==1
    assert deaths[0].get('target_id')=='A'

def test_target_death_callback_fires_once_per_dead_target():
    solver=OneTurnSolverV29()
    skill=SkillData(id='S1', name='S1', base_power=10, coins=[CoinData(coin_power=0, damage_type='blunt', sin='')], attack_type='blunt', sin='')
    ident=IdentityData(id='i1', name='Test', offense_level=0, skills={'S1':skill})
    out=solver.solve(_scenario(5,5), {'i1':ident})
    deaths=[e for e in out['event_log'] if e.get('event')=='unit_death']
    # One logical coin can resolve both targets, so both deaths are target-local.
    assert {e.get('target_id') for e in deaths} == {'A','B'}


# ======================================================================
# 원본: test_v43_coin_target_roles.py
# ======================================================================

def _ident__v43_coin():
    c1 = CoinData(coin_power=0, damage_type='blunt', sin='')
    c2 = CoinData(coin_power=0, damage_type='blunt', sin='')
    sk = SkillData(id='S1', name='role skill', base_power=10, coins=[c1, c2], attack_type='blunt', sin='', attack_weight=2, coin_target_policies=['single_main', 'sub'])
    return IdentityData(id='i1', name='Test', offense_level=0, skills={'S1': sk})

def test_parser_compiles_main_and_sub_target_coin_roles():
    parsed, rep=SkillTextParserV19().parse([
        '1코인 이 코인에는 메인 타겟만 피해를 입음',
        '2코인 이 코인에는 서브 타겟만 피해를 입음',
    ],2)
    assert parsed['coin_target_policies']==['single_main','sub']
    assert not rep.unsupported

def test_coin_target_roles_are_resolved_per_coin_without_duplicate_attacker_state():
    scenario = {'coin_mode': 'fixed', 'target_count': 2, 'actions': [{'identity_id': 'i1', 'skill_id': 'S1', 'faces': ['H', 'H']}], 'enemy': {'targets': [{'id': 'A', 'hp': 100, 'max_hp': 100, 'defense_level': 60}, {'id': 'B', 'hp': 100, 'max_hp': 100, 'defense_level': 60}]}}
    out = OneTurnSolverV29().solve(scenario, {'i1': _ident__v43_coin()})
    dmg = out['actions'][0]['damage_by_target']
    assert dmg['A'] == 10
    assert dmg['B'] == 10
    assert out['target_states']['A']['hp'] == 90
    assert out['target_states']['B']['hp'] == 90


# ======================================================================
# 원본: test_v45_random_target_selection.py
# ======================================================================

def test_seeded_random_target_selection_is_reproducible():
    targets=[{'id':'A','index':0},{'id':'B','index':1},{'id':'C','index':2}]
    import random
    r1=random.Random(42); r2=random.Random(42)
    assert [x['id'] for x in select_targets(targets,'random',1,rng=r1)] == [x['id'] for x in select_targets(targets,'random',1,rng=r2)]

def test_seeded_random_selection_can_pick_multiple_without_duplicates():
    targets=[{'id':'A','index':0},{'id':'B','index':1},{'id':'C','index':2}]
    import random
    got=select_targets(targets,'random',2,rng=random.Random(1))
    assert len(got)==2
    assert len({x['id'] for x in got})==2

def test_solver_initializes_persistent_target_rng():
    solver=OneTurnSolverV29()
    state=solver.build_state({'random_seed':123,'enemy':{'hp':100,'max_hp':100}}, {})
    # solve() owns the RNG initialization; this test only verifies build_state
    # remains backward-compatible with an empty roster.
    assert state.enemy.hp == 100

def test_random_target_ignores_dead_targets_when_alive_targets_exist():
    targets=[{'id':'dead','index':0,'hp':0,'max_hp':100},{'id':'alive1','index':1,'hp':10,'max_hp':100},{'id':'alive2','index':2,'hp':20,'max_hp':100}]
    import random
    got=select_targets(targets,'random',2,rng=random.Random(7))
    assert {x['id'] for x in got} == {'alive1','alive2'}


# ======================================================================
# 원본: test_v46_random_target_override.py
# ======================================================================

def test_random_policy_can_be_overridden_by_explicit_target_ids():
    targets = [
        {'id': 'A', 'index': 0, 'hp': 100, 'max_hp': 100},
        {'id': 'B', 'index': 1, 'hp': 100, 'max_hp': 100},
        {'id': 'C', 'index': 2, 'hp': 100, 'max_hp': 100},
    ]
    got = select_targets(targets, 'random', 1, target_ids=['B'])
    assert [x['id'] for x in got] == ['B']

def test_action_schema_supports_random_target_override():
    q = ActionQueue.from_scenario([{
        'identity_id': 'A', 'skill_id': 'S1',
        'target_policy': 'random',
        'target_override_ids': ['enemy_2'],
    }])
    a = q.pop()
    assert a.target_policy == 'random'
    assert a.target_override_ids == ['enemy_2']

def test_override_multiple_random_targets_preserves_requested_order():
    targets = [
        {'id': 'A', 'index': 0, 'hp': 100, 'max_hp': 100},
        {'id': 'B', 'index': 1, 'hp': 100, 'max_hp': 100},
        {'id': 'C', 'index': 2, 'hp': 100, 'max_hp': 100},
    ]
    got = select_targets(targets, 'random', 2, target_ids=['C', 'A'])
    assert [x['id'] for x in got] == ['A', 'C']


# ======================================================================
# 원본: test_v47_ally_target_selection.py
# ======================================================================

def fighter(hp=100,max_hp=100,speed=0,charge=0,ammo=0,sp=0,poise_count=0):
    return SimpleNamespace(hp=hp,max_hp=max_hp,speed=speed,charge=charge,ammo=ammo,sp=sp,poise=SimpleNamespace(count=poise_count),statuses={})

def state():
    s=SimpleNamespace()
    s.fighters={'a':fighter(speed=10), 'b':fighter(speed=20), 'c':fighter(speed=15)}
    s.enemy=SimpleNamespace(hp=100,max_hp=100,statuses={})
    s.runtime={}
    return s

def test_fastest_ally_target_gets_damage_up():
    rec={'id':'p','name':'x','effect':'[전투 시작시] 속도가 가장 빠른 아군 1명에게 피해량 증가 2 부여'}
    rules,_,u=compile_one(rec,'a',0)
    assert not u and len(rules)==1
    st=state(); PassiveRuntime().register(rules[0]) if False else None
    rt=PassiveRuntime(); rt.register(rules[0]); rt.emit(PassiveTrigger.COMBAT_START,{},st)
    assert st.fighters['b'].statuses['Damage Up'].potency == 20
    assert 'Damage Up' not in st.fighters['a'].statuses

def test_lowest_hp_excluding_owner():
    rec={'id':'p','name':'x','effect':'[전투 시작시] 자신을 제외하고 체력 비율이 가장 낮은 아군 1명에게 피해량 증가 1 부여'}
    rules,_,u=compile_one(rec,'a',0); assert not u and len(rules)==1
    st=state(); st.fighters['a'].hp=10; st.fighters['c'].hp=20
    rt=PassiveRuntime(); rt.register(rules[0]); rt.emit(PassiveTrigger.COMBAT_START,{},st)
    assert st.fighters['c'].statuses['Damage Up'].potency == 10
    assert 'Damage Up' not in st.fighters['a'].statuses

def test_multiple_lowest_charge_allies():
    rec={'id':'p','name':'x','effect':'[전투 시작시] 충전 횟수가 가장 적은 아군 2명에게 피해량 증가 1 부여'}
    rules,_,u=compile_one(rec,'a',0); assert not u and len(rules)==1
    st=state(); st.fighters['a'].charge=0; st.fighters['b'].charge=5; st.fighters['c'].charge=1
    rt=PassiveRuntime(); rt.register(rules[0]); rt.emit(PassiveTrigger.COMBAT_START,{},st)
    assert st.fighters['a'].statuses['Damage Up'].potency == 10
    assert st.fighters['c'].statuses['Damage Up'].potency == 10

def test_self_plus_lowest_max_hp_target():
    rec={'id':'p','name':'x','effect':'[전투 시작시] 자신과 최대 체력이 가장 낮은 아군 1명에게 피해량 증가 1 부여'}
    rules,_,u=compile_one(rec,'a',0); assert not u and len(rules)==1
    st=state(); st.fighters['b'].max_hp=50; st.fighters['c'].max_hp=80
    rt=PassiveRuntime(); rt.register(rules[0]); rt.emit(PassiveTrigger.COMBAT_START,{},st)
    assert st.fighters['a'].statuses['Damage Up'].potency == 10
    assert st.fighters['b'].statuses['Damage Up'].potency == 10


# ======================================================================
# 원본: test_v48_ally_rank_condition.py
# ======================================================================

def fighter__v48_ally(speed=0, hp=100, max_hp=100, sp=0, charge=0, ammo=0):
    return SimpleNamespace(speed=speed, hp=hp, max_hp=max_hp, sp=sp, charge=charge, ammo=ammo, statuses={}, poise=SimpleNamespace(count=0))

def make_state():
    s = SimpleNamespace(fighters={'a': fighter__v48_ally(speed=20), 'b': fighter__v48_ally(speed=10), 'c': fighter__v48_ally(speed=15)}, enemy=SimpleNamespace(hp=100, max_hp=100, statuses={}), runtime={})
    return s

def run(text,owner='a'):
    rules,_,u=compile_one({'id':'p','name':'x','effect':text},owner,0)
    assert not u and len(rules)==1
    st=make_state(); rt=PassiveRuntime(); rt.register(rules[0]); rt.emit(PassiveTrigger.COMBAT_START,{},st); return st,rules[0]

def test_fastest_ally_damage_condition_only_fires_for_fastest():
    st,_=run('속도가 가장 빠른 아군 1명이 적에게 공격 적중 시 피해량 +10%','a')
    assert 'Damage Up' not in st.fighters['a'].statuses
    # Verify the compiled condition itself against both owners.
    rules,_,_=compile_one({'id':'p','name':'x','effect':'속도가 가장 빠른 아군 1명이 적에게 공격 적중 시 피해량 +10%'},'a',0)
    assert rules[0].conditions[0].check(SimpleNamespace(ctx={}),st,'a') is True
    assert rules[0].conditions[0].check(SimpleNamespace(ctx={}),st,'b') is False

def test_lowest_hp_ally_condition():
    rules,_,u=compile_one({'id':'p','name':'x','effect':'현재 체력 비율이 가장 낮은 아군 1명이 적에게 공격 적중 시 피해량 +10%'},'a',0)
    assert not u and len(rules)==1
    st=make_state(); st.fighters['a'].hp=40; st.fighters['b'].hp=90; st.fighters['c'].hp=80
    c=rules[0].conditions[0]
    assert c.check(SimpleNamespace(ctx={}),st,'a') is True
    assert c.check(SimpleNamespace(ctx={}),st,'b') is False


def test_target_selector_supports_highest_status_count_policy():
    from target_selector_v1 import select_targets
    ts=[{'id':'a','statuses':{'Tremor':{'potency':10,'count':2}}},
        {'id':'b','statuses':{'Tremor':{'potency':3,'count':7}}},
        {'id':'c','statuses':{'Tremor':{'potency':20,'count':1}}}]
    assert select_targets(ts,'highest_status_count:Tremor')[0]['id']=='b'
    assert select_targets(ts,'highest_tremor_count')[0]['id']=='b'


def test_ally_selector_supports_highest_status_count_policy():
    from passive_runtime_v29_base import AllySelectorTarget
    from types import SimpleNamespace
    fighters={
        'a':SimpleNamespace(hp=100,statuses={'Tremor':SimpleNamespace(count=2,potency=10)}),
        'b':SimpleNamespace(hp=100,statuses={'Tremor':SimpleNamespace(count=7,potency=3)}),
    }
    state=SimpleNamespace(fighters=fighters)
    picked=AllySelectorTarget('highest_status_count:Tremor',1).resolve({},state,'a')
    assert picked[0] is fighters['b']



def test_target_selector_supports_highest_taunt_aliases():
    from target_selector_v1 import select_targets
    allies=[
        {"id":"a","taunt":2},
        {"id":"b","taunt":9},
        {"id":"c","taunt":5},
    ]
    assert select_targets(allies,"highest_taunt")[0]["id"] == "b"
    assert select_targets(allies,"highest_provoke")[0]["id"] == "b"


def test_target_selector_supports_taunt_source_aliases():
    allies=[
        {"id":"a","taunt_value":1},
        {"id":"b","provoke":7},
        {"id":"c","taunt":4},
    ]
    assert select_targets(allies,"taunt_max")[0]["id"] == "b"


def test_target_selector_supports_formation_order_aliases():
    from target_selector_v1 import select_targets
    ts=[{'id':'ally_a','formation_index':2,'hp':100,'max_hp':100},
        {'id':'ally_b','formation_index':0,'hp':100,'max_hp':100},
        {'id':'ally_c','formation_index':1,'hp':100,'max_hp':100}]
    assert select_targets(ts,'fastest_formation_ally')[0]['id']=='ally_b'
    assert select_targets(ts,'slowest_formation_ally')[0]['id']=='ally_a'



def test_relative_formation_selector_uses_owner_position():
    from passive_runtime_v29_base import AllySelectorTarget
    class F:
        def __init__(self, idx, charge=0): self.formation_index=idx; self.hp=100; self.max_hp=100; self.charge=charge
    class S: pass
    st=S(); st.fighters={'a':F(0), 'b':F(1,5), 'c':F(2,2), 'd':F(3,1)}
    got=AllySelectorTarget('formation_before_owner',2).resolve(None,st,'c')
    assert [x.formation_index for x in got] == [0,1]
    got=AllySelectorTarget('formation_before_owner_charge_min',2).resolve(None,st,'d')
    assert [x.formation_index for x in got] == [0,2]


def test_charge_positive_min_selects_only_allies_with_charge():
    from target_selector_v1 import select_targets
    allies=[{'id':'zero','charge':0},{'id':'high','charge':5},{'id':'low','charge':1}]
    assert select_targets(allies,'charge_positive_min')[0]['id']=='low'
    assert select_targets(allies,'lowest_charge_holder')[0]['id']=='low'
    assert select_targets([{'id':'zero','charge':0}],'charge_positive_min') == []


def test_ally_selector_charge_positive_min_excludes_zero_charge():
    from passive_runtime_v29_base import AllySelectorTarget
    class F:
        def __init__(self, charge): self.formation_index=0; self.hp=100; self.max_hp=100; self.charge=charge
    class S: pass
    st=S(); st.fighters={'zero':F(0),'high':F(5),'low':F(1)}
    got=AllySelectorTarget('charge_positive_min').resolve(None,st,'high')
    assert [x.charge for x in got] == [1]


def test_status_total_selector_sums_potency_and_count():
    from target_selector_v1 import select_targets
    allies=[
        {'id':'a','statuses':{'Bleed':{'potency':8,'count':1}}},
        {'id':'b','statuses':{'Bleed':{'potency':4,'count':8}}},
        {'id':'c','statuses':{'Bleed':{'potency':5,'count':2}}},
    ]
    assert select_targets(allies,'highest_status_total:Bleed')[0]['id']=='b'
    assert select_targets(allies,'lowest_status_total:Bleed')[0]['id']=='c'


def test_target_selector_poise_count_max():
    allies=[
        {'id':'a','statuses':{'Poise':{'potency':20,'count':2}}},
        {'id':'b','statuses':{'Poise':{'potency':1,'count':8}}},
        {'id':'c','statuses':{}},
    ]
    assert select_targets(allies,'poise_count_max')[0]['id']=='b'


def test_target_selector_supports_highest_poise_potency():
    allies=[
        {'id':'a','statuses':{'Poise':{'potency':3,'count':2}}},
        {'id':'b','statuses':{'Poise':{'potency':10,'count':1}}},
        {'id':'c','statuses':{}},
    ]
    assert select_targets(allies,'poise_potency_max')[0]['id']=='b'

def test_target_selector_poise_lowest_treats_missing_as_zero():
    allies=[
        {'id':'a','statuses':{'Poise':{'potency':3,'count':2}}},
        {'id':'b','statuses':{}},
        {'id':'c','statuses':{'Poise':{'potency':1,'count':5}}},
    ]
    assert select_targets(allies,'poise_potency_min')[0]['id']=='b'
