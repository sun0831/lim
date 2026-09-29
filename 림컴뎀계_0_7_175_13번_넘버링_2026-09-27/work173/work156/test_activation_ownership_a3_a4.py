"""A3/A4 activation ownership regression tests.

These tests verify the architectural boundary after legacy activation counters
and Solver Ledger<->TriggerRule sync/restore mirrors are removed.
"""
from activation_ledger_v1 import ActivationLedger
from activation_runtime_v1 import ActivationRuntime
from rule_ir_v1 import RuleIR
from trigger_rule_model_v1 import TriggerRule
from probabilistic_trigger_runtime_v1 import ProbabilisticTriggerRuntime
from one_turn_solver_v29 import OneTurnSolverV29


def test_trigger_rule_is_definition_only_for_activation_state():
    rule = TriggerRule("a3", "A", "e", max_activations=1, activation_scope="per_target")
    assert not hasattr(rule, "activations")
    assert not hasattr(rule, "activation_buckets")


def test_activation_runtime_uses_ledger_as_single_state_owner():
    ledger = ActivationLedger()
    runtime = ActivationRuntime(ledger)
    rule = RuleIR("a3-runtime", "A", "e", activation_limit=1, activation_scope="per_target")
    ctx = {"identity_id": "A", "target_id": "T1"}
    assert runtime.ledger is ledger
    assert runtime.eligible(rule, ctx)
    runtime.consume(rule, ctx)
    assert ledger.snapshot() == {"counts": {"a3-runtime": 1}, "buckets": {"a3-runtime\x1fT1": 1}}
    assert not runtime.eligible(rule, ctx)


def test_activation_runtime_has_no_duplicate_scope_key_implementation():
    assert not hasattr(ActivationRuntime, "_scope_key")


def test_probabilistic_runtime_does_not_write_activation_state_to_rule():
    rule = TriggerRule("a3-prob", "A", "e", max_activations=1)
    ledger = ActivationLedger()
    runtime = ProbabilisticTriggerRuntime([rule], ledger)
    assert runtime._eligible(rule, {"identity_id": "A"})
    runtime._consume(rule, {"identity_id": "A"})
    assert ledger.total_count(rule) == 1
    assert not hasattr(rule, "activations")
    assert not hasattr(rule, "activation_buckets")


def test_solver_no_longer_exposes_activation_sync_restore_mirrors():
    assert not hasattr(OneTurnSolverV29, "_sync_probabilistic_trigger_activation_state")
    assert not hasattr(OneTurnSolverV29, "_restore_probabilistic_trigger_activation_state")


def test_rule_definition_to_dict_contains_no_runtime_activation_counters():
    rule = TriggerRule("a3-dict", "A", "e", max_activations=1, activation_scope="global")
    payload = rule.to_dict()
    assert "activations" not in payload
    assert "activation_buckets" not in payload
