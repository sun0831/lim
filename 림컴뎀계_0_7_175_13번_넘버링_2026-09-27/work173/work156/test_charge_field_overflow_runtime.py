from limbus_damage_engine_v29 import BattleState, FighterState, EnemyState
from resource_runtime_v1 import ResourceRuntime, ResourceSpec


def _state():
    f=FighterState(hp=100,max_hp=100,charge=8)
    e=EnemyState(hp=100,max_hp=100)
    s=BattleState(fighters={'a':f}, enemy=e)
    rr=ResourceRuntime({'충전': ResourceSpec('충전', minimum=0, maximum=10),
                        '충전 역장': ResourceSpec('충전 역장', minimum=0, maximum=99)})
    s.runtime['resource_runtime']=rr
    return s,f,rr


def test_charge_gain_records_overflow_without_changing_count():
    s,f,rr=_state()
    rr.gain(f,'충전',5,state=s,reason='test')
    assert f.charge == 10
    ev=[e for e in s.event_log if e['event']=='resource_overflow'][-1]
    assert ev['resource']=='충전'
    assert ev['overflow']==3


def test_charge_field_is_independent_resource_axis():
    s,f,rr=_state()
    rr.gain(f,'충전 역장',3,state=s,reason='test')
    assert rr.get(f,'충전 역장')==3
    assert f.charge==8
    assert getattr(f,'charge_potency',0)==0
