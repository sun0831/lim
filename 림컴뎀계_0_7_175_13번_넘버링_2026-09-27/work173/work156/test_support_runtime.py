"""병합 테스트: support_runtime

원본 파일 (내용은 AST 병합기로 합쳤고 테스트 본문은 바꾸지 않음):
  - test_v71_support_runtime.py
  - test_v73_support_passive_runtime.py
  - test_v98_support_action_effect_runtime.py
이름 충돌 helper 는 `이름__vNN` 으로 분리했다. 매핑은 tools/MERGE_MAP.json 참고.
"""
import json
from types import SimpleNamespace
from support_runtime_v1 import SupportActionResolver, SupportCommand
from special_gimmick_v2 import GimmickRegistry
from limbus_damage_engine_v29 import IdentityData, SkillData, CoinData, Status
from one_turn_solver_v29 import IdentityCatalogV29
from action_queue_v1 import ActionQueue
from effect_executor_v1 import EffectExecutor
from effect_runtime_v1 import EffectCommand



# ======================================================================
# 원본: test_v71_support_runtime.py
# ======================================================================

def _skill(sid, name, slot='S1'):
    s=SkillData(sid,name,4,[CoinData(1,'slash','lust')],'slash','lust'); s._slot=slot; return s

def test_support_resolver_resolves_left_and_right_without_identity_specific_code():
    a=SimpleNamespace(id='a',name='A',full_name='A',skills={'s':_skill('s','A S1')})
    b=SimpleNamespace(id='b',name='B',full_name='B',skills={'s':_skill('s','B S1')})
    c=SimpleNamespace(id='c',name='C',full_name='C',skills={'s':_skill('s','C S1')})
    r=SupportActionResolver([a,b,c],['a','b','c'])
    x=r.resolve(SupportCommand('b',identity_policy='ally_right',skill_policy='first_attack'), 'b')
    y=r.resolve(SupportCommand('b',identity_policy='ally_left',skill_policy='first_attack'), 'b')
    assert x[0].id=='c' and x[1].id=='s'
    assert y[0].id=='a' and y[1].id=='s'

def test_generic_right_support_command_uses_support_runtime():
    c=_skill('c','명령','S2')
    a=_skill('a','지원','S1')
    captain=IdentityData('captain','지원자',0,{'S2':c},[])
    ally=IdentityData('ally','아군',0,{'S1':a},[])
    captain.passives=[{'name':'p','effect':'[사용시] 자신의 우측에 위치한 아군에게 이번 턴에 원호 공격을 명령함.'}]
    g=GimmickRegistry([captain,ally],{captain.id:captain.passives,ally.id:[]},available_identity_ids=['captain','ally'])
    out=g.after_skill(captain,c,{'current_resonance':{}})
    assert out and out[0].identity_id=='ally'
    assert out[0].skill_id=='__support_default__'
    assert out[0].trigger_kind=='support_right_assist'

def test_named_assist_is_still_resolved_through_common_provider():
    a=_skill('a','지원타')
    b=_skill('b','기본')
    actor=IdentityData('actor','지원자',0,{'S1':a},[])
    owner=IdentityData('owner','주체',0,{'S1':b},[])
    owner.passives=[{'name':'p','effect':"기본 사용 후 지원자가 지원타 스킬로 원호 공격함"}]
    g=GimmickRegistry([owner,actor],{owner.id:owner.passives,actor.id:[]},available_identity_ids=['owner','actor'])
    out=g.after_skill(owner,b,{})
    assert out and out[0].identity_id=='actor' and out[0].skill_id=='a'


# ======================================================================
# 원본: test_v73_support_passive_runtime.py
# ======================================================================
DATA=json.load(open('identity_catalog_v2.json',encoding='utf-8'))['identities']
CAT=IdentityCatalogV29(DATA)

def ident(i): return CAT.build_identity(i)

def state(ids, sp=None, poise=None):
    sp=sp or {}; poise=poise or {}
    fighters={}
    for iid in ids:
        f=SimpleNamespace(hp=100,max_hp=100,sp=sp.get(iid,0),resources={},statuses={},poise=Status())
        f.poise.potency=poise.get((iid,'potency'),poise.get(iid,0)); f.poise.count=poise.get((iid,'count'),0)
        fighters[iid]=f
    return SimpleNamespace(fighters=fighters,event_log=[],runtime={})

def test_generic_support_passive_sasa_ryoshu_grants_poise_to_formation_first():
    ryoshu=ident('identity-10415'); first=ident('identity-10103')
    ids=[first.id,ryoshu.id]
    g=GimmickRegistry([first,ryoshu],{first.id:first.passives,ryoshu.id:ryoshu.passives},[first.id])
    rules=[r for r in g.rules if r.kind=='support_poise_gain']
    assert len(rules)==1 and rules[0].max_activations==3
    st=state(ids,poise={first.id:0})
    sk=next(s for s in first.skills.values() if s._slot=='S1')
    ctx={'state':st,'fighter':st.fighters[first.id],'action_start_poise_potency':0,'action_start_poise_count':0,'action_end_poise_potency':1,'action_end_poise_count':1,'actual_damage':0}
    for _ in range(3):
        g.after_skill(first,sk,ctx)
    assert st.fighters[first.id].poise.potency==6
    g.after_skill(first,sk,ctx)
    assert st.fighters[first.id].poise.potency==6

def test_generic_support_passive_sasa_yisang_adds_poise_count_to_highest_sp_actor():
    yi=ident('identity-10103'); other=ident('identity-10208')
    ids=[yi.id,other.id]
    g=GimmickRegistry([yi,other],{yi.id:yi.passives,other.id:other.passives},[other.id])
    assert any(r.kind=='support_poise_count_bonus' for r in g.rules)
    st=state(ids,sp={yi.id:10,other.id:50},poise={(other.id,'potency'):3,(other.id,'count'):3})
    sk=next(s for s in other.skills.values() if s._slot=='S1')
    ctx={'state':st,'fighter':st.fighters[other.id],'action_start_poise_potency':2,'action_start_poise_count':2,'action_end_poise_potency':3,'action_end_poise_count':3,'actual_damage':0}
    g.after_skill(other,sk,ctx)
    assert st.fighters[other.id].poise.count==4


# ======================================================================
# 원본: test_v98_support_action_effect_runtime.py
# ======================================================================

def _identity(iid, name, skill_id, skill_name):
    skill = SimpleNamespace(id=skill_id, name=skill_name, _slot='S1')
    return SimpleNamespace(id=iid, name=name, full_name=name, skills={skill_id: skill})

def test_support_action_requested_next_queues_selected_ally_placeholder():
    a = _identity('A', 'A', 'A-S1', 'A S1')
    b = _identity('B', 'B', 'B-S1', 'B S1')
    q = ActionQueue.from_scenario([{'identity_id': 'A', 'skill_id': 'A-S1'}])
    source = q.pop()
    result = EffectExecutor().execute(EffectCommand('support_action', {
        'source_identity_id': 'A', 'identity_policy': 'ally_right',
        'skill_policy': 'requested_next', 'skill_name': '__support_default__',
        'trigger_kind': 'captain_right_assist', 'target_policy': 'main'
    }, 'r1', 'action'), {
        'action_queue': q, 'source_action': source, 'identity_id': 'A',
        'identity_map': {'A': a, 'B': b}, 'available_identity_ids': ['A', 'B'],
        'event': 'after_skill'
    })
    assert result['queued'] is True
    assert q.items[q.position].identity_id == 'B'
    assert q.items[q.position].skill_id == '__support_default__'
    assert q.items[q.position].trigger_kind == 'captain_right_assist'

def test_support_action_named_resolves_common_skill_and_preserves_target_policy():
    a = _identity('A', 'A', 'A-S1', 'A S1')
    b = _identity('B', 'B', 'B-S1', '지원타')
    q = ActionQueue.from_scenario([{'identity_id': 'A', 'skill_id': 'A-S1'}])
    source = q.pop()
    result = EffectExecutor().execute(EffectCommand('support_action', {
        'source_identity_id': 'A', 'identity_policy': 'ally_right',
        'skill_policy': 'named', 'skill_name': '지원타',
        'trigger_kind': 'named_assist', 'target_policy': 'enemy_main',
        'target_index': 0
    }, 'r2', 'action'), {
        'action_queue': q, 'source_action': source, 'identity_id': 'A',
        'identity_map': {'A': a, 'B': b}, 'available_identity_ids': ['A', 'B']
    })
    assert result['queued'] is True
    generated = q.items[q.position]
    assert generated.identity_id == 'B'
    assert generated.skill_id == 'B-S1'
    assert generated.target_policy == 'enemy_main'
    assert generated.target_index == 0
