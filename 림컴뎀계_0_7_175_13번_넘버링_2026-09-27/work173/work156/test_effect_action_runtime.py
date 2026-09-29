"""병합 테스트: effect_action_runtime

원본 파일 (내용은 AST 병합기로 합쳤고 테스트 본문은 바꾸지 않음):
  - test_v96_queue_action_effect_runtime.py
  - test_v97_queue_action_registry_integration.py
  - test_v99_targeted_effect_runtime.py
  - test_v100_generic_special_effects.py
  - test_v100_special_effect_generic_runtime.py
이름 충돌 helper 는 `이름__vNN` 으로 분리했다. 매핑은 tools/MERGE_MAP.json 참고.
"""
from types import SimpleNamespace
from action_queue_v1 import ActionQueue
from effect_runtime_v1 import EffectRuntime, EffectCommand
from rule_ir_v1 import EffectIR
from effect_executor_v1 import EffectExecutor
from trigger_runtime_v1 import TriggerRule, TriggerEffect, TriggerCondition
from rule_migration_runtime_v1 import RuleMigrationRuntime
from limbus_damage_engine_v29 import BattleState, EnemyState, FighterState, Status
from special_gimmick_v2 import GimmickRegistry
from affiliation_runtime_v1 import AffiliationResolver
from rule_runtime_v1 import RuleRuntime



# ======================================================================
# 원본: test_v96_queue_action_effect_runtime.py
# ======================================================================

def _ident(iid='B'):
    skill = SimpleNamespace(id='B1', name='B S1', _slot='S1')
    return SimpleNamespace(id=iid, skills={'B1': skill})

def test_queue_action_is_generic_and_materializes_into_shared_queue():
    source = ActionQueue.from_scenario([{'identity_id': 'A', 'skill_id': 'A1'}]).pop()
    queue = ActionQueue.from_scenario([{'identity_id': 'A', 'skill_id': 'A1'}])
    # Re-create a source that is already a popped action so insertion occurs at
    # the current cursor, matching real combat execution.
    source = queue.pop()
    ctx = {
        'action_queue': queue,
        'source_action': source,
        'identity_id': 'A',
        'rule_owner_id': 'B',
        'identity_map': {'A': _ident('A'), 'B': _ident('B')},
        'event': 'after_skill',
    }
    command = EffectRuntime().resolve(EffectIR('queue_action', {'identity_id': 'B', 'skill_name': 'B S1', 'trigger_kind': 'assist'}), ctx, 'r1')
    result = EffectExecutor().execute(command, ctx)
    assert result['queued'] is True
    assert queue.items[queue.position].generated is True
    assert queue.items[queue.position].identity_id == 'B'
    assert queue.items[queue.position].skill_id == 'B1'

def test_queue_action_without_live_queue_is_deferred_and_does_not_consume_activation():
    rule = TriggerRule('r1', 'A', 'after_skill', [], [TriggerEffect('queue_action', {'identity_id': 'B', 'skill_name': 'B S1'})], 1)
    rule.consume = lambda ctx: (_ for _ in ()).throw(AssertionError('activation must not be consumed'))
    actor = SimpleNamespace(id='A')
    out = RuleMigrationRuntime().fire_migrated([rule], 'after_skill', {'actor': actor, 'identity_id': 'A'})
    assert out[0]['migration_execution_deferred'] is True
    assert out[0]['execution_result']['reason'] == 'missing_action_queue_context'


# ======================================================================
# 원본: test_v97_queue_action_registry_integration.py
# ======================================================================

def _identity(iid, name):
    skill = SimpleNamespace(id=f'{iid}-S1', name='가척아원[加斥我援]', _slot='S1')
    return SimpleNamespace(id=iid, name=name, full_name=name, skills={skill.id: skill})

def test_registry_migrated_queue_action_uses_turnstate_queue_boundary():
    a = _identity('A', 'A')
    b = _identity('B', '홍원 방랑무사')
    reg = GimmickRegistry(
        [a, b], available_identity_ids=['A', 'B'],
        extra_trigger_rules=[{
            'id': 'queue-registry', 'owner_id': 'A', 'event': 'after_skill',
            'conditions': [{'type': 'always'}],
            'effects': [{'type': 'queue_action', 'identity_id': '홍원 방랑무사',
                         'skill_name': '가척아원[加斥我援]', 'trigger_kind': 'assist'}],
            'max_activations': 1,
        }],
    )
    state = BattleState(EnemyState(100, 100), {'A': FighterState(), 'B': FighterState()})
    q = ActionQueue.from_scenario([{'identity_id': 'A', 'skill_id': 'A-S1'}, {'identity_id': 'B', 'skill_id': 'B-S1'}])
    source = q.pop()
    state.runtime['action_queue'] = q
    state.runtime['current_action_request'] = source
    state.runtime['identity_map'] = {'A': a, 'B': b}
    out = reg.after_skill(a, a.skills['A-S1'], {'state': state, 'identity_id': 'A', 'actor': state.fighters['A']})
    assert out == []
    assert q.items[q.position].generated is True
    assert q.items[q.position].identity_id == 'B'
    assert q.items[q.position].skill_id == 'B-S1'


# ======================================================================
# 원본: test_v99_targeted_effect_runtime.py
# ======================================================================

def _state(ids):
    fighters={}
    for iid, hp, poise in ids:
        f=FighterState(hp=hp, max_hp=100, resources={"충전": poise})
        f.charge = poise
        f.poise.potency=poise
        f.poise.count=poise
        fighters[iid]=f
    return BattleState(EnemyState(1000,1000), fighters)

def _ctx(state, owner, identities=None):
    identities=identities or []
    return {"state":state,"identity_id":owner,"rule_owner_id":owner,
            "available_identity_ids":list(state.fighters),
            "identity_map":{str(x.id):x for x in identities},
            "affiliation_resolver":AffiliationResolver(identities,list(state.fighters))}

def test_lowest_ally_poise_preserves_formation_tiebreak_and_count():
    state=_state([("A",100,5),("B",100,0),("C",100,0)])
    r=EffectExecutor().execute(EffectCommand("poise_gain_lowest_ally",{"owner_id":"A","amount":1,"use_count":True},"r","status"),_ctx(state,"A"))
    assert r["target"]=="B"
    assert state.fighters["B"].poise.potency==1
    assert state.fighters["B"].poise.count==1

def test_lowest_affiliation_poise_selects_lowest_and_boosts_at_member_threshold():
    ids=[SimpleNamespace(id="A",affiliation=["BLADE LINEAGE"]),SimpleNamespace(id="B",affiliation=["BLADE LINEAGE"]),SimpleNamespace(id="C",affiliation=["BLADE LINEAGE"]),SimpleNamespace(id="D",affiliation=["BLADE LINEAGE"]),SimpleNamespace(id="E",affiliation=["BLADE LINEAGE"]),SimpleNamespace(id="F",affiliation=["BLADE LINEAGE"])]
    state=_state([("A",100,5),("B",100,1),("C",100,0),("D",100,2),("E",100,3),("F",100,4)])
    r=EffectExecutor().execute(EffectCommand("poise_gain_lowest_affiliation",{"owner_id":"A","affiliation":"BLADE LINEAGE","exclude_owner":True,"count":2,"amount":1,"amount_high":2,"member_count_threshold":6,"use_count":True},"r","status"),_ctx(state,"A",ids))
    assert r["targets"]==["C","B"]
    assert state.fighters["C"].poise.potency==2
    assert state.fighters["B"].poise.potency==3

def test_resource_lowest_allies_includes_owner_and_uses_charge_value():
    state=_state([("A",100,10),("B",100,2),("C",100,5)])
    r=EffectExecutor().execute(EffectCommand("resource_gain_lowest_allies",{"owner_id":"A","resource":"충전","amount_base":2,"amount_resource":"충전","count":1},"r","resource"),_ctx(state,"A"))
    assert r["targets"]==["A","B"]
    assert state.fighters["A"].charge==22
    assert state.fighters["B"].charge==14

def test_heal_lowest_ally_caps_at_max_hp():
    state=_state([("A",100,5),("B",20,0),("C",40,0)])
    r=EffectExecutor().execute(EffectCommand("heal_lowest_ally",{"amount":15},"r","status"),_ctx(state,"A"))
    assert r["target"]=="B"
    assert state.fighters["B"].hp==35


# ======================================================================
# 원본: test_v100_generic_special_effects.py
# ======================================================================

def _ctx__v100_generic():
    ids = [type('I', (), {'id': 'a', 'affiliation': ['BLADE LINEAGE']})(), type('I', (), {'id': 'b', 'affiliation': ['BLADE LINEAGE']})()]
    fighters = {'a': FighterState(hp=100, max_hp=100), 'b': FighterState(hp=100, max_hp=100)}
    fighters['a'].sp = 10
    fighters['b'].sp = 20
    state = BattleState(EnemyState(1000, 1000), fighters)
    return (state, {'state': state, 'identity_id': 'b', 'rule_owner_id': 'a', 'available_identity_ids': ['a', 'b'], 'affiliation_resolver': AffiliationResolver(ids, ['a', 'b'])})

def test_support_poise_gain_generic_uses_highest_sp_target():
    state, ctx = _ctx__v100_generic()
    ex = EffectExecutor()
    result = ex.execute(EffectRuntime().resolve(EffectIR('support_poise_gain', {'target_policy': 'highest_sp', 'amount': 2, 'use_count': False}), ctx, 'r1'), ctx)
    assert result['applied'] is True
    assert state.fighters['b'].poise.potency == 2

def test_support_poise_count_bonus_generic_targets_current_actor():
    state, ctx = _ctx__v100_generic()
    ex = EffectExecutor()
    result = ex.execute(EffectRuntime().resolve(EffectIR('support_poise_count_bonus', {'amount': 1}), ctx, 'r2'), ctx)
    assert result['applied'] is True
    assert state.fighters['b'].poise.count == 1

def test_fatal_prevention_and_highest_poise_modifier_are_generic():
    state, ctx = _ctx__v100_generic()
    ex = EffectExecutor()
    ex.execute(EffectRuntime().resolve(EffectIR('register_fatal_prevention', {'identity_id': 'a', 'uses': 1}), ctx, 'r3'), ctx)
    assert state.runtime['fatal_prevention']['a'] == 1
    state.fighters['b'].poise.potency = 7
    ex.execute(EffectRuntime().resolve(EffectIR('register_damage_modifier_highest_poise', {'affiliation': 'BLADE LINEAGE', 'amount': 0.15, 'kind': 'critical_damage_percent'}), ctx, 'r4'), ctx)
    mods = state.runtime.get('damage_modifiers', [])
    assert any((str(m.get('target_identity_id')) == 'b' for m in mods))

def test_status_gain_affiliation_generic_targets_live_members():
    state, ctx = _ctx__v100_generic()
    ex = EffectExecutor()
    result = ex.execute(EffectRuntime().resolve(EffectIR('status_gain_affiliation', {'affiliation': 'BLADE LINEAGE', 'status': '본국검술', 'amount': 1, 'exclude_owner': True, 'owner_id': 'a'}), ctx, 'r5'), ctx)
    assert result['applied'] is True
    assert state.fighters['b'].statuses['본국검술'].count == 1
    assert '본국검술' not in state.fighters['a'].statuses


# ======================================================================
# 원본: test_v100_special_effect_generic_runtime.py
# ======================================================================

def _state__v100_special():
    enemy = SimpleNamespace(id='enemy_1', hp=100, statuses={})
    return SimpleNamespace(enemy=enemy, fighters={}, runtime={}, event_log=[], turn_damage=0)

def test_hongmaehwa_crit_executes_through_generic_effect_executor():
    state = _state__v100_special()
    hm = Status()
    hm.count = 4
    hm.potency = 4
    state.enemy.statuses['홍매화'] = hm
    rule = TriggerRule('hong-generic', 'identity-10208', 'after_coin', conditions=[TriggerCondition('is_crit', True)], effects=[TriggerEffect('hongmaehwa_crit', {'threshold': 10, 'hongmaehwa_amount': 1, 'hongmaehwa_cap': 3, 'defense_down_amount': 1, 'defense_down_cap': 6})], max_activations=1)
    out = RuleRuntime().execute_trigger_rules([rule], 'after_coin', {'state': state, 'identity_id': 'identity-10208', 'is_crit': True})
    assert state.enemy.statuses['홍매화'].count == 5
    assert out

def test_enemy_status_count_gain_executes_through_generic_effect_executor():
    state = _state__v100_special()
    rule = TriggerRule('enemy-status-generic', 'middle', 'after_received_attack', conditions=[TriggerCondition('always')], effects=[TriggerEffect('enemy_status_count_gain', {'status': '복수 대상', 'amount': 1})], max_activations=1)
    out = RuleRuntime().execute_trigger_rules([rule], 'after_received_attack', {'state': state, 'attacker_id': 'enemy_1', 'identity_id': 'middle'})
    assert state.enemy.statuses['복수 대상'].count == 1
    assert out


def test_bare_highest_poise_modifier_can_select_by_count():
    state, ctx = _ctx__v100_generic()
    state.fighters['a'].poise.potency = 10
    state.fighters['a'].poise.count = 1
    state.fighters['b'].poise.potency = 3
    state.fighters['b'].poise.count = 5
    ex = EffectExecutor()
    ex.execute(EffectRuntime().resolve(EffectIR('register_damage_modifier_highest_poise', {'affiliation': 'BLADE LINEAGE', 'amount': 0.15, 'kind': 'critical_damage_percent', 'metric':'count'}), ctx, 'r-count'), ctx)
    mods=state.runtime.get('damage_modifiers',[])
    assert any(str(m.get('target_identity_id'))=='b' for m in mods)


def test_plain_lowest_hp_heal_uses_current_hp_not_hp_ratio():
    state, ctx = _ctx__v100_generic()
    state.fighters['a'].hp=40; state.fighters['a'].max_hp=100
    state.fighters['b'].hp=50; state.fighters['b'].max_hp=200
    ex=EffectExecutor()
    r=ex.execute(EffectCommand('heal_lowest_ally',{'amount':5},'r-heal','status'),ctx|{'identity_id':'a'})
    assert r['target']=='a'
