"""병합 테스트: coin_reuse_forced

원본 파일 (내용은 AST 병합기로 합쳤고 테스트 본문은 바꾸지 않음):
  - test_v29_coin_reuse.py
  - test_v29_coin_trigger_chain.py
  - test_v29_kill_reuse.py
  - test_v41_multitarget_reuse.py
  - test_v29_forced_skill.py
이름 충돌 helper 는 `이름__vNN` 으로 분리했다. 매핑은 tools/MERGE_MAP.json 참고.
"""
from one_turn_solver_v29 import SkillTextParserV19, IdentityCatalogV29, OneTurnSolverV29
from limbus_damage_engine_v29 import BattleState, EnemyState, FighterState, IdentityData, SkillData, CoinData
from one_turn_core_v29 import OneTurnCoreV17
from types import SimpleNamespace
from special_gimmick_v2 import GimmickRegistry



# ======================================================================
# 원본: test_v29_coin_reuse.py
# ======================================================================

def test_parser_recognizes_unconditional_coin_reuse():
    p=SkillTextParserV19()
    parsed, rep=p.parse(['1코인 [적중시] 이 코인 재사용 (최대 2회)'],1)
    assert parsed['coin_defs'][0]['reuse_rules'][0]['max_reuses']==2
    assert '재사용' in rep.supported[0]

def test_unopposed_coin_reuse_executes_immediately():
    cat=IdentityCatalogV29.from_json('identity_catalog_v2.json')
    ident=cat.build_identity('identity-10101')
    skill=next(iter(ident.skills.values()))
    # Replace the first coin with a tiny deterministic test coin and one reuse.
    skill.coins=skill.coins[:1]
    skill.coins[0].reuse_rules=[{'condition':{'type':'always'},'max_reuses':1,'mode':'same'}]
    enemy=EnemyState(hp=1000,max_hp=1000)
    fighter=FighterState(sp=0)
    state=BattleState(enemy=enemy,fighters={ident.id:fighter})
    core=OneTurnCoreV17()
    r=core.execute_unopposed(state,ident,skill,['H'],False)
    assert r['damage']>0
    assert state.turn_damage==r['damage']
    assert state.turn_damage >= 2

def test_parser_recognizes_last_coin_reuse_with_resource_threshold():
    p=SkillTextParserV19()
    parsed, rep=p.parse(['[사용시] 자신의 불꽃나비의 관이 20 이상이면, 마지막 코인 재사용 (스킬당 1회)'],2)
    e=[x for x in parsed['effects_on_use'] if x.get('type')=='last_coin_reuse'][0]
    assert e['condition']['type']=='resource_gte'
    assert e['condition']['value']==20
    assert e['max_reuses']==1

def test_parser_recognizes_critical_and_front_reuse_conditions():
    p=SkillTextParserV19()
    parsed, rep=p.parse(['1코인 [크리티컬 적중 시] 이 코인 재사용 (스킬당 1회)'],1)
    rule=parsed['coin_defs'][0]['reuse_rules'][0]
    assert rule['condition']=={'type':'critical_hit'}
    assert rule['max_reuses']==1

    parsed, rep=p.parse(['1코인 [앞면 적중 시] 이 코인 재사용 (스킬당 최대 2회)'],1)
    rule=parsed['coin_defs'][0]['reuse_rules'][0]
    assert rule['condition']=={'type':'front_hit'}
    assert rule['max_reuses']==2

    parsed, rep=p.parse(['1코인 [크리티컬 앞면 적중 시] 이 코인 재사용 (스킬당 1회)'],1)
    rule=parsed['coin_defs'][0]['reuse_rules'][0]
    assert rule['condition']['type']=='and'
    assert {c['type'] for c in rule['condition']['conditions']}=={'critical_hit','front_hit'}


# ======================================================================
# 원본: test_v29_coin_trigger_chain.py
# ======================================================================

def test_after_coin_trigger_changes_next_coin_same_skill():
    from one_turn_solver_v29 import OneTurnSolverV29
    from trigger_runtime_v1 import TriggerRuntime, TriggerRule, TriggerCondition, TriggerEffect

    solver = OneTurnSolverV29.__new__(OneTurnSolverV29)

    class FakeEngine:
        @staticmethod
        def simulate_coin(state, identity, skill, coin, face, is_crit, coin_index, prior_heads):
            # Coin 2 checks the flag produced by coin 1's trigger.
            damage = 10 if coin_index == 1 else (25 if state.runtime.get('condition_flags', {}).get('coin1_buff') else 10)
            state.enemy.hp -= damage

    solver.core = SimpleNamespace(machine=SimpleNamespace(engine=FakeEngine()))

    rule = TriggerRule(
        'coin1', 'a', 'after_coin',
        [TriggerCondition('equals', 1, field='coin_index')],
        [TriggerEffect('set_flag', {'flag': 'coin1_buff', 'value': True})], 1,
    )
    runtime = TriggerRuntime([rule])
    identity = SimpleNamespace(id='a')
    skill = SimpleNamespace(id='S1', name='S1', _slot='S1', coins=[object(), object()])
    fighter = SimpleNamespace(resources={}, statuses={}, ammo=0)
    state = SimpleNamespace(
        enemy=SimpleNamespace(hp=100, stagger_level=0, stagger_index=0, stagger_thresholds=[], staggered=False),
        fighters={'a': fighter},
        runtime={
            'condition_flags': {},
            'probabilistic_trigger_runtime_template': runtime,
            'probabilistic_identity_map': {'a': identity},
        },
        turn_damage=0,
    )

    clone, damage, trace = solver._execute_unopposed_coins_with_triggers(
        state, identity, skill, ['H', 'H'], 0
    )

    assert damage == 35
    assert clone.enemy.hp == 65
    assert clone.runtime['condition_flags']['coin1_buff'] is True
    assert trace == []
    assert clone.runtime['probabilistic_coin_trace'][1]['damage'] == 25

def test_unopposed_trigger_receives_real_ammo_before_after_values():
    from limbus_damage_engine_v29 import IdentityData, SkillData, CoinData, EnemyState, FighterState, BattleState
    from one_turn_solver_v29 import OneTurnSolverV29
    from trigger_runtime_v1 import TriggerRuntime, TriggerRule, TriggerCondition, TriggerEffect
    ident = IdentityData('a','A',0,{'s': SkillData('s','S',10,[CoinData(1,'slash','gloom')],'slash','gloom',coin_ammo_spend={1:1})})
    state = BattleState(EnemyState(100,100), {'a': FighterState(ammo=1)})
    solver = OneTurnSolverV29()
    rule = TriggerRule('ammo','a','after_coin',[TriggerCondition('final_ammo_coin')],[TriggerEffect('set_flag',{'flag':'final'})],1)
    rt = TriggerRuntime([rule])
    state.runtime.update({'probabilistic_trigger_runtime_template':rt,'probabilistic_identity_map':{'a':ident},'condition_flags':{},'ammo_min_identity':'a'})
    clone,_,_ = solver._execute_unopposed_coins_with_triggers(state, ident, ident.skills['s'], ['H'], 0)
    assert clone.runtime['condition_flags'].get('final') is True


# ======================================================================
# 원본: test_v29_kill_reuse.py
# ======================================================================

def test_kill_reuse_hits_next_aggregate_target_and_does_not_recurse():
    record = {
        'id': 'a', 'name': 'A', 'offense_level': 0,
        'stats': {'level': 60, 'speed': 10, 'hp': 1000, 'hpBase': 1000,
                  'defenseLevel': 0, 'resistances': {}},
        'skills': {
            'S1': {
                'id': 'S1', 'name': 'S1', 'base_power': 10,
                'coin_powers': [1], 'coin_count': 1,
                'coins': [{'coin_power': 1, 'damage_type': 'slash', 'sin': 'lust'}],
                'attack_type': 'slash', 'sin': 'lust',
                'effects': ['적 처치 시 스킬 1회 재사용'],
            }
        },
        'passives': []
    }
    ident = IdentityCatalogV29([record]).build_identity('a')
    skill = ident.skills['S1']
    assert skill.kill_reuse_rules

    sc = {
        'target_count': 2,
        'enemy': {'hp': 10, 'max_hp': 10, 'level': 60, 'defense_level': 0,
                  'physical_res': {'slash': 1, 'pierce': 1, 'blunt': 1},
                  'sin_res': {'lust': 1}},
        'allies': {'a': {}},
        'actions': [{'identity_id': 'a', 'skill_id': 'S1', 'faces': ['H']}],
        'passive_mode': 'off',
    }
    r = OneTurnSolverV29().solve(sc, {'a': ident})

    # First S1 kills target 1; the same skill is inserted once for target 2.
    assert r['execution_count'] == 2
    assert r['turn_damage'] > 0
    assert r['damage_by_identity']['a'] == r['turn_damage']
    assert sum(1 for x in r['actions'] if x['reason'] == 'kill_reuse:S1') == 1
    assert all(x['reason'] != 'kill_reuse:S1' or x['generated'] for x in r['actions'])
    assert any(e['event'] == 'kill_reuse_queued' for e in r['event_log'])

def test_kill_reuse_is_not_used_when_only_one_target_is_requested():
    record = {
        'id': 'a', 'name': 'A', 'offense_level': 0,
        'stats': {'level': 60, 'speed': 10, 'hp': 1000, 'hpBase': 1000,
                  'defenseLevel': 0, 'resistances': {}},
        'skills': {
            'S1': {
                'id': 'S1', 'name': 'S1', 'base_power': 10,
                'coin_powers': [1], 'coin_count': 1,
                'coins': [{'coin_power': 1, 'damage_type': 'slash', 'sin': 'lust'}],
                'attack_type': 'slash', 'sin': 'lust',
                'effects': ['적 처치 시 스킬 1회 재사용'],
            }
        },
        'passives': []
    }
    ident = IdentityCatalogV29([record]).build_identity('a')
    sc = {
        'target_count': 1,
        'enemy': {'hp': 10, 'max_hp': 10, 'level': 60, 'defense_level': 0,
                  'physical_res': {'slash': 1, 'pierce': 1, 'blunt': 1},
                  'sin_res': {'lust': 1}},
        'allies': {'a': {}},
        'actions': [{'identity_id': 'a', 'skill_id': 'S1', 'faces': ['H']}],
        'passive_mode': 'off',
    }
    r = OneTurnSolverV29().solve(sc, {'a': ident})
    assert r['execution_count'] == 1
    assert not any(e['event'] == 'kill_reuse_queued' for e in r['event_log'])


# ======================================================================
# 원본: test_v41_multitarget_reuse.py
# ======================================================================

def _ident(coin_reuse=False, last_reuse=False, kill_reuse=False):
    coin = {'coin_power': 10, 'damage_type': 'slash', 'sin': 'lust'}
    skill = {'id':'S1','name':'S1','base_power':10,'coin_powers':[10],'coin_count':1,
             'coins':[coin],'attack_type':'slash','sin':'lust'}
    ident = IdentityCatalogV29([{'id':'a','name':'A','offense_level':0,
        'stats':{'level':60,'speed':10,'hp':1000,'hpBase':1000,'defenseLevel':0,'resistances':{}},
        'skills':{'S1':skill},'passives':[]}]).build_identity('a')
    skill_obj=ident.skills['S1']
    if coin_reuse:
        skill_obj.coins[0].reuse_rules=[{'condition':{},'max_reuses':1,'mode':'same'}]
    if last_reuse:
        skill_obj.last_coin_reuse_rules=[{'condition':{},'max_reuses':1}]
    if kill_reuse:
        skill_obj.kill_reuse_rules=[{'condition':{},'max_reuses':1,'mode':'skill','recursive':False}]
    return ident

def _scenario(ident, hp=1000, resource=False):
    return {
        'coin_mode': 'fixed',
        'enemy': {'hp': 1000, 'max_hp': 1000, 'targets': [
            {'id': 't1', 'hp': hp, 'max_hp': hp},
            {'id': 't2', 'hp': 1000, 'max_hp': 1000},
        ]},
        'allies': {'a': {'resources': {'X': 2}} if resource else {}},
        'resource_specs': {'X': {'maximum': 99}} if resource else {},
        'actions': [{'identity_id': 'a', 'skill_id': 'S1', 'faces': ['H'],
                     'coin_target_ids': [['t1', 't2']]}],
        'passive_mode': 'off'
    }

def test_coin_reuse_repeats_same_mapped_targets_and_attacker_resource_once_per_reuse():
    ident = _ident(coin_reuse=True)
    ident.skills['S1'].coins[0].resource_cost = {'X': 1}
    r = OneTurnSolverV29().solve(_scenario(ident, resource=True), {'a': ident})
    assert r['fighters']['a']['resources']['X'] == 0
    events = [e for e in r['event_log'] if e.get('event') == 'coin_target_resolution']
    assert [(e['coin'], e['target_id'], e['reuse_index']) for e in events] == [
        (1, 't1', 0), (1, 't2', 0), (1, 't1', 1), (1, 't2', 1)
    ]
    assert r['actions'][0]['damage_by_target']['t1'] > 0
    assert r['actions'][0]['damage_by_target']['t2'] > 0

def test_last_coin_reuse_applies_to_explicitly_mapped_targets():
    ident = _ident(last_reuse=True)
    r = OneTurnSolverV29().solve(_scenario(ident), {'a': ident})
    events = [e for e in r['event_log'] if e.get('event') == 'last_coin_reuse_triggered']
    assert len(events) == 1
    assert events[0]['target_ids'] == ['t1', 't2']
    resolutions = [e for e in r['event_log'] if e.get('event') == 'coin_target_resolution']
    assert len(resolutions) == 4

def test_kill_reuse_is_target_aware_and_does_not_resurrect_dead_target():
    ident = _ident(kill_reuse=True)
    r = OneTurnSolverV29().solve(_scenario(ident, hp=1), {'a': ident})
    events = [e for e in r['event_log'] if e.get('event') == 'kill_skill_reuse_triggered']
    assert len(events) == 1
    assert events[0]['target_aware'] is True
    assert r['target_states']['t1']['hp'] <= 0
    assert r['target_states']['t2']['hp'] > 0


# ======================================================================
# 원본: test_v29_forced_skill.py
# ======================================================================

def test_forced_self_skill_is_compiled():
    s1=SkillData('s1','기본기',4,[CoinData(1,'slash','lust')],'slash','lust'); s1._slot='S1'
    s2=SkillData('s2','추가타',5,[CoinData(1,'slash','lust')],'slash','lust'); s2._slot='S2'
    ident=IdentityData('id1','테스트',0,{'S1':s1,'S2':s2},[])
    ident.passives=[{'name':'p','effect':"기본 공격 스킬 종료 시 자신의 묵 공방 15 이상이면, '추가타' 발동 (턴당 1회)"}]
    g=GimmickRegistry([ident],{ident.id:ident.passives},available_identity_ids=[ident.id])
    out=g.after_skill(ident,s1,{'action_start_staggered':False,'action_end_staggered':False,'resources':{'묵 공방':15}})
    assert out and out[0].identity_id=='id1' and out[0].skill_id=='s2'

def test_ambiguous_received_hit_and_ally_target_are_not_auto_compiled():
    s1=SkillData('s1','기본기',4,[CoinData(1,'slash','lust')],'slash','lust'); s1._slot='S1'
    s2=SkillData('s2','추가타',5,[CoinData(1,'slash','lust')],'slash','lust'); s2._slot='S2'
    ident=IdentityData('id1','테스트',0,{'S1':s1,'S2':s2},[])
    ident.passives=[{'name':'p','effect':"피격 후 '추가타' 발동"},{'name':'q','effect':"기본 공격 스킬 종료 시 가장 높은 대상에게 '추가타' 발동"}]
    g=GimmickRegistry([ident],{ident.id:ident.passives},available_identity_ids=[ident.id])
    assert g.summary()['forced_skill_rules']==0

def test_forced_followup_propagates_target_policy():
    s1=SkillData('s1','공격',4,[CoinData(1,'slash','lust')],'slash','lust'); s1._slot='S1'
    s2=SkillData('s2','황홀한 종말',5,[CoinData(1,'slash','lust')],'slash','lust'); s2._slot='S2'
    ident=IdentityData('id1','잔향',0,{'S1':s1,'S2':s2},[])
    ident.passives=[{'name':'p','effect':"자신의 공격 스킬 종료시, 자신의 꽃잎이 30 이상이면, 잔향이 가장 높은 대상에게 '황홀한 종말' 발동"}]
    g=GimmickRegistry([ident],{ident.id:ident.passives},available_identity_ids=[ident.id])
    out=g.after_skill(ident,s1,{'resources':{'꽃잎':30},'enemy_hp':100,'enemy_max_hp':100})
    assert out and out[0].target_policy=='highest_status:잔향'

def test_captain_ishmael_support_command_is_deterministic_and_right_ally():
    from special_gimmick_v2 import GimmickRegistry
    from limbus_damage_engine_v29 import IdentityData, SkillData, CoinData
    c=SkillData('c2','끝까지 추적한다!',4,[CoinData(1,'slash','lust')],'slash','lust'); c._slot='S2'
    a=SkillData('a1','지원 공격',4,[CoinData(1,'slash','lust')],'slash','lust'); a._slot='S1'
    captain=IdentityData('identity-10808','피쿼드호 선장',0,{'S2':c},[])
    ally=IdentityData('identity-foo','오른쪽 아군',0,{'S1':a},[])
    captain.passives=[{'name':'p','effect':'[사용시] 가장 높은 공명의 공명 당 20% 확률로 조작 패널에서 자신의 우측에 위치한 아군에게 이번 턴에 원호 공격을 명령함.'}]
    g=GimmickRegistry([captain,ally],{captain.id:captain.passives,ally.id:[]},available_identity_ids=[captain.id,ally.id])
    out=g.after_skill(captain,c,{'resources':{},'current_resonance':{'질투':1},'enemy_hp':100,'enemy_max_hp':100})
    assert out and out[0].identity_id=='identity-foo'
    assert out[0].skill_id=='__support_default__'
    assert out[0].trigger_kind=='captain_right_assist'

def test_clash_loss_followup_is_compiled_for_forecast_skill():
    s1=SkillData('s1','기본기',4,[CoinData(1,'slash','lust')],'slash','lust'); s1._slot='S1'
    s2=SkillData('s2','예지',5,[CoinData(1,'slash','lust')],'slash','lust'); s2._slot='S2'
    ident=IdentityData('identity-10916','거미집 엄지 아비',0,{'S1':s1,'S2':s2},[])
    ident.passives=[{'name':'예지안','effect':"일방 공격 또는 파괴 불가 코인 공격을 당하거나 공격 스킬에 합 패배 시 '예지' 스킬 발동 (턴 당 1회)"}]
    g=GimmickRegistry([ident],{ident.id:ident.passives},available_identity_ids=[ident.id])
    rules=[r for r in g.trigger_rules if r.metadata.get('legacy_kind')=='clash_loss_followup']
    assert rules and rules[0].event=='after_clash'
    out=g.after_clash(ident,s1,{'outcome':'lose','statuses':{}})
    assert out and out[0].skill_id=='s2'

def test_defense_clash_loss_followup_requires_haste():
    d=SkillData('d','방어',5,[CoinData(1,'slash','lust')],'방어','lust'); d._slot='수비 1'
    gskill=SkillData('g','골단',5,[CoinData(1,'slash','lust')],'slash','lust'); gskill._slot='S2'
    ident=IdentityData('identity-10815','LCD 현장추리팀',0,{'D':d,'S2':gskill},[])
    ident.passives=[{'name':'귀화요격','effect':"수비 스킬 합 패배 시 신속이 3 이상이면, 수비 스킬 종료 시까지 피해로 인해 흐트러짐 상태가 되지 않고, 피격 후 '골단' 발동 (턴당 2회, 강제 흐트러짐 제외)"}]
    g=GimmickRegistry([ident],{ident.id:ident.passives},available_identity_ids=[ident.id])
    out=g.after_clash(ident,d,{'outcome':'lose','statuses':{'신속':{'count':3,'potency':0}}})
    assert out and out[0].skill_id=='g'
    assert not g.after_clash(ident,d,{'outcome':'lose','statuses':{'신속':{'count':2,'potency':0}}})

def test_catalog_includes_defense_skill_for_generated_forecast():
    from one_turn_solver_v29 import IdentityCatalogV29
    c=IdentityCatalogV29.from_json('identity_catalog_v2.json')
    ident=c.build_identity('identity-10916')
    assert any(s.name=='예지' for s in ident.skills.values())

def test_catalog_compiles_forecast_clash_loss_rule():
    from one_turn_solver_v29 import IdentityCatalogV29
    c=IdentityCatalogV29.from_json('identity_catalog_v2.json')
    ident=c.build_identity('identity-10916')
    g=GimmickRegistry([ident],{ident.id:ident.passives},available_identity_ids=[ident.id])
    rules=[r for r in g.rules if r.kind=='clash_loss_followup']
    assert rules and rules[0].skill_hint=='예지'

def test_support_default_selects_next_requested_skill_without_consuming_it():
    from action_queue_v1 import ActionQueue, ActionRequest
    q=ActionQueue([
        ActionRequest('identity-10808','captain-s2',0),
        ActionRequest('ally','ally-s3',1),
    ])
    source=q.pop()
    generated=q.triggered_from(source,'ally','ally-s3','support',source_event='captain_right_assist')
    assert generated.generated is True
    assert generated.skill_id=='ally-s3'
    q.enqueue_triggered(generated)
    assert q.items[q.position].skill_id=='ally-s3'
    assert q.items[q.position+1].skill_id=='ally-s3'
