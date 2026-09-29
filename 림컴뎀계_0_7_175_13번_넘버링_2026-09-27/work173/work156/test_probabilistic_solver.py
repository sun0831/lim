from activation_ledger_v1 import ActivationLedger
"""병합 테스트: probabilistic_solver

원본 파일 (내용은 AST 병합기로 합쳤고 테스트 본문은 바꾸지 않음):
  - test_v29_probabilistic_clash_coin_resources.py
  - test_v29_probabilistic_clash_effects.py
  - test_v29_probabilistic_coin_state.py
  - test_v29_probabilistic_generated_attribution.py
  - test_v29_probabilistic_hp_stagger.py
  - test_v29_probabilistic_state_axes.py
  - test_v29_probabilistic_trigger_activation_persistence.py
  - test_v29_probabilistic_triggers.py
이름 충돌 helper 는 `이름__vNN` 으로 분리했다. 매핑은 tools/MERGE_MAP.json 참고.
"""
from one_turn_solver_v29 import IdentityCatalogV29, OneTurnSolverV29
from copy import deepcopy
from limbus_damage_engine_v29 import IdentityData, SkillData, CoinData, EnemyState, FighterState, BattleState
from types import SimpleNamespace



# ======================================================================
# 원본: test_v29_probabilistic_clash_coin_resources.py
# ======================================================================

def _ids():
    rec=[{'id':'a','name':'A','stats':{'level':60,'hp':1000,'max_hp':1000,'defenseLevel':0,'resistances':{}},
      'skills':{'S1':{'id':'S1','name':'S1','base_power':10,'coin_count':2,'coin_powers':[1,1],
        'coins':[{'coin_power':1,'damage_type':'slash','sin':'lust','resource_cost':{'X':1}},
                 {'coin_power':1,'damage_type':'slash','sin':'lust','resource_cost':{'X':1}}],
        'attack_type':'slash','sin':'lust'}},'passives':[]}]
    c=IdentityCatalogV29(rec); return {'a':c.build_identity('a')}

def test_clash_loss_consumes_removed_coin_resource_and_next_coin_keeps_remaining():
    ids=_ids()
    ids['a'].skills['S1'].coins[0].resource_cost={'X':1}
    ids['a'].skills['S1'].coins[1].resource_cost={'X':1}
    sc={'enemy':{'hp':1000,'max_hp':1000,'level':60,'defense_level':0,
        'physical_res':{'slash':1,'pierce':1,'blunt':1},'sin_res':{'lust':1},
        'statuses':{'Bleed':{'potency':1,'count':20}}},
      'allies':{'a':{'sp':0,'hp':1000,'max_hp':1000,'resources':{'X':2}}},
      'resource_specs':{'X':{'maximum':10}},
      'actions':[{'identity_id':'a','skill_id':'S1','faces':['H','H'],
        'bleed_clash_probability':{'initial_defender_coins':2,'skill_power':10,
          'outcome_probabilities':[{'win':0,'draw':0,'loss':1}, {'win':1,'draw':0,'loss':0}]}}],
      'passive_mode':'off'}
    r=OneTurnSolverV29().solve(sc,ids)
    branches=r['turn_bleed_state']['actions'][0]['branches']
    assert branches
    # first exchange loses coin 1 -> X 1; second wins -> coin 2 survives and
    # is resolved in the unopposed suffix -> X 0.
    sig=branches[0]
    trace=sig['coin_trace']
    assert trace
    assert trace[0]['resources_before']['X'] == 1
    assert trace[0]['resources_after']['X'] == 0


# ======================================================================
# 원본: test_v29_probabilistic_clash_effects.py
# ======================================================================

def _solver():
    ident = IdentityData('a', 'A', 0, {
        's': SkillData('s', 'S', 10, [CoinData(1,'slash','gloom'), CoinData(1,'slash','gloom')], 'slash', 'gloom',
                       effects_on_clash_win=[{'type':'sp','amount':10}])
    })
    enemy = EnemyState(100,100,sp=0)
    state = BattleState(enemy, {'a': FighterState(sp=0)})
    return OneTurnSolverV29(), ident, state

def test_probabilistic_clash_win_skill_effect_changes_branch_state():
    solver, ident, state = _solver()
    scenario = {
        'actions':[{'identity_id':'a','skill_id':'s','faces':['H','H'],
                    'bleed_clash_probability': {'coins':[{'coin_power':0},{'coin_power':0}],
                        'initial_attacker_coins':2,'initial_defender_coins':1,
                        'outcome_probabilities': {'win':1,'draw':0,'loss':0}, '_action_stub': {'identity_id':'a'}}}],
        'identities':[ident], 'bleed_count_infinite': True,
    }
    # Exercise the stateful method directly because this is a branch-state contract test.
    rt=solver._probabilistic_trigger_runtime([])
    result=solver._run_probabilistic_bleed_stateful(state, ident.skills['s'], scenario['actions'][0]['bleed_clash_probability'], state.fighters['a'], rt, {'a':ident})
    assert result['exchange_count_distribution'][1] == 1.0
    terminals = result['_terminal_states']
    # terminal state must have received the Clash Win SP effect
    st = next(iter(next(iter(terminals.values()))))[0]
    assert st.fighters['a'].sp == 10

def test_generated_action_applies_skill_effects_before_coins():
    solver, ident, state = _solver()
    gen = deepcopy(ident.skills['s'])
    gen.effects_on_use=[{'type':'sp','amount':5}]
    rt=solver._probabilistic_trigger_runtime([])
    solver._execute_probabilistic_generated_action(state, rt, {'a':ident}, 'a', gen, depth=1)
    assert state.fighters['a'].sp == 5


# ======================================================================
# 원본: test_v29_probabilistic_coin_state.py
# ======================================================================

def _catalog():
    from one_turn_solver_v29 import IdentityCatalogV29
    records=[{'id':'a','name':'A','offense_level':0,
      'stats':{'level':60,'speed':10,'hp':1000,'hpBase':1000,'defenseLevel':0,'resistances':{}},
      'skills':{'S1':{'id':'S1','name':'S1','base_power':10,'coin_powers':[1,1],'coin_count':2,
        'coins':[{'coin_power':1,'damage_type':'slash','sin':'lust','resource_cost':{'X':1}},
                 {'coin_power':1,'damage_type':'slash','sin':'lust'}],
        'attack_type':'slash','sin':'lust'}},'passives':[]}]
    from one_turn_solver_v29 import IdentityCatalogV29
    cat=IdentityCatalogV29(records)
    return {'a':cat.build_identity('a')}

def test_probabilistic_terminal_suffix_records_coin_state_changes():
    from one_turn_solver_v29 import OneTurnSolverV29
    ids=_catalog()
    ids['a'].skills['S1'].coins[0].resource_cost={'X':1}
    sc={'enemy':{'hp':1000,'max_hp':1000,'level':60,'defense_level':0,
        'physical_res':{'slash':1,'pierce':1,'blunt':1},'sin_res':{'lust':1},
        'statuses':{'Bleed':{'potency':1,'count':10}}},
        'allies':{'a':{'sp':0,'hp':1000,'max_hp':1000,'resources':{'X':2}}},
        'resource_specs':{'X':{'maximum':10}},
        'actions':[{'identity_id':'a','skill_id':'S1','faces':['H','H'],
          'bleed_clash_probability':{'initial_defender_coins':1,'skill_power':10,
            'outcome_probabilities':[{'win':1,'draw':0,'loss':0}]}}], 'passive_mode':'off'}
    r=OneTurnSolverV29().solve(sc,ids)
    branches=r['turn_bleed_state']['actions'][0]['branches']
    traces=[x.get('coin_trace',[]) for x in branches if x.get('coin_trace')]
    assert traces
    assert traces[0][0]['resources_before']['X'] == 2
    assert traces[0][0]['resources_after']['X'] == 1
    assert traces[0][1]['resources_before']['X'] == 1


# ======================================================================
# 원본: test_v29_probabilistic_generated_attribution.py
# ======================================================================

def test_generated_after_coin_action_is_attributed_to_generated_identity():
    from one_turn_solver_v29 import OneTurnSolverV29
    from trigger_runtime_v1 import TriggerRuntime, TriggerRule, TriggerCondition, TriggerEffect

    solver = OneTurnSolverV29.__new__(OneTurnSolverV29)

    class FakeEngine:
        @staticmethod
        def simulate_coin(state, identity, skill, coin, face, is_crit, coin_index, prior_heads):
            dmg = 10
            state.enemy.hp -= dmg

    solver.core = SimpleNamespace(machine=SimpleNamespace(engine=FakeEngine()))
    a = SimpleNamespace(id='a')
    b = SimpleNamespace(id='b')
    sa = SimpleNamespace(id='S1', name='A', _slot='S1', coins=[object()])
    sb = SimpleNamespace(id='S1', name='B', _slot='S1', coins=[object()])
    a.skills = {'S1': sa}
    b.skills = {'S1': sb}
    rule = TriggerRule(
        'r1', 'a', 'after_coin',
        [TriggerCondition('equals', 1, field='coin_index'), TriggerCondition('equals', 'a', field='identity_id')],
        [TriggerEffect('queue_action', {'identity_id': 'b', 'skill_id': 'S1'})], 1,
    )
    rt = TriggerRuntime([rule])
    state = SimpleNamespace(
        enemy=SimpleNamespace(hp=100, stagger_level=0, stagger_index=0, stagger_thresholds=[], staggered=False),
        fighters={
            'a': SimpleNamespace(resources={}, statuses={}, ammo=0),
            'b': SimpleNamespace(resources={}, statuses={}, ammo=0),
        },
        runtime={
            'probabilistic_trigger_runtime_template': rt,
            'probabilistic_identity_map': {'a': a, 'b': b},
            'condition_flags': {},
        },
        turn_damage=0,
    )
    clone, damage, trace = solver._execute_unopposed_coins_with_triggers(
        state, a, sa, ['H'], 0
    )

    assert damage == 20
    assert clone.enemy.hp == 80
    assert clone.runtime['probabilistic_generated_damage_by_identity']['b'] == 10
    assert clone.runtime['probabilistic_generated_damage_by_skill']['b:S1'] == 10
    assert any(row['identity_id'] == 'b' for row in trace)


# ======================================================================
# 원본: test_v29_probabilistic_hp_stagger.py
# ======================================================================

def _catalog__v29_probabilistic():
    from one_turn_solver_v29 import IdentityCatalogV29
    records = [{'id': 'a', 'name': 'A', 'offense_level': 0, 'stats': {'level': 60, 'speed': 10, 'hp': 1000, 'hpBase': 1000, 'defenseLevel': 0, 'resistances': {}}, 'skills': {'S1': {'id': 'S1', 'name': 'S1', 'base_power': 10, 'coin_powers': [1], 'coin_count': 1, 'coins': [{'coin_power': 1, 'damage_type': 'slash', 'sin': 'lust'}], 'attack_type': 'slash', 'sin': 'lust'}}, 'passives': []}]
    cat = IdentityCatalogV29(records)
    return {'a': cat.build_identity('a')}

def test_probabilistic_turn_carries_enemy_hp_between_actions():
    from one_turn_solver_v29 import OneTurnSolverV29
    sc = {'enemy': {'hp': 5, 'max_hp': 5, 'level': 60, 'defense_level': 0, 'physical_res': {'slash': 1, 'pierce': 1, 'blunt': 1}, 'sin_res': {'lust': 1}, 'statuses': {'Bleed': {'potency': 1, 'count': 10}}}, 'allies': {'a': {'sp': 0, 'hp': 1000, 'max_hp': 1000}}, 'actions': [{'identity_id': 'a', 'skill_id': 'S1', 'faces': ['H'], 'bleed_clash_probability': {'initial_defender_coins': 1, 'skill_power': 0, 'outcome_probabilities': [{'win': 1, 'draw': 0, 'loss': 0}]}}, {'identity_id': 'a', 'skill_id': 'S1', 'faces': ['H'], 'bleed_clash_probability': {'initial_defender_coins': 1, 'skill_power': 0, 'outcome_probabilities': [{'win': 1, 'draw': 0, 'loss': 0}]}}], 'passive_mode': 'off'}
    r = OneTurnSolverV29().solve(sc, _catalog__v29_probabilistic())
    assert r['turn_bleed_state']['actions'][0]['expected_damage'] == 5.0
    assert r['turn_bleed_state']['actions'][1]['expected_damage'] == 0.0

def test_probabilistic_terminal_state_records_new_stagger():
    from one_turn_solver_v29 import OneTurnSolverV29
    sc = {'enemy': {'hp': 20, 'max_hp': 100, 'level': 60, 'defense_level': 0, 'stagger_thresholds': [15], 'physical_res': {'slash': 1, 'pierce': 1, 'blunt': 1}, 'sin_res': {'lust': 1}, 'statuses': {'Bleed': {'potency': 1, 'count': 10}}}, 'allies': {'a': {'sp': 0, 'hp': 1000, 'max_hp': 1000}}, 'actions': [{'identity_id': 'a', 'skill_id': 'S1', 'faces': ['H'], 'bleed_clash_probability': {'initial_defender_coins': 1, 'skill_power': 0, 'outcome_probabilities': [{'win': 1, 'draw': 0, 'loss': 0}]}}], 'passive_mode': 'off'}
    r = OneTurnSolverV29().solve(sc, _catalog__v29_probabilistic())
    row = r['turn_bleed_state']['actions'][0]['branches'][0]
    assert row['enemy_staggered_after'] is True


# ======================================================================
# 원본: test_v29_probabilistic_state_axes.py
# ======================================================================

def _catalog__v29_probabilistic_2():
    from one_turn_solver_v29 import IdentityCatalogV29
    records = [{'id': 'a', 'name': 'A', 'offense_level': 0, 'stats': {'level': 60, 'speed': 10, 'hp': 1000, 'hpBase': 1000, 'defenseLevel': 0, 'resistances': {}}, 'skills': {'S1': {'id': 'S1', 'name': 'S1', 'base_power': 10, 'coin_powers': [1], 'coin_count': 1, 'coins': [{'coin_power': 1, 'damage_type': 'slash', 'sin': 'lust'}], 'attack_type': 'slash', 'sin': 'lust'}}, 'passives': []}]
    cat = IdentityCatalogV29(records)
    return {'a': cat.build_identity('a')}

def test_probabilistic_turn_carries_sp_between_actions():
    from one_turn_solver_v29 import OneTurnSolverV29
    sc = {'enemy': {'hp': 1000, 'max_hp': 1000, 'level': 60, 'defense_level': 0, 'physical_res': {'slash': 1, 'pierce': 1, 'blunt': 1}, 'sin_res': {'lust': 1}, 'sp': 0, 'statuses': {'Bleed': {'potency': 1, 'count': 10}}}, 'allies': {'a': {'sp': 0, 'hp': 1000, 'max_hp': 1000}}, 'actions': [{'identity_id': 'a', 'skill_id': 'S1', 'faces': ['H'], 'bleed_clash_probability': {'initial_defender_coins': 1, 'skill_power': 10, 'outcome_probabilities': [{'win': 1, 'draw': 0, 'loss': 0}]}, 'sp_delta_by_outcome': {'W': -30}}, {'identity_id': 'a', 'skill_id': 'S1', 'faces': ['H'], 'bleed_clash_probability': {'initial_defender_coins': 2, 'skill_power': 10, 'attacker_base_power': 9, 'max_exchanges': 99}}], 'passive_mode': 'off'}
    r = OneTurnSolverV29().solve(sc, _catalog__v29_probabilistic_2())
    second = r['turn_bleed_state']['actions'][1]
    assert second['state_count'] >= 1
    assert abs(r['turn_bleed_state']['expected_final_bleed_count'] - 8.0) < 2.0

def test_probabilistic_turn_carries_special_resource_cost():
    from one_turn_solver_v29 import OneTurnSolverV29
    ids = _catalog__v29_probabilistic_2()
    skill = ids['a'].skills['S1']
    skill.resource_cost = {'X': 2}
    sc = {'enemy': {'hp': 1000, 'max_hp': 1000, 'level': 60, 'defense_level': 0, 'physical_res': {'slash': 1, 'pierce': 1, 'blunt': 1}, 'sin_res': {'lust': 1}, 'statuses': {'Bleed': {'potency': 1, 'count': 10}}}, 'allies': {'a': {'sp': 0, 'hp': 1000, 'max_hp': 1000, 'resources': {'X': 5}}}, 'resource_specs': {'X': {'maximum': 10}}, 'actions': [{'identity_id': 'a', 'skill_id': 'S1', 'faces': ['H'], 'bleed_clash_probability': {'initial_defender_coins': 1, 'skill_power': 10, 'outcome_probabilities': [{'win': 1, 'draw': 0, 'loss': 0}]}}, {'identity_id': 'a', 'skill_id': 'S1', 'faces': ['H'], 'bleed_clash_probability': {'initial_defender_coins': 1, 'skill_power': 10, 'outcome_probabilities': [{'win': 1, 'draw': 0, 'loss': 0}]}}], 'passive_mode': 'off'}
    r = OneTurnSolverV29().solve(sc, ids)
    assert r['turn_bleed_state']['state_count'] == 1


# ======================================================================
# 원본: test_v29_probabilistic_trigger_activation_persistence.py
# ======================================================================

def test_probabilistic_clash_trigger_max_activation_persists_across_exchanges():
    from one_turn_solver_v29 import OneTurnSolverV29
    from trigger_runtime_v1 import TriggerRuntime, TriggerRule, TriggerCondition, TriggerEffect
    solver = OneTurnSolverV29.__new__(OneTurnSolverV29)
    solver._apply_probabilistic_trigger_effects = OneTurnSolverV29._apply_probabilistic_trigger_effects.__get__(solver)
    solver._probabilistic_state_signature = OneTurnSolverV29._probabilistic_state_signature
    solver._restore_probabilistic_state_signature = OneTurnSolverV29._restore_probabilistic_state_signature
    rule = TriggerRule('once','a','after_clash',[TriggerCondition('always')],[TriggerEffect('set_flag', {'flag':'ONCE','value':True})],1)
    rt=TriggerRuntime([rule])
    fighter=SimpleNamespace(id='a',sp=0,charge=0,ammo=0,poise=SimpleNamespace(potency=0,count=0),defense_level_bonus=0,resources={},sin_resources={},statuses={})
    enemy=SimpleNamespace(sp=0,hp=100,stagger_level=0,stagger_index=0,stagger_thresholds=[],defense_level_bonus=0,physical_res={'slash':1},sin_res={},statuses={})
    state=SimpleNamespace(fighters={'a':fighter},enemy=enemy,runtime={'condition_flags':{},'probabilistic_trigger_runtime_template':rt},turn_damage=0)
    sig=solver._probabilistic_state_signature(state)
    clone=SimpleNamespace(fighters={'a':SimpleNamespace(id='a',sp=0,charge=0,ammo=0,poise=SimpleNamespace(potency=0,count=0),defense_level_bonus=0,resources={},sin_resources={},statuses={})},enemy=SimpleNamespace(sp=0,hp=100,stagger_level=0,stagger_index=0,stagger_thresholds=[],defense_level_bonus=0,physical_res={'slash':1},sin_res={},statuses={}),runtime={'condition_flags':{}},turn_damage=0)
    solver._restore_probabilistic_state_signature(clone,sig)
    rt1=TriggerRuntime([TriggerRule('once','a','after_clash',[TriggerCondition('always')],[TriggerEffect('set_flag', {'flag':'ONCE','value':True})],1)])
    fired=rt1.fire('after_clash', {'identity_id':'a'})
    clone.activation_ledger = ActivationLedger(counts={'once': 1})
    sig2=solver._probabilistic_state_signature(clone)
    clone2=deepcopy(clone)
    clone2.activation_ledger = ActivationLedger()
    solver._restore_probabilistic_state_signature(clone2,sig2)
    rt2=TriggerRuntime([TriggerRule('once','a','after_clash',[TriggerCondition('always')],[TriggerEffect('set_flag', {'flag':'ONCE','value':True})],1)], clone2.activation_ledger)
    assert rt2.fire('after_clash', {'identity_id':'a'}) == []


# ======================================================================
# 원본: test_v29_probabilistic_triggers.py
# ======================================================================

def _catalog__v29_probabilistic_3():
    from one_turn_solver_v29 import IdentityCatalogV29
    records = []
    for iid, name, power in [('a', 'A', 10), ('b', 'B', 20)]:
        records.append({'id': iid, 'name': name, 'offense_level': 0, 'stats': {'level': 60, 'speed': 10, 'hp': 1000, 'hpBase': 1000, 'defenseLevel': 0, 'resistances': {}}, 'skills': {'S1': {'id': 'S1', 'name': 'S1', 'base_power': power, 'coin_powers': [1], 'coin_count': 1, 'coins': [{'coin_power': 1, 'damage_type': 'slash', 'sin': 'lust'}], 'attack_type': 'slash', 'sin': 'lust'}}, 'passives': []})
    cat = IdentityCatalogV29(records)
    return {x: cat.build_identity(x) for x in ('a', 'b')}

def test_probabilistic_branch_trigger_queues_generated_attack_and_carries_flag():
    from one_turn_solver_v29 import OneTurnSolverV29
    ids = _catalog__v29_probabilistic_3()
    sc = {'enemy': {'hp': 1000, 'max_hp': 1000, 'level': 60, 'defense_level': 0, 'physical_res': {'slash': 1, 'pierce': 1, 'blunt': 1}, 'sin_res': {'lust': 1}}, 'allies': {'a': {'sp': 0, 'hp': 1000, 'max_hp': 1000}, 'b': {'sp': 0, 'hp': 1000, 'max_hp': 1000}}, 'actions': [{'identity_id': 'a', 'skill_id': 'S1', 'faces': ['H'], 'bleed_clash_probability': {'initial_defender_coins': 1, 'skill_power': 10, 'outcome_probabilities': [{'win': 1, 'draw': 0, 'loss': 0}]}}], 'trigger_rules': [{'id': 'assist', 'owner_id': 'b', 'event': 'after_skill', 'conditions': [{'type': 'actual_damage_gt_zero'}], 'effects': [{'type': 'set_flag', 'flag': 'TRIGGERED', 'value': True}, {'type': 'queue_action', 'identity_id': 'b', 'skill_name': 'S1', 'trigger_kind': 'assist'}]}], 'passive_mode': 'off'}
    r = OneTurnSolverV29().solve(sc, ids)
    assert r['expected_turn_damage'] >= 11
    assert any((x[0] == 'TRIGGERED' for x in r['turn_bleed_state'].get('final_condition_flags', [])))

def test_probabilistic_generated_action_can_trigger_another_generated_action():
    from one_turn_solver_v29 import OneTurnSolverV29
    ids = _catalog__v29_probabilistic_3()
    sc = {'enemy': {'hp': 1000, 'max_hp': 1000, 'level': 60, 'defense_level': 0, 'physical_res': {'slash': 1, 'pierce': 1, 'blunt': 1}, 'sin_res': {'lust': 1}}, 'allies': {'a': {'sp': 0, 'hp': 1000, 'max_hp': 1000}, 'b': {'sp': 0, 'hp': 1000, 'max_hp': 1000}}, 'actions': [{'identity_id': 'a', 'skill_id': 'S1', 'faces': ['H'], 'bleed_clash_probability': {'initial_defender_coins': 1, 'skill_power': 10, 'outcome_probabilities': [{'win': 1, 'draw': 0, 'loss': 0}]}}], 'trigger_rules': [{'id': 'a_to_b', 'owner_id': 'b', 'event': 'after_skill', 'conditions': [{'type': 'actual_damage_gt_zero'}, {'type': 'owner_id', 'value': 'a'}], 'effects': [{'type': 'queue_action', 'identity_id': 'b', 'skill_name': 'S1'}], 'max_activations': 1}, {'id': 'b_to_a', 'owner_id': 'a', 'event': 'after_skill', 'conditions': [{'type': 'actual_damage_gt_zero'}, {'type': 'owner_id', 'value': 'b'}], 'effects': [{'type': 'queue_action', 'identity_id': 'a', 'skill_name': 'S1'}], 'max_activations': 1}], 'passive_mode': 'off', 'max_trigger_depth': 4}
    r = OneTurnSolverV29().solve(sc, ids)
    row = r['turn_bleed_state']['actions'][0]['branches'][0]
    assert row['generated_trace']
    assert len(row['generated_trace']) >= 2
    assert r['expected_turn_damage'] > 20

def test_probabilistic_generated_coin_trigger_applies_extra_damage():
    from one_turn_solver_v29 import OneTurnSolverV29
    ids = _catalog__v29_probabilistic_3()
    sc = {'enemy': {'hp': 1000, 'max_hp': 1000, 'level': 60, 'defense_level': 0, 'physical_res': {'slash': 1, 'pierce': 1, 'blunt': 1}, 'sin_res': {'lust': 1}}, 'allies': {'a': {'sp': 0, 'hp': 1000, 'max_hp': 1000}, 'b': {'sp': 0, 'hp': 1000, 'max_hp': 1000}}, 'actions': [{'identity_id': 'a', 'skill_id': 'S1', 'faces': ['H'], 'bleed_clash_probability': {'initial_defender_coins': 1, 'skill_power': 10, 'outcome_probabilities': [{'win': 1, 'draw': 0, 'loss': 0}]}}], 'trigger_rules': [{'id': 'assist', 'owner_id': 'b', 'event': 'after_skill', 'conditions': [{'type': 'actual_damage_gt_zero'}], 'effects': [{'type': 'queue_action', 'identity_id': 'b', 'skill_name': 'S1'}], 'max_activations': 1}, {'id': 'coin_extra', 'owner_id': 'b', 'event': 'after_coin', 'conditions': [{'type': 'actual_damage_gt_zero'}], 'effects': [{'type': 'extra_damage_scale', 'scale': 0.5}], 'max_activations': 1}], 'passive_mode': 'off'}
    r = OneTurnSolverV29().solve(sc, ids)
    assert r['expected_turn_damage'] >= 16

def test_probabilistic_after_clash_changes_next_exchange_probability_state():
    from one_turn_solver_v29 import OneTurnSolverV29
    ids = _catalog__v29_probabilistic_3()
    solver = OneTurnSolverV29()
    state = solver.build_state({'enemy': {'hp': 1000, 'max_hp': 1000, 'level': 60, 'defense_level': 0, 'physical_res': {'slash': 1, 'pierce': 1, 'blunt': 1}, 'sin_res': {'lust': 1}}, 'allies': {'a': {'sp': -45, 'hp': 1000, 'max_hp': 1000}}, 'actions': []}, ids)
    rules = solver._probabilistic_trigger_runtime([{'id': 'boost_sp', 'owner_id': 'a', 'event': 'after_clash', 'conditions': [{'type': 'equals', 'field': 'outcome', 'value': 'W'}], 'effects': [{'type': 'sp_set', 'identity_id': 'a', 'value': 45}], 'max_activations': 1}])
    skill = ids['a'].skills['S1']
    cfg = {'initial_defender_coins': 2, 'initial_attacker_coins': 2, 'attacker_base_power': 10, 'skill_power': 10, 'coins': [{'coin_power': 0, 'damage_type': 'slash', 'sin': 'lust'}, {'coin_power': 0, 'damage_type': 'slash', 'sin': 'lust'}], '_action_stub': {'identity_id': 'a'}}
    result = solver._run_probabilistic_bleed_stateful(state, skill, cfg, state.fighters['a'], rules, ids)
    states = []
    for rows in result['_terminal_states'].values():
        if isinstance(rows, list):
            states.extend(rows)
    assert any((int(st.fighters['a'].sp) == 45 and mass > 0 for st, mass in states))

def test_probabilistic_terminal_key_keeps_all_trigger_mutated_states():
    from one_turn_solver_v29 import OneTurnSolverV29
    ids = _catalog__v29_probabilistic_3()
    solver = OneTurnSolverV29()
    state = solver.build_state({'enemy': {'hp': 1000, 'max_hp': 1000, 'level': 60, 'defense_level': 0, 'physical_res': {'slash': 1, 'pierce': 1, 'blunt': 1}, 'sin_res': {'lust': 1}}, 'allies': {'a': {'sp': 0, 'hp': 1000, 'max_hp': 1000}}, 'actions': []}, ids)
    rules = solver._probabilistic_trigger_runtime([{'id': 'mark_first', 'owner_id': 'a', 'event': 'after_clash', 'conditions': [{'type': 'equals', 'field': 'exchange_index', 'value': 1}], 'effects': [{'type': 'set_flag', 'flag': 'FIRST', 'value': True}], 'max_activations': 1}, {'id': 'mark_second', 'owner_id': 'a', 'event': 'after_clash', 'conditions': [{'type': 'equals', 'field': 'exchange_index', 'value': 2}], 'effects': [{'type': 'set_flag', 'flag': 'SECOND', 'value': True}], 'max_activations': 1}])
    skill = ids['a'].skills['S1']
    cfg = {'initial_defender_coins': 1, 'initial_attacker_coins': 2, 'attacker_base_power': 10, 'skill_power': 10, 'coins': [{'coin_power': 0, 'damage_type': 'slash', 'sin': 'lust'}], 'max_exchanges': 2, 'outcome_probabilities': [{'win': 0.5, 'draw': 0.5, 'loss': 0.0}, {'win': 1.0, 'draw': 0.0, 'loss': 0.0}], '_action_stub': {'identity_id': 'a'}}
    result = solver._run_probabilistic_bleed_stateful(state, skill, cfg, state.fighters['a'], rules, ids)
    rows = []
    for vals in result['_terminal_states'].values():
        rows.extend(vals)
    flags = [tuple(sorted(st.runtime.get('condition_flags', {}).items())) for st, _m in rows]
    assert any((('FIRST', True) in f for f in flags))
    assert any((('SECOND', True) in f for f in flags))
