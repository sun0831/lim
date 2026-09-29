"""병합 테스트: rule_migration

원본 파일 (내용은 AST 병합기로 합쳤고 테스트 본문은 바꾸지 않음):
  - test_v85_rule_runtime_trigger_migration.py
  - test_v86_rule_migration_runtime.py
  - test_v87_migration_parity.py
  - test_v88_rule_migration_execution.py
  - test_v89_migration_safety.py
  - test_v91_rule_migration_integration.py
  - test_v92_probabilistic_rule_ir_migration.py
  - test_v92_production_migration_boundary.py
  - test_v93_golden_rule_parity.py
이름 충돌 helper 는 `이름__vNN` 으로 분리했다. 매핑은 tools/MERGE_MAP.json 참고.
"""
from rule_runtime_v1 import RuleRuntime
from trigger_runtime_v1 import TriggerRule, TriggerCondition, TriggerEffect
from rule_migration_runtime_v1 import RuleMigrationRuntime
from migration_parity_runtime_v1 import MigrationParityRuntime
from dataclasses import dataclass, field
from limbus_damage_engine_v29 import (
    Status,
    BattleState,
    EnemyState,
    FighterState,
    IdentityData,
    SkillData,
    CoinData,
)
from special_gimmick_v2 import GimmickRegistry
from one_turn_solver_v29 import OneTurnSolverV29
from probabilistic_trigger_runtime_v1 import ProbabilisticTriggerRuntime
from golden_rule_parity_v1 import assert_golden



# ======================================================================
# 원본: test_v85_rule_runtime_trigger_migration.py
# ======================================================================

class Fighter:
    def __init__(self):
        self.id = 'A'
        self.resources = {}
        self.statuses = {}

def test_trigger_rule_generic_resource_executes_through_ir():
    f = Fighter()
    r = TriggerRule(
        'r1', 'A', 'skill_end',
        conditions=[TriggerCondition('always')],
        effects=[TriggerEffect('resource_gain', {'resource': 'charge', 'amount': 3})],
        max_activations=1,
    )
    out = RuleRuntime().execute_trigger_rules([r], 'skill_end', {'actor': f, 'identity_id': 'A'})
    assert f.resources['charge'] == 3
    assert len(out) == 1

def test_trigger_rule_generic_status_executes_through_ir():
    f = Fighter()
    r = TriggerRule(
        'r2', 'A', 'skill_end',
        conditions=[TriggerCondition('always')],
        effects=[TriggerEffect('status_gain', {'status': 'poise', 'amount': 2})],
        max_activations=1,
    )
    RuleRuntime().execute_trigger_rules([r], 'skill_end', {'actor': f, 'identity_id': 'A'})
    assert f.statuses['poise'] == 2

def test_trigger_rule_wrong_event_does_not_execute():
    f = Fighter()
    r = TriggerRule('r3', 'A', 'turn_start', effects=[TriggerEffect('resource_gain', {'resource': 'charge', 'amount': 9})])
    out = RuleRuntime().execute_trigger_rules([r], 'skill_end', {'actor': f, 'identity_id': 'A'})
    assert out == []
    assert f.resources == {}


# ======================================================================
# 원본: test_v86_rule_migration_runtime.py
# ======================================================================

def test_migration_planner_separates_generic_and_deferred_effects():
    rules = [
        TriggerRule('r1', 'A', 'skill_end', [TriggerCondition('always')],
                    [TriggerEffect('resource_gain', {'resource': 'charge', 'amount': 2})]),
        TriggerRule('r2', 'A', 'skill_end', [TriggerCondition('always')],
                    [TriggerEffect('queue_action', {'skill_name': 'S1'})]),
    ]
    report = RuleMigrationRuntime().analyze(rules)
    assert report['total_rules'] == 2
    assert report['fully_generic_rules'] == 2
    assert report['deferred_rules'] == 0
    assert report['effect_state_counts']['generic'] == 2
    assert report['effect_state_counts'].get('deferred', 0) == 0

def test_execute_generic_reports_action_rules_as_runtime_deferred_without_queue():
    f = Fighter()
    rules = [
        TriggerRule('r1', 'A', 'skill_end', [TriggerCondition('always')],
                    [TriggerEffect('resource_gain', {'resource': 'charge', 'amount': 2})]),
        TriggerRule('r2', 'A', 'skill_end', [TriggerCondition('always')],
                    [TriggerEffect('queue_action', {'skill_name': 'S1'})]),
    ]
    out = RuleMigrationRuntime().execute_generic(
        rules, 'skill_end', {'actor': f, 'identity_id': 'A'}
    )
    assert f.resources['charge'] == 2
    assert out[0] == 2
    assert out[1]['deferred'] is True
    assert out[1]['reason'] == 'missing_action_queue_context'


# ======================================================================
# 원본: test_v87_migration_parity.py
# ======================================================================

def test_parity_preserves_effect_payload():
    rule = TriggerRule(
        'r1', 'A', 'skill_end', [TriggerCondition('always')],
        [TriggerEffect('resource_gain', {'resource': 'charge', 'amount': 2})],
    )
    row = MigrationParityRuntime().compare(rule)
    assert row.status == 'exact'
    assert row.effects_match is True
    assert row.ir_effects == ({'type': 'resource_gain', 'resource': 'charge', 'amount': 2},)

def test_parity_audit_counts_exact_rules():
    rules = [
        TriggerRule('r1', 'A', 'skill_end', [], [TriggerEffect('status_gain', {'status': 'bleed', 'amount': 2})]),
        TriggerRule('r2', 'A', 'skill_end', [], [TriggerEffect('queue_action', {'skill_name': 'S1'})]),
    ]
    report = MigrationParityRuntime().audit(rules)
    assert report['total_rules'] == 2
    assert report['exact_rules'] == 2
    assert report['loss_rules'] == 0
    assert report['exact_ratio'] == 1.0

def test_evaluate_parity_does_not_execute_effect():
    rule = TriggerRule(
        'r1', 'A', 'skill_end', [TriggerCondition('always')],
        [TriggerEffect('resource_gain', {'resource': 'charge', 'amount': 2})],
    )
    out = MigrationParityRuntime().evaluate_parity(rule, {'identity_id': 'A'})
    assert out['ir_matched'] is True
    assert out['effects_match'] is True


# ======================================================================
# 원본: test_v88_rule_migration_execution.py
# ======================================================================

@dataclass
class Fighter__v88_rule:
    id: str
    resources: dict = field(default_factory=dict)
    statuses: dict = field(default_factory=dict)
    charge: int = 0
    ammo: int = 0

@dataclass
class Enemy:
    hp: int = 100
    statuses: dict = field(default_factory=dict)

@dataclass
class State:
    fighters: dict
    enemy: Enemy = field(default_factory=Enemy)
    runtime: dict = field(default_factory=dict)
    event_log: list = field(default_factory=list)
    turn_damage: int = 0

def test_migrated_resource_gain_updates_core_charge_not_legacy_resource_dict():
    f = Fighter__v88_rule('A', charge=2)
    state = State({'A': f})
    rule = TriggerRule('r', 'A', 'after_kill', [TriggerCondition('always')], [TriggerEffect('resource_gain', {'resource': '충전', 'amount': 3})])
    out = RuleMigrationRuntime().fire_migrated([rule], 'after_kill', {'actor': f, 'identity_id': 'A', 'state': state})
    assert out[0]['executed_generic'] is True
    assert f.charge == 5
    assert f.resources.get('충전', 0) == 0

def test_migrated_forsight_consume_preserves_overheat_transition():
    f = Fighter__v88_rule('A', resources={'예지안': 1})
    state = State({'A': f})
    rule = TriggerRule('r', 'A', 'after_clash', [TriggerCondition('always')], [TriggerEffect('resource_consume', {'resource': '예지안', 'amount': 1, 'overheat_at_zero': True})])
    RuleMigrationRuntime().fire_migrated([rule], 'after_clash', {'actor': f, 'identity_id': 'A', 'state': state})
    assert f.resources['예지안'] == 0
    assert f.resources['예지안 과열'] == 1

def test_migrated_extra_damage_scale_matches_legacy_timing_shape():
    f = Fighter__v88_rule('A')
    state = State({'A': f}, enemy=Enemy(hp=100))
    rule = TriggerRule('r', 'A', 'after_coin', [TriggerCondition('always')], [TriggerEffect('extra_damage_scale', {'scale': 0.5})])
    out = RuleMigrationRuntime().fire_migrated([rule], 'after_coin', {'actor': f, 'identity_id': 'A', 'state': state, 'actual_damage': 11, 'skill_id': 'S1', 'coin_index': 1})
    assert out[0]['executed_generic'] is True
    assert state.enemy.hp == 94
    assert state.turn_damage == 6

def test_migrated_status_potency_damage_uses_turn_cap():
    f = Fighter__v88_rule('A')
    enemy = Enemy(hp=100, statuses={'Burn': Status(potency=8, count=5)})
    state = State({'A': f}, enemy=enemy)
    rule = TriggerRule('r', 'A', 'after_coin', [TriggerCondition('always')], [TriggerEffect('status_potency_damage', {'status': 'Burn', 'max_per_coin': 10, 'turn_cap': 20})])
    out = RuleMigrationRuntime().fire_migrated([rule], 'after_coin', {'actor': f, 'identity_id': 'A', 'state': state, 'skill_id': 'S1', 'coin_index': 1, 'reuse_index': 1})
    assert out[0]['executed_generic'] is True
    assert state.enemy.hp == 92
    assert state.turn_damage == 8


# ======================================================================
# 원본: test_v89_migration_safety.py
# ======================================================================

class Fighter__v89_migration:

    def __init__(self, fid):
        self.id = fid
        self.resources = {}
        self.statuses = {}

class State__v89_migration:

    def __init__(self, fighters):
        self.fighters = fighters
        self.runtime = {}
        self.event_log = []

def test_migration_uses_rule_owner_for_untargeted_resource_effect():
    owner = Fighter__v89_migration('owner')
    actor = Fighter__v89_migration('actor')
    state = State__v89_migration({'owner': owner, 'actor': actor})
    rule = TriggerRule('r', 'owner', 'after_coin', [TriggerCondition('actual_damage_gt_zero')], [TriggerEffect('resource_gain', {'resource': '생체 재료', 'amount': 2})])
    out = RuleMigrationRuntime().fire_migrated([rule], 'after_coin', {'actor': actor, 'identity_id': 'actor', 'state': state, 'actual_damage': 5})
    assert out[0]['executed_generic'] is True
    assert owner.resources['생체 재료'] == 2 and actor.resources == {}

def test_unsupported_condition_is_not_migration_safe():
    f = Fighter__v89_migration('A')
    state = State__v89_migration({'A': f})
    rule = TriggerRule('r', 'A', 'skill_end', [TriggerCondition('not_yet_supported')], [TriggerEffect('resource_gain', {'resource': 'charge', 'amount': 2})])
    safe, reasons = RuleMigrationRuntime().migration_safe(rule)
    assert safe is False
    assert 'unsupported_condition:not_yet_supported' in reasons
    out = RuleMigrationRuntime().fire_migrated([rule], 'skill_end', {'actor': f, 'identity_id': 'A', 'state': state})
    assert out == []
    assert f.resources == {}

def test_target_resolution_failure_does_not_consume_activation():
    f = Fighter__v89_migration('A')
    state = State__v89_migration({'A': f})
    rule = TriggerRule('r', 'A', 'skill_end', [], [TriggerEffect('resource_gain', {'resource': 'charge', 'amount': 2})], max_activations=1)
    rule.metadata['target'] = {'side': 'ally', 'selector': 'explicit', 'count': 1, 'filters': {'target_ids': ['missing']}}
    out = RuleMigrationRuntime().fire_migrated([rule], 'skill_end', {'actor': f, 'identity_id': 'A', 'state': state})
    assert out and out[0].get('migration_target_unresolved') is True


# ======================================================================
# 원본: test_v91_rule_migration_integration.py
# ======================================================================

def _identity(iid='A'):
    s = SkillData('s1', '테스트', 5, [CoinData(1, 'slash', 'lust')], 'slash', 'lust')
    s._slot = 'S1'
    return IdentityData(iid, '테스트', 0, {'S1': s}, [])

def test_registry_executes_migration_safe_resource_rule_once():
    a = _identity('A'); b = _identity('B')
    state = BattleState(EnemyState(100, 100), {'A': FighterState(), 'B': FighterState()})
    reg = GimmickRegistry([a, b], {'A': [], 'B': []}, available_identity_ids=['A', 'B'], extra_trigger_rules=[{
        'id': 'generic_gain', 'owner_id': 'A', 'event': 'after_coin',
        'conditions': [{'type': 'actual_damage_gt_zero'}],
        'effects': [{'type': 'resource_gain', 'resource': '생체 재료', 'amount': 2}],
    }])
    reg.after_coin(state, b, b.skills['S1'], 1, 5)
    assert state.fighters['A'].resources.get('생체 재료', 0) == 2
    assert state.fighters['B'].resources.get('생체 재료', 0) == 0

def test_registry_executes_migration_safe_extra_damage_and_returns_amount():
    a = _identity('A')
    state = BattleState(EnemyState(100, 100), {'A': FighterState()})
    reg = GimmickRegistry([a], {'A': []}, available_identity_ids=['A'], extra_trigger_rules=[{
        'id': 'generic_extra', 'owner_id': 'A', 'event': 'after_coin',
        'conditions': [{'type': 'actual_damage_gt_zero'}],
        'effects': [{'type': 'extra_damage_scale', 'scale': 0.5}],
    }])
    extra = reg.after_coin(state, a, a.skills['S1'], 1, 11)
    assert extra == 6
    assert state.enemy.hp == 94
    assert state.turn_damage == 6


# ======================================================================
# 원본: test_v92_probabilistic_rule_ir_migration.py
# ======================================================================

def _state():
    return BattleState(EnemyState(100, 100), {'A': FighterState(), 'B': FighterState()})

def test_probabilistic_event_uses_rule_ir_for_generic_effect_once():
    rule = TriggerRule(
        'r1', 'A', 'after_coin',
        [TriggerCondition('actual_damage_gt_zero')],
        [TriggerEffect('resource_gain', {'resource': 'Charge', 'amount': 2})],
        1,
    )
    runtime = ProbabilisticTriggerRuntime([rule])
    state = _state()
    solver = OneTurnSolverV29()
    fired = solver._fire_probabilistic_trigger_event(
        runtime, 'after_coin',
        {'identity_id': 'A', 'actual_damage': 10, 'skill_id': 'S1', 'skill_name': 'S1'},
        state,
    )
    assert fired and all(x.get('executed_generic') for x in fired)
    assert state.fighters['A'].resources.get('Charge', 0) == 2
    assert state.activation_ledger.counts == {'r1': 1}

def test_probabilistic_scoped_activation_state_preserves_bucket_across_branch_event():
    rule = TriggerRule(
        'r2', 'A', 'after_coin',
        [],
        [TriggerEffect('resource_gain', {'resource': 'Charge', 'amount': 1})],
        1, activation_scope='per_skill',
    )
    runtime = ProbabilisticTriggerRuntime([rule])
    state = _state()
    solver = OneTurnSolverV29()
    ctx = {'identity_id': 'A', 'skill_id': 'S1', 'skill_name': 'S1', 'actual_damage': 1}
    solver._fire_probabilistic_trigger_event(runtime, 'after_coin', ctx, state)
    assert state.fighters['A'].resources.get('Charge', 0) == 1
    # The same scoped skill is no longer eligible, but another skill is.
    solver._fire_probabilistic_trigger_event(runtime, 'after_coin', ctx, state)
    assert state.fighters['A'].resources.get('Charge', 0) == 1
    ctx2 = dict(ctx, skill_id='S2', skill_name='S2')
    solver._fire_probabilistic_trigger_event(runtime, 'after_coin', ctx2, state)
    assert state.fighters['A'].resources.get('Charge', 0) == 2


# ======================================================================
# 원본: test_v92_production_migration_boundary.py
# ======================================================================

class DummyQueue:
    pass

def _rule(effect):
    return TriggerRule(
        'boundary_rule', 'A', 'after_coin',
        [TriggerCondition('actual_damage_gt_zero', {})],
        [TriggerEffect(effect['type'], {k: v for k, v in effect.items() if k != 'type'})],
        1, 0, 'global', {}, 'boundary', {}
    )

def test_production_boundary_rejects_deferred_effect_inside_live_queue():
    # support/queue effects need a source action to materialize.  A live queue
    # without that source must fail fast rather than falling back to the bridge.
    rt = RuleMigrationRuntime()
    rule = _rule({'type': 'support_action', 'source_identity_id': 'A'})
    try:
        rt.production_fire([rule], 'after_coin', {
            'actual_damage': 5,
            'action_queue': DummyQueue(),
            'source_action': None,
            'identity_map': {},
        })
    except RuntimeError as exc:
        assert 'production Rule IR execution deferred' in str(exc)
    else:
        raise AssertionError('live production context must not silently defer to legacy')

def test_compatibility_context_may_still_return_deferred_payload():
    rt = RuleMigrationRuntime()
    rule = _rule({'type': 'support_action', 'source_identity_id': 'A'})
    fired, fallback = rt.production_fire([rule], 'after_coin', {
        'actual_damage': 5,
        'action_queue': None,
        'source_action': None,
        'identity_map': {},
    })
    assert fallback == 0
    assert fired and fired[0].get('migration_execution_deferred') is True


# ======================================================================
# 원본: test_v93_golden_rule_parity.py
# ======================================================================

def _ctx():
    state = BattleState(EnemyState(100, 100), {"A": FighterState(), "B": FighterState()})
    return {"actor": state.fighters["A"], "identity_id": "A", "state": state,
            "actual_damage": 7, "skill_id": "S1", "target_id": "B"}

def _rule__v93_golden(effect, conditions=None, scope='global', max_activations=1):
    return TriggerRule('golden', 'A', 'after_coin', conditions or [TriggerCondition('actual_damage_gt_zero')], [effect], max_activations, 0, scope, {}, 'golden', {})

def test_resource_gain_golden_parity():
    assert_golden(_rule__v93_golden(TriggerEffect('resource_gain', {'resource': '충전', 'amount': 2})), _ctx())

def test_status_gain_golden_parity():
    assert_golden(_rule__v93_golden(TriggerEffect('status_gain', {'status': '출혈', 'amount': 2})), _ctx())

def test_modifier_golden_parity():
    assert_golden(_rule__v93_golden(TriggerEffect('damage_percent', {'amount': 0.1})), _ctx())

def test_flag_golden_parity():
    assert_golden(_rule__v93_golden(TriggerEffect('set_flag', {'flag': 'golden_flag', 'value': True})), _ctx())

def test_scoped_activation_golden_parity():
    rule = _rule__v93_golden(TriggerEffect('resource_gain', {'resource': '충전', 'amount': 1}), scope='per_identity', max_activations=2)
    ctx = _ctx()
    assert_golden(rule, ctx)

def test_failed_condition_does_not_consume_activation():
    rule = _rule__v93_golden(TriggerEffect('resource_gain', {'resource': '충전', 'amount': 1}), conditions=[TriggerCondition('equals', value='never', field='identity_id')])
    result = assert_golden(rule, _ctx())
    assert result.legacy_activation['activations'] == 0
    assert result.migrated_activation['activations'] == 0
