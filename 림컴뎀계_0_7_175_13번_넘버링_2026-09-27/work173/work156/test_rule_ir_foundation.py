"""병합 테스트: rule_ir_foundation

원본 파일 (내용은 AST 병합기로 합쳤고 테스트 본문은 바꾸지 않음):
  - test_v78_rule_ir_bridge.py
  - test_v79_condition_effect_ir.py
  - test_v80_rule_runtime.py
  - test_v81_target_effect_foundation.py
  - test_v82_rule_ir_migration.py
  - test_v83_activation_runtime.py
  - test_v84_effect_executor.py
  - test_v118_rule_ir_metadata.py
이름 충돌 helper 는 `이름__vNN` 으로 분리했다. 매핑은 tools/MERGE_MAP.json 참고.
"""
from rule_ir_bridge_v1 import trigger_rule_to_ir, gimmick_rule_to_ir
from trigger_runtime_v1 import TriggerRule, TriggerCondition, TriggerEffect
from special_gimmick_v2 import GimmickRule
from condition_runtime_v1 import ConditionRuntime
from effect_runtime_v1 import EffectRuntime, EffectCommand
from rule_ir_v1 import ConditionIR, EffectIR, RuleIR, TargetIR
from rule_runtime_v1 import RuleRuntime
from target_runtime_v1 import TargetRuntime
from rule_ir_migration_v1 import migration_report
from activation_runtime_v1 import ActivationRuntime
from dataclasses import dataclass, field
from effect_executor_v1 import EffectExecutor
from trigger_rule_model_v1 import (
    TriggerRule as TriggerRule__v118_rule,
    TriggerCondition as TriggerCondition__v118_rule,
    TriggerEffect as TriggerEffect__v118_rule,
)



# ======================================================================
# 원본: test_v78_rule_ir_bridge.py
# ======================================================================

def test_trigger_rule_bridge_preserves_core_fields():
    r = TriggerRule(
        "r1", "id1", "after_skill",
        [TriggerCondition("gte", 5, "x")],
        [TriggerEffect("damage_modifier", {"amount": 10})],
        2, 0, "global", {}, "source"
    )
    ir = trigger_rule_to_ir(r)
    assert ir.rule_id == "r1"
    assert ir.trigger == "after_skill"
    assert ir.conditions[0].op == "gte"
    assert ir.effects[0].kind == "damage_modifier"
    assert ir.activation_limit == 2

def test_gimmick_rule_bridge_is_loss_aware():
    r = GimmickRule("id1", "원문", "assist", ("S3",), "A", "S2", 1, 0,
                    False, False, 0.0, "per_skill", "pequod")
    ir = gimmick_rule_to_ir(r)
    assert ir.status == "legacy"
    assert ir.effects[0].kind == "legacy_gimmick"
    assert ir.effects[0].params["module"] == "pequod"
    assert ir.effects[0].params["skill_hint"] == "S2"


# ======================================================================
# 원본: test_v79_condition_effect_ir.py
# ======================================================================

def test_condition_ir_common_comparisons():
    ctx={'poise':7,'skill_slot':'S2','statuses':{'출혈':{'count':3}}}
    assert ConditionRuntime.evaluate(ConditionIR('gte',{'field':'poise','value':7}),ctx)
    assert ConditionRuntime.evaluate(ConditionIR('skill_slot',{'value':'S2'}),ctx)
    assert ConditionRuntime.evaluate(ConditionIR('status_count_gte',{'value':'출혈','threshold':3}),ctx)

def test_condition_ir_negation():
    assert not ConditionRuntime.evaluate(ConditionIR('equals',{'field':'x','value':1,'negate':True}),{'x':1})

def test_effect_runtime_unregistered_is_safe_command():
    rt=EffectRuntime(); out=rt.dispatch(EffectIR('damage_percent',{'amount':10}),{},'r1')
    assert isinstance(out,EffectCommand) and out.kind=='damage_percent' and out.rule_id=='r1'

def test_effect_runtime_registered_handler():
    rt=EffectRuntime(); rt.register('gain',lambda cmd,ctx: ctx.get('base',0)+cmd.params['amount'])
    assert rt.dispatch(EffectIR('gain',{'amount':2}),{'base':5})==7


# ======================================================================
# 원본: test_v80_rule_runtime.py
# ======================================================================

def test_rule_runtime_matches_and_emits_commands():
    rule=RuleIR('r1','id1','after_coin',
                 conditions=(ConditionIR('gte',{'field':'poise','value':5}),),
                 effects=(EffectIR('damage_percent',{'amount':10}),))
    out=RuleRuntime().evaluate(rule,{'poise':5})
    assert out.matched and out.reason=='matched'
    assert out.commands[0].kind=='damage_percent'

def test_rule_runtime_rejects_condition_without_side_effect():
    rule=RuleIR('r1','id1','after_coin',
                 conditions=(ConditionIR('gte',{'field':'poise','value':5}),),
                 effects=(EffectIR('damage_percent',{'amount':10}),))
    out=RuleRuntime().evaluate(rule,{'poise':4})
    assert not out.matched and out.commands==()

def test_disabled_rule_does_not_evaluate_conditions():
    rule=RuleIR('r1','id1','after_coin',status='disabled',effects=(EffectIR('x'),))
    out=RuleRuntime().evaluate(rule,{})
    assert not out.matched and out.reason=='disabled'


# ======================================================================
# 원본: test_v81_target_effect_foundation.py
# ======================================================================

def test_target_runtime_self_resolution():
    target = TargetIR(side='self', selector='self', count=1)
    out = TargetRuntime().resolve(target, {'actor': {'id':'a'}})
    assert out.resolved and out.targets[0]['id'] == 'a'

def test_target_runtime_affiliation_and_alive_filter():
    target = TargetIR(side='allies', selector='slowest', count=2,
                      filters={'affiliation':'blade_lineage', 'alive_only':True})
    ctx={'allies':[
        {'id':'a','speed':5,'hp':10,'affiliations':['blade_lineage']},
        {'id':'b','speed':2,'hp':10,'affiliations':['blade_lineage']},
        {'id':'c','speed':1,'hp':0,'affiliations':['blade_lineage']},
        {'id':'d','speed':3,'hp':10,'affiliations':['ring']},
    ]}
    out=TargetRuntime().resolve(target,ctx)
    assert [x['id'] for x in out.targets] == ['b','a']

def test_rule_runtime_requires_resolvable_target():
    rule=RuleIR('r','a','x',target=TargetIR(side='enemy',selector='lowest_hp'),effects=(EffectIR('damage_percent',{'amount':10}),))
    out=RuleRuntime().evaluate(rule,{'enemies':[]})
    assert not out.matched and out.reason=='no_candidates'

def test_effect_categories_are_explicit():
    rt=EffectRuntime()
    assert rt.category_for('damage_percent') == 'modifier'
    assert rt.category_for('resource_gain') == 'resource'
    assert rt.category_for('support_action') == 'action'
    assert rt.category_for('status_gain') == 'status'

def test_rule_dependency_execution_order_is_deterministic():
    from rule_ir_v1 import RuleDependencyGraph
    a=RuleIR('a','i','x')
    b=RuleIR('b','i','x',dependencies=('a',))
    c=RuleIR('c','i','x',dependencies=('b',))
    graph=RuleDependencyGraph([c,b,a])
    assert graph.execution_order() == ['a','b','c']
    assert graph.execution_order({'a'}) == ['b','c']

def test_rule_dependency_order_rejects_cycle_and_missing_dependency():
    from rule_ir_v1 import RuleDependencyGraph
    x=RuleIR('x','i','x',dependencies=('y',))
    y=RuleIR('y','i','x',dependencies=('x',))
    try:
        RuleDependencyGraph([x,y]).execution_order()
        assert False
    except ValueError as exc:
        assert 'cycle' in str(exc)
    z=RuleIR('z','i','x',dependencies=('missing',))
    try:
        RuleDependencyGraph([z]).execution_order()
        assert False
    except ValueError as exc:
        assert 'missing' in str(exc)


# ======================================================================
# 원본: test_v82_rule_ir_migration.py
# ======================================================================

def test_gimmick_bridge_uses_stable_id_and_common_conditions():
    r = GimmickRule("id1", "원문", "assist", ("S3",), "A", "S2", 1, 0, True, True, 0.0, "per_skill", "pequod")
    a = gimmick_rule_to_ir(r)
    b = gimmick_rule_to_ir(r)
    assert a.rule_id == b.rule_id
    assert {c.op for c in a.conditions} == {"action_start_not_staggered", "action_end_staggered", "skill_name_any", "actor_id", "skill_name_contains"}
    assert a.status == "legacy"

def test_migration_report_counts_compiled_rules():
    r = GimmickRule("id1", "원문", "assist")
    report = migration_report(gimmick_rules=[r])
    assert report["legacy_gimmick_rules"] == 1
    assert report["compiled_rules"] == 1
    assert report["compiled_effects"] == 1


# ======================================================================
# 원본: test_v83_activation_runtime.py
# ======================================================================

def test_activation_runtime_global_limit():
    r = RuleIR('r','i','x',activation_limit=1)
    rt = RuleRuntime()
    assert rt.evaluate(r, {}).matched
    assert rt.evaluate(r, {}).reason == 'activation_limit'
    rt.reset_turn()
    assert rt.evaluate(r, {}).matched

def test_activation_runtime_per_identity_scope():
    r = RuleIR('r','i','x',activation_limit=1, activation_scope='per_identity')
    a = ActivationRuntime()
    assert a.eligible(r, {'identity_id':'a'})
    a.consume(r, {'identity_id':'a'})
    assert not a.eligible(r, {'identity_id':'a'})
    assert a.eligible(r, {'identity_id':'b'})


# ======================================================================
# 원본: test_v84_effect_executor.py
# ======================================================================

@dataclass
class Fighter:
    id: str
    resources: dict = field(default_factory=dict)
    statuses: dict = field(default_factory=dict)

@dataclass
class State:
    runtime: dict = field(default_factory=dict)
    event_log: list = field(default_factory=list)

def test_generic_resource_effect_executes_through_rule_runtime():
    f=Fighter('a', {'charge': 2})
    s=State()
    r=RuleIR('r','a','x',effects=(EffectIR('resource_gain',{'resource':'charge','amount':3}),))
    ev,out=RuleRuntime().execute(r, {'actor':f,'state':s})
    assert ev.matched and f.resources['charge']==5

def test_generic_status_effect_executes():
    f=Fighter('a')
    r=RuleIR('r','a','x',effects=(EffectIR('status_gain',{'status':'poise','amount':2}),))
    _,out=RuleRuntime().execute(r, {'actor':f})
    assert f.statuses['poise']==2

def test_action_effect_remains_deferred():
    cmd=EffectRuntime().resolve(EffectIR('support_action',{'identity_id':'b'}),'','r')
    out=EffectExecutor().execute(cmd,{})
    assert out['deferred'] is True


# ======================================================================
# 원본: test_v118_rule_ir_metadata.py
# ======================================================================

def test_trigger_rule_metadata_survives_ir_bridge():
    rule = TriggerRule__v118_rule('metadata.cap', 'A', 'after_received_attack', [TriggerCondition__v118_rule('always')], [TriggerEffect__v118_rule('flag', {'key': 'probe', 'value': True})], 1, 0, 'per_target', {}, 'probe', {'turn_cap': 2})
    ir = trigger_rule_to_ir(rule)
    assert ir.metadata['turn_cap'] == 2

def test_per_target_activation_honors_turn_cap():
    rule = TriggerRule__v118_rule('metadata.cap', 'A', 'after_received_attack', [TriggerCondition__v118_rule('always')], [TriggerEffect__v118_rule('flag', {'key': 'probe', 'value': True})], 1, 0, 'per_target', {}, 'probe', {'turn_cap': 2})
    runtime = RuleRuntime()
    ir = trigger_rule_to_ir(rule)
    assert runtime.evaluate(ir, {'target_id': 't1'}).matched
    assert runtime.evaluate(ir, {'target_id': 't2'}).matched
    assert not runtime.evaluate(ir, {'target_id': 't3'}).matched
