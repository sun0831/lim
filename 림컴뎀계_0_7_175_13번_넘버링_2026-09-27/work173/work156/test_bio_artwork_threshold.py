from types import SimpleNamespace
from special_gimmick_v2 import GimmickRegistry
from limbus_damage_engine_v29 import Status

def ident():
    return SimpleNamespace(id='identity-10215',name='x',full_name='x',affiliation=['RING FINGER'],skills={},passives=[{'type':'전투','name':'x','effect':'전투 중 누적으로 자신의 생체 재료 횟수 10을 소모할 때마다 생체 재료를 1 얻음\n- 위 효과로 생체 재료 위력이 2 이상이 되면, 작품명: 파시아 얻음'}])

def test_bio_material_post_conversion_threshold_is_declarative():
    i=ident(); g=GimmickRegistry([i],{i.id:i.passives},[i.id]); r=[x for x in g.rules if x.kind=='cumulative_resource_gain'][0]
    assert r._post_gain_threshold==2 and r._post_gain_status=='작품명: 파시아'
    assert any(e.get('type')=='resource_threshold_status_gain' for e in g.trigger_rules_data()[0]['effects'])

def test_bio_material_threshold_unlocks_artwork_only_after_conversion_reaches_two():
    i=ident(); g=GimmickRegistry([i],{i.id:i.passives},[i.id]); f=SimpleNamespace(resources={'생체 재료':1},statuses={}); st=SimpleNamespace(fighters={i.id:f},runtime={},event_log=[])
    g.after_resource_event(st,{'event':'resource_cumulative_consumed','identity_id':i.id,'resource':'생체 재료','amount':10,'cumulative_before':0,'cumulative_after':10},{i.id:i},0)
    assert f.resources['생체 재료']==2
    assert '작품명: 파시아' in f.statuses

def test_bio_material_threshold_does_not_retrigger_when_already_above_two():
    i=ident(); g=GimmickRegistry([i],{i.id:i.passives},[i.id]); f=SimpleNamespace(resources={'생체 재료':2},statuses={'작품명: 파시아':Status(potency=1,count=1)}); st=SimpleNamespace(fighters={i.id:f},runtime={},event_log=[])
    g.after_resource_event(st,{'event':'resource_cumulative_consumed','identity_id':i.id,'resource':'생체 재료','amount':10,'cumulative_before':0,'cumulative_after':10},{i.id:i},0)
    assert sum(1 for e in st.event_log if e.get('event')=='resource_threshold_status_gain')==0
