"""C 단계: RuleIR execution boundary 계약 테스트.

Production boundary와 temporary parallel parity audit을 분리해서 고정한다.
이 테스트는 RuleIR이 실제 Damage Engine까지 완전히 연결됐다고 주장하지 않는다.
"""
from copy import deepcopy

import pytest

from activation_ledger_v1 import ActivationLedger
from golden_rule_parity_v1 import compare_rule
from rule_migration_runtime_v1 import RuleMigrationRuntime
from rule_runtime_v1 import RuleRuntime
from trigger_rule_model_v1 import TriggerCondition, TriggerEffect, TriggerRule
from trigger_runtime_v1 import TriggerRuntime


def _generic(effect_type="resource_gain", payload=None):
    return TriggerRule(
        "c.boundary",
        "A",
        "after_coin",
        [TriggerCondition("actual_damage_gt_zero")],
        [TriggerEffect(effect_type, payload or {"resource": "charge", "amount": 1})],
        1,
        0,
        "global",
        {},
        "C boundary",
        {},
    )


def test_c_production_boundary_is_ir_only_for_migration_safe_rule(monkeypatch):
    rule = _generic()

    def fail(*args, **kwargs):
        raise AssertionError("production C boundary entered TriggerRuntime")

    monkeypatch.setattr(TriggerRuntime, "fire", fail)
    fired, legacy_count = RuleMigrationRuntime().production_fire(
        [rule], "after_coin", {"actual_damage": 3, "identity_id": "A"}
    )
    assert legacy_count == 0
    assert fired and fired[0]["rule_id"] == "c.boundary"


def test_c_production_boundary_fails_fast_for_deferred_rule():
    rule = _generic("not_a_generic_effect", {"x": 1})
    with pytest.raises(RuntimeError, match="deferred rules"):
        RuleMigrationRuntime().production_fire(
            [rule], "after_coin", {"actual_damage": 3, "identity_id": "A"}
        )


def test_c_parallel_audit_compares_legacy_and_ir_on_separate_state():
    rule = _generic()
    result = compare_rule(rule, {"actual_damage": 3, "identity_id": "A"})
    assert result.safe
    assert result.effects_match
    assert result.activation_match
    assert result.ok


def test_c_parallel_audit_uses_independent_rule_copies():
    rule = _generic()
    original = deepcopy(rule)
    result = compare_rule(rule, {"actual_damage": 3, "identity_id": "A"})
    assert result.ok
    # A3 contract: activation is not stored on the definition object.
    assert rule.to_dict() == original.to_dict()
    assert not hasattr(rule, "activations")
    assert not hasattr(rule, "activation_buckets")


def test_c_rule_runtime_owns_ledger_for_live_state():
    rule = _generic()
    ir = __import__("rule_ir_bridge_v1", fromlist=["trigger_rule_to_ir"]).trigger_rule_to_ir(rule)
    rt = RuleRuntime()
    ev, _ = rt.execute(ir, {"actual_damage": 3, "identity_id": "A"})
    assert ev.matched
    assert isinstance(rt.activations.ledger, ActivationLedger)
    assert rt.activations.ledger.total_count(ir) == 1
