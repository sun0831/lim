"""Safely merged test file (AST-aware, whole-file rename incl. call sites, decorators preserved via line-removal import stripping).
Originals: test_0_7_88_status_potency_count_source_audit.py, test_tremor_burst_explicit_count_parsing_v2.py, test_tremor_burst_special_boundaries_v1.py, test_tremor_dynamic_application_v1.py, test_tremor_reuse_hit_effects_v1.py
"""
from __future__ import annotations

from skill_text_parser_v19 import SkillTextParserV19
import json
from types import SimpleNamespace


# ---- merged from test_0_7_88_status_potency_count_source_audit.py ----

def test_bare_status_extra_grant_is_potency():
    p=SkillTextParserV19(); out,_=p.parse(['1코인 [적중시] 화상 3 추가 부여'],1)
    assert out['coin_defs'][0]['effects'][0]['potency']==3
    assert 'count' not in out['coin_defs'][0]['effects'][0]

def test_explicit_status_count_increase_is_count():
    p=SkillTextParserV19(); out,_=p.parse(['1코인 [적중시] 화상 횟수 3 증가'],1)
    assert out['coin_defs'][0]['effects'][0]['count']==3
    assert 'potency' not in out['coin_defs'][0]['effects'][0]

def test_status_extra_potency_source_examples():
    p=SkillTextParserV19(); out,_=p.parse(['1코인 [적중시] 출혈 15 추가로 얻음'],1)
    assert out['coin_defs'][0]['effects'][0]['potency']==15

def test_passive_bare_status_extra_grant_is_potency():
    from passive_compiler_v29 import parse_effects
    specs=parse_effects('대상에게 화상 2 추가 부여')
    vals=[s.effect for s in specs if getattr(s.effect,'name',None)=='Burn']
    assert vals and vals[0].potency.resolve(None,None,'')==2
    assert vals[0].count.resolve(None,None,'')==0

def test_passive_explicit_status_count_is_count():
    from passive_compiler_v29 import parse_effects
    specs=parse_effects('대상에게 화상 횟수 2 증가')
    vals=[s.effect for s in specs if getattr(s.effect,'name',None)=='Burn']
    assert vals and vals[0].count.resolve(None,None,'')==2
    assert vals[0].potency.resolve(None,None,'')==0


# ---- merged from test_tremor_burst_explicit_count_parsing_v2.py ----

def parse(t):
    return SkillTextParserV19().parse([t], 1)[0]['coin_defs'][0]['effects'][0]

def test_plain_burst_has_no_count_cost():
    e=parse('1코인 [적중시] 진동 폭발')
    assert e['type']=='tremor_burst'
    assert 'count_cost' not in e

def test_explicit_count_cost_one():
    e=parse('1코인 [적중시] 진동 폭발. 대상의 진동 횟수 1 감소')
    assert e['count_cost']==1

def test_explicit_count_cost_two():
    e=parse('1코인 [적중시] 진동 폭발. 대상의 진동 횟수 2 감소')
    assert e['count_cost']==2

def test_burst_count_and_count_cost_are_separate():
    e=parse('1코인 [적중시] 진동 폭발 2회. 대상의 진동 횟수 1 감소')
    assert e['burst_count']==2
    assert e['count_cost']==1

def test_burst_followed_by_newline_count_cost():
    e=parse('1코인 [적중시] 진동 폭발\n진동 폭발 시 진동 횟수 3 감소')
    assert e['count_cost']==3


# ---- merged from test_tremor_burst_special_boundaries_v1.py ----

CAT='identity_catalog_v2.json'

def _identity(i):
    d=json.load(open(CAT))
    return next(x for x in d['identities'] if x['id']==i)

def _skill(i,sid):
    ident=_identity(i)
    return next(s for s in ident['skills'] if s['id']==sid)

def test_10414_loneliness_replacement_is_explicit_not_generic_burst():
    text=_skill('identity-10414','1041405')['effects'][2]
    out,rep=SkillTextParserV19().parse([text],3)
    assert not rep.unsupported
    e=out['effects_on_use'][0]
    assert e['type']=='tremor_burst_replacement'
    assert e['replacement_status']=='고독'
    assert e['count_cost']==1
    assert e['condition']['type']=='loneliness_present_current_or_next_turn'

def test_10716_book_or_duel_condition_and_explicit_count():
    text=_skill('identity-10716','107162')['effects'][4]
    out,rep=SkillTextParserV19().parse([text],3)
    assert not rep.unsupported
    e=out['effects_on_use'][0]
    assert e['type']=='tremor_burst'
    assert e['burst_count']==1
    assert e['count_cost']==1
    assert e['condition']['type']=='or'
    assert {c.get('type') for c in e['condition']['conditions']} == {'resource_gte','status'}

def test_10813_last_reuse_resource_gate_and_burst_count():
    text=_skill('identity-10813','1081305')['effects'][6]
    out,rep=SkillTextParserV19().parse([text],1)
    assert not rep.unsupported
    rule=out['last_coin_reuse_rules'][0]
    assert rule['condition']=={'type':'resource_gte','resource':'광【光】','value':5}
    eff=rule['reuse_hit_effects'][0]
    assert eff['type']=='tremor_burst'
    assert eff['burst_count']==2
    assert eff['count_cost']==1

def test_11216_added_coin_burst_keeps_added_coin_boundary():
    text=_skill('identity-11216','112162')['effects'][3]
    out,rep=SkillTextParserV19().parse([text],3)
    assert not rep.unsupported
    e=out['effects_on_use'][0]
    assert e['type']=='pending_added_coin_burst'
    assert e['condition']['type']=='added_coin_hit'
    assert e['count_cost']==1


# ---- merged from test_tremor_dynamic_application_v1.py ----


def test_source_text_10810_dynamic_tremor_div2_parser():
    p=SkillTextParserV19()
    parsed, rep=p.parse(['3코인 [적중시] (자신의 진동 횟수/2)만큼 진동 부여 (최대 4)'], 3)
    e=parsed['coin_defs'][2]['effects'][0]
    assert e['type']=='tremor_apply_from_self_count_div'
    assert e['divisor']==2 and e['cap']==4


def test_source_text_10810_dynamic_tremor_all_consume_parser():
    p=SkillTextParserV19()
    parsed, rep=p.parse(['3코인 [적중시] 자신의 진동 횟수를 전부 소모하여, 소모한 값만큼 진동 부여. (최대 20)'], 3)
    e=parsed['coin_defs'][2]['effects'][0]
    assert e['type']=='tremor_apply_from_self_count_all'
    assert e['cap']==20

def test_dynamic_div_runtime_uses_floor_and_cap():
    from limbus_damage_engine_v29 import DamageEngine
    from types import SimpleNamespace
    from limbus_damage_engine_v29 import BattleState, FighterState, EnemyState, Status
    ident=SimpleNamespace(id='src')
    state=BattleState(fighters={'src':FighterState(statuses={'Tremor':Status(potency=7,count=9)})}, enemy=EnemyState(hp=1000,max_hp=1000,statuses={'Tremor':Status(potency=0,count=1)}), runtime={})
    DamageEngine().apply_effect(state,'src','enemy',{'type':'tremor_apply_from_self_count_div','cap':4,'divisor':2})
    assert state.enemy.statuses['Tremor'].count==5


def test_dynamic_all_runtime_consumes_source_count_and_caps():
    from limbus_damage_engine_v29 import DamageEngine
    from types import SimpleNamespace
    from limbus_damage_engine_v29 import BattleState, FighterState, EnemyState, Status
    state=BattleState(fighters={'src':FighterState(statuses={'Tremor':Status(potency=7,count=25)})}, enemy=EnemyState(hp=1000,max_hp=1000,statuses={'Tremor':Status(potency=1,count=0)}), runtime={})
    DamageEngine().apply_effect(state,'src','enemy',{'type':'tremor_apply_from_self_count_all','cap':20})
    assert state.fighters['src'].statuses['Tremor'].count==5
    assert state.enemy.statuses['Tremor'].count==20


# ---- merged from test_tremor_reuse_hit_effects_v1.py ----

def _skill__test_tremor_reuse_hit_effects_v1(sid):
    D=json.load(open('identity_catalog_v2.json',encoding='utf8'))['identities']
    for i in D:
        for s in i.get('skills',[]):
            if s['id']==sid:return s
    raise AssertionError(sid)

def test_102162_reuse_hit_burst_is_separate_and_limited():
    s=_skill__test_tremor_reuse_hit_effects_v1('102162')
    out,rep=SkillTextParserV19().parse(s['effects'],s['coinCount'])
    rules=out['last_coin_reuse_rules']
    assert rules and rules[0]['max_reuses']==2
    effects=rules[0]['reuse_hit_effects']
    assert any(e['type']=='tremor_burst' and e['count_cost']==1 and e['reuse_hit_limit']==1 for e in effects)
    assert any(e['type']=='status' and e['name']=='Burn' and e.get('reuse_hit_limit') is None for e in effects)
    assert not [x for x in rep.unsupported if '재사용 적중시' in x]

# 0.7.125 source-mismatch regressions: parser ordering and explicit final-coin targets.
def test_0_7_125_critical_damage_checked_before_generic_damage():
    p = SkillTextParserV19()
    out, _ = p.parse(["1코인 [적중시] 크리티컬 피해량 +30%"], 1)
    assert out['coin_defs'][0]['crit_damage_bonus'] == 0.30
    assert out['coin_defs'][0]['damage_bonus'] == 0.0

def test_0_7_125_stagger_critical_damage_not_flat_damage():
    p = SkillTextParserV19()
    out, _ = p.parse(["대상이 흐트러짐 상태면, 크리티컬 피해량 +30%"], 1)
    assert out['effects_on_use'][0]['effect'] == 'crit_damage_bonus'
    assert out['effects_on_use'][0]['crit_damage_bonus'] == 0.30

def test_0_7_125_last_coin_front_hit_targets_final_coin():
    p = SkillTextParserV19()
    out, _ = p.parse(["1코인 [앞면 적중시] 마지막 코인의 피해량 +10%", "2코인 [앞면 적중시] 마지막 코인의 피해량 +5%"], 2)
    assert len(out['last_coin_damage_rules']) == 2
    assert out['last_coin_damage_rules'][0]['condition']['type'] == 'front_hit'
    assert out['last_coin_damage_rules'][0]['amount'] == 0.10
    assert out['last_coin_damage_rules'][1]['amount'] == 0.05
    assert out['coin_defs'][0]['damage_bonus'] == 0.0
    assert out['coin_defs'][1]['damage_bonus'] == 0.0

def test_0_7_125_last_coin_hit_unconditional():
    p = SkillTextParserV19()
    out, _ = p.parse(["1코인 [적중시] 마지막 코인의 피해량 +10%"], 2)
    assert out['last_coin_damage_rules'][0]['condition'] is None

def test_0_7_125_last_coin_reveal_status_scaling():
    p = SkillTextParserV19()
    text = "[전투 시작시] 자신에게 발각[發角]이 있으면, 이 스킬의 마지막 코인이 파괴 불가 코인으로 변경되고 수치 1당 마지막 코인의 피해량 +5% (최대 15%)"
    out, _ = p.parse([text], 3)
    rule = out['last_coin_damage_rules'][0]
    assert rule['condition']['name'] == '발각'
    assert rule['status_scaling']['amount'] == 0.05
    assert rule['status_scaling']['max'] == 0.15

def test_0_7_125_cross_poise_target_rupture_critical_damage_skill_path():
    p = SkillTextParserV19()
    text = "4코인 [코인 시작 시] (자신의 호흡 위력 + 대상의 파열 위력) 1당 크리티컬 피해량 +2% (최대 120%)"
    out, _ = p.parse([text], 4)
    crit = [x for x in out['effects_on_use'] if x.get('effect') == 'crit_damage_bonus']
    assert crit
    c = crit[0]['condition']
    assert c['type'] == 'cross_status_crit_damage_per'
    assert c['self_status'] == 'Poise'
    assert c['enemy_status'] == 'Rupture'
    assert c['amount'] == 0.02
    assert c['max'] == 1.20

# ---- 0.7.126 source mismatch: conditional final-coin named-resource scaling ----

def test_0_7_126_final_coin_named_resource_keeps_target_threshold_and_scaling():
    from limbus_damage_engine_v29 import DamageEngine, BattleState, FighterState, EnemyState, IdentityData, SkillData, CoinData, Status
    p = SkillTextParserV19()
    text = '[사용시] 대상의 파열이 15 이상이면, 딜리버리 캐리어 - 싱클레어 1 당 마지막 코인의 피해량 +4% (최대 120%)'
    parsed, rep = p.parse([text], 3)
    assert not rep.unsupported
    rule = parsed['last_coin_damage_rules'][0]
    assert rule['condition'] == {'type':'status','name':'Rupture','target':'enemy','potency_gte':15}
    assert rule['status_scaling']['name'] == '딜리버리 캐리어 - 싱클레어'
    assert rule['status_scaling']['max'] == 1.20

    skill = SkillData(id='s', name='s', base_power=10,
                      coins=[CoinData(0,'slash','lust'), CoinData(1,'slash','lust'), CoinData(2,'slash','lust')],
                      attack_type='slash', sin='lust')
    skill.last_coin_damage_rules = parsed['last_coin_damage_rules']
    ident = IdentityData('i','i',0,{'s':skill})
    fighter = FighterState(resources={'딜리버리 캐리어 - 싱클레어': 10})
    enemy = EnemyState(100,100)
    enemy.statuses={'Rupture': Status(potency=15)}
    state = BattleState(fighters={'i':fighter}, enemy=enemy, runtime={})
    # Final coin: 10 resource -> +40%; non-final coins must receive nothing.
    final = DamageEngine.dynamic_modifier(state, ident, skill, 3, skill.coins[2])
    first = DamageEngine.dynamic_modifier(state, ident, skill, 1, skill.coins[0])
    assert abs(final - 0.40) < 1e-9
    assert abs(first) < 1e-9

    # Below the target threshold, the final-coin bonus must disappear entirely.
    enemy.statuses={'Rupture': Status(potency=14)}
    final_below = DamageEngine.dynamic_modifier(state, ident, skill, 3, skill.coins[2])
    assert abs(final_below) < 1e-9

# 0.7.127 source mismatch: named special-resource final-coin reuse must keep its threshold.
def test_0_7_127_named_special_resource_final_coin_reuse_keeps_threshold():
    p = SkillTextParserV19()
    parsed, rep = p.parse(["[사용시] 불꽃나비의 관이 20 이상이면, 마지막 코인 재사용 (스킬당 1회)"], 3)
    assert not rep.unsupported, rep.unsupported
    rule = next(e for e in parsed['effects_on_use'] if e.get('type') == 'last_coin_reuse')
    assert rule['condition'] == {'type': 'resource_gte', 'resource': '불꽃나비의 관', 'value': 20}
    assert rule['max_reuses'] == 1

# 0.7.127 source mismatch regressions: specific target-dependent damage clauses
# must not fall through to generic named-stack parsing.
def test_0_7_127_target_negative_effect_damage_scaling_is_explicit():
    p = SkillTextParserV19()
    parsed, rep = p.parse(["4코인 대상의 부정적인 효과 1개당, 피해량 +5% (최대 30%)"], 4)
    assert not rep.unsupported, rep.unsupported
    c = parsed['coin_defs'][3]['damage_conditions'][0]['condition']
    assert c == {'type': 'negative_status_count_per', 'target': 'enemy', 'per': 1, 'amount': 0.05, 'max': 0.30}

def test_0_7_127_target_named_status_strips_coin_prefix():
    p = SkillTextParserV19()
    parsed, rep = p.parse(["3코인 대상의 시선 1당 피해량 +10% (최대 70%)"], 3)
    assert not rep.unsupported, rep.unsupported
    c = parsed['coin_defs'][2]['damage_conditions'][0]['condition']
    assert c == {'type': 'named_stack_per', 'name': '시선', 'target': 'enemy', 'per': 1, 'amount': 0.10, 'max': 0.70}

def test_0_7_127_target_speed_difference_damage_is_not_named_resource():
    p = SkillTextParserV19()
    parsed, rep = p.parse(["대상의 속도가 자신보다 느리면, 대상과의 속도 차이 1 당 피해량 +10% (최대 50%)"], 1)
    assert not rep.unsupported, rep.unsupported
    c = next(e for e in parsed['effects_on_use'] if e.get('type') == '_skill_damage_condition_marker')['condition']
    assert c == {'type': 'speed_difference_per', 'direction': 'lower', 'per': 1, 'amount': 0.10, 'max': 0.50}

# 0.7.127 additional source mismatches: reused-coin condition and cross-scope damage.
def test_0_7_127_reuse_front_hit_target_status_damage_stays_conditional():
    p = SkillTextParserV19()
    parsed, rep = p.parse(["1코인 [재사용 앞면 적중 시] 대상의 출혈이 10 이상이면, 피해량 +50%"], 1)
    assert not rep.unsupported, rep.unsupported
    rule = parsed['coin_defs'][0]['damage_conditions'][0]
    assert rule['amount'] == 0.50
    assert rule['condition']['type'] == 'and'
    assert [x['type'] for x in rule['condition']['conditions']] == ['reuse_hit', 'front_hit', 'status']

def test_0_7_127_cross_scope_status_damage_stays_dynamic():
    p = SkillTextParserV19()
    parsed, rep = p.parse(["1코인 대상의 (파열 위력 + 자신의 호흡 위력)당 피해량 +10% (최대 200%)"], 1)
    assert not rep.unsupported, rep.unsupported
    c = parsed['coin_defs'][0]['damage_conditions'][0]['condition']
    assert c == {'type':'cross_status_sum_per','self_status':'Poise','enemy_status':'Rupture','per':1,'amount':0.10,'max':2.0}


def test_0_7_130_coin_damage_conditions_are_retained_in_catalog():
    from identity_catalog_v29 import IdentityCatalogV29
    import json
    cat = IdentityCatalogV29(json.load(open("identity_catalog_v2.json", encoding="utf-8"))["identities"])
    ident = cat.build_identity("identity-10211")
    skill = ident.skills["S4"]
    assert skill.coins[2].damage_conditions
    assert skill.coins[2].damage_conditions[0]["condition"]["type"] == "self_lost_hp_per"


def test_0_7_130_bracketed_named_resource_is_not_truncated():
    from skill_text_parser_v19 import SkillTextParserV19
    import json
    records = json.load(open("identity_catalog_v2.json", encoding="utf-8"))["identities"]
    ident = next(x for x in records if x["id"] == "identity-10613")
    skill = next(x for x in ident["skills"] if x["id"] == "1061305")
    parsed, _ = SkillTextParserV19().parse(skill["effects"], skill["coinCount"])
    names = [x["condition"].get("name") for x in parsed["effects_on_use"] if x.get("type") == "_skill_damage_condition_marker"]
    assert "흑수환염[黑獣丸染]" in names
    assert "]" not in names


def test_0_7_131_coin_conditional_damage_does_not_flatten():
    p = SkillTextParserV19()
    out, report = p.parse(["2코인 [적중시] 대상의 화상이 6 이상이면, 피해량 +50%"], 2)
    q = out['coin_defs'][1]
    assert q['damage_bonus'] == 0.0
    assert q['damage_conditions'][0]['condition']['type'] == 'status_threshold'
    assert q['damage_conditions'][0]['condition']['name'] == 'Burn'
    assert q['damage_conditions'][0]['amount'] == 0.50
    assert not report.unsupported


def test_0_7_131_coin_consumed_ammo_damage_is_dynamic():
    p = SkillTextParserV19()
    out, report = p.parse(["1코인 피해량 + (소모한 탄환 x 15)%"], 1)
    q = out['coin_defs'][0]
    assert q['damage_bonus'] == 0.0
    assert q['damage_conditions'][0]['condition']['type'] == 'resource_consumed_sum_per'
    assert q['damage_conditions'][0]['condition']['resources'] == ['탄환']
    assert q['damage_conditions'][0]['condition']['amount'] == 0.15
    assert not report.unsupported


def test_0_7_131_coin_conditional_critical_scaling_is_dynamic():
    p = SkillTextParserV19()
    out, report = p.parse(["2코인 자신의 호흡당 크리티컬 피해량 +5% (최대 50%)"], 2)
    q = out['coin_defs'][1]
    assert q['crit_damage_bonus'] == 0.0
    assert q['damage_conditions'][0]['effect'] == 'crit_damage_bonus'
    assert q['damage_conditions'][0]['condition']['name'] == '호흡'
    assert q['damage_conditions'][0]['condition']['amount'] == 0.05
    assert not report.unsupported


def test_0_7_132_generic_status_threshold_damage_modifier():
    parsed, report = SkillTextParserV19().parse(['대상의 화상이 6 이상이면, 피해량 +50%'], 3)
    marker = next(x for x in parsed['effects_on_use'] if x.get('type') == '_skill_condition_marker')
    assert marker['condition']['type'] == 'status'
    assert marker['condition']['potency_gte'] == 6
    assert marker['damage_bonus'] == 0.5


def test_0_7_132_generic_presence_damage_modifier():
    parsed, report = SkillTextParserV19().parse(['대상에게 못이 있으면, 피해량 +70%'], 3)
    marker = next(x for x in parsed['effects_on_use'] if x.get('type') == '_skill_condition_marker')
    assert marker['condition'] == {'type':'status','name':'Nails','target':'enemy','count_gte':1}
    assert marker['damage_bonus'] == 0.7


def test_0_7_135_clash_win_damage_stays_conditional():
    parsed, report = SkillTextParserV19().parse(['[합 승리시] 피해량 +30%'], 1)
    marker = next(x for x in parsed['effects_on_use'] if x.get('type') == '_skill_condition_marker')
    assert marker['condition'] == {'type':'clash_result','value':'win'}
    assert marker['damage_bonus'] == 0.30
    assert not report.unsupported


def test_0_7_135_speed_threshold_damage_stays_conditional():
    parsed, report = SkillTextParserV19().parse(['자신의 속도가 7 이상이면, 피해량 +25%'], 1)
    marker = next(x for x in parsed['effects_on_use'] if x.get('type') == '_skill_condition_marker')
    assert marker['condition'] == {'type':'speed_gte','value':7}
    assert marker['damage_bonus'] == 0.25
    assert not report.unsupported


def test_0_7_135_special_resource_threshold_damage_stays_conditional():
    parsed, report = SkillTextParserV19().parse(['K사 앰플이 5 이상이면, 피해량 +20%'], 1)
    marker = next(x for x in parsed['effects_on_use'] if x.get('type') == '_skill_condition_marker')
    assert marker['condition'] == {'type':'resource_gte','resource':'K사 앰플','value':5}
    assert marker['damage_bonus'] == 0.20
    assert not report.unsupported


def test_0_7_137_resource_multiplier_damage_preserves_speed_gate():
    from skill_text_parser_v19 import SkillTextParserV19
    parser = SkillTextParserV19()
    parsed, report = parser.parse([
        '자신의 속도가 대상보다 높으면,',
        '- 최종 위력 +1',
        '- (자신의 적진 주파 x 20)%만큼 피해량이 증가 (최대 80%)',
    ], 3)
    assert not any('적진 주파' in x for x in report.unsupported)
    marker = next(x for x in parsed['effects_on_use'] if x.get('type') == '_skill_damage_condition_marker')
    cond = marker['condition']
    assert cond['type'] == 'resource_per'
    assert cond['resource'] == '적진 주파'
    assert cond['amount'] == 0.20
    assert cond['max'] == 0.80
    assert cond['gate']['type'] == 'speed_difference_gte'


def test_0_7_137_shield_multiplier_damage_reads_shield_field():
    from skill_text_parser_v19 import SkillTextParserV19
    parser = SkillTextParserV19()
    parsed, report = parser.parse([
        '자신의 (보호막 수치 x 2)% 만큼 피해량이 증가 (최대 50%)',
    ], 3)
    assert not report.unsupported
    marker = next(x for x in parsed['effects_on_use'] if x.get('type') == '_skill_damage_condition_marker')
    cond = marker['condition']
    assert cond['resource'] == '보호막 수치'
    assert cond['amount'] == 0.02
    assert cond['max'] == 0.50


def test_0_7_138_bracketed_named_critical_damage_resource_is_not_truncated():
    p = SkillTextParserV19()
    out, rep = p.parse(['1코인 자신의 시[始]당 크리티컬 피해량 +5% (최대 30%)'], 1)
    conds = out['coin_defs'][0]['damage_conditions']
    assert conds == [{'effect':'crit_damage_bonus','condition':{'type':'named_stack_per','name':'시[始]','target':'self','per':1,'amount':0.05,'max':0.30}}]
    assert rep.supported == ['1코인 자신의 시[始]당 크리티컬 피해량 +5% (최대 30%)']
    assert rep.unsupported == []


def test_0_7_138_mixed_constant_cross_resource_damage_remains_unsupported():
    p = SkillTextParserV19()
    out, rep = p.parse(['1코인 피해량 +(50 + 자신의 호흡 + 메인 타겟의 파열)% (최대 75%)'], 1)
    assert out['coin_defs'][0]['damage_conditions'] == []
    assert out['coin_defs'][0]['damage_bonus'] == 0.0
    assert rep.unsupported == ['1코인 피해량 +(50 + 자신의 호흡 + 메인 타겟의 파열)% (최대 75%)']


def test_0_7_139_coin_damage_status_or_with_or_conjunction():
    p = SkillTextParserV19()
    out, rep = p.parse(['2코인 대상에게 주살【신속】 또는 주살【파】가 있으면, 피해량 +50%'], 2)
    conds = out['coin_defs'][1]['damage_conditions']
    assert len(conds) == 1
    cond = conds[0]['condition']
    assert cond['type'] == 'or'
    assert [x['name'] for x in cond['conditions']] == ['주살【신속】', '주살【파】']
    assert conds[0]['amount'] == 0.50
    assert rep.unsupported == []


def test_0_7_140_cumulative_consumed_blood_coin_damage_is_dynamic():
    from skill_text_parser_v19 import SkillTextParserV19
    parsed, report = SkillTextParserV19().parse(['1코인 공용 누적 소모 혈찬 1당, 피해량 +0.1% (최대 10%)'], 1)
    c = parsed['coin_defs'][0]['damage_conditions'][0]['condition']
    assert c['type'] == 'cumulative_resource_consumed_per'
    assert c['resource'] == '혈찬'
    assert c['scope'] == 'shared'
    assert c['per'] == 1
    assert c['amount'] == 0.001
    assert c['max'] == 0.10
    assert report.unsupported == []


def test_0_7_140_cumulative_consumed_threshold_damage_is_preserved():
    from skill_text_parser_v19 import SkillTextParserV19
    parsed, report = SkillTextParserV19().parse(['2코인 공용 누적 소모 혈찬 100이상이면, 1당 피해량 +0.1% (최대 20%)'], 2)
    c = parsed['coin_defs'][1]['damage_conditions'][0]['condition']
    assert c['type'] == 'cumulative_resource_consumed_per'
    assert c['resource'] == '혈찬'
    assert c['scope'] == 'shared'
    assert c['min_value'] == 100
    assert c['amount'] == 0.001
    assert c['max'] == 0.20
    assert report.unsupported == []


def test_0_7_140_cumulative_consumed_self_damage_is_not_current_resource():
    from skill_text_parser_v19 import SkillTextParserV19
    parsed, report = SkillTextParserV19().parse(['적중시 자신의 누적 소모 혈찬 10당, 피해량 +1% (최대 20%)'], 1)
    c = parsed['effects_on_use'][0]['condition']
    assert c['type'] == 'cumulative_resource_consumed_per'
    assert c['resource'] == '혈찬'
    assert c['scope'] == 'self'
    assert c['per'] == 10
    assert c['amount'] == 0.01
    assert c['max'] == 0.20
    assert report.unsupported == []


def test_0_7_141_self_lost_hp_and_speed_crit_damage_are_dynamic():
    p = SkillTextParserV19()
    parsed, report = p.parse([
        "자신의 잃은 체력 1당, 피해량 +0.5% (최대 20%)",
        "자신의 신속 1당, 크리티컬 피해량 +3% (최대 15%)",
        "[사용시] 자신의 호흡 1당, 크리티컬 피해량 +1.5% (최대 30%)",
    ], 1)
    assert "자신의 잃은 체력 1당, 피해량 +0.5% (최대 20%)" in report.supported
    assert "자신의 신속 1당, 크리티컬 피해량 +3% (최대 15%)" in report.supported
    assert "[사용시] 자신의 호흡 1당, 크리티컬 피해량 +1.5% (최대 30%)" in report.supported
    flat = [e for e in parsed["effects_on_use"] if e.get("type") == "_skill_damage_condition_marker" and e["condition"].get("type") == "self_lost_hp_flat_per"]
    assert flat and flat[0]["condition"]["per"] == 1 and flat[0]["condition"]["amount"] == 0.005
    crits = [e for e in parsed["effects_on_use"] if e.get("type") == "_skill_condition_marker" and e.get("effect") == "crit_damage_bonus"]
    assert any(e["condition"].get("name") == "신속" and e["condition"].get("field") == "count" for e in crits)
    assert any(e["condition"].get("name") == "호흡" and e["condition"].get("field") == "potency" for e in crits)


def test_0_7_141_cross_status_crit_scaling_uses_sum_not_single_bonus():
    p = SkillTextParserV19()
    parsed, report = p.parse(["자신의 호흡 + 대상의 화상 1당 크리티컬 피해량 +5% (최대 30%)"], 1)
    assert report.unsupported == []
    conds = [e for e in parsed["effects_on_use"] if e.get("type") == "_skill_condition_marker"]
    assert conds and conds[0]["condition"]["type"] == "cross_status_crit_damage_per"
    assert conds[0]["condition"]["amount"] == 0.05

# ---- 0.7.143 parser coverage: existing runtime predicates, omitted surface forms ----
def test_0_7_143_bare_self_speed_threshold_damage_is_dynamic():
    out, rep = SkillTextParserV19().parse(['속도가 7 이상이면, 피해량 +25%'], 1)
    assert not rep.unsupported
    marker = out['effects_on_use'][0]
    assert marker['condition'] == {'type':'speed_gte','value':7}
    assert marker['damage_bonus'] == 0.25


def test_0_7_143_speed_ahead_of_target_damage_is_dynamic():
    out, rep = SkillTextParserV19().parse(['자신의 속도가 대상보다 빠르면, 피해량 +20%'], 1)
    assert not rep.unsupported
    marker = out['effects_on_use'][0]
    assert marker['condition'] == {'type':'speed_difference_gte','value':1}
    assert marker['damage_bonus'] == 0.20


def test_0_7_143_target_hp_threshold_without_current_keyword_is_dynamic():
    out, rep = SkillTextParserV19().parse(['대상의 체력이 30% 미만이면, 피해량 +30%'], 1)
    assert not rep.unsupported
    marker = out['effects_on_use'][0]
    assert marker['type'] == '_skill_damage_condition_marker'
    assert marker['condition'] == {'type':'enemy_hp_pct_lte','value':30.0,'strict':True}
    assert marker['damage_bonus'] == 0.30



def test_0_7_143_coin_target_hp_threshold_damage_increase_is_dynamic():
    out, rep = SkillTextParserV19().parse(['3코인 [적중시] 대상의 체력이 30% 미만이면, 피해량 30% 증가'], 3)
    assert not rep.unsupported
    cond = out['coin_defs'][2]['damage_conditions'][0]
    assert cond['condition'] == {'type':'enemy_hp_pct_lte','value':30.0,'strict':True}
    assert cond['amount'] == 0.30

def test_0_7_145_skill_level_self_burn_damage_scaling_is_dynamic_status_condition():
    p = SkillTextParserV19()
    out, _ = p.parse(['자신의 화상 10 당 피해량 +10% (최대 20%)'], 1)
    marker = next(e for e in out['effects_on_use'] if e.get('type') == '_skill_damage_condition_marker')
    assert marker['condition']['type'] == 'status_count_per'
    assert marker['condition']['name'] == 'Burn'
    assert marker['condition']['target'] == 'self'
    assert marker['condition']['per'] == 10
    assert marker['condition']['amount'] == 0.10
    assert marker['condition']['max'] == 0.20


def test_0_7_145_skill_level_enemy_burn_damage_scaling_stays_enemy_scoped():
    p = SkillTextParserV19()
    out, _ = p.parse(['대상의 화상 10 당 피해량 +10% (최대 20%)'], 1)
    marker = next(e for e in out['effects_on_use'] if e.get('type') == '_skill_damage_condition_marker')
    assert marker['condition']['type'] == 'status_sum_per'
    assert marker['condition']['names'] == ['Burn']
    assert marker['condition']['target'] == 'enemy'



def test_0_7_146_skill_level_self_poise_damage_scaling():
    p = SkillTextParserV19()
    out, rep = p.parse(['[사용시] 자신의 호흡 4당 피해량 +11% (최대 44%)'], 2)
    marker = next(e for e in out['effects_on_use'] if e.get('type') == '_skill_damage_condition_marker')
    assert marker['condition'] == {'type':'named_stack_per','name':'호흡','target':'self','per':4,'amount':0.11,'max':0.44}
    assert '[사용시] 자신의 호흡 4당 피해량 +11% (최대 44%)' in rep.supported


def test_skill_level_presence_fanaticism_damage_bonus():
    out, rep = SkillTextParserV19().parse(['자신에게 광신이 있으면, 피해량 +15%'], 2)
    assert '자신에게 광신이 있으면, 피해량 +15%' in rep.supported
    assert not rep.unsupported
    markers = [x for x in out['effects_on_use'] if x.get('type') == '_skill_condition_marker']
    assert markers
    c = markers[-1]['condition']
    assert c == {'type':'status','name':'광신','target':'self','count_gte':1}
    assert markers[-1]['damage_bonus'] == 0.15


def test_0_7_147_affiliation_count_damage_is_not_false_positive():
    out, rep = SkillTextParserV19().parse([
        "자신에게 광신이 있으면 피해량 +15%",
        "파티의 생존한 N사 광신도 수당 피해량 +5%",
    ], 2)
    assert "자신에게 광신이 있으면 피해량 +15%" in rep.supported
    assert "파티의 생존한 N사 광신도 수당 피해량 +5%" in rep.unsupported
    assert not any(
        c.get("condition", {}).get("name") == "파티의 생존한 N사 광신도 수"
        for c in out.get("effects_on_use", [])
    )


def test_0_7_149_leading_catalog_bullet_is_formatting_for_skill_damage_conditions():
    out, rep = SkillTextParserV19().parse([
        '- [사용시] 정신력 10 감소',
        '- 자신에게 광신 이 있을 때 피해량 +10%',
        '- 자신에게 광신 이 있을 때 피해량 +15%',
    ], 4)
    assert rep.unsupported == []
    assert len([x for x in out['effects_on_use'] if x.get('type') == 'sp']) == 1
    markers = [x for x in out['effects_on_use'] if x.get('type') == '_skill_condition_marker']
    assert [m['damage_bonus'] for m in markers] == [0.10, 0.15]
    assert all(m['condition'] == {'type':'status','name':'광신','target':'self','count_gte':1} for m in markers)

def test_0_7_149_skill_level_named_status_presence_damage_conditions():
    p = SkillTextParserV19()
    for text, name, target, bonus in [
        ('[사용시] 대상에게 찢긴 상처가 있으면, 피해량 +20%', '찢긴 상처', 'enemy', 0.20),
        ('자신에게 우제트의 눈 [선봉]이 있으면, 피해량 +50%', '우제트의 눈 [선봉]', 'self', 0.50),
        ('대상에게 보호막이 있으면, 피해량 +30%', '보호막', 'enemy', 0.30),
    ]:
        parsed, report = p.parse([text], 1)
        assert text in report.supported
        assert not report.unsupported
        cond = parsed['effects_on_use'][0]['condition']
        assert cond == {'type':'status', 'name':name, 'target':target, 'count_gte':1}
        assert parsed['effects_on_use'][0]['damage_bonus'] == bonus

def test_0_7_151_coin_target_damaged_this_turn_is_coin_local():
    from skill_text_parser_v19 import SkillTextParserV19
    p=SkillTextParserV19()
    r, rep = p.parse(['1코인 대상이 이번 턴에 피해를 받은 상태면 피해량 +30%', '2코인 대상이 이번 턴에 피해를 받은 상태면 피해량 +30%'], 2)
    assert rep.unsupported == []
    assert r['coin_defs'][0]['damage_conditions'][0]['condition']['type'] == 'target_damaged_this_turn'
    assert r['coin_defs'][1]['damage_conditions'][0]['condition']['type'] == 'target_damaged_this_turn'


def test_0_7_151_coin_self_status_presence_critical_damage_bonus():
    p = SkillTextParserV19()
    text = '1코인 자신에게 사완이 있으면, 크리티컬 피해량 +100%'
    out, rep = p.parse([text], 1)
    assert rep.unsupported == []
    conds = out['coin_defs'][0]['damage_conditions']
    assert conds == [{
        'effect':'crit_damage_bonus',
        'condition':{'type':'status','name':'사완','target':'self','count_gte':1},
        'amount':1.0,
    }]


def test_0_7_152_coin_plain_critical_damage_bonus_is_local():
    p = SkillTextParserV19()
    out, rep = p.parse(['3코인 크리티컬 피해량 +70%'], 3)
    assert rep.unsupported == []
    assert out['coin_defs'][2]['crit_damage_bonus'] == 0.70
    assert out['coin_defs'][0]['crit_damage_bonus'] == 0.0
    assert out['coin_defs'][1]['crit_damage_bonus'] == 0.0


def test_0_7_154_target_aim_critical_damage_scaling():
    parser = SkillTextParserV19()
    parsed, report = parser.parse(["목표 조준 1당 크리티컬 피해량 +48% (최대 144%)"], 3)
    assert report.unsupported == []
    assert report.supported == ["목표 조준 1당 크리티컬 피해량 +48% (최대 144%)"]
    cond = parsed["effects_on_use"][0]["condition"]
    assert cond == {
        "type": "named_stack_per",
        "name": "목표 조준",
        "target": "self",
        "field": "count",
        "per": 1,
        "amount": 0.48,
        "max": 1.44,
    }


def test_0_7_155_self_target_same_status_damage_sum():
    parser = SkillTextParserV19()
    parsed, report = parser.parse(['피해량 +(자신과 타겟의 화상 위력 합)% (최대 20%, 대상별로 적용)'], 3)
    assert report.unsupported == []
    c = parsed['effects_on_use'][0]['condition']
    assert c['type'] == 'cross_status_sum_per'
    assert c['self_status'] == 'Burn' and c['enemy_status'] == 'Burn'
    assert c['per'] == 1 and c['amount'] == 1.0 and c['max'] == 0.2
