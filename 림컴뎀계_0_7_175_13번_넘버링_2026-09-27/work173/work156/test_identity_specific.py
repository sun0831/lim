"""병합 테스트: identity_specific

원본 파일 (내용은 AST 병합기로 합쳤고 테스트 본문은 바꾸지 않음):
  - test_v47_dawn-cross-identity.py
  - test_v60_cross_identity_catalog.py
  - test_v60_cross_identity_reactions.py
  - test_v61_high_impact_gimmicks.py
  - test_v62_foresight_eye.py
  - test_v63_user_afterimage_input.py
  - test_v64_middle_revenge_ledger.py
  - test_v65_revenge_tattoo_transform.py
  - test_v72_blade_lineage_module.py
  - test_v74_blade_hongmaehwa_runtime.py
  - test_v75_blade_survival_runtime.py
  - test_v75_blade_transfer_runtime.py
이름 충돌 helper 는 `이름__vNN` 으로 분리했다. 매핑은 tools/MERGE_MAP.json 참고.
"""
import json
import unittest
from one_turn_solver_v29 import IdentityCatalogV29, OneTurnSolverV29
from special_gimmick_v2 import GimmickRegistry
from legacy_trigger_adapter_v1 import LegacyTriggerAdapter
from limbus_damage_engine_v29 import (
    BattleState,
    EnemyState,
    FighterState,
    Status,
    IdentityData,
    SkillData,
    CoinData,
    DamageEngine,
)
from types import SimpleNamespace
from trigger_runtime_v1 import TriggerRuntime
from resource_runtime_v1 import ResourceRuntime



# ======================================================================
# 원본: test_v47_dawn-cross-identity.py
# ======================================================================

def build(ids):
    cat = IdentityCatalogV29(json.load(open('identity_catalog_v2.json', encoding='utf-8'))['identities'])
    return [cat.build_identity(i) for i in ids]

def test_dawn_stagger_followup_requires_dawn_actor_and_new_stagger():
    faust, gregor, sinclair = build(['identity-10216','identity-11216','identity-11009'])
    g = GimmickRegistry([faust, gregor, sinclair], {x.id:x.passives for x in [faust,gregor,sinclair]},
                        available_identity_ids=[faust.id, gregor.id, sinclair.id])
    # A Dawn S1 that newly staggers should queue Faust's follow-up.
    ctx = {
        'identity_id': gregor.id, 'skill_id': gregor.skills['S1'].id,
        'skill_name': gregor.skills['S1'].name, 'skill_slot':'S1',
        'action_start_staggered':False, 'action_end_staggered':True,
        'actual_damage':10, 'generated':False,
        'available_identity_ids':[faust.id,gregor.id,sinclair.id],
        'state':None,
    }
    out=g.after_skill(gregor,gregor.skills['S1'],ctx)
    assert any(x.identity_id==faust.id and x.skill_id==next(s.id for s in faust.skills.values() if s.name=='연계') for x in out)

    # Non-Dawn S1 must not trigger the Dawn stagger assist.
    ctx['identity_id']='other-id'
    out=LegacyTriggerAdapter(g.trigger_rules).fire('after_skill',{**ctx,'identity_id':'other-id'})
    assert not any(e['effect'].get('trigger_kind')=='stagger_assist' for e in out)

def test_dawn_reused_coin_burn_damage_is_capped_and_requires_reuse():
    faust, gregor, sinclair = build(['identity-10216','identity-11216','identity-11009'])
    g = GimmickRegistry([faust, gregor, sinclair], {x.id:x.passives for x in [faust,gregor,sinclair]},
                        available_identity_ids=[faust.id,gregor.id,sinclair.id])
    state=BattleState(enemy=EnemyState(hp=100,max_hp=100,statuses={'Burn':Status(potency=17,count=10)}),
                      fighters={x.id:FighterState() for x in [faust,gregor,sinclair]})
    # First normal coin: no reused-coin bonus.
    extra=g.after_coin(state,faust,faust.skills['S1'],1,20,reuse_index=0)
    assert extra==0 and state.enemy.hp==100
    # Reused coin: Burn 17 -> per-coin cap 10.
    extra=g.after_coin(state,faust,faust.skills['S1'],1,20,reuse_index=1)
    assert state.enemy.hp==90
    assert state.turn_damage==10
    assert any(e['event']=='reused_coin_status_damage' and e['damage']==10 for e in state.event_log)

def test_dawn_reused_coin_damage_has_turn_cap_20():
    faust, gregor, sinclair = build(['identity-10216','identity-11216','identity-11009'])
    g = GimmickRegistry([faust, gregor, sinclair], {x.id:x.passives for x in [faust,gregor,sinclair]},
                        available_identity_ids=[faust.id,gregor.id,sinclair.id])
    state=BattleState(enemy=EnemyState(hp=100,max_hp=100,statuses={'Burn':Status(potency=10,count=10)}),
                      fighters={x.id:FighterState() for x in [faust,gregor,sinclair]})
    g.after_coin(state,faust,faust.skills['S1'],1,20,reuse_index=1)
    g.after_coin(state,faust,faust.skills['S1'],1,20,reuse_index=2)
    g.after_coin(state,faust,faust.skills['S1'],1,20,reuse_index=3)
    assert state.turn_damage==20
    assert state.enemy.hp==80


# ======================================================================
# 원본: test_v60_cross_identity_catalog.py
# ======================================================================

def _skill(i,n,slot='S1'):
    s=SkillData(i,n,4,[CoinData(1,'slash','lust')],'slash','lust'); s._slot=slot; return s

def _record(name):
    c=json.load(open('identity_catalog_v2.json', encoding='utf-8'))['identities']
    return next(x for x in c if x.get('fullName')==name)

def test_catalog_hongwon_passive_is_compiled():
    r=_record('홍원 방랑무사 료슈')
    skills={}
    for x in r['skills']:
        skills[x['id']]=_skill(x['id'],x['name'],x['slot'])
    ident=IdentityData(r['id'],r['name'],0,skills,r['passives'])
    g=GimmickRegistry([ident],{ident.id:ident.passives},available_identity_ids=[ident.id])
    kinds=[x.kind for x in g.rules]
    assert 'ally_hit_followup' in kinds and 'received_attack_followup' in kinds

def test_received_attack_bridge_queues_hongwon_s3():
    r=_record('홍원 방랑무사 료슈')
    skills={x['id']:_skill(x['id'],x['name'],x['slot']) for x in r['skills']}
    ident=IdentityData(r['id'],r['name'],0,skills,r['passives'])
    g=GimmickRegistry([ident],{ident.id:ident.passives},available_identity_ids=[ident.id])
    out=g.after_received_attack(None,{'identity_id':ident.id,'received_target_id':ident.id,'received_target_hp':10,'received_target_max_hp':100,'received_target_died':False,'attacker_id':'enemy_1'})
    assert out and out[0].skill_id=='1041303'


# ======================================================================
# 원본: test_v60_cross_identity_reactions.py
# ======================================================================

class I:
    def __init__(self,id,name,skills): self.id=id; self.name=name; self.full_name=name; self.skills={x.id:x for x in skills}

class Skill:
    def __init__(self,id,name,slot='S1'): self.id=id; self.name=name; self._slot=slot

def test_hongwon_ally_hit_followup_compiles():
    s1=Skill('r-s1','어이, 물러서라')
    owner=I('10413','홍원 방랑무사 료슈',[s1]); ally=I('ally','아군',[Skill('a-s1','공격')])
    owner.passives=[{'effect':"자신을 제외한 아군의 스킬이 적에게 적중하면, 해당 공격 종료시 ‘어이, 물러서라’로 일방 공격 (턴 당 1회)"}]
    g=GimmickRegistry([owner,ally],{owner.id:owner.passives},[owner.id,ally.id])
    rules=[r for r in g.trigger_rules if r.metadata.get('legacy_kind')=='ally_hit_followup']
    assert rules and rules[0].event=='after_skill'
    fired=LegacyTriggerAdapter(g.trigger_rules).fire('after_skill',{'identity_id':ally.id,'skill_slot':'S1','skill_name':'공격','actual_damage':10,'available_identity_ids':[owner.id,ally.id]})
    assert fired and fired[0]['effect']['identity_id']==owner.id

def test_hongwon_does_not_self_trigger():
    s1=Skill('r-s1','어이, 물러서라'); owner=I('10413','홍원 방랑무사 료슈',[s1])
    owner.passives=[{'effect':"자신을 제외한 아군의 스킬이 적에게 적중하면, 해당 공격 종료시 ‘어이, 물러서라’로 일방 공격 (턴 당 1회)"}]
    g=GimmickRegistry([owner],{owner.id:owner.passives},[owner.id])
    fired=LegacyTriggerAdapter(g.trigger_rules).fire('after_skill',{'identity_id':owner.id,'skill_slot':'S1','skill_name':'어이, 물러서라','actual_damage':10,'available_identity_ids':[owner.id]})
    assert not fired

def test_received_attack_bridge_handles_death_or_hp_threshold():
    s3=Skill('r-s3','가척아원[加斥我援]'); owner=I('10413','홍원 방랑무사 료슈',[s3])
    owner.passives=[{'effect':"적이 아군을 공격하여 해당 아군이 사망했거나 체력이 25% 미만이면, 해당 공격 종료시 홍원 방랑무사 료슈가 ‘가척아원[加斥我援]’으로 해당 적 일방 공격 (전투 당 1회)"}]
    g=GimmickRegistry([owner],{owner.id:owner.passives},[owner.id])
    rules=[r for r in g.trigger_rules if r.metadata.get('legacy_kind')=='received_attack_followup']; assert rules
    fired=g.after_received_attack(None,{'identity_id':owner.id,'received_target_id':owner.id,'received_target_hp':20,'received_target_max_hp':100,'received_target_died':False,'attacker_id':'enemy_1'})
    assert fired and fired[0].skill_id==s3.id
    g.reset_turn()
    fired=g.after_received_attack(None,{'identity_id':owner.id,'received_target_id':owner.id,'received_target_hp':0,'received_target_max_hp':100,'received_target_died':True,'attacker_id':'enemy_1'})
    assert fired and fired[0].skill_id==s3.id


# ======================================================================
# 원본: test_v61_high_impact_gimmicks.py
# ======================================================================

def _catalog_identity(iid):
    d=json.load(open('identity_catalog_v2.json', encoding='utf-8'))['identities']
    c=IdentityCatalogV29(d)
    return c.build_identity(iid)

def test_lccb_mast_compiles_lowest_ammo_poise_and_final_ammo_damage():
    ident=_catalog_identity('identity-10406')
    g=GimmickRegistry([ident],{ident.id:ident.passives},[ident.id])
    kinds={r.kind for r in g.rules}
    assert 'lowest_ammo_poise' in kinds
    assert any(r.event=='after_coin' and any(e.type=='extra_damage_scale' for e in r.effects) for r in g.trigger_rules)
    fired=LegacyTriggerAdapter(g.trigger_rules).fire('after_skill',{
        'identity_id':ident.id,'skill_slot':'S3','action_ammo_spent':1,
        'is_lowest_ammo_identity':True,'available_identity_ids':[ident.id]
    })
    assert fired and fired[0]['effect']['type']=='poise_gain' and fired[0]['effect']['amount']==3

def test_lccb_poise_is_once_per_turn():
    ident=_catalog_identity('identity-10406')
    g=GimmickRegistry([ident],{ident.id:ident.passives},[ident.id])
    st=BattleState(EnemyState(100,100),{ident.id:FighterState()})
    skill=next(iter(ident.skills.values()))
    ctx={'state':st,'fighter':st.fighters[ident.id],'identity_id':ident.id,'action_ammo_spent':1,'is_lowest_ammo_identity':True}
    assert g.after_skill(ident,skill,ctx) == []
    assert st.fighters[ident.id].poise.potency == 3
    assert g.after_skill(ident,skill,ctx) == []
    assert st.fighters[ident.id].poise.potency == 3
    g.reset_turn()
    assert g.after_skill(ident,skill,ctx) == []
    assert st.fighters[ident.id].poise.potency == 6

def test_bio_material_initializes_from_ring_finger_count_and_gains_on_damage_kill():
    ident=_catalog_identity('identity-10215')
    # lightweight identities only need affiliation for the dynamic start effect
    ally=SimpleNamespace(id='ring-ally', affiliation=['RING FINGER'])
    g=GimmickRegistry([ident,ally],{ident.id:ident.passives},[ident.id,ally.id])
    class F: 
        def __init__(self): self.hp=100; self.resources={}
    class S:
        def __init__(self): self.fighters={ident.id:F(),ally.id:F()}; self.event_log=[]; self.runtime={}
    st=S()
    g.after_lifecycle_event(st,{'event':'battle_start','identity_id':ident.id},{ident.id:ident,ally.id:ally},0)
    assert st.fighters[ident.id].resources.get('생체 재료')==4
    fired=LegacyTriggerAdapter(g.trigger_rules).fire('after_skill',{'identity_id':ident.id,'actual_damage':20,'target_died':True})
    assert fired

def test_blackcloud_prefers_s4_on_death_or_low_hp_and_caps_two_per_turn():
    ident=_catalog_identity('identity-10712')
    g=GimmickRegistry([ident],{ident.id:ident.passives},[ident.id])
    ctx={'identity_id':ident.id,'received_target_id':'ally1','received_target_hp':10,'received_target_max_hp':100,'received_target_died':False,'received_target_damaged':True,'attacker_id':'enemy'}
    adapter=LegacyTriggerAdapter(g.trigger_rules)
    fired=adapter.fire('after_received_attack',ctx)
    assert fired and fired[0]['effect']['skill_name']=='뒷골목의 규칙'
    # a normal hit on another ally can still use S1
    ctx2=dict(ctx); ctx2.update(received_target_id='ally2',received_target_hp=80,received_target_died=False)
    fired2=adapter.fire('after_received_attack',ctx2)
    assert fired2 and fired2[0]['effect']['skill_name']=='구름베기'
    # third qualifying target is blocked by the turn-wide cap of 2
    ctx3=dict(ctx); ctx3.update(received_target_id='ally3',received_target_hp=10)
    assert not adapter.fire('after_received_attack',ctx3)


# ======================================================================
# 원본: test_v62_foresight_eye.py
# ======================================================================

def _identity():
    data = json.load(open('identity_catalog_v2.json', encoding='utf-8'))['identities']
    return IdentityCatalogV29(data).build_identity('identity-10916')

class _Fighter:
    def __init__(self):
        self.resources = {}
        self.statuses = {}
        self.hp = 100

class _State:
    def __init__(self, identity_id):
        self.fighters = {identity_id: _Fighter()}
        self.event_log = []
        self.runtime = {}

def test_foresight_eye_initializes_and_spends_one_per_clash():
    identity = _identity()
    registry = GimmickRegistry([identity], {identity.id: identity.passives}, [identity.id])
    assert {'foresight_start', 'foresight_clash_cost'} <= {rule.kind for rule in registry.rules}

    state = _State(identity.id)
    registry.after_lifecycle_event(state, {'event': 'battle_start', 'identity_id': identity.id}, {identity.id: identity})
    assert state.fighters[identity.id].resources['예지안'] == 30

    skill = next(skill for skill in identity.skills.values() if skill._slot == 'S1')
    registry.after_clash(identity, skill, {'state': state, 'fighter': state.fighters[identity.id], 'outcome': 'win'})
    assert state.fighters[identity.id].resources['예지안'] == 29

def test_foresight_eye_enters_overheat_only_when_last_stack_is_spent():
    identity = _identity()
    registry = GimmickRegistry([identity], {identity.id: identity.passives}, [identity.id])
    state = _State(identity.id)
    state.fighters[identity.id].resources['예지안'] = 1
    skill = next(skill for skill in identity.skills.values() if skill._slot == 'S1')

    registry.after_clash(identity, skill, {'state': state, 'fighter': state.fighters[identity.id], 'outcome': 'win'})
    assert state.fighters[identity.id].resources['예지안'] == 0
    assert state.fighters[identity.id].resources['예지안 과열'] == 1


# ======================================================================
# 원본: test_v63_user_afterimage_input.py
# ======================================================================

class TestV63UserAfterimageInput(unittest.TestCase):
    def test_single_enemy_afterimage_count_is_loaded_as_status(self):
        solver=OneTurnSolverV29()
        ids={}
        state=solver.build_state({'enemy':{'hp':100,'max_hp':100,'afterimage_count':3},'allies':{}}, ids)
        self.assertEqual(state.enemy.statuses['잔영'].count,3)

    def test_zero_afterimage_clears_direct_status(self):
        solver=OneTurnSolverV29()
        state=solver.build_state({'enemy':{'hp':100,'max_hp':100,'afterimage_count':0,'statuses':{'잔영':{'count':2}}},'allies':{}}, {})
        self.assertNotIn('잔영', state.enemy.statuses)

    def test_enemy_target_slots_accept_individual_afterimage_counts(self):
        solver=OneTurnSolverV29()
        state=solver.build_state({'enemy':{'hp':100,'max_hp':100,'targets':[
            {'id':'a','hp':100,'max_hp':100,'afterimage_count':2},
            {'id':'b','hp':100,'max_hp':100,'afterimage_count':1},
        ]},'allies':{}}, {})
        # build_state only constructs the primary enemy; per-slot mapping is applied in solve().
        self.assertIsNotNone(state.enemy)
if __name__=='__main__': unittest.main()


# ======================================================================
# 원본: test_v64_middle_revenge_ledger.py
# ======================================================================

def identities():
    data=json.load(open('identity_catalog_v2.json',encoding='utf8'))['identities']
    cat=IdentityCatalogV29(data)
    owner=cat.build_identity('identity-10715')
    ally=cat.build_identity('identity-10306')
    return owner,ally

class Fighter:
    def __init__(self): self.resources={}; self.statuses={}; self.hp=100; self.max_hp=100

class State:
    def __init__(self, ids):
        self.fighters={i:Fighter() for i in ids}; self.enemy=SimpleNamespace(id='enemy_1',statuses={}); self.event_log=[]; self.runtime={}

def test_middle_hit_adds_revenge_target_and_ledger_once_per_skill():
    owner,ally=identities(); ids=[owner,ally]
    g=GimmickRegistry(ids,{i.id:i.passives for i in ids},[i.id for i in ids])
    state=State([owner.id,ally.id])
    ctx={'state':state,'received_target_id':ally.id,'received_target_hp':80,'received_target_max_hp':100,'received_target_died':False,'received_target_damaged':True,'attacker_id':'enemy_1','skill_id':'enemy_skill_1'}
    g.after_received_attack(state,ctx)
    assert state.fighters[owner.id].resources['앙갚음 장부 [히스클리프]']==1
    assert state.enemy.statuses['복수 대상'].count==1

def test_middle_ally_death_adds_three_ledger():
    owner,ally=identities(); ids=[owner,ally]
    g=GimmickRegistry(ids,{i.id:i.passives for i in ids},[i.id for i in ids])
    state=State([owner.id,ally.id])
    skill=next(iter(owner.skills.values()))
    ctx={'state':state,'target_died':True,'target_id':ally.id,'actual_damage':10}
    g.after_skill(owner,skill,ctx)
    assert state.fighters[owner.id].resources['앙갚음 장부 [히스클리프]']==3


# ======================================================================
# 원본: test_v65_revenge_tattoo_transform.py
# ======================================================================

def _catalog():
    data=json.load(open('identity_catalog_v2.json',encoding='utf8'))['identities']
    return IdentityCatalogV29(data)

def test_revenge_tattoo_transforms_selected_basic_skill_to_execution():
    cat=_catalog(); ident=cat.build_identity('identity-10715')
    solver=OneTurnSolverV29(cat)
    fighter=FighterState(level=60,speed=5,sp=0,hp=100,max_hp=100,resources={'원한 문신':15})
    state=SimpleNamespace(fighters={ident.id:fighter}, event_log=[], statuses={}, runtime={})
    skill=ident.skills['S1']
    resolved, info=solver._resolve_skill_transformation(state,ident,skill,{'skill_id':'S1'},ResourceRuntime())
    assert resolved.name == '전원, 처형이다!!'
    assert info['reason'] == 'turn_start_revenge_tattoo'
    assert any(e.get('event')=='skill_transformed' for e in state.event_log)

def test_revenge_tattoo_transform_is_exposed_in_catalog_and_resource_name_is_supported():
    cat=_catalog(); ident=cat.build_identity('identity-10715')
    assert any(s.name == '전원, 처형이다!!' for s in ident.skills.values())
    assert '원한 문신' in ident.passives[0]['effect']


# ======================================================================
# 원본: test_v72_blade_lineage_module.py
# ======================================================================

def _ident(iid):
    data=json.load(open('identity_catalog_v2.json',encoding='utf-8'))['identities']
    return IdentityCatalogV29(data).build_identity(iid)

def _state(ids, hp=None, poise=None):
    from limbus_damage_engine_v29 import Status
    hp=hp or {}
    poise=poise or {}
    fighters={}
    for iid in ids:
        f=SimpleNamespace(hp=hp.get(iid,100), max_hp=100, resources={}, statuses={}, poise=Status())
        f.poise.potency=poise.get(iid,0)
        f.poise.count=poise.get((iid,'count'),0)
        fighters[iid]=f
    return SimpleNamespace(fighters=fighters,event_log=[],runtime={})

def test_blade_bonguk_start_targets_other_blade_members():
    boss=_ident('identity-10508')
    ally=_ident('identity-10103')
    g=GimmickRegistry([boss,ally], {boss.id:boss.passives, ally.id:ally.passives}, [boss.id,ally.id])
    assert any(r.kind=='blade_bonguk_start' for r in g.rules)
    st=_state([boss.id,ally.id])
    g.after_lifecycle_event(st, {'event':'battle_start','identity_id':boss.id}, {boss.id:boss,ally.id:ally}, 0)
    assert st.fighters[ally.id].statuses['본국검술'].count == 1
    assert '본국검술' not in st.fighters[boss.id].statuses

def test_blade_bonguk_poise_support_scales_at_six_members():
    boss=_ident('identity-10508')
    allies=[_ident(x) for x in ['identity-10103','identity-10208','identity-10308','identity-11002','identity-11102']]
    ids=[boss.id]+[x.id for x in allies]
    g=GimmickRegistry([boss,*allies], {x.id:x.passives for x in [boss,*allies]}, ids)
    st=_state(ids, poise={boss.id:0, **{x.id:i for i,x in enumerate(allies)}})
    ctx={'identity_id':boss.id,'actual_damage':10,'action_start_poise_potency':0,'action_start_poise_count':0,
         'action_end_poise_potency':1,'action_end_poise_count':1,'state':st,'available_identity_ids':ids}
    g.after_skill(boss, next(iter(boss.skills.values())), ctx)
    # Two lowest other blade members receive +2 potency/count because six are present.
    vals=sorted((st.fighters[x.id].poise.potency,x.id) for x in allies)
    assert [v[0] for v in vals[:2]] == [2,2]

def test_blade_boss_dead_threshold_adds_self_poise_bonus():
    boss=_ident('identity-10508')
    allies=[_ident(x) for x in ['identity-10103','identity-10208','identity-10308']]
    ids=[boss.id]+[x.id for x in allies]
    g=GimmickRegistry([boss,*allies], {x.id:x.passives for x in [boss,*allies]}, ids)
    st=_state(ids, hp={allies[0].id:0, allies[1].id:0, allies[2].id:0}, poise={boss.id:2})
    skill=next(iter(boss.skills.values()))
    ctx={'identity_id':boss.id,'actual_damage':10,'action_start_poise_potency':2,'action_start_poise_count':2,
         'action_end_poise_potency':3,'action_end_poise_count':3,'state':st,'available_identity_ids':ids}
    g.after_skill(boss,skill,ctx)
    assert st.fighters[boss.id].poise.potency == 3
    assert st.fighters[boss.id].poise.count == 1


# ======================================================================
# 원본: test_v74_blade_hongmaehwa_runtime.py
# ======================================================================
D=json.load(open('identity_catalog_v2.json',encoding='utf8'))['identities']
CAT=IdentityCatalogV29(D)

def ident(i): return CAT.build_identity(i)

def st(ids, hong=0, defense=0):
    fighters={}
    for iid in ids:
        fighters[iid]=SimpleNamespace(hp=100,max_hp=100,sp=0,resources={},statuses={},poise=Status())
    enemy=SimpleNamespace(hp=100,max_hp=100,statuses={},level=0,defense_level=0,defense_level_bonus=0)
    if hong:
        x=Status(); x.count=hong; x.potency=hong; enemy.statuses['홍매화']=x
    if defense:
        x=Status(); x.potency=defense; x.count=defense; enemy.statuses['Defense Level Down']=x
    return SimpleNamespace(fighters=fighters,enemy=enemy,event_log=[],runtime={})

def test_hongmaehwa_crit_adds_one_before_ten():
    a=ident('identity-10208')
    g=GimmickRegistry([a],{a.id:a.passives},[a.id])
    s=st([a.id],hong=4)
    g.after_coin(s,a,a.skills['S1'],0,10,is_crit=True)
    assert s.enemy.statuses['홍매화'].count==5
    assert s.enemy.statuses.get('Defense Level Down') is None

def test_hongmaehwa_ten_converts_crit_to_defense_down():
    a=ident('identity-10208')
    g=GimmickRegistry([a],{a.id:a.passives},[a.id])
    s=st([a.id],hong=10)
    g.after_coin(s,a,a.skills['S1'],0,10,is_crit=True)
    assert s.enemy.statuses['홍매화'].count==10
    assert s.enemy.statuses['Defense Level Down'].potency==1

def test_hongmaehwa_defense_down_caps_at_six():
    a=ident('identity-10208')
    g=GimmickRegistry([a],{a.id:a.passives},[a.id])
    s=st([a.id],hong=10,defense=6)
    for _ in range(3): g.after_coin(s,a,a.skills['S1'],0,10,is_crit=True)
    assert s.enemy.statuses['Defense Level Down'].potency==6


# ======================================================================
# 원본: test_v75_blade_survival_runtime.py
# ======================================================================

def _state__v75_blade(hp=100):
    f = FighterState(hp=hp, max_hp=hp)
    e = EnemyState(hp=100, max_hp=100)
    return BattleState(enemy=e, fighters={'blade': f})

def test_bonguk_fatal_damage_is_prevented_once_when_registered():
    st = _state__v75_blade(100)
    st.runtime['fatal_prevention'] = {'blade': 1}
    eng = DamageEngine()
    actual = eng.apply_ally_damage(st, 'blade', 150, 'enemy_attack')
    assert actual == 0
    assert st.fighters['blade'].hp == 1
    assert st.runtime['fatal_prevention']['blade'] == 0
    assert st.event_log[-1]['event'] == 'fatal_damage_prevented'

def test_bonguk_second_fatal_damage_is_not_prevented():
    st = _state__v75_blade(100)
    st.runtime['fatal_prevention'] = {'blade': 1}
    eng = DamageEngine()
    eng.apply_ally_damage(st, 'blade', 150, 'enemy_attack')
    actual = eng.apply_ally_damage(st, 'blade', 10, 'enemy_attack')
    assert actual == 1
    assert st.fighters['blade'].hp == 0
    assert st.event_log[-1]['event'] == 'ally_death'

def test_bonguk_status_grants_one_use_fatal_prevention():
    st = _state__v75_blade(100)
    st.fighters['blade'].statuses['본국검술'] = Status(potency=1, count=1, data={'fatal_prevention_once': True})
    eng = DamageEngine()
    actual = eng.apply_ally_damage(st, 'blade', 999, 'enemy_attack')
    assert actual == 0
    assert st.fighters['blade'].hp == 1
    assert st.fighters['blade'].statuses['본국검술'].data['fatal_prevention_used'] is True


# ======================================================================
# 원본: test_v75_blade_transfer_runtime.py
# ======================================================================

def ident__v75_blade(iid, name, speed):
    return SimpleNamespace(id=iid, name=name, full_name=name, affiliation=['BLADE LINEAGE'], skills={}, passives=[], speed=speed)

def test_blade_transfer_marks_slowest_members_and_six_member_boost():
    owner = ident__v75_blade('o', '검계 우두머리', 6)
    allies = [ident__v75_blade(str(i), f'검계{i}', i) for i in range(1, 7)]
    ids = [owner] + allies
    for x in ids:
        x.passives = []
    owner.passives = [{'type': '전투', 'name': '전수', 'effect': '[전투 시작시] 자신을 제외한 검계 조직원 (최대 완전 공명 수)명에게 속도가 느린 순으로 본국검 - 세법 전수 1 부여 (최대 2회)\n- 검계 조직원이 6명 이상 전투에 참여했으면, 대신 2 부여'}]
    g = GimmickRegistry(ids, {owner.id: owner.passives}, available_identity_ids=[x.id for x in ids])
    fighters = {x.id: SimpleNamespace(hp=100, statuses={}, resources={}, poise=Status(), speed=x.speed) for x in ids}
    state = SimpleNamespace(fighters=fighters, runtime={'max_resonance_count': 2}, event_log=[])
    g.after_lifecycle_event(state, {'event': 'battle_start', 'identity_id': owner.id}, {x.id: x for x in ids}, 0)
    assert fighters['1'].statuses['본국검 - 세법 전수'].count == 2
    assert fighters['2'].statuses['본국검 - 세법 전수'].count == 2
    assert '본국검 - 세법 전수' not in fighters['6'].statuses

# ======================================================================
# 0.7.48: Ring Finger bio-material cumulative conversion
# ======================================================================
def test_ring_finger_bio_material_cumulative_conversion_compiles_for_both_identities():
    cat=_catalog()
    for identity_id, expected_name in (('identity-10215','작품명: 파시아'), ('identity-10614','작품명: 티비아')):
        ident=cat.build_identity(identity_id)
        g=GimmickRegistry([ident], {ident.id: ident.passives}, [ident.id])
        rules=[r for r in g.rules if r.kind=='cumulative_resource_gain' and '생체 재료 횟수 10을 소모할 때마다' in r.source_text]
        assert len(rules)==1, (identity_id, [(r.kind,r.source_text) for r in g.rules])
        assert rules[0].skill_hint=='생체 재료'
        f=FighterState()
        st=BattleState(enemy=EnemyState(100,100), fighters={ident.id:f})
        st.runtime['resource_runtime']=ResourceRuntime()
        ev={'event':'resource_cumulative_consumed','identity_id':ident.id,'resource':'생체 재료','amount':10,
            'cumulative_before':0,'cumulative_after':10}
        g.after_resource_event(st,ev,{ident.id:ident},1)
        assert f.resources.get('생체 재료',0)==1
