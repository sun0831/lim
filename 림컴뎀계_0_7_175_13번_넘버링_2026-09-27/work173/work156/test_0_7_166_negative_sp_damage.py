import json
from passive_compiler_v29 import compile_passive_v15


def _mods(record, owner):
    r=compile_passive_v15(record, owner, 0)
    return [e for rule in r.rules for e in rule.effects]


def test_10710_target_negative_sp_per_point_damage_scaling():
    record={
        'type':'서포트','name':'울고 또 울어라','affinity':'gloom','cost':3,
        'condition':'공명',
        'effect':'정신력이 가장 높은 아군 1명이 정신력이 0 미만인 대상에게 입히는 피해량 +5%\n대상의 정신력이 0보다 낮을수록 입히는 피해량이 증가 (정신력 1당 +0.5%, 최대 20%)'
    }
    mods=_mods(record,'identity-10710')
    dyn=[e for e in mods if type(e).__name__=='ModifyContext' and e.field=='dynamic_damage_bonus']
    assert len(dyn) >= 2
    # The second modifier is the per-negative-SP scaling and must be a
    # negative-target-SP expression, not an unconditional fixed bonus.
    assert any(getattr(e,'amount',None).__class__.__name__=='Clamp' for e in dyn)


def test_negative_sp_divisor_scaling_uses_percent_units_and_real_cap():
    record={
        'type':'전투','name':'test','affinity':'','cost':0,'condition':'보유',
        'effect':'대상의 정신력이 0 미만이면, 피해량이 (-대상의 정신력 / 3)%만큼 증가 (최대 15%)'
    }
    mods=_mods(record,'identity-test')
    dyn=[e for e in mods if type(e).__name__=='ModifyContext' and e.field=='dynamic_damage_bonus']
    assert dyn
    amount=dyn[0].amount
    assert type(amount).__name__=='Clamp'
    assert float(amount.hi)==0.15


def test_negative_target_sp_scaling_resolves_per_point_and_cap():
    record={
        'type':'서포트','name':'울고 또 울어라','affinity':'gloom','cost':3,
        'condition':'공명',
        'effect':'대상의 정신력이 0보다 낮을수록 입히는 피해량이 증가 (정신력 1당 +0.5%, 최대 20%)'
    }
    mods=_mods(record,'identity-10710')
    effect=next(e for e in mods if type(e).__name__=='ModifyContext')
    amount=effect.amount
    class U:
        sp=-10
    class S:
        enemy=U()
        fighters={'enemy':enemy}
    assert abs(amount.resolve(None,S(),'owner')-0.05) < 1e-9
    S.enemy.sp=-50
    assert abs(amount.resolve(None,S(),'owner')-0.20) < 1e-9
    S.enemy.sp=10
    assert abs(amount.resolve(None,S(),'owner')-0.0) < 1e-9
