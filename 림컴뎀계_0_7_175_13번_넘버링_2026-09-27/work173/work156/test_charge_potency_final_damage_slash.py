import json
from skill_text_parser_v19 import SkillTextParserV19
from identity_catalog_v29 import IdentityCatalogV29
from limbus_damage_engine_v29 import BattleState, FighterState, EnemyState, DamageEngine, SkillData, CoinData, IdentityData
from types import SimpleNamespace


def test_charge_potency_final_damage_slash_parser():
    p = SkillTextParserV19()
    parsed, _ = p.parse([
        '4코인 [적중시] 이 코인 최종 피해량의 (충전 위력 x 10)%만큼 참격 피해 (최대 50%)'
    ], 4)
    e = parsed['coin_defs'][3]['effects'][0]
    assert e['type'] == 'resource_final_damage_scale'
    assert e['resource'] == '충전 위력'
    assert e['scale_per'] == 0.10
    assert e['cap'] == 0.50
    assert e['damage_type'] == 'slash'


def _identity(charge_potency=3):
    effect = {'type':'resource_final_damage_scale','resource':'충전 위력',
              'scale_per':0.10,'cap':0.50,'damage_type':'slash','target':'enemy'}
    coin = CoinData(1, 'blunt', 'lust', effects=[effect])
    skill = SkillData(id='S', name='S', base_power=10, coins=[coin], attack_type='blunt', sin='lust')
    ident = IdentityData(id='i', name='test', offense_level=0, skills={'S':skill})
    fighter = FighterState(hp=100, max_hp=100, sp=0, level=0, speed=5)
    fighter.charge_potency = charge_potency
    enemy = EnemyState(hp=100, max_hp=100, level=60, defense_level=0,
                       physical_res={'slash':1.0,'blunt':1.0,'pierce':1.0}, sin_res={'lust':1.0})
    state = BattleState(fighters={'i':fighter}, enemy=enemy)
    state.runtime['defense_level_is_absolute'] = True
    return state, ident, skill, coin


def test_charge_potency_final_damage_slash_is_separate_post_hit_component():
    state, ident, skill, coin = _identity()
    dmg = DamageEngine().simulate_coin(state, ident, skill, coin, 'H', False, 1, consume_attacker_state=False)
    # Direct damage: roll 11 against equal level/resistance => 11.
    # Charge Potency 3 => +30%, so typed Slash add = 3.
    assert dmg == 11.0
    assert state.enemy.hp == 86.0
    assert any(e['event']=='resource_final_damage_scale' and e['base_damage']==11.0 and e['actual_damage']==3 for e in state.event_log)


def test_charge_potency_final_damage_slash_uses_slash_resistance():
    state, ident, skill, coin = _identity()
    state.enemy.physical_res['slash'] = 0.5
    dmg = DamageEngine().simulate_coin(state, ident, skill, coin, 'H', False, 1, consume_attacker_state=False)
    # 11 direct + floor/round(11*0.30*0.75) = 2 additional Slash damage.
    assert dmg == 11.0
    assert state.enemy.hp == 87.0
    ev = [e for e in state.event_log if e['event']=='resource_final_damage_scale'][-1]
    assert ev['damage_type'] == 'slash'
    assert ev['resistance_multiplier'] == 0.75
