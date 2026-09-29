import sys
sys.path.insert(0,'.')
from skill_text_parser_v19 import SkillTextParserV19
from limbus_damage_engine_v29 import BattleState, EnemyState, FighterState, Status, DamageEngine
from amplitude_runtime_v1 import AmplitudeRuntime


def parse(text, coins=1):
    p=SkillTextParserV19(); data, report=p.parse([text], coins)
    return data, report


def test_identity_1021635_named_amplitude_absence_conversion():
    data, report = parse('- 진동 - 작열이 없으면, 진동 - 작열로 진폭 변환')
    assert not report.unsupported
    e=data['effects_on_use'][0]
    assert e['type']=='amplitude_conversion' and e['amplitude']=='작열'
    assert e['condition']['type']=='not'
    assert e['condition']['condition']['amplitude']=='작열'


def test_identity_1070803_tremor_sum_threshold_conversion():
    data, report = parse('3코인 [적중시] 대상의 진동 위력과 횟수의 합이 20 이상이면, 진동 - 붕괴로 진폭 변환', 3)
    assert not report.unsupported
    e=data['coin_defs'][2]['effects'][0]
    assert e['amplitude']=='붕괴'
    assert e['condition']['type']=='tremor_potency_count_sum_gte'


def test_amplitude_conversion_preserves_tremor_and_requires_threshold():
    enemy=EnemyState(100,100,statuses={'Tremor':Status(potency=11,count=9)})
    state=BattleState(enemy=enemy,fighters={'i':FighterState()},runtime={})
    eng=DamageEngine()
    eff={'type':'amplitude_conversion','amplitude':'붕괴','target':'enemy','condition':{'type':'tremor_potency_count_sum_gte','value':20,'target':'enemy'}}
    assert eng.condition_met(state, state.fighters['i'].identity if hasattr(state.fighters['i'],'identity') else type('I',(),{'id':'i'})(), eff['condition'])
    eng.apply_effect(state,'i','enemy',eff)
    assert AmplitudeRuntime().has_state(enemy,'붕괴','conversion')
    assert enemy.statuses['Tremor'].potency==11 and enemy.statuses['Tremor'].count==9
