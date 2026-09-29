"""병합 테스트: resource_runtime

원본 파일 (내용은 AST 병합기로 합쳤고 테스트 본문은 바꾸지 않음):
  - test_v29_resource_runtime.py
  - test_v29_resource_runtime_lifecycle.py
  - test_v29_cumulative_resource_consumption.py
  - test_v29_resource_trigger_integration.py
  - test_v29_resource_conversion.py
  - test_v29_special_resource_lifecycle.py
  - test_v29_special_resource_skill_parser.py
  - test_v29_special_resource_analyzer.py
  - test_v29_special_resource_analyzer_v2.py
이름 충돌 helper 는 `이름__vNN` 으로 분리했다. 매핑은 tools/MERGE_MAP.json 참고.
"""
from resource_runtime_v1 import ResourceRuntime
from one_turn_solver_v29 import IdentityCatalogV29, OneTurnSolverV29, SkillTextParserV19
from dataclasses import dataclass
from special_gimmick_v2 import GimmickRegistry
from special_resource_analyzer_v1 import analyze
from special_resource_analyzer_v2 import analyze as analyze__v29_special, scan



# ======================================================================
# 원본: test_v29_resource_runtime.py
# ======================================================================

def test_resource_runtime_gain_clamps_and_checks_threshold():
    class F: pass
    f=F(); f.resources={"새벽불":25}
    class S: pass
    s=S(); s.event_log=[]
    rr=ResourceRuntime(); rr.register("새벽불", maximum=30, threshold_variants={"새벽녘":30})
    assert rr.change(f,"새벽불",10,s,"assist") == 30
    assert rr.get(f,"새벽불") == 30
    assert rr.variant_ready(f,"새벽불","새벽녘")
    assert next(e for e in reversed(s.event_log) if e["event"]=="resource_change")["delta"] == 5

def test_solver_accepts_explicit_special_resource_spec():
    cat=IdentityCatalogV29.from_json('identity_catalog_v2.json')
    ident=cat.build_identity('identity-10114')
    sc={
        'enemy':{'hp':10000,'max_hp':10000,'level':60},
        'allies':{'identity-10114':{'sp':45,'resources':{'테스트자원':9}}},
        'resource_specs':{'테스트자원':{'maximum':10,'threshold_variants':{'강화':10}}},
        'actions':[{'identity_id':'identity-10114','skill_id':'1011401'}],
    }
    r=OneTurnSolverV29().solve(sc,{'identity-10114':ident})
    assert r['resource_specs']['테스트자원']['maximum'] == 10
    assert r['fighters']['identity-10114']['resources']['테스트자원'] == 9


# ======================================================================
# 원본: test_v29_resource_runtime_lifecycle.py
# ======================================================================

def test_threshold_crossing_emits_distinct_event_once_per_crossing():
    class F: pass
    class S: pass
    f=F(); f.resources={'X':8}
    s=S(); s.event_log=[]
    rr=ResourceRuntime(); rr.register('X', maximum=20, threshold_variants={'강화':10})
    rr.gain(f,'X',2,s,'test')
    events=[e for e in s.event_log if e['event']=='resource_threshold_reached']
    assert len(events)==1
    assert events[0]['variant']=='강화'
    rr.gain(f,'X',1,s,'test')
    assert len([e for e in s.event_log if e['event']=='resource_threshold_reached'])==1

def test_threshold_operator_and_consume_are_supported():
    class F: pass
    f=F(); f.resources={'X':5}
    rr=ResourceRuntime(); rr.register('X', threshold_variants={'low':3}, threshold_operators={'low':'<='})
    assert rr.variant_ready(f,'X','low') is False
    rr.consume(f,'X',2)
    assert rr.get(f,'X')==3
    assert rr.variant_ready(f,'X','low') is True


# ======================================================================
# 원본: test_v29_cumulative_resource_consumption.py
# ======================================================================

@dataclass
class Skill:
    id: str
    name: str
    _slot: str = 'S1'

@dataclass
class Ident:
    id: str
    name: str
    skills: dict
    passives: list

class Fighter:
    def __init__(self):
        self.resources={}
        self.charge=0

class State:
    def __init__(self):
        self.event_log=[]; self.runtime={'condition_flags':{}, 'cumulative_resource_consumed':{}}
        self.fighters={'A':Fighter()}

def test_cumulative_consumption_crossing_fires_once_per_threshold():
    a=Ident('A','A',{'S1':Skill('S1','S1')},[
        {'name':'passive','effect':'전투 중 누적으로 자신의 충전 횟수 10을 소모할 때마다, 충전 1 얻음'}
    ])
    reg=GimmickRegistry([a], {'A':a.passives}, available_identity_ids=['A'])
    assert any(r.kind=='cumulative_resource_gain' for r in reg.rules)
    st=State(); st.fighters['A'].charge=12
    # Simulate a 12-charge consumption as one lifecycle event.
    st.fighters['A'].charge=0
    st.event_log.append({'event':'charge_change','identity_id':'A','delta':-12,'before':12,'after':0})
    st.runtime['cumulative_resource_consumed'][('A','충전')]=12
    ev={'event':'resource_cumulative_consumed','identity_id':'A','resource':'충전','amount':12,
        'cumulative_before':0,'cumulative_after':12}
    acts=reg.after_resource_event(st,ev,{'A':a},1)
    # The rule is triggered once by crossing 10; its effect restores 1 charge.
    assert st.fighters['A'].charge==1
    assert acts==[]

def test_resource_runtime_tracks_cumulative_consumption_separately_from_live_value():
    class F: pass
    f=F(); f.resources={'X':12}
    class S: pass
    st=S(); st.event_log=[]; st.runtime={}; st.fighters={'A':f}
    rr=ResourceRuntime(); rr.register('X', maximum=20)
    rr.consume(f,'X',7,st,'test')
    assert f.resources['X']==5
    assert st.runtime['cumulative_resource_consumed'][('A','X')]==7
    rr.consume(f,'X',5,st,'test2')
    assert f.resources['X']==0
    assert st.runtime['cumulative_resource_consumed'][('A','X')]==12

def test_cumulative_consumption_can_cross_multiple_thresholds_in_one_event():
    a=Ident('A','A',{'S1':Skill('S1','S1')},[
        {'name':'passive','effect':'전투 중 누적으로 자신의 충전 횟수 10을 소모할 때마다, 충전 1 얻음'}
    ])
    reg=GimmickRegistry([a], {'A':a.passives}, available_identity_ids=['A'])
    st=State(); st.fighters['A'].charge=25; st.fighters['A'].charge=0
    ev={'event':'resource_cumulative_consumed','identity_id':'A','resource':'충전','amount':25,
        'cumulative_before':0,'cumulative_after':25}
    reg.after_resource_event(st,ev,{'A':a},1)
    assert st.fighters['A'].charge==2


# ======================================================================
# 원본: test_v29_resource_trigger_integration.py
# ======================================================================

class Fighter__v29_resource:

    def __init__(self):
        self.resources = {}

class State__v29_resource:

    def __init__(self):
        self.event_log = []
        self.runtime = {'condition_flags': {}}
        self.fighters = {'B': Fighter__v29_resource()}

def test_resource_threshold_trigger_can_set_flag_and_queue_action():
    b = Ident('B', 'B', {'S1': Skill('S1', 'S1')}, [])
    reg = GimmickRegistry([b], {'B': []}, available_identity_ids=['B'], extra_trigger_rules=[{'id': 'r1', 'owner_id': 'B', 'event': 'resource_threshold_reached', 'conditions': [{'type': 'resource', 'value': 'X'}, {'type': 'resource_variant', 'value': 'ready'}], 'effects': [{'type': 'set_flag', 'flag': 'X_READY', 'value': True}, {'type': 'queue_action', 'identity_id': 'B', 'skill_name': 'S1', 'trigger_kind': 'resource_activation'}]}])
    reg.reset_turn()
    st = State__v29_resource()
    acts = reg.after_resource_event(st, {'event': 'resource_threshold_reached', 'resource': 'X', 'variant': 'ready', 'threshold': 10, 'before': 9, 'after': 10, 'delta': 1}, {'B': b}, 1)
    assert st.runtime['condition_flags']['X_READY'] is True
    assert len(acts) == 1 and acts[0].skill_id == 'S1'

def test_resource_runtime_threshold_event_can_feed_trigger_runtime():
    class F: pass
    f=F(); f.resources={'X':9}
    class S: pass
    st=S(); st.event_log=[]; st.runtime={'condition_flags':{}}; st.fighters={'B':f}
    rr=ResourceRuntime(); rr.register('X', maximum=20, threshold_variants={'ready':10})
    rr.gain(f,'X',1,st,'test')
    events=[e for e in st.event_log if e['event']=='resource_threshold_reached']
    assert len(events)==1 and events[0]['after']==10


# ======================================================================
# 원본: test_v29_resource_conversion.py
# ======================================================================

def test_resource_conversion_parse_from_consumed_amount():
    parser = SkillTextParserV19()
    parsed, report = parser.parse(
        ['[사용시] 가속탄 소모한 수치 1당, 호흡 2 얻음'], 2
    )
    conv = [x for x in parsed['effects_on_use'] if x.get('type') == 'resource_gain_from_consumed']
    assert conv == [{'type': 'resource_gain_from_consumed', 'source': '가속탄', 'source_per': 1, 'target': '호흡', 'target_amount': 2}]
    assert not any(x.get('type') == 'resource_cost' and x.get('resource') == '가속탄' for x in parsed['effects_on_use'])

def test_fixed_resource_conversion_parse():
    parser = SkillTextParserV19()
    parsed, report = parser.parse(
        ['[사용시] 포자탄[기본] 2 소모하여, 포자탄[산탄] 1 얻음'], 2
    )
    conv = [x for x in parsed['effects_on_use'] if x.get('type') == 'resource_convert']
    assert conv == [{'type': 'resource_convert', 'source': '포자탄[기본]', 'source_amount': 2, 'target': '포자탄[산탄]', 'target_amount': 1}]
    assert not any(x.get('type') == 'resource_cost' for x in parsed['effects_on_use'])
    assert not any(x.get('type') == 'resource_gain' for x in parsed['effects_on_use'])

def test_fixed_conversion_is_retained_as_executable_use_effect():
    p = SkillTextParserV19()
    parsed, _ = p.parse(['[사용시] 포자탄[기본] 2 소모하여, 포자탄[산탄] 1 얻음'], 1)
    assert any(x.get('type') == 'resource_convert' for x in parsed['effects_on_use'])


# ======================================================================
# 원본: test_v29_special_resource_lifecycle.py
# ======================================================================

def test_special_resource_max_and_all_consume_are_parsed():
    p=SkillTextParserV19()
    parsed,_=p.parse(['[사용시] 자신의 생체 재료 횟수가 10 이상이면, 생체 재료 횟수를 최대 20까지 소모하고 아래 효과 적용', '[사용시] 새벽불 전부 소모'],1)
    assert any(x.get('type')=='resource_conditional_cost_max' and x.get('resource')=='생체 재료' and x.get('amount')==20 for x in parsed['effects_on_use'])
    assert any(x.get('type')=='resource_cost_all' and x.get('resource')=='새벽불' for x in parsed['effects_on_use'])

def test_special_resource_per_coin_cost_is_parsed():
    p=SkillTextParserV19()
    parsed,_=p.parse(['1코인 가속탄 1 소모'],1)
    assert parsed['coin_defs'][0]['resource_cost']=={'가속탄':1}

def test_conditional_resource_cost_is_not_unconditionally_applied():
    p=SkillTextParserV19()
    parsed,_=p.parse(['[사용시] 자신의 생체 재료 횟수가 10 이상이면, 생체 재료 횟수를 5 소모하고 아래 효과 적용'],1)
    assert parsed['effects_on_use'] == [{"type":"resource_conditional_cost","resource":"생체 재료","threshold":10,"amount":5,"operator":">="}]

def test_turn_start_zero_resource_transformation_pattern_is_recognized():
    import re
    rp='|'.join(re.escape(x) for x in sorted(SkillTextParserV19.SPECIAL_RESOURCE_NAMES,key=len,reverse=True))
    text="턴 시작 시 가속탄이 없다면, '세치오나투라 디 체르보'로 변경됨"
    m=re.search(r"턴\s*시작\s*시\s*("+rp+r")\s*(?:이|가|은|는)?\s*없(?:다면|으면|을 때).*?['‘’\"]([^'‘’\"]+)['‘’\"]\s*로\s*(?:변경|발동)",text)
    assert m and m.group(1)=='가속탄' and m.group(2)=='세치오나투라 디 체르보'

def test_resource_threshold_coin_power_is_parsed():
    p=SkillTextParserV19()
    parsed,_=p.parse(['자신의 적진 주파가 3 이상이면, 코인 위력 +1'],1)
    assert parsed['effects_on_use'][0]['type']=='_skill_condition_marker'
    assert parsed['effects_on_use'][0]['condition']['type']=='resource_gte'
    assert parsed['effects_on_use'][0]['condition']['resource']=='적진 주파'

def test_resource_threshold_coin_power_condition_reads_live_resource():
    from limbus_damage_engine_v29 import BattleState, EnemyState, FighterState, IdentityData, SkillData, CoinData, Status
    from one_turn_solver_v29 import OneTurnSolverV29
    f=FighterState(resources={'적진 주파':3})
    e=EnemyState(hp=999,max_hp=999)
    ident=IdentityData('A','A',0,{},[])
    skill=SkillData('S','S',1,[CoinData(1,'slash','lust')],'slash','lust')
    st=BattleState(enemy=e, fighters={'A':f})
    solver=OneTurnSolverV29()
    assert solver._condition_met(st, ident, {'type':'resource_gte','resource':'적진 주파','value':3}) is True
    f.resources['적진 주파']=2
    assert solver._condition_met(st, ident, {'type':'resource_gte','resource':'적진 주파','value':3}) is False

def test_turn_reset_all_applies_declared_reset():
    from resource_runtime_v1 import ResourceRuntime
    class F: pass
    class S: pass
    f=F(); f.resources={'X':7}
    st=S(); st.fighters={'A':f}; st.event_log=[]
    rr=ResourceRuntime(); rr.register('X',maximum=20,turn_reset=0)
    rr.reset_turn_all(st, {'A':None})
    assert f.resources['X']==0


# ======================================================================
# 원본: test_v29_special_resource_skill_parser.py
# ======================================================================

def test_identity_resource_gain_and_consume_are_parsed_separately():
    p=SkillTextParserV19()
    parsed,_=p.parse(["[사용시] 새벽불 5 얻음", "[사용시] 새벽불 2 소모"], 1)
    assert {x['type']: x['amount'] for x in parsed['effects_on_use'] if x.get('resource')=='새벽불'} == {
        'resource_gain': 5, 'resource_cost': 2
    }


# ======================================================================
# 원본: test_v29_special_resource_analyzer.py
# ======================================================================

def test_analyzer_excludes_ego_and_sin_candidates():
    r=analyze('identity_catalog_v2.json')
    for row in r['rows']:
        for name in row['resources']:
            assert 'E.G.O' not in name
            assert name not in {'분노','색욕','나태','탐식','우울','오만','질투'}

def test_analyzer_finds_dawn_fire():
    r=analyze('identity_catalog_v2.json')
    row=next(x for x in r['rows'] if x['identity_name']=='새벽 사무소 대표')
    assert any('새벽불' in name for name in row['resources'])

def test_lifecycle_score_bounded():
    r=analyze('identity_catalog_v2.json')
    assert 0 <= r['average_structural_lifecycle_coverage_pct'] <= 100


# ======================================================================
# 원본: test_v29_special_resource_analyzer_v2.py
# ======================================================================

def test_normalizer_does_not_treat_status_count_as_special_resource():
    r=scan("[적중시] 진동 횟수 2 증가. 진동 횟수 1 감소")
    assert '진동 횟수' not in r

def test_normalizer_keeps_dawn_fire():
    r = analyze__v29_special('identity_catalog_v2.json')
    row = next((x for x in r['rows'] if x['identity_name'] == '새벽 사무소 대표'))
    assert '새벽불' in row['resources']

def test_normalizer_keeps_ego_and_sin_excluded():
    r = analyze__v29_special('identity_catalog_v2.json')
    for row in r['rows']:
        for name in row['resources']:
            assert 'E.G.O' not in name
            assert name not in {'분노', '색욕', '나태', '탐식', '우울', '오만', '질투'}

def test_confidence_is_bounded():
    r = analyze__v29_special('identity_catalog_v2.json')
    assert all((0 <= d['confidence_pct'] <= 100 for row in r['rows'] for d in row['resources'].values()))

# ======================================================================
# Charge Count / Potency separation
# ======================================================================

def test_charge_count_and_potency_are_independent_axes():
    class F:
        def __init__(self):
            self.charge = 12
            self.charge_potency = 3
            self.ammo = 0
            self.resources = {}
    class S:
        def __init__(self):
            self.event_log = []
            self.runtime = {}
    f=F(); st=S(); rr=ResourceRuntime()
    assert rr.get(f, '충전') == 12
    assert rr.get(f, '충전 위력') == 3
    rr.consume(f, '충전', 5, st, 'test_count')
    assert f.charge == 7
    assert f.charge_potency == 3
    rr.gain(f, '충전 위력', 2, st, 'test_potency')
    assert f.charge == 7
    assert f.charge_potency == 5


def test_charge_potency_is_scenario_input_and_solver_output():
    cat=IdentityCatalogV29.from_json('identity_catalog_v2.json')
    ident=cat.build_identity('identity-10114')
    sc={
        'enemy':{'hp':10000,'max_hp':10000,'level':60},
        'allies':{'identity-10114':{'sp':45,'charge':12,'charge_potency':4}},
        'actions':[],
    }
    state=OneTurnSolverV29().build_state(sc, {'identity-10114':ident})
    f=state.fighters['identity-10114']
    assert f.charge == 12
    assert f.charge_potency == 4


def test_charge_potency_does_not_share_cumulative_count_bucket():
    class F:
        def __init__(self):
            self.charge = 20
            self.charge_potency = 2
            self.resources = {}
    class S:
        def __init__(self):
            self.event_log=[]
            self.runtime={}
            self.fighters={'A': self.f}
        f=None
    st=S(); st.f=F(); st.fighters={'A':st.f}
    rr=ResourceRuntime()
    rr.consume(st.f, '충전', 10, st, 'test')
    assert st.runtime['cumulative_resource_consumed'][('A','충전')] == 10
    assert st.f.charge == 10
    assert st.f.charge_potency == 2


def test_charge_turn_end_decay_is_not_cumulative_spend_and_potency_persists_at_zero():
    from keyword_runtime_v1 import KeywordRuntime
    from limbus_damage_engine_v29 import BattleState, EnemyState, FighterState
    f = FighterState(charge=1, charge_potency=3)
    st = BattleState(enemy=EnemyState(hp=100, max_hp=100), fighters={'A': f})
    st.runtime['resource_runtime'] = ResourceRuntime()

    # Turn-end decay is lifecycle loss, not explicit Charge consumption.
    KeywordRuntime.turn_end(st)
    assert f.charge == 0
    assert f.charge_potency == 3
    assert st.runtime.get('cumulative_resource_consumed', {}) == {}

    # Explicit skill/resource consumption is cumulative-spend eligible.
    rr = st.runtime['resource_runtime']
    f.charge = 10
    rr.consume(f, '충전', 10, st, 'skill_spend')
    assert f.charge == 0
    assert f.charge_potency == 3
    assert st.runtime['cumulative_resource_consumed'][('A', '충전')] == 10


def test_only_explicit_charge_potency_rules_can_generate_potency():
    """Charge possession must not implicitly enable Charge Potency generation.

    The catalog currently contains exactly one identity with an explicit
    cumulative Charge Count -> Charge Potency rule. Other Charge identities
    may have cumulative Charge Count -> Charge Count conversions, but those
    must not mutate charge_potency.
    """
    from identity_catalog_v29 import IdentityCatalogV29
    from special_gimmick_v2 import GimmickRegistry
    from limbus_damage_engine_v29 import BattleState, EnemyState, FighterState
    cat=IdentityCatalogV29.from_json('identity_catalog_v2.json')
    charge_identities=[]
    potency_rule_owners=[]
    for identity_id, record in cat.records.items():
        if '충전' not in (record.get('keywords') or []):
            continue
        charge_identities.append(str(identity_id))
        ident=cat.build_identity(identity_id)
        reg=GimmickRegistry([ident], {str(ident.id):ident.passives}, available_identity_ids=[str(ident.id)])
        for r in reg.rules:
            if r.kind != 'cumulative_resource_gain':
                continue
            if '충전 위력' in r.source_text and '충전 횟수' in r.source_text:
                potency_rule_owners.append(str(ident.id))
    assert len(charge_identities) >= 1
    assert potency_rule_owners == ['identity-10116']


def test_non_potency_charge_identity_cumulative_spend_does_not_raise_potency():
    from identity_catalog_v29 import IdentityCatalogV29
    from special_gimmick_v2 import GimmickRegistry
    from limbus_damage_engine_v29 import BattleState, EnemyState, FighterState
    cat=IdentityCatalogV29.from_json('identity_catalog_v2.json')
    for identity_id in ('identity-10210','identity-10612','identity-10709','identity-10713','identity-10914','identity-11110'):
        ident=cat.build_identity(identity_id)
        reg=GimmickRegistry([ident], {str(ident.id):ident.passives}, available_identity_ids=[str(ident.id)])
        f=FighterState(charge=10, charge_potency=0)
        st=BattleState(enemy=EnemyState(hp=100, max_hp=100), fighters={str(ident.id):f})
        st.runtime['resource_runtime']=ResourceRuntime()
        ev={'event':'resource_cumulative_consumed','identity_id':str(ident.id),'resource':'충전','amount':10,
            'cumulative_before':0,'cumulative_after':10}
        reg.after_resource_event(st,ev,{str(ident.id):ident},1)
        assert f.charge_potency == 0, identity_id


def test_catalog_charge_potency_cumulative_rule_compiles_and_executes():
    from identity_catalog_v29 import IdentityCatalogV29
    from special_gimmick_v2 import GimmickRegistry
    from limbus_damage_engine_v29 import BattleState, EnemyState, FighterState
    cat=IdentityCatalogV29.from_json('identity_catalog_v2.json')
    ident=cat.build_identity('identity-10116')
    reg=GimmickRegistry([ident], {str(ident.id): ident.passives}, available_identity_ids=[str(ident.id)])
    rules=[r for r in reg.rules if r.kind=='cumulative_resource_gain']
    assert any('충전 위력 1' in r.source_text for r in rules)
    f=FighterState(charge=10, charge_potency=0)
    st=BattleState(enemy=EnemyState(hp=100, max_hp=100), fighters={str(ident.id):f})
    st.runtime['resource_runtime'] = ResourceRuntime()
    ev={'event':'resource_cumulative_consumed','identity_id':str(ident.id),'resource':'충전','amount':10,
        'cumulative_before':0,'cumulative_after':10}
    reg.after_resource_event(st,ev,{str(ident.id):ident},1)
    assert f.charge_potency == 1
    assert f.charge == 10


def test_cumulative_blood_spent_damage_scaling_reads_encounter_counter_not_live_resource():
    import passive_compiler_v29 as pc
    text = '적중시 자신의 누적 소모 혈찬 10당, 피해량 +1% (최대 20%)'
    effects = pc.parse_effects(text)
    assert effects
    expr = effects[0].effect.amount
    from passive_compiler_v29 import CumulativeResourceConsumedField, ResourceField
    def walk(v):
        yield v
        for name in ('inner','left','right'):
            x=getattr(v,name,None)
            if x is not None:
                yield from walk(x)
    assert any(isinstance(v, CumulativeResourceConsumedField) and v.name == '혈찬' for v in walk(expr))
    assert not any(isinstance(v, ResourceField) and v.name == '누적 소모 혈찬' for v in walk(expr))


def test_cumulative_blood_spent_damage_scaling_resolves_from_encounter_bucket():
    import passive_compiler_v29 as pc
    from types import SimpleNamespace
    fighter = SimpleNamespace(id='A', resources={'혈찬': 0})
    state = SimpleNamespace(runtime={'cumulative_resource_consumed': {('A','혈찬'): 55}}, fighters={'A': fighter})
    event = {}
    effects = pc.parse_effects('적중시 자신의 누적 소모 혈찬 10당, 피해량 +1% (최대 20%)')
    expr = effects[0].effect.amount
    assert abs(expr.resolve(event, state, 'A') - 0.05) < 1e-9
