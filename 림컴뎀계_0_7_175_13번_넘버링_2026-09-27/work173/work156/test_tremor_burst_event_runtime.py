from passive_compiler_v29 import compile_clause_template
from passive_runtime_v29_base import PassiveTrigger, PassiveRuntime, PassiveDefinition, Always, SelfTarget, ConsumeCharge, ModifyBurstContext
from limbus_damage_engine_v29 import DamageEngine, EnemyState, FighterState, BattleState, IdentityData
from skill_text_parser_v19 import SkillTextParserV19


def test_tremor_burst_trigger_compiles_charge_cost_and_bonus():
    t, reasons, unsupported = compile_clause_template('진동 폭발 시 충전 횟수 3을 소모하여, 진동 폭발의 흐트러짐 피해량 +40%')
    assert not unsupported
    assert t.trigger == PassiveTrigger.TREMOR_BURST
    assert any(isinstance(e, ConsumeCharge) for e in t.effects)
    assert any(isinstance(e, ModifyBurstContext) for e in t.effects)


def test_tremor_burst_event_modifier_changes_threshold():
    e=DamageEngine()
    enemy=EnemyState(100,100,stagger_thresholds=[70],statuses={'Tremor':__import__('limbus_damage_engine_v29').Status(potency=10,count=2)})
    f=FighterState('i',45,45); f.charge=3
    state=BattleState(enemy=enemy,fighters={'i':f},runtime={})
    pr=PassiveRuntime(); e.passive_runtime=pr
    pr.register(PassiveDefinition('p','p','i',PassiveTrigger.TREMOR_BURST,[Always()],SelfTarget(),[ConsumeCharge(__import__('passive_runtime_v29_base').Const(3)),ModifyBurstContext(__import__('passive_runtime_v29_base').Const(.4))]))
    e.apply_effect(state,'i','enemy',{'type':'tremor_burst','name':'Tremor','count_cost':1})
    assert enemy.stagger_thresholds == [84]
    assert f.charge == 0
    assert enemy.statuses['Tremor'].count == 1


def test_burst_parser_remains_unchanged():
    p=SkillTextParserV19(); parsed,rep=p.parse(['1코인 [적중시] 진동 폭발. 대상의 진동 횟수 1 감소'],1)
    assert not rep.unsupported
    assert parsed['coin_defs'][0]['effects'][0]['type']=='tremor_burst'
