"""병합 테스트: clash_bleed_probability

원본 파일 (내용은 AST 병합기로 합쳤고 테스트 본문은 바꾸지 않음):
  - test_clash_exchange_runtime_v1.py
  - test_v29_bleed_probability.py
  - test_v29_trim_scope.py
  - test_v29_clash_event_consistency.py
  - test_v29_clash_exchange_integration.py
  - test_v29_clash_lifecycle_alignment.py
  - test_v29_reuse_probability.py
이름 충돌 helper 는 `이름__vNN` 으로 분리했다. 매핑은 tools/MERGE_MAP.json 참고.
"""
from clash_exchange_runtime_v1 import ClashExchangeRuntime
from bleed_clash_probability_v1 import ProbabilisticBleedClashRuntime
from limbus_damage_engine_v29 import (
    DamageEngine,
    IdentityData,
    SkillData,
    CoinData,
    ClashData,
    EnemyState,
    FighterState,
    BattleState,
)
from one_turn_solver_v29 import IdentityCatalogV29, OneTurnSolverV29, SkillTextParserV19
from reuse_probability_runtime_v1 import reuse_probability, expected_reuses, bounded_reuse_distribution



# ======================================================================
# 원본: test_clash_exchange_runtime_v1.py
# ======================================================================

def test_ww_w_3_2_1():
    r = ClashExchangeRuntime().resolve(3, 3, ["W", "W", "W"])
    assert [x["defender_coins_rolled"] for x in r["exchanges"]] == [3, 2, 1]
    assert r["total_bleed_procs"] == 6

def test_wwlll():
    r = ClashExchangeRuntime().resolve(3, 3, ["W", "W", "L", "L", "L"])
    assert [x["defender_coins_rolled"] for x in r["exchanges"]] == [3, 2, 1, 1, 1]
    assert r["total_bleed_procs"] == 8
    assert r["defender_coins_remaining"] == 1

def test_llwww():
    r = ClashExchangeRuntime().resolve(3, 3, ["L", "L", "W", "W", "W"])
    assert [x["defender_coins_rolled"] for x in r["exchanges"]] == [3, 3, 3, 2, 1]
    assert r["total_bleed_procs"] == 12

def test_five_losses():
    r = ClashExchangeRuntime().resolve(3, 3, ["L"] * 5)
    assert [x["bleed_procs"] for x in r["exchanges"]] == [3] * 5
    assert r["total_bleed_procs"] == 15

def test_unopposed_transition():
    r = ClashExchangeRuntime().resolve(3, 3, ["W", "W", "W"])
    assert r["exchanges"][-1]["unopposed_after"] is True
    assert r["defender_coins_remaining"] == 0

def test_explicit_attacker_state_allows_more_exchanges_than_nominal_coins():
    r = ClashExchangeRuntime().resolve(3, 3, ["L"] * 5,
                                       attacker_coins_after=[3, 3, 2, 1, 1])
    assert r["exchange_count"] == 5
    assert r["total_bleed_procs"] == 15
    assert r["exchanges"][-1]["attacker_coins_after"] == 1

def test_attacker_tracking_is_opt_in():
    r = ClashExchangeRuntime().resolve(3, 3, ["L"] * 5, track_attacker_coins=True)
    assert r["exchange_count"] == 3
    assert r["attacker_coins_remaining"] == 0

def test_mixed_sequence_defender_evolution_is_authoritative():
    r = ClashExchangeRuntime().resolve(3, 3, ["L", "L", "W", "W", "W"])
    assert [x["defender_coins_rolled"] for x in r["exchanges"]] == [3, 3, 3, 2, 1]
    assert r["attacker_coins_remaining"] == 3

def test_tie_keeps_both_coin_counts():
    r = ClashExchangeRuntime().resolve(3, 3, ["T", "W", "W", "W"])
    assert [x["defender_coins_rolled"] for x in r["exchanges"]] == [3, 3, 2, 1]
    assert r["total_bleed_procs"] == 9


# ======================================================================
# 원본: test_v29_bleed_probability.py
# ======================================================================

def always_win(ctx):
    return (1.0, 0.0, 0.0)

def always_loss(ctx):
    return (0.0, 0.0, 1.0)

def always_tie(ctx):
    return (0.0, 1.0, 0.0)

def test_probabilistic_win_matches_3_2_1():
    r = ProbabilisticBleedClashRuntime().resolve(3, 3, always_win)
    assert r["expected_bleed_procs_raw"] == 6
    assert r["expected_bleed_procs"] == 6
    assert r["exchange_count_distribution"] == {3: 1.0}

def test_probabilistic_loss_keeps_defender_coins():
    r = ProbabilisticBleedClashRuntime().resolve(3, 3, always_loss, max_exchanges=5)
    assert r["expected_bleed_procs_raw"] == 9
    assert r["final_defender_coin_distribution"] == {3: 1.0}

def test_draw_keeps_both_sides_unchanged():
    r = ProbabilisticBleedClashRuntime().resolve(3, 3, always_tie, max_exchanges=4)
    assert r["expected_bleed_procs_raw"] == 12
    assert r["final_defender_coin_distribution"] == {3: 1.0}
    assert r["final_attacker_coin_distribution"] == {3: 1.0}
    assert r["final_attacker_coin_distribution"] == {3: 1.0}

def test_99th_exchange_is_forced_defender_win():
    r = ProbabilisticBleedClashRuntime().resolve(1, 1, always_tie, max_exchanges=99)
    assert r["exchange_count_distribution"] == {99: 1.0}
    assert r["final_defender_coin_distribution"] == {1: 1.0}
    assert r["final_attacker_coin_distribution"] == {0: 1.0}
    assert r["probability_reaching_99_exchanges"] == 1.0

def test_two_sided_five_percent_trim():
    runtime = ProbabilisticBleedClashRuntime(trim_extremes=True, trim_fraction=0.05)
    # 90% at 10, 5% at 0, 5% at 100 => trimmed mean must be 10.
    assert runtime._trimmed_mean({0: 0.05, 10: 0.90, 100: 0.05}) == 10.0

def test_unbreakable_coin_is_active_for_first_bleed_then_deactivates_on_win():
    r = ProbabilisticBleedClashRuntime().resolve(3, 3, always_win, defender_unbreakable_coins=1)
    assert r["initial_defender_coins"] == 4
    assert r["expected_bleed_procs_raw"] == 10

def test_solver_integrates_probabilistic_bleed_and_virtual_count():
    from one_turn_solver_v29 import IdentityCatalogV29, OneTurnSolverV29
    records=[{'id':'a','name':'A','offense_level':0,'stats':{'level':60,'speed':10,'hp':1000,'hpBase':1000,'defenseLevel':0,'resistances':{}},
      'skills':{'S1':{'id':'S1','name':'S1','base_power':10,'coin_powers':[1],'coin_count':1,
        'coins':[{'coin_power':1,'damage_type':'slash','sin':'lust'}],'attack_type':'slash','sin':'lust'}},'passives':[]}]
    cat=IdentityCatalogV29(records); ident=cat.build_identity('a')
    sc={'enemy':{'hp':1000,'max_hp':1000,'level':60,'defense_level':0,
        'physical_res':{'slash':1,'pierce':1,'blunt':1},'sin_res':{'lust':1},
        'statuses':{'Bleed':{'potency':1,'count':10}}},
        'allies':{'a':{'sp':0,'hp':1000,'max_hp':1000}},
        'actions':[{'identity_id':'a','skill_id':'S1','faces':['H'],
          'bleed_clash_probability':{'initial_defender_coins':3,'skill_power':10,
            'outcome_probabilities':[{'win':1,'draw':0,'loss':0}]}}],
        'passive_mode':'off'}
    r=OneTurnSolverV29().solve(sc,{'a':ident})
    bp=r['actions'][0]['bleed_probability']
    assert bp['expected_bleed_procs'] == 6
    assert r['virtual_bleed_count'] == 4.0
    assert any(e.get('event') == 'bleed_probability' for e in r['event_log'])

def test_probabilistic_mode_reports_expected_clash_damage():
    from one_turn_solver_v29 import IdentityCatalogV29, OneTurnSolverV29
    records=[{'id':'a','name':'A','offense_level':0,'stats':{'level':60,'speed':10,'hp':1000,'hpBase':1000,'defenseLevel':0,'resistances':{}},
      'skills':{'S1':{'id':'S1','name':'S1','base_power':10,'coin_powers':[1],'coin_count':1,
        'coins':[{'coin_power':1,'damage_type':'slash','sin':'lust'}],'attack_type':'slash','sin':'lust'}},'passives':[]}]
    cat=IdentityCatalogV29(records); ident=cat.build_identity('a')
    sc={'enemy':{'hp':1000,'max_hp':1000,'level':60,'defense_level':0,
        'physical_res':{'slash':1,'pierce':1,'blunt':1},'sin_res':{'lust':1}},
        'allies':{'a':{'sp':0,'hp':1000,'max_hp':1000}},
        'actions':[{'identity_id':'a','skill_id':'S1','faces':['H'],
          'bleed_clash_probability':{'initial_defender_coins':1,'skill_power':10,
            'outcome_probabilities':[{'win':1,'draw':0,'loss':0}]}}],
        'passive_mode':'off'}
    r=OneTurnSolverV29().solve(sc,{'a':ident})
    bp=r['actions'][0]['bleed_probability']
    assert bp['raw_expected_damage'] > 0
    assert bp['expected_damage'] == bp['trimmed_expected_damage']
    assert '_terminal_meta' not in bp

def test_probabilistic_loss_has_zero_expected_clash_damage():
    from one_turn_solver_v29 import IdentityCatalogV29, OneTurnSolverV29
    records=[{'id':'a','name':'A','offense_level':0,'stats':{'level':60,'speed':10,'hp':1000,'hpBase':1000,'defenseLevel':0,'resistances':{}},
      'skills':{'S1':{'id':'S1','name':'S1','base_power':10,'coin_powers':[1],'coin_count':1,
        'coins':[{'coin_power':1,'damage_type':'slash','sin':'lust'}],'attack_type':'slash','sin':'lust'}},'passives':[]}]
    cat=IdentityCatalogV29(records); ident=cat.build_identity('a')
    sc={'enemy':{'hp':1000,'max_hp':1000,'level':60,'defense_level':0,
        'physical_res':{'slash':1,'pierce':1,'blunt':1},'sin_res':{'lust':1}},
        'allies':{'a':{'sp':0,'hp':1000,'max_hp':1000}},
        'actions':[{'identity_id':'a','skill_id':'S1','faces':['H'],
          'bleed_clash_probability':{'initial_defender_coins':1,'skill_power':999,
            'outcome_probabilities':[{'win':0,'draw':0,'loss':1}]}}],
        'passive_mode':'off'}
    r=OneTurnSolverV29().solve(sc,{'a':ident})
    assert r['actions'][0]['bleed_probability']['raw_expected_damage'] == 0.0


# ======================================================================
# 원본: test_v29_trim_scope.py
# ======================================================================

def test_99th_exchange_is_forced_defender_win_only_at_real_99_cap():
    def tie(_ctx):
        return (0.0, 1.0, 0.0)
    r = ProbabilisticBleedClashRuntime().resolve(1, 1, tie, max_exchanges=4)
    assert r['exchange_count_distribution'] == {4: 1.0}
    assert r['final_attacker_coin_distribution'] == {1: 1.0}
    assert r['final_defender_coin_distribution'] == {1: 1.0}

def test_turn_trim_is_reported_as_final_total_proc_trim():
    # This test uses the standalone statistical layer so the contract is explicit:
    # intermediate states are not trimmed; only the final accumulated proc
    # distribution is trimmed.
    rt = ProbabilisticBleedClashRuntime(trim_extremes=True, trim_fraction=0.05)
    raw = {2: 0.10, 3: 0.90}
    trimmed = rt._trimmed_mean(raw)
    assert abs(trimmed - (0.05*2 + 0.85*3)/0.9) < 1e-9

def test_trimmed_distribution_preserves_partial_probability_atoms():
    from turn_bleed_state_runtime_v1 import TurnBleedStateRuntime
    rt = TurnBleedStateRuntime(trim_fraction=0.05)
    # 5% is cut from each tail atom rather than dropping the whole atom.
    out = rt.trim_distribution({2: 0.10, 3: 0.80, 4: 0.10})
    assert abs(sum(out.values()) - 1.0) < 1e-9
    assert out[2] > 0.0 and out[4] > 0.0


# ======================================================================
# 원본: test_v29_clash_event_consistency.py
# ======================================================================

def test_normal_clash_draw_keeps_both_coins_for_next_exchange():
    eng = DamageEngine()
    attacker = SkillData(id='S1', name='S1', base_power=10, attack_type='slash', sin='',
                         coins=[CoinData(0,'slash',''), CoinData(0,'slash','')])
    defender = ClashData(skill_power=10, coins=[CoinData(0,'slash',''), CoinData(0,'slash','')])
    result = eng.resolve_clash(attacker, defender, ['H','H'], ['H','H'])
    # Equal coins repeat on draw; the 99th exchange is the hard-cap defender win.
    assert len(result['exchanges']) == 99
    assert all(x['outcome'] == 'tie' for x in result['exchanges'][:-1])
    ex = result['exchanges'][-1]
    assert ex['outcome'] == 'lose'
    assert ex['attacker_coins_after'] == 1
    assert ex['defender_coins_after'] == 2
    assert result['attacker_remaining_coins'] == 1
    assert result['defender_remaining_coins'] == 2


# ======================================================================
# 원본: test_v29_clash_exchange_integration.py
# ======================================================================

def _identity():
    record={'id':'a','name':'A','offense_level':0,
      'stats':{'level':60,'speed':10,'hp':100,'hpBase':100,'defenseLevel':0,'resistances':{}},
      'skills':{'S1':{'id':'S1','name':'S1','base_power':10,'coin_powers':[1,1,1],'coin_count':3,
        'coins':[{'coin_power':1,'damage_type':'slash','sin':'lust'}]*3,'attack_type':'slash','sin':'lust'}},
      'passives':[]}
    return IdentityCatalogV29([record]).build_identity('a')

def test_solver_exposes_defender_coins_per_exchange():
    ident=_identity()
    sc={'enemy':{'hp':1000,'max_hp':1000,'level':60,'defense_level':0,
        'physical_res':{'slash':1,'pierce':1,'blunt':1},'sin_res':{'lust':1}},
        'actions':[{'identity_id':'a','skill_id':'S1','faces':['H','H','H'],
                    'clash':{'skill_power':5,'coins':[{'coin_power':1}]*3,
                             'exchange_outcomes':['W','W','L','L','L'],
                             'initial_attacker_coins':3,'initial_defender_coins':3}}],
        'passive_mode':'off'}
    r=OneTurnSolverV29().solve(sc,{'a':ident})
    trace=r['actions'][0]['clash_trace']
    assert [x['defender_coins_rolled'] for x in trace['exchanges']]==[3,2,1,1,1]
    assert trace['total_bleed_procs']==8
    events=[e for e in r['event_log'] if e.get('event')=='bleed_proc_batch']
    assert events[-1]['total_procs']==8


# ======================================================================
# 원본: test_v29_clash_lifecycle_alignment.py
# ======================================================================

def _identity__v29_clash(skill):
    return IdentityData('a', 'A', 0, {'s': skill})

def test_deterministic_clash_applies_clash_and_on_hit_effects_before_after_coins():
    skill = SkillData(id='s', name='S', base_power=10, coins=[CoinData(1, 'slash', 'gloom')], attack_type='slash', sin='gloom', effects_on_clash_win=[{'type': 'sp', 'amount': 7}], effects_on_hit=[{'type': 'sp', 'amount': 5}])
    ident = _identity__v29_clash(skill)
    state = BattleState(EnemyState(100, 100, sp=0), {'a': FighterState(sp=0)})
    solver = OneTurnSolverV29()
    from battle_core_v29 import ClashAwareBattleStateMachineV23
    machine = ClashAwareBattleStateMachineV23(identities=[ident])
    machine.start(state)
    result = machine.execute_clash(state, ident, skill, ClashData(0, [CoinData(0, 'slash', 'gloom')]), ['H'], ['H'])
    assert result['outcome'] == 'win'
    assert state.fighters['a'].sp == 12

def test_explicit_exchange_path_applies_same_clash_lifecycle():
    skill = SkillData(id='s', name='S', base_power=10, coins=[CoinData(1, 'slash', 'gloom')], attack_type='slash', sin='gloom', effects_on_clash_win=[{'type': 'sp', 'amount': 7}], effects_on_hit=[{'type': 'sp', 'amount': 5}])
    ident = _identity__v29_clash(skill)
    solver = OneTurnSolverV29()
    scenario = {'enemy': {'hp': 100, 'max_hp': 100}, 'identities': [ident], 'actions': [{'identity_id': 'a', 'skill_id': 's', 'faces': ['H'], 'clash': {'coins': [{'coin_power': 0}], 'initial_defender_coins': 1, 'exchange_outcomes': ['W']}}]}
    result = solver.solve(scenario, {'a': ident})
    assert result['fighters']['a']['sp'] == 12


# ======================================================================
# 원본: test_v29_reuse_probability.py
# ======================================================================

def test_parser_recognizes_probability_reuse_with_negative_status_bonus():
    p = SkillTextParserV19()
    parsed, rep = p.parse([
        '1코인 [적중시] 40% 확률로 코인 재사용. 대상이 보유한 부정적인 효과 1개당 재사용 확률 +20%. (스킬당 최대 2회 재사용 가능)'
    ], 1)
    r = parsed['coin_defs'][0]['reuse_rules'][0]
    assert r['mode'] == 'same'
    assert r['high_point_assumption'] is True
    assert abs(r['original_probability'] - 0.4) < 1e-9
    assert r['probability'] == 0.4
    assert r['negative_status_bonus'] == 0.2
    assert r['max_reuses'] == 2
    assert '재사용' in rep.supported[0]

def test_probability_reuse_is_capped():
    r = {'probability':0.4, 'negative_status_bonus':0.2, 'max_reuses':2}
    statuses = {'Bleed': {'potency':3,'count':2}, 'Burn': {'potency':2,'count':1}, 'Offense Level Up': {'potency':5,'count':1}}
    r['mode'] = 'same'
    r['high_point_assumption'] = True
    assert reuse_probability(r, statuses) == 1.0
    assert abs(expected_reuses(r, statuses) - 2.0) < 1e-9

def test_bounded_reuse_distribution_is_exact_and_normalized():
    d = bounded_reuse_distribution({'probability': 0.5, 'max_reuses': 2, 'mode': 'same', 'high_point_assumption': True})
    assert abs(d[0] - 0.0) < 1e-12
    assert abs(d[1] - 0.0) < 1e-12
    assert abs(d[2] - 1.0) < 1e-12
    assert abs(sum(d.values()) - 1.0) < 1e-12
