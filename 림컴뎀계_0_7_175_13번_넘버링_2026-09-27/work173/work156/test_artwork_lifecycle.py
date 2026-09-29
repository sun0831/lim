from types import SimpleNamespace
from special_gimmick_v2 import GimmickRegistry
from limbus_damage_engine_v29 import Status

def ident():
    return SimpleNamespace(id='identity-10215', name='거미집 약지 제자', full_name='거미집 약지 제자', affiliation=['RING FINGER'], skills={}, passives=[{'type':'전투','name':'보호와 억제를 위한 갑주','effect':'스테이지에 첫 등장 시 아이언 메이든 얻음\n\n턴 종료 시 자신에게 작품명: 파시아가 있으면, 아이언 메이든이 소멸하고, 구속 해제 - 창작 몰입 얻음 (전투당 1회)\n- 흐트러짐 상태면, 흐트러짐 해제 (강제 흐트러짐 제외)'}])

def test_artwork_turn_end_rule_compiles():
    i=ident(); g=GimmickRegistry([i],{i.id:i.passives},[i.id])
    rs=[r for r in g.rules if r.kind=='turn_end_status_transform']
    assert len(rs)==1
    assert rs[0]._turn_end_source_status=='아이언 메이든'
    assert rs[0]._turn_end_gate_status=='작품명: 파시아'
    assert rs[0]._turn_end_reward_status=='구속 해제 - 창작 몰입'

def test_artwork_turn_end_consumes_iron_maiden_and_grants_release():
    i=ident(); g=GimmickRegistry([i],{i.id:i.passives},[i.id])
    f=SimpleNamespace(resources={},statuses={'작품명: 파시아':Status(potency=1,count=1),'아이언 메이든':Status(potency=1,count=1)})
    st=SimpleNamespace(fighters={i.id:f},runtime={},event_log=[])
    g.after_lifecycle_event(st,{'event':'turn_end','identity_id':i.id}, {i.id:i}, 0)
    assert '아이언 메이든' not in f.statuses
    assert f.statuses['구속 해제 - 창작 몰입'].count>=1
    assert any(e.get('event')=='status_transform' for e in st.event_log)

def test_artwork_turn_end_requires_both_gate_and_source():
    i=ident(); g=GimmickRegistry([i],{i.id:i.passives},[i.id])
    cases=({'아이언 메이든':Status(potency=1,count=1)}, {'작품명: 파시아':Status(potency=1,count=1)})
    for statuses in cases:
        f=SimpleNamespace(resources={},statuses=statuses.copy())
        st=SimpleNamespace(fighters={i.id:f},runtime={},event_log=[])
        g.after_lifecycle_event(st,{'event':'turn_end','identity_id':i.id}, {i.id:i}, 0)
        assert '구속 해제 - 창작 몰입' not in f.statuses
    assert '아이언 메이든' in cases[0]
