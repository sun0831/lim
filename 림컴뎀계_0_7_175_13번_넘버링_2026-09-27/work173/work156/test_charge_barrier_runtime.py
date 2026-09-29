from limbus_damage_engine_v29 import BattleState, EnemyState, FighterState
from resource_runtime_v1 import ResourceRuntime, ResourceSpec
from keyword_runtime_v1 import KeywordRuntime


def _state(w=False, barrier=0, charge=0, shield=0):
    f=FighterState(hp=100,max_hp=100,charge=charge,is_wcorp=w,shield=shield)
    e=EnemyState(hp=100,max_hp=100)
    s=BattleState(fighters={'a':f}, enemy=e)
    rr=ResourceRuntime({'충전': ResourceSpec('충전',minimum=0,maximum=20),
                        '충전 역장': ResourceSpec('충전 역장',minimum=0,maximum=99)})
    s.runtime['resource_runtime']=rr
    if barrier:
        rr.gain_charge_barrier(f, barrier, state=s, reason='test')
    return s,f,rr


def test_charge_barrier_non_wcorp_grants_three_shield_per_stack():
    s,f,rr=_state(False,3)
    assert rr.get(f,'충전 역장') == 3
    assert f.shield == 9
    assert f.charge_barrier_shield == 9


def test_charge_barrier_wcorp_grants_five_shield_per_stack():
    s,f,rr=_state(True,3)
    assert rr.get(f,'충전 역장') == 3
    assert f.shield == 15
    assert f.charge_barrier_shield == 15


def test_charge_barrier_shield_consumption_reduces_barrier_by_full_units():
    s,f,rr=_state(False,2)
    absorbed=rr.consume_shield(f,4,state=s,reason='incoming')
    assert absorbed == 4
    assert f.shield == 2
    assert f.charge_barrier_shield == 2
    assert rr.get(f,'충전 역장') == 1


def test_charge_barrier_turn_end_converts_to_charge_and_expires_generated_shield():
    s,f,rr=_state(False,3,charge=2)
    out=KeywordRuntime.turn_end(s)
    assert out['charge_consumed']['a'] == 1
    assert f.charge == 4
    assert rr.get(f,'충전 역장') == 0
    assert f.charge_barrier_shield == 0
    assert f.shield == 0


def test_charge_barrier_turn_end_preserves_unrelated_shield():
    s,f,rr=_state(False,2,shield=7)
    # _state adds barrier shield on top of the pre-existing 7 shield.
    KeywordRuntime.turn_end(s)
    assert f.shield == 7
    assert f.charge == 2
