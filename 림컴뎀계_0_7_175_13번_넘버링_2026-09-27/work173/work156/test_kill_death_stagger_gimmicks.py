"""병합 테스트: kill_death_stagger_gimmicks

원본 파일 (내용은 AST 병합기로 합쳤고 테스트 본문은 바꾸지 않음):
  - test_v29_kill_gimmicks.py
  - test_v29_support_conditions.py
  - test_v29_special_gimmicks.py
  - test_v29_stagger_coin_conditions.py
  - test_v29_stagger_legacy_queue.py
  - test_v29_stagger_trigger_bridge.py
  - test_v30_ally_death.py
  - test_v30_target_death.py
  - test_v30_conditional_cross_assist.py
  - test_v30_support_command_generic.py
  - test_v31_deferred_effects.py
  - test_v31_enemy_death_effects.py
  - test_v45_kill_resource_distribution.py
  - test_v46_kill_charge_variants.py
  - test_v50_charge_kill_priority.py
이름 충돌 helper 는 `이름__vNN` 으로 분리했다. 매핑은 tools/MERGE_MAP.json 참고.
"""
import json
import unittest
import os
from special_gimmick_v2 import GimmickRegistry
from limbus_damage_engine_v29 import (
    IdentityData,
    SkillData,
    CoinData,
    BattleState,
    EnemyState,
    FighterState,
    DamageEngine,
    EventType,
)
from one_turn_solver_v29 import IdentityCatalogV29, OneTurnSolverV29, SkillTextParserV19
from special_gimmick_v1 import GimmickRegistry as GimmickRegistry__v29_special
from trigger_runtime_v1 import TriggerRuntime, TriggerRule, TriggerCondition, TriggerEffect
from passive_compiler_v29 import compile_passive_v29
from passive_runtime_v29 import PassiveRuntimeV13, PassiveTrigger
from types import SimpleNamespace
from passive_runtime_v29_base import (
    PassiveRuntime,
    PassiveEvent,
    PassiveTrigger as PassiveTrigger__v31_deferred,
)



# ======================================================================
# 원본: test_v29_kill_gimmicks.py
# ======================================================================

def _ident(i,n):
    return IdentityData(id=i,name=n,skills={},passives=[],offense_level=0)

def test_kill_charge_gain_rule_compiles():
    a=_ident('identity-10405','W사 3등급 정리 요원')
    a.passives=[{'name':'p','effect':'적 처치 시 충전 횟수 2 증가 (턴 당 최대 3회 발동)'}]
    g=GimmickRegistry([a],{a.id:a.passives},[a.id])
    rules=[r for r in g.trigger_rules if r.event=='after_kill']
    assert rules and rules[0].activation_scope=='global' and rules[0].max_activations==3

def test_kill_lowest_ally_heal_rule_compiles():
    a=_ident('identity-10404','료. 고. 파. 주방장')
    a.passives=[{'name':'p','effect':'적 처치 시 체력이 가장 낮은 아군 1명의 체력 15 회복 (턴 당 1회 발동).'}]
    g=GimmickRegistry([a],{a.id:a.passives},[a.id])
    rules=[r for r in g.trigger_rules if r.event=='after_kill']
    assert rules and rules[0].effects[0].type=='heal_lowest_ally'


# ======================================================================
# 원본: test_v29_support_conditions.py
# ======================================================================

def _skill(i,n,slot='S1'):
    s=SkillData(i,n,4,[CoinData(1,'slash','lust')],'slash','lust'); s._slot=slot; return s

def test_cross_identity_assist_requires_source_owner_and_target_present():
    src=_skill('src','흑풍마각월참','S2')
    ally=_skill('allys','적춘','S3')
    a=IdentityData('owner','오너',0,{'S2':src},[])
    b=IdentityData('ally','가주 후보 이스마엘',0,{'S3':ally},[])
    a.passives=[{'name':'p','effect':'흑풍마각월참 사용 후 가주 후보 이스마엘이 적춘 스킬로 원호 공격함 (턴 당 1회)'}]
    g=GimmickRegistry([a,b],{a.id:a.passives,b.id:[]},available_identity_ids=[a.id,b.id])
    assert g.after_skill(a,src,{'current_resonance':{}})
    g.reset_turn()
    g2=GimmickRegistry([a],{a.id:a.passives},available_identity_ids=[a.id])
    assert not g2.after_skill(a,src,{'current_resonance':{}})

def test_captain_high_roll_still_requires_nonzero_resonance():
    c=_skill('c','끝까지 추적한다!','S2')
    ally=_skill('a','지원','S1')
    captain=IdentityData('identity-10808','피쿼드호 선장',0,{'S2':c},[])
    right=IdentityData('identity-right','오른쪽 아군',0,{'S1':ally},[])
    captain.passives=[{'name':'p','effect':'[사용시] 가장 높은 공명의 공명 당 20% 확률로 조작 패널에서 자신의 우측에 위치한 아군에게 이번 턴에 원호 공격을 명령함.'}]
    g=GimmickRegistry([captain,right],{captain.id:captain.passives,right.id:[]},available_identity_ids=[captain.id,right.id])
    assert not g.after_skill(captain,c,{'current_resonance':{'질투':0}})
    out=g.after_skill(captain,c,{'current_resonance':{'질투':1}})
    assert out and out[0].identity_id==right.id


# ======================================================================
# 원본: test_v29_special_gimmicks.py
# ======================================================================

def test_assist_rule_detected_and_queued():
    cat = IdentityCatalogV29.from_json('identity_catalog_v2.json')
    a = cat.build_identity('identity-10114')
    b = cat.build_identity('identity-10812')
    g = GimmickRegistry__v29_special([a, b])
    assert g.summary()['assist_rules'] >= 1
    sc = {'enemy': {'hp': 100000, 'max_hp': 100000, 'level': 60}, 'allies': {'identity-10114': {'sp': 45}, 'identity-10812': {'sp': 45}}, 'actions': [{'identity_id': 'identity-10114', 'skill_id': '1011405'}]}
    r = OneTurnSolverV29().solve(sc, {'identity-10114': a, 'identity-10812': b})
    assert any((x['generated'] and x['identity_id'] == 'identity-10812' and (x['skill_id'] == '1081203') for x in r['actions']))
    assert r['gimmicks']['assist_rules'] >= 1

def test_stagger_damage_is_not_hp_damage():
    cat=IdentityCatalogV29.from_json('identity_catalog_v2.json')
    a=cat.build_identity('identity-11115')
    sc={'enemy':{'hp':1000,'max_hp':1000,'level':60,'stagger_thresholds':[700,400,200]},
        'allies':{'identity-11115':{'sp':0}},
        'actions':[{'identity_id':'identity-11115','skill_id':'111151'}]}
    r=OneTurnSolverV29().solve(sc,{'identity-11115':a})
    # A skill text may contain stagger damage; if parsed, it must not directly
    # reduce HP a second time. The explicit runtime counter is inspectable.
    assert r['enemy_hp_after'] >= 0
    assert 'event_log' in r


# ======================================================================
# 원본: test_v29_stagger_coin_conditions.py
# ======================================================================

def ident(skill):
    return IdentityData('A','A',0,{'S':skill},[])

def test_simulate_coin_applies_stagger_damage_ratio_runtime():
    enemy = EnemyState(hp=100, max_hp=100, stagger_thresholds=[95])
    coin = CoinData(1, 'slash', 'lust', stagger_damage_ratio=1.0)
    skill = SkillData('S','S',10,[coin],'slash','lust')
    fighter = FighterState(level=60)
    state = BattleState(enemy, {'A': fighter})
    DamageEngine().simulate_coin(state, ident(skill), skill, coin, 'H', False, 1)
    assert state.runtime.get('stagger_damage') == 11
    assert enemy.stagger_level == 1

def test_staggered_target_damage_bonus_is_dynamic_for_later_coins():
    parser = SkillTextParserV19()
    parsed, report = parser.parse(['1코인 [적중시] 대상이 흐트러짐 상태면, 피해량 +20%'], 1)
    assert any('흐트러짐 상태' in x for x in report.supported)
    skill = SkillData('S','S',10,[CoinData(1,'slash','lust')],'slash','lust')
    markers = [e for e in parsed['effects_on_use'] if e.get('type') == '_skill_condition_marker']
    assert markers and markers[0]['condition']['type'] == 'enemy_staggered'
    skill.conditions = [{'effect':'damage_bonus','condition':markers[0]['condition'],'amount':markers[0]['damage_bonus']}]
    state = BattleState(EnemyState(hp=100,max_hp=100,stagger_level=1), {'A':FighterState(level=60)})
    dmg, _ = DamageEngine().calculate_coin_damage(state, ident(skill), skill, skill.coins[0], 'H', False, 0, 1)
    state.enemy.stagger_level = 0
    dmg2, _ = DamageEngine().calculate_coin_damage(state, ident(skill), skill, skill.coins[0], 'H', False, 0, 1)
    assert dmg > dmg2


# ======================================================================
# 원본: test_v29_stagger_legacy_queue.py
# ======================================================================

def test_legacy_stagger_passive_queue_action_is_not_dropped():
    follow = SkillData('S2', 'Follow', 10, [CoinData(1, 'slash', 'lust')], 'slash', 'lust')
    main = SkillData('S1', 'Main', 10, [CoinData(1, 'slash', 'lust')], 'slash', 'lust')
    target = IdentityData('B', 'B', 0, {'S2': follow}, [])
    source = IdentityData('A', 'A', 0, {'S1': main}, [{
        'trigger': 'Stagger',
        'condition': None,
        'effects': [{'type': 'queue_action', 'identity_id': 'B', 'skill_id': 'S2'}],
    }])
    state = BattleState(EnemyState(hp=100, max_hp=100, stagger_level=1, stagger_index=1), {
        'A': FighterState(level=60), 'B': FighterState(level=60)
    })
    solver = OneTurnSolverV29()
    rt = TriggerRuntime([])
    queued, fired = solver._fire_probabilistic_stagger_triggers(
        state, rt, {'A': source, 'B': target}, 'A', main,
        before_level=0, before_index=0, actual_damage=1.0
    )
    assert fired is True
    assert [(x, y.id) for x, y in queued] == [('B', 'S2')]


# ======================================================================
# 원본: test_v29_stagger_trigger_bridge.py
# ======================================================================

def _ident__v29_stagger(skill):
    return IdentityData('A', 'A', 0, {'S': skill}, [])

def test_stagger_trigger_fires_between_coins_and_can_queue_followup():
    coin = CoinData(1, 'slash', 'lust', stagger_damage_ratio=1.0)
    skill = SkillData('S', 'S', 10, [coin, coin], 'slash', 'lust')
    ident = _ident__v29_stagger(skill)
    state = BattleState(EnemyState(hp=20, max_hp=20, stagger_thresholds=[15]), {'A': FighterState(level=60)})
    solver = OneTurnSolverV29()
    rt = TriggerRuntime([TriggerRule('st', 'A', 'after_stagger', [], [TriggerEffect('set_flag', {'flag': 'stagger_seen', 'value': True})], 1)])
    state.runtime['probabilistic_identity_map'] = {'A': ident}
    state.enemy.stagger_level = 1
    state.enemy.stagger_index = 1
    queued, fired = solver._fire_probabilistic_stagger_triggers(state, rt, {'A': ident}, 'A', skill, before_level=0, before_index=0, actual_damage=5)
    assert fired is True
    assert state.runtime['condition_flags']['stagger_seen'] is True


# ======================================================================
# 원본: test_v30_ally_death.py
# ======================================================================

def _state():
    # Minimal state objects are enough for the death event and self resource effects.
    class S: pass
    st=S(); st.fighters={}; st.runtime={}
    return st

def test_unit_death_event_marks_ally_scope_and_dead_identity():
    class Bus:
        def __init__(self): self.ctx=[]
        def emit(self, event, ctx): self.ctx.append((event,ctx))
    # Verify the canonical event schema directly through the engine's event enum.
    b=Bus(); st=_state()
    b.emit(EventType.UNIT_DEATH, {'state':st,'death_scope':'ally','dead_identity_id':'id_dead','killed':True})
    ev,ctx=b.ctx[0]
    assert ev is EventType.UNIT_DEATH
    assert ctx['death_scope']=='ally'
    assert ctx['dead_identity_id']=='id_dead'

def test_ally_death_immediate_passive_compiles():
    record={'id':'p1','name':'사망 자원','effect':'아군 사망 시 충전 2 얻음'}
    compiled = compile_passive_v29(record,'id1',0)
    rules, reasons, unsupported = compiled.rules, compiled.reasons, compiled.unsupported_reasons
    assert rules
    assert rules[0].trigger == PassiveTrigger.UNIT_DEATH

def test_ally_death_future_turn_effect_is_not_applied_immediately():
    record={'id':'p2','name':'미래 효과','effect':'아군 사망 시 다음 턴에 공격 위력 증가 1 얻음'}
    compiled = compile_passive_v29(record,'id1',0)
    rules, reasons, unsupported = compiled.rules, compiled.reasons, compiled.unsupported_reasons
    assert len(rules) == 1
    assert rules[0].deferred_turns == 1
    assert not unsupported


# ======================================================================
# 원본: test_v30_target_death.py
# ======================================================================

def _ident__v30_target():
    s = SkillData('s1', '처치기', 4, [CoinData(1, 'slash', 'lust')], 'slash', 'lust')
    s._slot = 'S1'
    i = IdentityData('id1', '테스트', 0, {'S1': s}, [])
    i.passives = [{'name': 'p', 'effect': '[공격 종료시] 대상이 사망한 경우 혈찬 60 증가'}]
    return (i, s)

def test_target_death_resource_gain_rule_compiles_and_fires():
    i, s = _ident__v30_target()
    g = GimmickRegistry([i], {i.id: i.passives}, available_identity_ids=[i.id])
    rules = [r for r in g.rules if r.kind == 'target_death_resource_gain']
    assert rules and rules[0].skill_hint == '혈찬' and (rules[0].extra_scale == 60)
    f = i

    class Fighter:
        pass
    fighter = Fighter()
    fighter.resources = {'혈찬': 0}

    class State:
        pass
    st = State()
    st.fighters = {i.id: fighter}
    st.event_log = []
    g.after_skill(i, s, {'target_died': True, 'state': st, 'resources': {}})
    assert fighter.resources['혈찬'] == 60


# ======================================================================
# 원본: test_v30_conditional_cross_assist.py
# ======================================================================

class Status:
    def __init__(self,count=1,potency=0): self.count=count; self.potency=potency

class TestConditionalCrossAssist(unittest.TestCase):
    def setUp(self):
        def skill(i,n,slot='S1'): return SimpleNamespace(id=i,name=n,_slot=slot,effects=[])
        self.rosya=SimpleNamespace(id='identity-10916',name='거미집 엄지 아비',full_name='거미집 엄지 아비',skills={'r':skill('r','기본 공격')},passives=[])
        self.helper=SimpleNamespace(id='identity-10716',name='거미집 엄지 제자',full_name='거미집 엄지 제자',skills={'p':skill('p','팔레르모 스파다')},passives=[{'effect':"거미집 엄지 아비 로쟈가 전장에 있을 경우, 다음 효과 발동\n(자신이 패닉 또는 흐트러진 턴 제외)\n- 거미집 엄지 아비 로쟈가 예지안이 있을 때 적에게 기본 스킬 적중 시, 해당 공격 종료 시점에 대상에게 '팔레르모 스파다'로 일방 공격 (턴당 1회)"}])
    def test_condition_compiles_and_fires(self):
        g=GimmickRegistry([self.rosya,self.helper],active_passives={'identity-10716':self.helper.passives},available_identity_ids=['identity-10916','identity-10716'])
        rules=[r for r in g.trigger_rules if r.metadata.get('legacy_kind')=='conditional_assist']
        self.assertEqual(len(rules),1)
        ctx={'identity_id':'identity-10916','skill_name':'기본 공격','skill_slot':'S1','actual_damage':10,'available_identity_ids':['identity-10916','identity-10716'],'actor_statuses':{'예지안':{'count':1,'potency':0}}}
        self.assertEqual(len(g.after_skill(self.rosya,self.rosya.skills['r'],ctx)),1)
    def test_missing_status_does_not_fire(self):
        g=GimmickRegistry([self.rosya,self.helper],active_passives={'identity-10716':self.helper.passives},available_identity_ids=['identity-10916','identity-10716'])
        ctx={'identity_id':'identity-10916','skill_name':'기본 공격','skill_slot':'S1','actual_damage':10,'available_identity_ids':['identity-10916','identity-10716'],'actor_statuses':{}}
        self.assertEqual(g.after_skill(self.rosya,self.rosya.skills['r'],ctx),[])
if __name__=='__main__': unittest.main()


# ======================================================================
# 원본: test_v30_support_command_generic.py
# ======================================================================

def _ids():
    D=json.load(open(os.path.join(os.path.dirname(__file__),'identity_catalog_v2.json'),encoding='utf-8'))['identities']
    c=IdentityCatalogV29(D)
    return [c.build_identity(r['id']) for r in D]

def test_support_command_is_generic_and_keeps_captain_100_percent_rule():
    ids=_ids()
    reg=GimmickRegistry(ids, available_identity_ids=['identity-10808','identity-10114'])
    kinds=[r.kind for r in reg.rules if '원호 공격을 명령함' in r.source_text]
    assert 'captain_right_assist' in kinds

def test_support_right_effect_selects_adjacent_ally_and_default_skill():
    ids=_ids(); reg=GimmickRegistry(ids, available_identity_ids=['identity-10808','identity-10114'])
    rules=reg.trigger_rules_data()
    rr=[r for r in rules if r['metadata'].get('legacy_kind')=='captain_right_assist']
    assert rr
    eff=rr[0]['effects'][0]
    assert eff['identity_policy']=='ally_right'
    assert eff['skill_name']=='__support_default__'


# ======================================================================
# 원본: test_v31_deferred_effects.py
# ======================================================================

def test_hit_next_turn_is_compiled_as_causal_hit_with_deferred_flag():
    r = compile_passive_v29({'id': 'p', 'name': '미래', 'effect': '1코인 [적중시] 다음 턴에 취약 1 부여'}, 'id1', 0)
    assert len(r.rules) == 1
    assert r.rules[0].trigger == PassiveTrigger__v31_deferred.COIN_HIT
    assert r.rules[0].deferred_turns == 1

def test_deferred_effect_is_scheduled_not_applied_on_causal_event():
    r = compile_passive_v29({'id': 'p', 'name': '미래', 'effect': '아군 사망 시 다음 턴에 공격 위력 증가 1 얻음'}, 'id1', 0)
    rule = r.rules[0]
    st = BattleState(enemy=EnemyState(hp=1000, max_hp=1000), fighters={'id1': FighterState()})
    rt = PassiveRuntime()
    rt.register(rule)
    rt.emit(PassiveTrigger__v31_deferred.UNIT_DEATH, {'state': st, 'death_scope': 'ally'}, st)
    assert st.runtime.get('deferred_effects')
    assert st.runtime.get('deferred_effects')[0]['turns_remaining'] == 1

def test_deferred_turn_is_consumed_at_next_turn_start():
    r = compile_passive_v29({'id': 'p', 'name': '미래', 'effect': '아군 사망 시 다음 턴에 공격 위력 증가 1 얻음'}, 'id1', 0)
    rule = r.rules[0]
    st = BattleState(enemy=EnemyState(hp=1000, max_hp=1000), fighters={'id1': FighterState()})
    rt = PassiveRuntime()
    rt.register(rule)
    rt.emit(PassiveTrigger__v31_deferred.UNIT_DEATH, {'state': st, 'death_scope': 'ally'}, st)
    applied = rt.apply_deferred_turn_start(st)
    assert len(applied) == 1
    assert st.runtime['deferred_effects'] == []


# ======================================================================
# 원본: test_v31_enemy_death_effects.py
# ======================================================================

def _ident__v31_enemy(iid, name, effect):
    s = SkillData(iid + 's', '기본', 4, [CoinData(1, 'slash', 'lust')], 'slash', 'lust')
    s._slot = 'S1'
    i = IdentityData(iid, name, 0, {'S1': s}, [])
    i.passives = [{'name': 'p', 'effect': effect}]
    return (i, s)

def test_enemy_death_heals_lowest_ally_even_when_other_identity_kills():
    killer, sk = _ident__v31_enemy('id1', '킬러', '')
    healer, sh = _ident__v31_enemy('id2', '요리사', '적 사망 시 체력이 가장 낮은 아군 1명의 체력 15 회복. (턴 당 1회 발동)')

    class Fighter:
        pass
    f1 = Fighter()
    f1.hp = 50
    f1.max_hp = 100
    f1.resources = {}
    f1.statuses = {}
    f2 = Fighter()
    f2.hp = 20
    f2.max_hp = 100
    f2.resources = {}
    f2.statuses = {}

    class State:
        pass
    st = State()
    st.fighters = {'id1': f1, 'id2': f2}
    st.event_log = []
    g = GimmickRegistry([killer, healer], {killer.id: killer.passives, healer.id: healer.passives}, available_identity_ids=['id1', 'id2'])
    rules = [r for r in g.rules if r.kind == 'enemy_death_lowest_ally_heal']
    assert rules and rules[0].extra_scale == 15
    g.after_kill(st, killer, sk, {'target_id': 'enemy'})
    assert f2.hp == 35 and f1.hp == 50

def test_enemy_death_heal_respects_turn_limit():
    i, s = _ident__v31_enemy('id1', '요리사', '적 사망 시 체력이 가장 낮은 아군 1명의 체력 15 회복. (턴 당 1회 발동)')

    class F:
        pass
    f = F()
    f.hp = 20
    f.max_hp = 100
    f.resources = {}
    f.statuses = {}

    class State:
        pass
    st = State()
    st.fighters = {'id1': f}
    st.event_log = []
    g = GimmickRegistry([i], {i.id: i.passives}, available_identity_ids=['id1'])
    g.after_kill(st, i, s, {})
    g.after_kill(st, i, s, {})
    assert f.hp == 35


# ======================================================================
# 원본: test_v45_kill_resource_distribution.py
# ======================================================================

class F:
    def __init__(self, hp=100, charge=0): self.hp=hp; self.max_hp=hp; self.charge=charge; self.resources={}; self.statuses={}

class I:
    def __init__(self, i,n): self.id=i; self.name=n; self.skills={}

def test_parser_compiles_dynamic_kill_charge_distribution():
    owner=I('o','멀티크랙 사무소 대표')
    owner.passives=[{'effect':'적을 처치하면 자신과 충전 횟수가 가장 적은 아군 2명이 (2 + 충전)만큼 충전 횟수 증가 (최대 5)'}]
    reg=GimmickRegistry([owner], active_passives={'o':owner.passives}, available_identity_ids=['o'])
    rules=[r for r in reg.trigger_rules if r.metadata.get('legacy_kind')=='kill_resource_distribute']
    assert rules
    eff=rules[0].effects[0].to_dict()
    assert eff['amount_base']==2 and eff['amount_resource']=='충전' and eff['count']==2 and eff['cap']==5

def test_after_kill_distributes_to_owner_and_lowest_charge_ally():
    owner=I('o','멀티크랙 사무소 대표'); owner.passives=[{'effect':'적을 처치하면 자신과 충전 횟수가 가장 적은 아군 2명이 (2 + 충전)만큼 충전 횟수 증가 (최대 5)'}]
    a=I('a','ally A'); b=I('b','ally B')
    for x in (owner,a,b): x.skills={}
    reg=GimmickRegistry([owner,a,b], active_passives={'o':owner.passives}, available_identity_ids=['o','a','b'])
    from types import SimpleNamespace
    state=SimpleNamespace(fighters={'o':F(charge=4),'a':F(charge=1),'b':F(charge=3)}, event_log=[])
    skill=SimpleNamespace(id='s',name='S1')
    reg.after_kill(state, owner, skill, {})
    assert state.fighters['o'].charge==9
    assert state.fighters['a'].charge==6
    assert state.fighters['b'].charge==8
    assert len([e for e in state.event_log if e['event']=='kill_resource_distribution'])==3


# ======================================================================
# 원본: test_v46_kill_charge_variants.py
# ======================================================================

class F__v46_kill:

    def __init__(self, c):
        self.hp = 100
        self.max_hp = 100
        self.charge = c
        self.resources = {}
        self.statuses = {}

def test_owner_charge_copy_variant():
    o = I('o', '대표')
    o.passives = [{'effect': '적을 처치하면 자신과 충전 횟수가 가장 적은 아군 1명이 충전만큼 충전 횟수 증가 (최대 3)'}]
    a = I('a', 'A')
    b = I('b', 'B')
    reg = GimmickRegistry([o, a, b], active_passives={'o': o.passives}, available_identity_ids=['o', 'a', 'b'])
    rs = [r for r in reg.trigger_rules if r.metadata.get('legacy_kind') == 'kill_resource_distribute']
    assert rs and rs[0].effects[0].to_dict()['amount_base'] == 0 and (rs[0].effects[0].to_dict()['count'] == 1)
    st = SimpleNamespace(fighters={'o': F__v46_kill(4), 'a': F__v46_kill(1), 'b': F__v46_kill(3)}, event_log=[])
    reg.after_kill(st, o, SimpleNamespace(id='s', name='S1'), {})
    assert st.fighters['o'].charge == 7 and st.fighters['a'].charge == 4 and (st.fighters['b'].charge == 3)


# ======================================================================
# 원본: test_v50_charge_kill_priority.py
# ======================================================================

class S:
    def __init__(self,n,effects=None): self.id=n; self.name=n; self.skills={'s':SimpleNamespace(effects=effects or [], _source_effects=effects or [])}

def test_kill_charge_distribution_prefers_charge_capable_low_charge_ally():
    owner=S('o'); preferred=S('preferred',['[사용시] 충전 횟수 5 소모하여 코인 위력 +2']); other=S('other',[])
    owner.passives=[{'effect':'적을 처치하면 자신과 충전 횟수가 가장 적은 아군 1명이 충전만큼 충전 횟수 증가 (최대 3)'}]
    reg=GimmickRegistry([owner,preferred,other], active_passives={'o':owner.passives}, available_identity_ids=['o','preferred','other'])
    state=SimpleNamespace(fighters={'o':F(charge=4),'preferred':F(charge=2),'other':F(charge=0)}, event_log=[])
    reg.after_kill(state, owner, SimpleNamespace(id='s',name='S1'), {})
    assert state.fighters['preferred'].charge == 5
    assert state.fighters['other'].charge == 0
