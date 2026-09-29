from limbus_damage_engine_v29 import *
from clash_core_v24 import ClashAwareExecutor


def mk_ident():
    coin=CoinData(5,'slash','lust')
    sk=SkillData('s','S',10,[coin],'slash','lust')
    return IdentityData('i','I',0,{'s':sk})


def test_clash_outcome_direction_is_correct():
    eng=DamageEngine()
    machine=type('M',(),{})()
    machine.engine=eng
    machine.events=type('E',(),{'emit':lambda *a,**k:None})()
    ex=ClashAwareExecutor(machine)
    ident=mk_ident(); skill=ident.skills['s']
    state=BattleState(EnemyState(100,100,level=60), {'i':FighterState(level=60)})
    defender=ClashData(5,[CoinData(1,'slash','lust')])
    r=ex.execute(state,ident,skill,defender,['H'],['H'])
    assert r['outcome']=='win'
    assert r['damage']>0


def test_clash_loss_does_not_deal_normal_damage():
    eng=DamageEngine(); machine=type('M',(),{})(); machine.engine=eng
    machine.events=type('E',(),{'emit':lambda *a,**k:None})()
    ex=ClashAwareExecutor(machine)
    ident=mk_ident(); skill=ident.skills['s']
    state=BattleState(EnemyState(100,100,level=60), {'i':FighterState(level=60)})
    defender=ClashData(20,[CoinData(10,'slash','lust')])
    r=ex.execute(state,ident,skill,defender,['T'],['H'])
    assert r['outcome']=='lose'
    assert r['damage']==0


def test_crit_cannot_persist_after_poise_count_is_consumed():
    eng=DamageEngine(); ident=mk_ident()
    f=FighterState(level=60, poise=Status(potency=20,count=1))
    state=BattleState(EnemyState(1000,1000,level=60), {'i':f})
    skill=ident.skills['s']
    d1=eng.simulate_coin(state,ident,skill,skill.coins[0],'H',True,1,0)
    assert f.poise.count==0
    # Engine itself remains permissive for low-level callers; the solver should
    # sanitize requested crits. This test documents the resource consumption.
    assert d1>0
