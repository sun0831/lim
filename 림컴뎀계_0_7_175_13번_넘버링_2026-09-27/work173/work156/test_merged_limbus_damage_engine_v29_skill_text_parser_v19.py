"""Safely merged test file (AST-aware, whole-file rename incl. call sites, decorators preserved via line-removal import stripping).
Originals: test_charge_potency_reference_audit.py, test_identity_10406_tremor_2x.py, test_tremor_burst_count_semantics.py, test_tremor_dynamic_transfers_0742.py
"""
from __future__ import annotations

from skill_text_parser_v19 import SkillTextParserV19
from limbus_damage_engine_v29 import DamageEngine, BattleState, FighterState, EnemyState, IdentityData, SkillData, CoinData
import json
from limbus_damage_engine_v29 import DamageEngine, BattleState, EnemyState, FighterState, SkillData, CoinData, IdentityData
from limbus_damage_engine_v29 import DamageEngine, EnemyState, FighterState, BattleState, Status
from limbus_damage_engine_v29 import BattleState, EnemyState, FighterState, Status, DamageEngine


# ---- merged from test_charge_potency_reference_audit.py ----

def test_charge_potency_threshold_coin_power_is_separate_from_count():
    p=SkillTextParserV19()
    parsed, rep=p.parse(["[사용시] 자신의 충전 위력이 3 이상이면, 코인 위력 +1"], 1)
    assert not rep.unsupported
    cond=parsed["effects_on_use"][0]["condition"]
    assert cond == {"type":"resource_gte","resource":"충전 위력","value":3,"amount":1}

def test_charge_potency_dynamic_clash_power_is_parsed():
    p=SkillTextParserV19()
    parsed, rep=p.parse(["[사용시] 자신의 충전 위력만큼 합 위력이 증가 (최대 5)"], 1)
    assert not rep.unsupported
    assert parsed["effects_on_use"][0]["type"] == "_skill_clash_power_dynamic_marker"

def test_charge_potency_coin_reuse_is_parsed():
    p=SkillTextParserV19()
    parsed, rep=p.parse(["4코인 [적중시] 자신의 충전 위력이 5 이상이면, 이 코인 재사용 (스킬당 1회)"], 4)
    assert not rep.unsupported
    rule=parsed["coin_defs"][3]["reuse_rules"][0]
    assert rule["condition"] == {"type":"resource_gte","resource":"충전 위력","value":5}

def test_resource_condition_reads_charge_potency_not_charge_count():
    engine=DamageEngine()
    ident=IdentityData("i","I",60,{})
    f=FighterState(charge=2, charge_potency=5)
    e=EnemyState(hp=1000,max_hp=1000)
    st=BattleState(fighters={"i":f}, enemy=e)
    skill=SkillData(id="s",name="s",base_power=1,coins=[CoinData(1,"slash","lust")],attack_type="slash",sin="lust")
    assert engine.condition_met(st, ident, {"type":"resource_gte","resource":"충전 위력","value":5}, skill)
    assert not engine.condition_met(st, ident, {"type":"resource_gte","resource":"충전 위력","value":6}, skill)

def test_charge_potency_conditional_unbreakable_is_not_flattened():
    p=SkillTextParserV19()
    parsed, rep=p.parse(["[전투 시작시] 자신의 충전 위력이 3 이상이거나, 현재 체력이 최대 체력의 50% 미만이면, 이 스킬의 모든 코인이 파괴 불가 코인으로 변경됨"], 4)
    assert not rep.unsupported
    assert all(not q["unbreakable"] for q in parsed["coin_defs"])
    marker=parsed["effects_on_use"][0]
    assert marker["type"] == "_skill_unbreakable_condition_marker"
    assert marker["condition"]["type"] == "or"


# ---- merged from test_identity_10406_tremor_2x.py ----


def _load_s3():
    data=json.load(open('identity_catalog_v2.json', encoding='utf-8'))
    identity=next(x for x in data['identities'] if x['id']=='identity-10406')
    skill=next(x for x in identity['skills'] if x['id']=='1040603')
    parsed, report=SkillTextParserV19().parse(skill['effects'], 3)
    return identity, skill, parsed, report


def test_source_clause_exists_only_on_identity_10406_s3():
    data=json.load(open('identity_catalog_v2.json', encoding='utf-8'))
    hits=[]
    for identity in data['identities']:
        for skill in identity.get('skills', []) or []:
            for text in skill.get('effects', []) or []:
                if '진동, 파열 의 위력과 횟수가 2배로 부여됨' in str(text):
                    hits.append((identity['id'], skill['id'], text))
    assert hits == [('identity-10406', '1040603', '3코인 [크리티컬 적중 시] 진동, 파열 의 위력과 횟수가 2배로 부여됨')]


def test_s3_third_coin_carries_crit_scoped_double_to_tremor_and_rupture():
    _, _, parsed, report=_load_s3()
    effects=parsed['coin_defs'][2]['effects']
    tremor=next(e for e in effects if e.get('type')=='status' and e.get('name')=='Tremor')
    rupture=next(e for e in effects if e.get('type')=='status' and e.get('name')=='Rupture')
    assert (tremor['potency'], tremor['count']) == (4,2)
    assert (rupture['potency'], rupture['count']) == (4,2)
    assert tremor['potency_multiplier']==2 and tremor['count_multiplier']==2
    assert rupture['potency_multiplier']==2 and rupture['count_multiplier']==2
    assert tremor['multiplier_condition']['type']=='critical_hit'
    assert rupture['multiplier_condition']['type']=='critical_hit'


def test_s3_critical_branch_doubles_both_axes_and_noncritical_does_not():
    _, raw_skill, parsed, _=_load_s3()
    q=parsed['coin_defs'][2]
    coin=CoinData(3,'pierce','pride',effects=q['effects'])
    skill=SkillData(id='1040603',name=raw_skill['name'],base_power=4,coins=[coin],attack_type='pierce',sin='pride')
    identity=IdentityData('A','LCCB 대리 료슈',0,{'S3':skill},[])
    engine=DamageEngine()
    for crit, expected_potency, expected_count in ((True,8,4),(False,4,2)):
        state=BattleState(enemy=EnemyState(1000,1000),fighters={'A':FighterState()})
        state.fighters['A'].poise.count=1
        engine.simulate_coin(state, identity, skill, coin, 'H', crit, 0, allow_crit_without_poise=True)
        # The final Tremor Burst has no source-explicit Count reduction.
        assert state.enemy.statuses['Tremor'].potency == expected_potency
        assert state.enemy.statuses['Tremor'].count == expected_count
        assert state.enemy.statuses['Rupture'].potency == expected_potency
        assert state.enemy.statuses['Rupture'].count == expected_count


# ---- merged from test_tremor_burst_count_semantics.py ----


def test_plain_tremor_burst_does_not_imply_count_loss():
    parser = SkillTextParserV19()
    effect = parser._status_effect('진동 폭발')
    assert effect == {'type': 'tremor_burst', 'name': 'Tremor'}


def test_explicit_tremor_count_reduction_is_kept_separate():
    parser = SkillTextParserV19()
    effect = parser._status_effect('진동 폭발. 대상의 진동 횟수 1 감소')
    assert effect['type'] == 'tremor_burst'
    assert effect['count_cost'] == 1


def test_plain_tremor_burst_preserves_count():
    e = DamageEngine()
    state = BattleState(
        enemy=EnemyState(100, 100, stagger_thresholds=[70], statuses={'Tremor': Status(potency=8, count=4)}),
        fighters={'i': FighterState('i', 45, 45)}, runtime={}
    )
    e.apply_effect(state, 'i', 'enemy', {'type': 'tremor_burst', 'name': 'Tremor'})
    assert state.enemy.statuses['Tremor'].count == 4
    assert state.enemy.stagger_thresholds == [78]


def test_explicit_tremor_burst_count_cost_reduces_count():
    e = DamageEngine()
    state = BattleState(
        enemy=EnemyState(100, 100, stagger_thresholds=[70], statuses={'Tremor': Status(potency=8, count=4)}),
        fighters={'i': FighterState('i', 45, 45)}, runtime={}
    )
    e.apply_effect(state, 'i', 'enemy', {'type': 'tremor_burst', 'name': 'Tremor', 'count_cost': 1})
    assert state.enemy.statuses['Tremor'].count == 3


# ---- merged from test_tremor_dynamic_transfers_0742.py ----

def test_target_tremor_to_self():
    p=SkillTextParserV19()
    e=p._status_effect('1코인 [적중시] 대상의 진동을 최대 3 소모\n(소모한 진동 x 2)만큼 자신의 진동 횟수 증가')
    assert e == {'type':'tremor_consume_target_to_self','target':'enemy','cap':3,'multiplier':2}

def test_self_tremor_to_target():
    p=SkillTextParserV19()
    e=p._status_effect('3코인 [적중시] 자신의 진동 횟수를 최대 8 소모하여, 소모한 진동 횟수만큼 대상의 진동 횟수 증가')
    assert e == {'type':'tremor_consume_self_to_target','target':'enemy','cap':8}

def test_self_all_tremor_to_target():
    p=SkillTextParserV19()
    e=p._status_effect('자신의 진동 횟수를 전부 소모하여, 소모한 값만큼 대상의 진동 횟수 증가')
    assert e == {'type':'tremor_consume_self_to_target','target':'enemy','cap':999999}


def test_target_to_self_runtime_consumes_capped_count_and_transfers_multiplier():
    enemy=EnemyState(100,100,statuses={'Tremor':Status(potency=5,count=4)})
    fighter=FighterState(statuses={'Tremor':Status(potency=0,count=1)})
    state=BattleState(enemy=enemy,fighters={'A':fighter})
    DamageEngine().apply_effect(state,'A','enemy',{'type':'tremor_consume_target_to_self','cap':3,'multiplier':2})
    assert enemy.statuses['Tremor'].count == 1
    assert fighter.statuses['Tremor'].count == 7

def test_self_to_target_runtime_consumes_capped_count():
    enemy=EnemyState(100,100,statuses={'Tremor':Status(potency=2,count=1)})
    fighter=FighterState(statuses={'Tremor':Status(potency=0,count=6)})
    state=BattleState(enemy=enemy,fighters={'A':fighter})
    DamageEngine().apply_effect(state,'A','enemy',{'type':'tremor_consume_self_to_target','cap':4})
    assert fighter.statuses['Tremor'].count == 2
    assert enemy.statuses['Tremor'].count == 5

# ---- 0.7.133 implicit-self conditional damage/critical scaling regressions ----

def test_0_7_133_implicit_charge_threshold_damage_is_conditional():
    p = SkillTextParserV19()
    parsed, report = p.parse(['충전 횟수가 10 이상이면, 피해량 +10%'], 1)
    assert '충전 횟수가 10 이상이면, 피해량 +10%' in report.supported
    assert not report.unsupported
    assert parsed['effects_on_use'][0]['condition'] == {'type': 'resource_gte', 'resource': '충전', 'value': 10}


def test_0_7_133_implicit_self_status_damage_scaling_is_dynamic():
    p = SkillTextParserV19()
    parsed, report = p.parse(['자신의 화상 10 당, 피해량 +10% (최대 20%)'], 1)
    assert not report.unsupported
    c = parsed['effects_on_use'][0]['condition']
    assert c == {'type': 'status_count_per', 'name': 'Burn', 'target': 'self', 'per': 10, 'amount': 0.10, 'max': 0.20, 'use_potency': True}


def test_0_7_133_implicit_poise_critical_damage_scaling_is_dynamic():
    p = SkillTextParserV19()
    parsed, report = p.parse(['[크리티컬 발동 시] 호흡 위력 1당 크리티컬 피해량 +3% (최대 75%)'], 1)
    assert not report.unsupported
    e = parsed['effects_on_use'][0]
    assert e['effect'] == 'crit_damage_bonus'
    assert e['condition']['name'] == 'Poise'
    assert e['condition']['target'] == 'self'
    assert e['condition']['max'] == 0.75


def test_0_7_133_implicit_lost_hp_damage_scaling_keeps_cap():
    p = SkillTextParserV19()
    parsed, report = p.parse(['잃은 체력 1%당 피해량 0.5% 증가 (최대 25%)'], 1)
    assert not report.unsupported
    c = parsed['effects_on_use'][0]['condition']
    assert c == {'type': 'self_lost_hp_per', 'per': 1.0, 'amount': 0.005, 'max': 0.25}


def test_0_7_133_target_owned_negative_effect_count_is_dynamic():
    p = SkillTextParserV19()
    parsed, report = p.parse(['대상이 보유한 부정적인 효과 1개당 피해량이 6% 증가(최대 30%)'], 1)
    assert not report.unsupported
    c = parsed['effects_on_use'][0]['condition']
    assert c == {'type': 'negative_status_count_per', 'target': 'enemy', 'per': 1, 'amount': 0.06, 'max': 0.30}
