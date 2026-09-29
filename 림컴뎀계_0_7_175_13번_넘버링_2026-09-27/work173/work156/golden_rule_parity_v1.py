"""Golden parity harness for migration-safe TriggerRule -> Rule IR rules.

The legacy runtime is effect-producing while the migrated runtime may also
mutate state.  Therefore the authoritative parity surface here is:
- eligibility / fired rule identity
- effect payload (what the rule asked the engine to do)
- activation budget / scope state
- migration safety classification

State mutation is separately checked through the migrated executor result when
an explicit golden case declares an expected post-state projection.
"""
from __future__ import annotations
from copy import deepcopy
from dataclasses import dataclass, asdict
from typing import Any, Callable, Dict

from trigger_runtime_v1 import TriggerRuntime, TriggerRule
from activation_ledger_v1 import ActivationLedger
from activation_runtime_v1 import ActivationRuntime
from rule_migration_runtime_v1 import RuleMigrationRuntime
from rule_ir_bridge_v1 import trigger_rule_to_ir


def _effect_payload(rows):
    return [dict(r.get("effect", {})) for r in rows]


def _activation(ledger, rule):
    rid = str(getattr(rule, "id", getattr(rule, "rule_id", "")))
    return {
        "activations": int(ledger.total_count(rule)),
        "buckets": {str(key): int(value) for (br, key), value in ledger.buckets.items() if str(br) == rid},
    }


@dataclass(frozen=True)
class GoldenParity:
    rule_id: str
    event: str
    safe: bool
    reasons: tuple[str, ...]
    legacy_effects: tuple[dict, ...]
    migrated_effects: tuple[dict, ...]
    legacy_activation: dict
    migrated_activation: dict
    effects_match: bool
    activation_match: bool
    ok: bool


def compare_rule(rule: TriggerRule, ctx: Dict[str, Any]) -> GoldenParity:
    migrated_ledger = ActivationLedger()
    migration = RuleMigrationRuntime(rule_runtime=__import__('rule_runtime_v1', fromlist=['RuleRuntime']).RuleRuntime(activation_runtime=ActivationRuntime(migrated_ledger)))
    safe, reasons = migration.migration_safe(rule)
    if not safe:
        return GoldenParity(rule.id, rule.event, False, tuple(reasons), (), (), {}, {}, False, False, False)

    legacy_rule = deepcopy(rule)
    migrated_rule = deepcopy(rule)
    legacy_ledger = ActivationLedger()
    legacy_rows = TriggerRuntime([legacy_rule], legacy_ledger).fire(rule.event, deepcopy(ctx))
    migrated_rows = migration.fire_migrated([migrated_rule], rule.event, deepcopy(ctx))

    le = tuple(_effect_payload(legacy_rows))
    me = tuple(_effect_payload(migrated_rows))
    la = _activation(legacy_ledger, legacy_rule)
    ma = _activation(migration.runtime.activations.ledger, migrated_rule)
    effects_match = le == me
    activation_match = la == ma
    return GoldenParity(
        rule.id, rule.event, True, (), le, me, la, ma,
        effects_match, activation_match, effects_match and activation_match,
    )


def assert_golden(rule: TriggerRule, ctx: Dict[str, Any]) -> GoldenParity:
    result = compare_rule(rule, ctx)
    assert result.safe, f"rule is not migration-safe: {result.rule_id}: {result.reasons}"
    assert result.effects_match, f"effect parity failed: {asdict(result)}"
    assert result.activation_match, f"activation parity failed: {asdict(result)}"
    return result
