import json
from pathlib import Path
from types import SimpleNamespace
from gimmick_modules.common import build_trigger
from trigger_rule_model_v1 import TriggerRule
from special_gimmick_v2 import GimmickRegistry
from limbus_damage_engine_v29 import DamageEngine, BattleState, FighterState, EnemyState, IdentityData, SkillData, CoinData, Status
from action_queue_v1 import ActionRequest


def test_10409_source_rule_is_identity_local_and_exact():
    d=json.load(open('identity_catalog_v2.json',encoding='utf8'))
    ident=next(x for x in d['identities'] if x['id']=='identity-10409')
    p=next(x for x in ident['passives'] if x['name']=='제.지')
    assert '자신을 제외한 아군의 공격으로 흐트러짐 상태가 된 적을 스킬 1로 공격함. (턴 당 1회)' in p['effect']
    assert '여러 적이 흐트러졌을 경우 체력이 가장 낮은 적' in p['effect']
    assert '해당 스킬의 마지막 코인 적중시 진동 폭발' in p['effect']


def test_10409_trigger_shape_is_ally_new_stagger_not_s1():
    r=SimpleNamespace(kind='ally_new_stagger_assist', owner_id='identity-10409', actor_hint='identity-10409', skill_hint='나사빠진 놈들', trigger_skill_names=())
    event,conds,effects=build_trigger(None,r)
    assert event=='after_skill'
    kinds=[c.type for c in conds]
    assert 'identity_id_not' in kinds
    assert 'newly_staggered' in kinds
    assert 'skill_slot' not in kinds
    assert effects[0].type=='support_action'
    assert effects[0].params['target_policy']=='lowest_hp_staggered'


def test_10409_generated_s1_gets_coin_tremor_count_plus_one_only():
    eng=DamageEngine()
    enemy=EnemyState(hp=100,max_hp=100,stagger_thresholds=[50])
    f=FighterState(hp=100,max_hp=100)
    state=BattleState(enemy=enemy,fighters={'identity-10409':f})
    state.runtime['current_action_request']=ActionRequest('identity-10409','1040901',1,generated=True,trigger_kind='ryoshu_10409_stagger_assist')
    state.runtime['_current_coin_effect_ctx']={'is_crit':False}
    eng.apply_effect(state,'identity-10409','self',{'type':'status','name':'Tremor','potency':0,'count':2})
    assert f.statuses['Tremor'].count==3
    state.runtime['current_action_request']=ActionRequest('identity-10409','1040901',1,generated=True,trigger_kind='other')
    eng.apply_effect(state,'identity-10409','self',{'type':'status','name':'Tremor','potency':0,'count':2})
    assert f.statuses['Tremor'].count==5


def test_10409_burst_has_no_implicit_count_cost():
    eng=DamageEngine()
    enemy=EnemyState(hp=100,max_hp=100,stagger_thresholds=[50])
    enemy.statuses['Tremor']=Status(potency=4,count=2)
    f=FighterState(hp=100,max_hp=100)
    state=BattleState(enemy=enemy,fighters={'identity-10409':f})
    eng.apply_effect(state,'identity-10409','enemy',{'type':'tremor_burst','name':'Tremor','target':'enemy','condition':None,'count_cost':0})
    assert enemy.statuses['Tremor'].count==2

def test_10409_live_rule_emits_support_s1_only_for_ally_new_stagger():
    import json
    from identity_catalog_v29 import IdentityCatalogV29
    from action_queue_v1 import ActionQueue
    D=json.load(open('identity_catalog_v2.json',encoding='utf8'))['identities']
    cat=IdentityCatalogV29(D)
    ry=cat.build_identity('identity-10409')
    ally=SimpleNamespace(id='ally-1', name='아군', full_name='아군', affiliation=[], keywords=[], resources=[], skills={})
    reg=GimmickRegistry([ry, ally], {ry.id:ry.passives, ally.id:[]}, available_identity_ids=[ally.id, ry.id])
    src=ActionRequest('ally-1','S1',1)
    q=ActionQueue([src])
    enemy=SimpleNamespace(hp=40,max_hp=100,staggered=True,stagger_level=1,stagger_index=1)
    state=SimpleNamespace(runtime={'action_queue':q,'current_action_request':src,'identity_map':{'identity-10409':ry,'ally-1':ally}},fighters={},enemy=enemy,event_log=[])
    out=reg.after_skill(ally, SimpleNamespace(id='S1',name='아군 S1',_slot='S1'), {
        'state':state,'action_index':1,'identity_id':'ally-1','skill_id':'S1','skill_name':'아군 S1','skill_slot':'S1',
        'action_start_staggered':False,'action_end_staggered':True,'newly_staggered':True,
        'available_identity_ids':['ally-1','identity-10409'],'target':enemy})
    generated=[x for x in q.items if x.generated]
    assert generated and generated[0].identity_id=='identity-10409'
    assert generated[0].skill_id=='1040901'
    assert generated[0].trigger_kind=='ryoshu_10409_stagger_assist'
    assert generated[0].target_policy=='lowest_hp_staggered'


def test_10409_rule_uses_generic_new_stagger_assist_runtime():
    from one_turn_solver_v29 import IdentityCatalogV29
    from special_gimmick_v2 import GimmickRegistry
    cat=IdentityCatalogV29.from_json(str(Path(__file__).parent/'identity_catalog_v2.json'))
    ry=cat.build_identity('identity-10409')
    reg=GimmickRegistry([ry], available_identity_ids=[ry.id])
    rules=[r for r in reg.rules if '자신을 제외한 아군의 공격으로 흐트러짐 상태가 된 적을' in r.source_text]
    assert rules and rules[0].kind == 'ally_new_stagger_assist'
    built=[r for r in reg.trigger_rules if r.source_text == rules[0].source_text]
    assert built and any(c.type == 'newly_staggered' for c in built[0].conditions)
    assert built[0].effects[0].params['trigger_kind'] == 'ryoshu_10409_stagger_assist'


def test_10409_does_not_fire_from_already_staggered_target():
    from types import SimpleNamespace
    from trigger_runtime_v1 import TriggerRuntime
    from gimmick_modules.common import build_trigger
    r=SimpleNamespace(kind='ally_new_stagger_assist', owner_id='identity-10409', actor_hint='identity-10409', skill_hint='나사빠진 놈들', trigger_skill_names=(), max_activations=1, activation_scope='global')
    event, conditions, effects = build_trigger(SimpleNamespace(_find_identity=lambda x: None, identities=[]), r)
    from trigger_rule_model_v1 import TriggerRule
    rule=TriggerRule('jiji','identity-10409',event,conditions,effects,1,0,'global')
    rt=TriggerRuntime([rule])
    ctx={'identity_id':'ally-1','action_start_staggered':True,'action_end_staggered':True,'newly_staggered':False}
    assert rt.fire('after_skill',ctx) == []
