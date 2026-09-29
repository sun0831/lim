"""병합 테스트: keyword_runtime

원본 파일 (내용은 AST 병합기로 합쳤고 테스트 본문은 바꾸지 않음):
  - test_v126_keyword_poise_charge_runtime.py
  - test_v128_keyword_runtime.py
  - test_v129_keyword_runtime_engine_bridge.py
이름 충돌 helper 는 `이름__vNN` 으로 분리했다. 매핑은 tools/MERGE_MAP.json 참고.
"""
from limbus_damage_engine_v29 import BattleState, EnemyState, FighterState, Status, DamageEngine
from keyword_runtime_v1 import KeywordRuntime
from resource_runtime_v1 import ResourceRuntime



# ======================================================================
# 원본: test_v126_keyword_poise_charge_runtime.py
# ======================================================================

def _state(poise_count=0, charge=0):
    f=FighterState(poise=Status(potency=20,count=poise_count), charge=charge)
    e=EnemyState(hp=100,max_hp=100)
    st=BattleState(enemy=e, fighters={"A":f})
    st.runtime["resource_runtime"] = ResourceRuntime()
    return st

def test_poise_critical_consumes_once_and_logs():
    st=_state(poise_count=2)
    r=KeywordRuntime.on_critical(st,"A")
    assert r["consumed"]==1
    assert st.fighters["A"].poise.count==1
    assert [e for e in st.event_log if e["event"]=="poise_consume_critical"]

def test_turn_end_consumes_poise_once_and_charge_once():
    st=_state(poise_count=2, charge=3)
    r=KeywordRuntime.turn_end(st)
    assert st.fighters["A"].poise.count==1
    assert st.fighters["A"].charge==2
    assert r["charge_consumed"]["A"]==1

def test_turn_end_does_not_consume_bio_material_resource():
    st=_state(charge=1)
    st.fighters["A"].resources["생체 재료"] = 10
    KeywordRuntime.turn_end(st)
    assert st.fighters["A"].charge==0
    assert st.fighters["A"].resources["생체 재료"]==10


# ======================================================================
# 원본: test_v128_keyword_runtime.py
# ======================================================================

def test_burn_turn_end_consumes_one_count_and_damage():
    e=EnemyState(100,100,statuses={'Burn':Status(potency=7,count=2)})
    s=BattleState(enemy=e, fighters={})
    r=KeywordRuntime.turn_end(s)
    assert r['burn_damage']==7 and s.enemy.hp==93 and s.enemy.statuses['Burn'].count==1

def test_rupture_and_sinking_are_hit_consumers():
    e=EnemyState(100,100,sp=10,statuses={'Rupture':Status(potency=5,count=2),'Sinking':Status(potency=3,count=2)})
    s=BattleState(enemy=e, fighters={})
    r=KeywordRuntime.on_target_hit(s)
    assert r['rupture_damage']==5 and s.enemy.hp==95
    assert s.enemy.sp==7
    assert s.enemy.statuses['Rupture'].count==1 and s.enemy.statuses['Sinking'].count==1

def test_tremor_burst_raises_threshold_and_consumes_count():
    e=EnemyState(100,100,stagger_thresholds=[70],statuses={'Tremor':Status(potency=9,count=2)})
    s=BattleState(enemy=e, fighters={})
    r=KeywordRuntime.burst(s,'Tremor',1)
    assert r['applied'] and r['damage']==0 and r['stagger_threshold_raised']==9
    assert s.enemy.hp==100 and s.enemy.stagger_thresholds==[79] and s.enemy.statuses['Tremor'].count==1

def test_tremor_turn_end_consumes_one_count_without_burst():
    e=EnemyState(100,100,stagger_thresholds=[70],statuses={'Tremor':Status(potency=9,count=2)})
    s=BattleState(enemy=e, fighters={})
    r=KeywordRuntime.turn_end(s)
    assert s.enemy.statuses['Tremor'].count==1
    assert s.enemy.stagger_thresholds==[70]
    assert any(ev.get('event')=='tremor_turn_end' for ev in s.event_log)
    assert 'Tremor' not in r['expired']


def test_poise_critical_chance_helper():
    st=_state(poise_count=2)
    st.fighters['A'].poise.potency=18
    assert KeywordRuntime.critical_chance_percent(st.fighters['A'])==90.0
    st.fighters['A'].poise.potency=25
    assert KeywordRuntime.critical_chance_percent(st.fighters['A'])==100.0


# ======================================================================
# 원본: test_v129_keyword_runtime_engine_bridge.py
# ======================================================================

def test_damage_engine_hit_lifecycle_uses_shared_keyword_runtime():
    enemy = EnemyState(100, 100, sp=10, statuses={
        'Rupture': Status(potency=5, count=1),
        'Sinking': Status(potency=3, count=1),
    })
    state = BattleState(enemy=enemy, fighters={})
    DamageEngine().on_target_hit(state)
    assert state.enemy.hp == 95
    assert state.enemy.sp == 7
    assert 'Rupture' not in state.enemy.statuses
    assert 'Sinking' not in state.enemy.statuses
    assert [e['event'] for e in state.event_log[-2:]] == ['rupture', 'sinking']

def test_damage_engine_turn_end_uses_shared_burn_runtime():
    enemy = EnemyState(100, 100, statuses={'Burn': Status(potency=7, count=2)})
    state = BattleState(enemy=enemy, fighters={})
    DamageEngine().turn_end(state)
    assert state.enemy.hp == 93
    assert state.enemy.statuses['Burn'].count == 1
    assert any(e.get('event') == 'turn_end_burn' for e in state.event_log)


def test_sinking_respects_per_unit_abnormality_flag():
    from limbus_damage_engine_v29 import BattleState, EnemyState, FighterState, Status
    from keyword_runtime_v1 import KeywordRuntime
    normal = EnemyState(100, 100, sp=10, statuses={'Sinking': Status(potency=3, count=1)}, is_abnormality=False)
    abnormal = EnemyState(100, 100, sp=10, statuses={'Sinking': Status(potency=3, count=1)}, is_abnormality=True)
    out_n = KeywordRuntime.on_target_hit(BattleState(normal, {'A': FighterState()}))
    out_a = KeywordRuntime.on_target_hit(BattleState(abnormal, {'A': FighterState()}))
    assert out_n['sinking_sp'] == -3
    assert normal.sp == 7
    assert abnormal.sp == 10
    assert out_a['events'][0]['event'] == 'sinking_gloom'
    assert out_a['sinking_gloom_damage'] == 3
    assert abnormal.statuses.get('Sinking') is None

def test_sinking_abnormality_deals_gloom_hp_and_consumes_count():
    from limbus_damage_engine_v29 import BattleState, EnemyState, FighterState, Status
    from keyword_runtime_v1 import KeywordRuntime
    abnormal = EnemyState(100, 100, sp=0, statuses={'Sinking': Status(potency=7, count=2)}, is_abnormality=True)
    state = BattleState(abnormal, {'A': FighterState()})
    out = KeywordRuntime.on_target_hit(state)
    assert out['sinking_gloom_damage'] == 7
    assert abnormal.hp == 93
    assert abnormal.statuses['Sinking'].count == 1


def test_sinking_deluge_abnormality_uses_potency_times_count_and_removes_status():
    from limbus_damage_engine_v29 import BattleState, EnemyState, FighterState, Status
    from keyword_runtime_v1 import KeywordRuntime
    abnormal = EnemyState(100, 100, sp=0, statuses={'Sinking': Status(potency=7, count=3)}, is_abnormality=True)
    state = BattleState(abnormal, {'A': FighterState()})
    out = KeywordRuntime.sinking_deluge(state)
    assert out['applied'] is True
    assert out['raw'] == 21
    assert out['gloom_damage'] == 21
    assert abnormal.hp == 79
    assert 'Sinking' not in abnormal.statuses


def test_sinking_deluge_sp_target_converts_excess_below_minus_45_to_gloom():
    from limbus_damage_engine_v29 import BattleState, EnemyState, FighterState, Status
    from keyword_runtime_v1 import KeywordRuntime
    enemy = EnemyState(100, 100, sp=-40, statuses={'Sinking': Status(potency=10, count=2)}, is_abnormality=False, sinking_sp_overflow_to_hp=True)
    state = BattleState(enemy, {'A': FighterState()})
    out = KeywordRuntime.sinking_deluge(state)
    assert out['raw'] == 20
    assert enemy.sp == -45
    assert out['sp_damage'] == 5
    assert out['gloom_damage'] == 15
    assert enemy.hp == 85
    assert 'Sinking' not in enemy.statuses

def test_effect_executor_can_execute_explicit_sinking_deluge_on_selected_target():
    from limbus_damage_engine_v29 import BattleState, EnemyState, FighterState, Status
    from effect_executor_v1 import EffectExecutor
    from effect_runtime_v1 import EffectCommand
    target = EnemyState(100, 100, sp=0, statuses={'Sinking': Status(potency=4, count=2)}, is_abnormality=True)
    state = BattleState(target, {'A': FighterState()})
    result = EffectExecutor().execute(EffectCommand('sinking_deluge', {}, 'r1', 'status'), {'state': state, 'target': target})
    assert result['applied'] is True
    assert result['gloom_damage'] == 8
    assert target.hp == 92
    assert 'Sinking' not in target.statuses

# ======================================================================
# Sinking damage routing / target-side modifiers
# ======================================================================

def test_sinking_gloom_uses_keyword_damage_modifier_and_gloom_resistance():
    # Sinking damage x0.5, Gloom resistance 0.5 => Gloom multiplier 0.75.
    # 20 * 0.5 * 0.75 = 7.5 HP damage.
    enemy = EnemyState(100, 100, sp=0,
                       sin_res={'gloom': 0.5},
                       keyword_damage_modifiers={'Sinking': 0.5},
                       statuses={'Sinking': Status(potency=20, count=1)},
                       is_abnormality=True)
    state = BattleState(enemy, {'A': FighterState()})
    out = KeywordRuntime.on_target_hit(state)
    assert out['sinking_gloom_damage'] == 7.5
    assert enemy.hp == 92.5


def test_sinking_sp_target_routes_deluge_overflow_below_minus_45_to_gloom_hp():
    enemy = EnemyState(100, 100, sp=-40,
                       statuses={'Sinking': Status(potency=20, count=1)},
                       is_abnormality=False)
    state = BattleState(enemy, {'A': FighterState()})
    out = KeywordRuntime.sinking_deluge(state)
    assert out['sp_damage'] == 5
    assert out['gloom_damage'] == 15
    assert enemy.sp == -45
    assert enemy.hp == 85


def test_sinking_deluge_hp_overflow_is_canonical_even_without_compatibility_flag():
    enemy = EnemyState(100, 100, sp=-40,
                       statuses={'Sinking': Status(potency=20, count=1)},
                       is_abnormality=False)
    state = BattleState(enemy, {'A': FighterState()})
    out = KeywordRuntime.sinking_deluge(state)
    assert out['sp_damage'] == 5
    assert out['gloom_damage'] == 15
    assert enemy.hp == 85
