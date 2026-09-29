from limbus_damage_engine_v29 import *
from special_gimmick_v2 import GimmickRegistry, GimmickRule
from one_turn_solver_v29 import IdentityData, SkillData, CoinData


def test_generic_damage_modifier_critical_slash_only():
    state=BattleState(enemy=EnemyState(1000,1000), fighters={
        'a': FighterState(poise=Status(potency=10,count=5)),
        'b': FighterState(poise=Status(potency=3,count=3)),
    })
    state.runtime['damage_modifiers']=[{'target_identity_id':'a','kind':'critical_damage_percent','amount':0.15,'attack_type':'slash','critical_only':True}]
    ident=IdentityData('a','A',0,{})
    skill=SkillData('s','S',10,[CoinData(0,'slash','pride')],'slash','pride')
    normal=DamageEngine().calculate_coin_damage(state,ident,skill,skill.coins[0],'H',False,coin_index=1)[0]
    crit=DamageEngine().calculate_coin_damage(state,ident,skill,skill.coins[0],'H',True,coin_index=1)[0]
    assert crit>normal


def test_blade_support_rule_compiles_to_generic_modifier():
    from gimmick_modules import blade_lineage
    r=GimmickRule('identity-10508','전투 시작 시 호흡을 가장 많이 보유한 아군 1명의 참격 속성 스킬의 크리티컬 피해량 +15%', 'blade_bonguk_support_crit', (), '검계 우두머리 뫼르소', '본국검술', 1, 0)
    event, conditions, effects=blade_lineage.build_trigger(None,r)
    assert event == 'battle_start'
    assert effects[0].type == 'register_damage_modifier_highest_poise'
    assert effects[0].params['kind'] == 'critical_damage_percent'
    assert effects[0].params['amount'] == 0.15
    assert effects[0].params['attack_type'] == 'slash'
    assert effects[0].params['critical_only'] is True


def test_generic_damage_and_flat_modifiers_resolve():
    from damage_modifier_runtime_v1 import DamageModifierRuntime
    state=BattleState(enemy=EnemyState(1000,1000), fighters={'a':FighterState()})
    ident=IdentityData('a','A',0,{})
    skill=SkillData('s','S',10,[CoinData(0,'slash','pride')],'slash','pride')
    coin=skill.coins[0]
    DamageModifierRuntime.register(state,target_identity_id='a',kind='damage_percent',amount=0.10)
    DamageModifierRuntime.register(state,target_identity_id='a',kind='flat_damage',amount=3)
    values=DamageModifierRuntime.resolve(state,ident,skill,coin,False)
    assert values['damage_percent']==0.10 and values['flat_damage']==3


def test_bare_poise_target_uses_potency_for_bonguk_support():
    from gimmick_modules import blade_lineage
    r=GimmickRule('identity-10508','전투 시작 시 호흡을 가장 많이 보유한 아군 1명의 참격 속성 스킬의 크리티컬 피해량 +15%', 'blade_bonguk_support_crit', (), '검계 우두머리 뫼르소', '본국검술', 1, 0)
    _, _, effects=blade_lineage.build_trigger(None,r)
    assert effects[0].params.get('metric','potency')=='potency'
