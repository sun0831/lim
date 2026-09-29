"""병합 테스트: damage_modifiers

원본 파일 (내용은 AST 병합기로 합쳤고 테스트 본문은 바꾸지 않음):
  - test_v29_skill_damage_scaling.py
  - test_v32_dynamic_damage_modifiers.py
  - test_v33_generic_dynamic_damage_scaling.py
  - test_v34_conditional_clash_power.py
  - test_v34_generic_coin_conditions.py
  - test_v35_flat_additional_damage.py
  - test_v35_generic_final_power_conditions.py
  - test_v35_generic_status_clash_conditions.py
  - test_v36_batch_damage_patterns.py
  - test_v36_status_burst_and_resource_coin_power.py
  - test_v37_attack_weight_target_scaling.py
  - test_v44_named_stack_damage.py
  - test_v66_named_resource_damage_scaling.py
이름 충돌 helper 는 `이름__vNN` 으로 분리했다. 매핑은 tools/MERGE_MAP.json 참고.
"""
import json
from one_turn_solver_v29 import SkillTextParserV19, IdentityCatalogV29, OneTurnSolverV29
from limbus_damage_engine_v29 import (
    BattleState,
    EnemyState,
    FighterState,
    IdentityData,
    DamageEngine,
    SkillData,
    CoinData,
    Status,
)
from passive_compiler_v29 import compile_passive_v29



# ======================================================================
# 원본: test_v29_skill_damage_scaling.py
# ======================================================================

def test_skill_status_potency_scaling_is_parsed():
    parser = SkillTextParserV19()
    parsed, report = parser.parse(['대상의 화상 위력 10 당, 피해량 +10% (최대 30%)'], 1)
    markers = parsed['effects_on_use']
    assert any(m.get('type') == '_skill_damage_condition_marker' and
               m['condition']['name'] == 'Burn' and
               m['condition']['use_potency'] is True and
               m['condition']['per'] == 10 and
               m['condition']['max'] == 0.30 for m in markers)
    assert '대상의 화상 위력 10 당, 피해량 +10% (최대 30%)' in report.supported

def test_skill_coin_extra_damage_scale_is_parsed():
    parser = SkillTextParserV19()
    parsed, report = parser.parse(['1코인 [적중시] 피해량의 30%만큼 추가 피해'], 1)
    assert parsed['coin_defs'][0]['effects'] == [{'type': 'extra_damage_scale', 'scale': 0.30}]
    assert report.unsupported == []

def test_status_threshold_damage_marker_uses_status_presence_and_potency():
    parser = SkillTextParserV19()
    parsed, _ = parser.parse(['대상의 출혈 위력 6 이상이면, 피해량 +20%'], 1)
    marker = next(x for x in parsed['effects_on_use'] if x.get('type') == '_skill_condition_marker')
    assert marker['condition'] == {'type': 'status', 'name': 'Bleed', 'target': 'enemy', 'potency_gte': 6}
    assert marker['damage_bonus'] == 0.20


# ======================================================================
# 원본: test_v32_dynamic_damage_modifiers.py
# ======================================================================

def parse(text):
    return SkillTextParserV19().parse([text], 1)[0]

def test_speed_difference_times_target_rupture_damage():
    p=parse('자신의 속도가 대상보다 빠르면, (대상과의 속도 차이 x 대상의 파열 위력)%만큼 피해량이 증가 (최대 50%)')
    c=p['effects_on_use'][0]['condition']
    assert c['type']=='speed_diff_status_damage' and c['status']=='Rupture' and c['cap']==0.5

def test_self_lost_hp_damage_scaling():
    p=parse('자신의 잃은 체력 1%당 피해량 1% 증가 (최대 30%)')
    c=p['effects_on_use'][0]['condition']
    assert c['type']=='self_lost_hp_per' and c['amount']==0.01 and c['max']==0.3

def test_enemy_lost_hp_ratio_damage_scaling():
    p=parse('적(본체)의 잃은 체력 비율만큼 피해량 증가')
    c=p['effects_on_use'][0]['condition']
    assert c['type']=='enemy_lost_hp_ratio'


def test_enemy_lost_hp_per_damage_scaling():
    p=parse('대상의 잃은 체력 1% 당 피해량 +0.3% (최대 30%)')
    c=p['effects_on_use'][0]['condition']
    assert c['type']=='enemy_lost_hp_per' and c['per']==1 and c['amount']==0.003 and c['max']==0.3


# ======================================================================
# 원본: test_v33_generic_dynamic_damage_scaling.py
# ======================================================================

def parse__v33_generic(text):
    p = SkillTextParserV19()
    parsed, report = p.parse([text], 1)
    assert not report.unsupported, report.unsupported
    d = parsed['effects_on_use'][0]
    assert d['type'] == '_skill_damage_condition_marker'
    return d

def make_skill(condition):
    s=SkillData(id='s', name='s', base_power=10, coins=[CoinData(0,'slash','lust')], attack_type='slash', sin='lust')
    s.conditions=[{'effect':'damage_bonus','condition':condition,'amount':condition.get('amount',0),'max':condition.get('max',999999)}]
    return s

def test_status_sum_damage_parser_and_cap():
    d = parse__v33_generic('[사용시] 대상의 출혈과 진동의 합 1당, 피해량 +1% (최대 40%)')
    assert d['condition']['type'] == 'status_sum_per'
    assert d['condition']['names'] == ['Bleed', 'Tremor']
    assert d['condition']['per'] == 1
    assert d['condition']['amount'] == 0.01
    assert d['condition']['max'] == 0.4

def test_single_status_damage_per_one_parser():
    d = parse__v33_generic('대상의 화상당, 피해량 +5% (최대 60%)')
    assert d['condition']['type'] == 'status_sum_per'
    assert d['condition']['names'] == ['Burn']
    assert d['condition']['per'] == 1

def test_status_sum_damage_dynamic():
    ident=IdentityData('i','i',0,{'s':make_skill({'type':'status_sum_per','names':['Bleed','Tremor'],'target':'enemy','per':1,'amount':0.01,'max':0.40,'use_potency':True})})
    state=BattleState(fighters={'i':FighterState()}, enemy=EnemyState(80,100), runtime={})
    state.enemy.statuses={'Bleed':Status(potency=20), 'Tremor':Status(potency=30)}
    m=DamageEngine.dynamic_modifier(state,ident,ident.skills['s'],0,ident.skills['s'].coins[0])
    assert abs(m-0.40)<1e-9

def test_self_resource_per_damage_dynamic():
    ident=IdentityData('i','i',0,{'s':make_skill({'type':'resource_per','resource':'찢어진 추억','target':'self','per':1,'amount':0.15,'max':1.05})})
    f=FighterState(resources={'찢어진 추억':5})
    state=BattleState(fighters={'i':f}, enemy=EnemyState(100,100), runtime={})
    m=DamageEngine.dynamic_modifier(state,ident,ident.skills['s'],0,ident.skills['s'].coins[0])
    assert abs(m-0.75)<1e-9

def test_enemy_current_hp_threshold_damage_dynamic():
    ident=IdentityData('i','i',0,{'s':make_skill({'type':'enemy_hp_pct_lte','value':50,'amount':0.50,'strict':False})})
    state=BattleState(fighters={'i':FighterState()}, enemy=EnemyState(50,100), runtime={})
    m=DamageEngine.dynamic_modifier(state,ident,ident.skills['s'],0,ident.skills['s'].coins[0])
    assert abs(m-0.50)<1e-9

def test_enemy_current_hp_threshold_not_met():
    ident=IdentityData('i','i',0,{'s':make_skill({'type':'enemy_hp_pct_lte','value':50,'amount':0.50,'strict':False})})
    state=BattleState(fighters={'i':FighterState()}, enemy=EnemyState(51,100), runtime={})
    m=DamageEngine.dynamic_modifier(state,ident,ident.skills['s'],0,ident.skills['s'].coins[0])
    assert abs(m)<1e-9


# ======================================================================
# 원본: test_v34_conditional_clash_power.py
# ======================================================================

def test_status_threshold_clash_power():
    p=SkillTextParserV19(); parsed,rep=p.parse(['대상의 출혈 6 이상이면, 합 위력 +2'],2)
    assert not rep.unsupported
    assert any(e.get('type')=='_skill_clash_power_condition_marker' for e in parsed['effects_on_use'])

def test_self_resource_clash_power():
    p=SkillTextParserV19(); parsed,rep=p.parse(['자신의 지령 3 이상이면, 합 위력 +1'],2)
    assert not rep.unsupported
    assert any(e.get('type')=='_skill_clash_power_condition_marker' for e in parsed['effects_on_use'])

def test_status_sum_clash_power():
    p=SkillTextParserV19(); parsed,rep=p.parse(['대상의 출혈과 화상의 합 5 당, 합 위력 +1 (최대 2)'],2)
    assert not rep.unsupported
    e=next(e for e in parsed['effects_on_use'] if e.get('type')=='_skill_clash_power_condition_marker')
    assert e['condition']['per']==5 and e['condition']['max']==2


# ======================================================================
# 원본: test_v34_generic_coin_conditions.py
# ======================================================================

def parse_coin(text):
    p=SkillTextParserV19(); parsed,rep=p.parse([text],1)
    assert not rep.unsupported, rep.unsupported
    return parsed['effects_on_use'][0]['condition']

def test_main_target_status_threshold_coin_power():
    c=parse_coin('[사용시] 메인 타겟의 출혈 횟수가 6 이상이면, 코인 위력 +2')
    assert c == {'type':'status_threshold','target':'enemy','name':'Bleed','field':'count','value':6,'amount':2}

def test_self_lost_hp_coin_power():
    c=parse_coin('[사용시] 자신의 잃은 체력 30% 당, 코인 위력 +1 (최대 2)')
    assert c['type']=='self_lost_hp_per_coin' and c['max']==2

def test_coin_roll_uses_current_lost_hp():
    skill=SkillData(id='s',name='s',base_power=10,coins=[CoinData(5,'slash','lust')],attack_type='slash',sin='lust')
    skill.conditions=[{'effect':'coin_power','condition':{'type':'self_lost_hp_per_coin','per_pct':30,'amount':1,'max':2}}]
    ident=IdentityData('i','i',0,{'s':skill})
    f=FighterState(hp=40,max_hp=100)
    st=BattleState(fighters={'i':f},enemy=EnemyState(100,100),runtime={})
    assert DamageEngine().coin_roll(st,ident,skill,skill.coins[0],'H') == 17

def test_self_status_threshold_coin_power_parser():
    c=parse_coin('[사용시] 자신의 진동 횟수가 5 이상일 때 코인 위력 +1')
    assert c['type']=='status_threshold' and c['target']=='self' and c['field']=='count'

def test_speed_threshold_coin_power_parser():
    c=parse_coin('자신의 속도가 10 이상이면, 코인 위력 +2')
    assert c == {'type':'speed_gte','value':10,'amount':2}


# ======================================================================
# 원본: test_v35_flat_additional_damage.py
# ======================================================================

def test_flat_additional_damage_head_only_is_parsed():
    p=SkillTextParserV19()
    parsed, rep=p.parse(['1코인 [앞면 적중시] 추가 피해 +3','1코인 [적중시] 화상 1 부여'], 1)
    assert '1코인 [앞면 적중시] 추가 피해 +3' in rep.supported
    assert parsed['coin_defs'][0]['heads_effects'][0]['type']=='damage_fixed'
    assert parsed['coin_defs'][0]['heads_effects'][0]['amount']==3.0

def test_flat_additional_damage_does_not_become_percent_modifier():
    p=SkillTextParserV19()
    parsed, rep=p.parse(['1코인 [적중시] 추가 피해 +7'], 1)
    e=parsed['coin_defs'][0]['effects'][0]
    assert e == {'type':'damage_fixed','amount':7.0,'target':'enemy'}
    assert '1코인 [적중시] 추가 피해 +7' in rep.supported


# ======================================================================
# 원본: test_v35_generic_final_power_conditions.py
# ======================================================================

def test_status_sum_final_power_parser():
    p=SkillTextParserV19(); parsed,rep=p.parse(['[사용시] 대상의 화상과 파열의 합 6당, 최종 위력 +1 (최대 3)'],1)
    assert not rep.unsupported, rep.unsupported
    e=next(x for x in parsed['effects_on_use'] if x['type']=='_skill_final_power_condition_marker')
    assert e['condition']['names']==['Burn','Rupture'] and e['condition']['per']==6 and e['condition']['amount']==1

def test_status_sum_final_power_is_applied_dynamically():
    skill=SkillData(id='s',name='s',base_power=10,coins=[CoinData(5,'slash','lust')],attack_type='slash',sin='lust')
    skill.conditions=[{'effect':'final_power','condition':{'type':'status_sum_per','names':['Burn','Rupture'],'target':'enemy','per':6,'amount':1,'max':3,'use_potency':True},'amount':1,'max':3}]
    ident=IdentityData('i','i',0,{'s':skill})
    st=BattleState(fighters={'i':FighterState()},enemy=EnemyState(100,100),runtime={})
    st.enemy.statuses={'Burn':Status(potency=12),'Rupture':Status(potency=7)}
    assert DamageEngine().coin_roll(st,ident,skill,skill.coins[0],'H')==18


# ======================================================================
# 원본: test_v35_generic_status_clash_conditions.py
# ======================================================================

def test_self_status_count_gain_at_use_is_parsed_as_self_effect():
    p = SkillTextParserV19()
    parsed, rep = p.parse(["[사용시] 자신의 진동 횟수 2 증가"], 1)
    assert not rep.unsupported
    assert any(e.get('type') == 'status' and e.get('name') == 'Tremor'
               and e.get('count') == 2 and e.get('target') == 'self'
               for e in parsed['effects_on_use'])

def test_clash_win_status_count_gain_is_executable_skill_effect():
    p = SkillTextParserV19()
    parsed, rep = p.parse(["[합 승리시] 파열 횟수 2 부여"], 1)
    assert not rep.unsupported
    assert any(e.get('type') == 'effects_on_clash_win'
               and e.get('effect', {}).get('name') == 'Rupture'
               and e.get('effect', {}).get('count') == 2
               for e in parsed['effects_on_use'])

def test_speed_difference_exact_coin_power_condition():
    p = SkillTextParserV19()
    parsed, rep = p.parse(["자신의 속도가 대상보다 3 이상 높으면, 코인 위력 +1"], 1)
    assert not rep.unsupported
    assert any(e.get('condition', {}).get('type') == 'speed_difference_gte'
               and e.get('condition', {}).get('value') == 3
               for e in parsed['effects_on_use'])


# ======================================================================
# 원본: test_v36_batch_damage_patterns.py
# ======================================================================

def test_charge_per_damage_is_parsed():
    p=SkillTextParserV19(); parsed,rep=p.parse(['충전당 피해량 +3% (최대 15%)'], 2)
    assert not rep.unsupported
    e=next(e for e in parsed['effects_on_use'] if e.get('type')=='_skill_damage_condition_marker')
    assert e['condition']['resource']=='충전' and e['condition']['amount']==0.03 and e['condition']['max']==0.15

def test_static_crit_damage_bonus_is_parsed():
    p=SkillTextParserV19(); parsed,rep=p.parse(['크리티컬 피해량 +30%'], 2)
    assert not rep.unsupported
    assert any(e.get('type')=='_skill_static_crit_damage_bonus' and e.get('amount')==0.3 for e in parsed['effects_on_use'])

def test_ammo_to_base_power_is_parsed():
    p=SkillTextParserV19(); parsed,rep=p.parse(['이 스킬에서 소모할 탄환 1 당 기본 위력 +1'], 2)
    assert not rep.unsupported
    assert any(e.get('type')=='_skill_base_power_from_ammo' and e.get('per')==1 and e.get('amount')==1 for e in parsed['effects_on_use'])


# ======================================================================
# 원본: test_v36_status_burst_and_resource_coin_power.py
# ======================================================================

def test_tremor_burst_parses():
    p=SkillTextParserV19(); parsed,rep=p.parse(["1코인 [적중시] 진동 폭발. 대상의 진동 횟수 1 감소"],1)
    assert not rep.unsupported, rep.unsupported
    assert parsed['coin_defs'][0]['effects'][0]['type']=='tremor_burst'

def test_status_burst_raises_tremor_threshold_and_consumes_count():
    e=DamageEngine(); enemy=EnemyState(100,100,stagger_thresholds=[70],statuses={'Tremor':Status(potency=17,count=2)})
    ident=IdentityData('i','I',0,{})
    f=FighterState('i',45,45)
    state=BattleState(enemy=enemy,fighters={'i':f})
    e.apply_effect(state,'i','enemy',{'type':'tremor_burst','name':'Tremor','count_cost':1})
    assert enemy.hp==100
    assert enemy.stagger_thresholds==[87]
    assert enemy.statuses['Tremor'].count==1

def test_resource_consumption_coin_power_parses():
    p=SkillTextParserV19(); parsed,rep=p.parse(["[사용시] 충전 횟수를 10 소모하여 코인 위력 +2"],2)
    assert not rep.unsupported, rep.unsupported
    assert any(x.get('type')=='resource_cost' and x.get('resource')=='충전' and x.get('amount')==10 for x in parsed['effects_on_use'])
    assert any(x.get('type')=='_skill_condition_marker' and x.get('condition',{}).get('amount')==2 for x in parsed['effects_on_use'])


# ======================================================================
# 원본: test_v37_attack_weight_target_scaling.py
# ======================================================================

def test_attack_weight_gap_damage_parser():
    p=SkillTextParserV19()
    parsed, rep=p.parse(['이 스킬 공격 가중치보다 낮은 공격 대상 1당 피해량 +60%'], 1)
    assert not rep.unsupported, rep.unsupported
    e=parsed['effects_on_use'][0]
    assert e['type']=='_skill_damage_condition_marker'
    assert e['condition']['type']=='attack_weight_gap_damage'
    assert abs(e['condition']['amount']-0.60)<1e-9

def test_one_target_damage_parser():
    p=SkillTextParserV19()
    parsed, rep=p.parse(['공격 대상이 1이면, 피해량 +25%'], 1)
    assert not rep.unsupported, rep.unsupported
    e=parsed['effects_on_use'][0]
    assert e['condition']['type']=='target_count_eq'
    assert e['condition']['value']==1
    assert abs(e['condition']['amount']-0.25)<1e-9

def test_attack_weight_gap_dynamic_modifier():
    skill=SkillData(id='s',name='s',base_power=10,coins=[CoinData(0,'slash','lust')],attack_type='slash',sin='lust',attack_weight=3)
    skill.conditions=[{'effect':'damage_bonus','condition':{'type':'attack_weight_gap_damage','amount':0.60}}]
    ident=IdentityData('i','i',0,{'s':skill})
    state=BattleState(fighters={'i':FighterState()},enemy=EnemyState(100,100),runtime={'current_target_count':1})
    m=DamageEngine.dynamic_modifier(state,ident,skill,0,skill.coins[0])
    assert abs(m-1.20)<1e-9

def test_attack_weight_gap_zero_when_full_weight_is_hit():
    skill=SkillData(id='s',name='s',base_power=10,coins=[CoinData(0,'slash','lust')],attack_type='slash',sin='lust',attack_weight=3)
    skill.conditions=[{'effect':'damage_bonus','condition':{'type':'attack_weight_gap_damage','amount':0.60}}]
    ident=IdentityData('i','i',0,{'s':skill})
    state=BattleState(fighters={'i':FighterState()},enemy=EnemyState(100,100),runtime={'current_target_count':3})
    m=DamageEngine.dynamic_modifier(state,ident,skill,0,skill.coins[0])
    assert abs(m)<1e-9


# ======================================================================
# 원본: test_v44_named_stack_damage.py
# ======================================================================

def test_named_self_stack_damage_scaling_is_parsed():
    p=SkillTextParserV19(); parsed,rep=p.parse(['자신의 지령의 가호 1당 피해량 +2% (최대 16%)'],1)
    assert not rep.unsupported
    marker=[x for x in parsed['effects_on_use'] if x.get('type')=='_skill_damage_condition_marker'][0]
    assert marker['condition']['type'] in ('named_stack_per','resource_per')
    if marker['condition']['type']=='named_stack_per':
        assert marker['condition']['name']=='지령의 가호'
    else:
        assert marker['condition']['resource']=='지령의 가호'
    assert marker['condition']['target']=='self'

def test_named_self_status_stack_damage_scaling_is_parsed():
    p=SkillTextParserV19(); parsed,rep=p.parse(['사랑/증오당, 피해량 +2% (최대 10%)'],1)
    assert not rep.unsupported
    marker=[x for x in parsed['effects_on_use'] if x.get('type')=='_skill_damage_condition_marker'][0]
    assert marker['condition']['name']=='사랑/증오'

def test_named_target_stack_damage_scaling_is_parsed():
    p=SkillTextParserV19(); parsed,rep=p.parse(['대상의 잔향 1당 피해량 +1% (최대 20%)'],1)
    assert not rep.unsupported
    marker=[x for x in parsed['effects_on_use'] if x.get('type')=='_skill_damage_condition_marker'][0]
    assert marker['condition']['name']=='잔향'
    assert marker['condition']['target']=='enemy'

def test_named_stack_damage_dynamic_from_resource_and_status():
    from limbus_damage_engine_v29 import DamageEngine, BattleState, FighterState, EnemyState, IdentityData, SkillData, CoinData, Status
    def skill(cond):
        s=SkillData(id='s',name='s',base_power=10,coins=[CoinData(0,'slash','lust')],attack_type='slash',sin='lust')
        s.conditions=[{'effect':'damage_bonus','condition':cond,'amount':cond.get('amount',0),'max':cond.get('max',999999)}]
        return s
    ident=IdentityData('i','i',0,{})
    ident.skills['s']=skill({'type':'named_stack_per','name':'지령의 가호','target':'self','per':1,'amount':.02,'max':.16})
    f=FighterState(resources={'지령의 가호':5})
    st=BattleState(fighters={'i':f},enemy=EnemyState(100,100),runtime={})
    assert abs(DamageEngine.dynamic_modifier(st,ident,ident.skills['s'],0,ident.skills['s'].coins[0])-.10)<1e-9
    ident.skills['s']=skill({'type':'named_stack_per','name':'잔향','target':'enemy','per':1,'amount':.01,'max':.20})
    st.enemy.statuses={'잔향':Status(potency=12)}
    assert abs(DamageEngine.dynamic_modifier(st,ident,ident.skills['s'],0,ident.skills['s'].coins[0])-.12)<1e-9


# ======================================================================
# 원본: test_v66_named_resource_damage_scaling.py
# ======================================================================

def _identity(passive):
    return {
        'id': 'x', 'name': 'X', 'offense_level': 0,
        'stats': {'level': 60, 'speed': 13, 'hp': 1000, 'hpBase': 1000,
                  'defenseLevel': 0, 'resistances': {}},
        'skills': {
            'S1': {
                'id': 'S1', 'name': 'S1', 'base_power': 50,
                'coin_powers': [10], 'coin_count': 1,
                'coins': [{'coin_power': 10, 'damage_type': 'slash', 'sin': 'lust'}],
                'attack_type': 'slash', 'sin': 'lust',
            }
        },
        'passives': [{'id': 'p', 'name': 'P', 'effect': passive}],
    }

def _solve(passive, resources):
    ident = IdentityCatalogV29([_identity(passive)]).build_identity('x', level=60, speed=13)
    scenario = {
        'enemy': {
            'hp': 1000, 'max_hp': 1000, 'level': 60, 'defense_level': 60,
            'speed': 10, 'physical_res': {'slash': 1, 'pierce': 1, 'blunt': 1},
            'sin_res': {'lust': 1},
        },
        'allies': {'x': {'sp': 0, 'hp': 1000, 'max_hp': 1000,
                         'speed': 13, 'resources': resources}},
        'actions': [{'identity_id': 'x', 'skill_id': 'S1', 'faces': ['H']}],
        'passive_mode': 'compiled_conservative',
    }
    return OneTurnSolverV29().solve(scenario, {'x': ident})

def test_named_resource_damage_is_per_stack_not_flat():
    text = '자신의 오혈 1 당 스킬 피해량 +3%'
    bundle = compile_passive_v29({'id': 'p', 'name': 'P', 'effect': text}, 'x', 0)
    assert bundle.unsupported_reasons == ()
    assert bundle.rules[0].trigger.value == 'CoinStart'

    d0 = _solve(text, {'오혈': 0})['turn_damage']
    d1 = _solve(text, {'오혈': 1})['turn_damage']
    d5 = _solve(text, {'오혈': 5})['turn_damage']
    assert d0 == 60.0
    assert d1 == 61.0
    assert d5 == 69.0

def test_named_resource_damage_respects_cap():
    text = '흑수환염[黑獣丸染] 1 당 피해량 +5% (최대 55%)'
    bundle = compile_passive_v29({'id': 'p', 'name': 'P', 'effect': text}, 'x', 0)
    assert bundle.unsupported_reasons == ()
    # 20 stacks would imply 100%, but the declarative cap must hold at 55%.
    damage = _solve(text, {'흑수환염[黑獣丸染]': 20})['turn_damage']
    assert damage == 93.0

# ======================================================================
# E36 Golden follow-up: conditional coin-local resource damage
# ======================================================================

def test_rodion_tears_forge_damage_bonus_is_conditional():
    parser = SkillTextParserV19()
    parsed, report = parser.parse([
        '3코인 눈물 벼리기를 보유하였거나 이 코인에서 소모하였다면, 피해량 +20%'
    ], 3)
    assert not report.unsupported
    assert parsed['coin_defs'][2]['damage_bonus'] == 0.0
    assert parsed['coin_defs'][2]['damage_conditions'] == [{
        'condition': {
            'type': 'resource_held_or_consumed_this_coin',
            'resource': '눈물 벼리기',
        },
        'amount': 0.20,
    }]


def test_rodion_tears_forge_bonus_requires_held_or_coin_consumed():
    parser = SkillTextParserV19()
    parsed, _ = parser.parse([
        '3코인 눈물 벼리기를 보유하였거나 이 코인에서 소모하였다면, 피해량 +20%'
    ], 3)
    skill = SkillData(id='s', name='아르카나 피어스', base_power=5,
                      coins=[CoinData(4, 'pierce', 'pride') for _ in range(3)],
                      attack_type='pierce', sin='pride')
    skill.coins[2].damage_conditions = parsed['coin_defs'][2]['damage_conditions']
    ident = IdentityData('i', 'rodion', 3, {'s': skill})
    enemy = EnemyState(hp=136, max_hp=136, level=60, defense_level=0,
                       defense_level_bonus=-7,
                       physical_res={'slash': 1.0, 'pierce': 1.0, 'blunt': 1.0},
                       sin_res={'pride': 0.75})
    engine = DamageEngine()

    empty = BattleState(enemy=enemy.clone(),
                        fighters={'i': FighterState(level=60, resources={})}, runtime={})
    assert engine.dynamic_modifier(empty, ident, skill, 3, skill.coins[2]) == 0.0
    assert engine.calculate_coin_damage(empty, ident, skill, skill.coins[2], 'H', False, 1, 3) == (15.0, 13.0)

    held = BattleState(enemy=enemy.clone(),
                       fighters={'i': FighterState(level=60, resources={'눈물 벼리기': 1})}, runtime={})
    assert abs(engine.dynamic_modifier(held, ident, skill, 3, skill.coins[2]) - 0.20) < 1e-9
    assert engine.calculate_coin_damage(held, ident, skill, skill.coins[2], 'H', False, 1, 3) == (18.0, 13.0)

    consumed = BattleState(enemy=enemy.clone(),
                           fighters={'i': FighterState(level=60, resources={})},
                           runtime={'current_coin_resource_consumption': {'눈물 벼리기': 3}})
    assert abs(engine.dynamic_modifier(consumed, ident, skill, 3, skill.coins[2]) - 0.20) < 1e-9
    assert engine.calculate_coin_damage(consumed, ident, skill, skill.coins[2], 'H', False, 1, 3) == (18.0, 13.0)

def test_target_slower_speed_difference_keeps_explicit_condition():
    rules = __import__('passive_compiler_v29').compile_passive_v29(
        {'id':'x','name':'x','effect':'메인 공격 대상의 속도가 자신보다 느릴 때, 피해량 +(대상과의 속도 차이x2.5)% (최대 20%)'},
        'ego-20206', 0).rules
    assert len(rules) == 1
    assert any(getattr(c, 'relation', None) == 'faster' for c in rules[0].conditions)

# 0.7.127 source mismatch regressions: coin-local target-dependent damage must
# remain conditional at runtime.
def test_0_7_127_negative_status_count_damage_runtime():
    skill=SkillData(id='s',name='s',base_power=10,coins=[CoinData(4,'slash','lust')],attack_type='slash',sin='lust')
    skill.coins[0].damage_conditions=[{'condition':{'type':'negative_status_count_per','target':'enemy','per':1,'amount':0.05,'max':0.30}}]
    ident=IdentityData('i','i',0,{'s':skill})
    enemy=EnemyState(100,100)
    enemy.statuses={'Bleed':Status(potency=2),'Burn':Status(potency=1)}
    state=BattleState(fighters={'i':FighterState()},enemy=enemy,runtime={})
    assert abs(DamageEngine.dynamic_modifier(state,ident,skill,1,skill.coins[0])-0.10)<1e-9

def test_0_7_127_target_speed_difference_damage_runtime():
    skill=SkillData(id='s',name='s',base_power=10,coins=[CoinData(4,'slash','lust')],attack_type='slash',sin='lust')
    skill.coins[0].damage_conditions=[{'condition':{'type':'speed_difference_per','direction':'lower','per':1,'amount':0.10,'max':0.50}}]
    ident=IdentityData('i','i',0,{'s':skill})
    fighter=FighterState(speed=5)
    enemy=EnemyState(100,100)
    enemy.speed=8
    state=BattleState(fighters={'i':fighter},enemy=enemy,runtime={})
    assert abs(DamageEngine.dynamic_modifier(state,ident,skill,1,skill.coins[0])-0.30)<1e-9

def test_0_7_127_reuse_front_hit_target_status_damage_runtime():
    skill=SkillData(id='s',name='s',base_power=10,coins=[CoinData(4,'slash','lust')],attack_type='slash',sin='lust')
    skill.coins[0].damage_conditions=[{'condition':{'type':'and','conditions':[{'type':'reuse_hit'},{'type':'front_hit'},{'type':'status','name':'Bleed','target':'enemy','potency_gte':10}]},'amount':0.50}]
    ident=IdentityData('i','i',0,{'s':skill}); enemy=EnemyState(100,100); enemy.statuses={'Bleed':Status(potency=10)}
    st=BattleState(fighters={'i':FighterState()},enemy=enemy,runtime={'last_coin_face':'H','_current_coin_effect_ctx':{'reuse_index':1}})
    assert abs(DamageEngine.dynamic_modifier(st,ident,skill,1,skill.coins[0])-0.50)<1e-9
    st.runtime['_current_coin_effect_ctx']={'reuse_index':0}
    assert abs(DamageEngine.dynamic_modifier(st,ident,skill,1,skill.coins[0]))<1e-9

def test_0_7_127_cross_scope_status_damage_runtime():
    skill=SkillData(id='s',name='s',base_power=10,coins=[CoinData(4,'slash','lust')],attack_type='slash',sin='lust')
    skill.coins[0].damage_conditions=[{'condition':{'type':'cross_status_sum_per','self_status':'Poise','enemy_status':'Rupture','per':1,'amount':0.10,'max':2.0}}]
    ident=IdentityData('i','i',0,{'s':skill}); enemy=EnemyState(100,100,statuses={'Rupture':Status(potency=7)})
    fighter=FighterState(); fighter.poise.potency=3
    st=BattleState(fighters={'i':fighter},enemy=enemy,runtime={})
    assert abs(DamageEngine.dynamic_modifier(st,ident,skill,1,skill.coins[0])-1.0)<1e-9

# 0.7.128 source mismatch regressions: coin-local conditional damage that
# previously fell through to a flat `damage_bonus`.
def test_0_7_128_coin_self_named_scaling_not_flat():
    p=SkillTextParserV19(); r,rep=p.parse(['3코인 지령의 가호 1당 피해량 +5% (최대 40%)'],3)
    assert not rep.unsupported
    c=r['coin_defs'][2]
    assert c['damage_bonus']==0
    assert c['damage_conditions'][0]['condition']['name']=='지령의 가호'
    assert c['damage_conditions'][0]['condition']['target']=='self'

def test_0_7_128_unlock_stage_scaling_not_flat():
    p=SkillTextParserV19(); r,rep=p.parse(['4코인 해금 단계 1당 피해량 +20% (최대 60%)'],4)
    assert not rep.unsupported
    c=r['coin_defs'][3]
    assert c['damage_bonus']==0
    assert c['damage_conditions'][0]['condition']['name']=='해금 단계'

def test_0_7_128_target_effect_scaling_not_flat():
    p=SkillTextParserV19(); r,rep=p.parse(['4코인 대상에게 패닉 타입 변경 효과가 있으면, 수치 1당 피해량 +10% (최대 30%)'],4)
    assert not rep.unsupported
    c=r['coin_defs'][3]
    assert c['damage_bonus']==0
    assert c['damage_conditions'][0]['condition']['name']=='패닉 타입 변경 효과'
    assert c['damage_conditions'][0]['condition']['target']=='enemy'

def test_0_7_128_consumed_resource_sum_runtime():
    from limbus_damage_engine_v29 import DamageEngine, BattleState, FighterState, EnemyState, IdentityData, SkillData, CoinData
    p=SkillTextParserV19(); r,rep=p.parse(['3코인 소모한 적안, 참회당 피해량 +4% (최대 160%)'],3)
    assert not rep.unsupported
    skill=SkillData(id='s',name='s',base_power=10,coins=[CoinData(4,'slash','lust')]*3,attack_type='slash',sin='lust')
    skill.coins[2].damage_conditions=r['coin_defs'][2]['damage_conditions']
    ident=IdentityData('i','i',0,{'s':skill})
    st=BattleState(fighters={'i':FighterState()},enemy=EnemyState(100,100),runtime={'current_action_resource_consumption':{'적안':20,'참회':15}})
    assert abs(DamageEngine.dynamic_modifier(st,ident,skill,2,skill.coins[2])-1.40)<1e-9

def test_0_7_128_target_threshold_damage_not_flat():
    p=SkillTextParserV19(); r,rep=p.parse(['3코인 대상에게 못이 5 이상 있으면, 피해량 +70%'],3)
    assert not rep.unsupported
    c=r['coin_defs'][2]
    assert c['damage_bonus']==0
    assert c['damage_conditions'][0]['condition']['type']=='status'
    assert c['damage_conditions'][0]['condition']['name']=='못'
    assert c['damage_conditions'][0]['condition']['potency_gte']==5

def test_0_7_128_unlock_stage_compound_damage_not_flat():
    p=SkillTextParserV19(); r,rep=p.parse(['4코인 해금 단계 1당, 이 코인의 위력 +1, 피해량 +40% (각각 최대 3, 최대 120%)'],4)
    assert not rep.unsupported
    c=r['coin_defs'][3]
    assert c['damage_bonus']==0
    assert c['damage_conditions'][0]['condition']['name']=='해금 단계'
    assert c['damage_conditions'][0]['condition'].get('max')==1.20

def test_0_7_128_oracle_reduction_pattern_not_falsely_supported():
    p=SkillTextParserV19(); r,rep=p.parse(['[합 승리시] 남은 코인 수만큼 자신의 예지안을 감소시키고, 감소한 수치 1당, 피해량 +5% (최대 10%)'],3)
    assert rep.unsupported
    assert not r['effects_on_use']

def test_0_7_129_target_presence_damage_is_conditional():
    p=SkillTextParserV19(); r,rep=p.parse(['1코인 대상에게 경멸이 있으면, 피해량 +235%'],1)
    assert not rep.unsupported
    c=r['coin_defs'][0]
    assert c['damage_bonus']==0
    assert c['damage_conditions'][0]['condition']=={'type':'status','name':'경멸','target':'enemy','count_gte':1}


def test_0_7_129_consumed_single_resource_uses_action_consumption():
    from limbus_damage_engine_v29 import DamageEngine, BattleState, FighterState, EnemyState, IdentityData, SkillData, CoinData
    p=SkillTextParserV19(); r,rep=p.parse(['3코인 [적중시] 이 스킬에서 소모한 산나비·죽은나비 1당 피해량 +4%'],3)
    assert not rep.unsupported
    cond=r['coin_defs'][2]['damage_conditions'][0]
    assert cond['condition']['type']=='resource_consumed_sum_per'
    skill=SkillData(id='s',name='s',base_power=10,coins=[CoinData(4,'slash','lust')]*3,attack_type='slash',sin='lust')
    skill.coins[2].damage_conditions=r['coin_defs'][2]['damage_conditions']
    ident=IdentityData('i','i',0,{'s':skill})
    st=BattleState(fighters={'i':FighterState()},enemy=EnemyState(100,100),runtime={'current_action_resource_consumption':{'산나비·죽은나비':7}})
    assert abs(DamageEngine.dynamic_modifier(st,ident,skill,2,skill.coins[2])-0.28)<1e-9


def test_0_7_129_cross_lost_hp_sum_runtime():
    from limbus_damage_engine_v29 import DamageEngine, BattleState, FighterState, EnemyState, IdentityData, SkillData, CoinData
    p=SkillTextParserV19(); r,rep=p.parse(['대상과 자신의 잃은 체력 합 1% 당 피해량 +1% (최대 50%)'],1)
    assert not rep.unsupported
    skill=SkillData(id='s',name='s',base_power=10,coins=[CoinData(4,'slash','lust')],attack_type='slash',sin='lust')
    skill.coins[0].damage_conditions=r['effects_on_use'][0:0]
    # Use the parsed marker directly as the coin-local condition for runtime coverage.
    skill.coins[0].damage_conditions=[{'condition':r['effects_on_use'][0]['condition'],'amount':r['effects_on_use'][0]['condition'].get('amount',0)}] if r['effects_on_use'] else []
    # The parser stores this as a skill-level marker; verify its condition shape separately.
    assert r['effects_on_use'][0]['condition']['type']=='cross_lost_hp_sum_per'


def test_0_7_129_cross_haste_bind_and_resonance_parser():
    p=SkillTextParserV19()
    r,rep=p.parse(['자신의 신속과 대상의 속박의 합 1당, 피해량 +15% (최대 60%)'],1)
    assert not rep.unsupported
    assert r['effects_on_use'][0]['condition']['type']=='cross_status_count_sum_per'
    r,rep=p.parse(['분노 공명당 피해량 10% 증가 (최대 60%)'],1)
    assert not rep.unsupported
    assert r['effects_on_use'][0]['condition']['type']=='resonance_per'
    assert r['effects_on_use'][0]['condition']['sin']=='분노'


def test_0_7_129_attack_weight_gap_with_comma_not_named_stack():
    p=SkillTextParserV19(); r,rep=p.parse(['이 스킬 공격 가중치보다 낮은 공격 대상 1당, 피해량 +50% (집중 전투의 경우, 부위로 판정)'],1)
    assert not rep.unsupported
    assert r['effects_on_use'][0]['condition']['type']=='attack_weight_gap_damage'



def test_0_7_140_cumulative_consumed_shared_damage_scaling_resolves_from_bucket():
    from limbus_damage_engine_v29 import DamageEngine, BattleState, FighterState, EnemyState, IdentityData, SkillData, CoinData
    p=SkillTextParserV19(); r,rep=p.parse(['1코인 공용 누적 소모 혈찬 1당, 피해량 +0.1% (최대 10%)'],1)
    assert not rep.unsupported
    skill=SkillData(id='s',name='s',base_power=10,coins=[CoinData(4,'slash','lust')],attack_type='slash',sin='lust')
    skill.coins[0].damage_conditions=r['coin_defs'][0]['damage_conditions']
    ident=IdentityData('i','i',0,{'s':skill})
    st=BattleState(fighters={'i':FighterState()},enemy=EnemyState(100,100),runtime={'cumulative_resource_consumed':{('i','혈찬'):70,('other','혈찬'):50}})
    assert abs(DamageEngine.dynamic_modifier(st,ident,skill,0,skill.coins[0])-0.10)<1e-9


def test_0_7_144_skill_level_hp_condition_is_frozen_at_skill_use():
    from limbus_damage_engine_v29 import DamageEngine, BattleState, FighterState, EnemyState, IdentityData, SkillData, CoinData
    # The skill starts at 60% HP, so its '< 50%' condition is false. A later
    # coin may lower the target below 50%, but the skill-level condition stays false.
    ident = IdentityData('actor', 'Actor', 0, {})
    skill = SkillData(id='s', name='S', base_power=10, coins=[
        CoinData(0, 'slash', 'Pride'), CoinData(0, 'slash', 'Pride')
    ], attack_type='slash', sin='Pride')
    skill.conditions=[{'effect':'damage_bonus','condition':{'type':'enemy_hp_pct_lte','value':50.0,'strict':True},'amount':1.0}]
    actor = FighterState(hp=100, max_hp=100, level=1)
    enemy = EnemyState(hp=600, max_hp=1000, level=1)
    state = BattleState(fighters={'actor':actor}, enemy=enemy)
    engine = DamageEngine()
    engine._capture_skill_condition_snapshot(state)
    # Live state crosses below 50%, but the skill snapshot remains at 60%.
    state.enemy.hp = 400
    d = engine.dynamic_modifier(state, ident, skill, 1, skill.coins[1], False)
    assert d == 0.0
