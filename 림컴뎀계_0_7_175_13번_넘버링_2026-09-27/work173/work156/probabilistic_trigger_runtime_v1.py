"""Probability-branch trigger runtime without executing the retired TriggerRuntime.

This runtime accepts the existing TriggerRule-shaped objects for compatibility,
but owns event eligibility/activation for probabilistic branches itself. Generic
effects are executed through RuleMigrationRuntime; deferred effects are emitted
as the historical effect payload so the probabilistic solver can apply them.
"""
from __future__ import annotations
from typing import Any, Iterable

from condition_runtime_v1 import ConditionRuntime
from rule_ir_v1 import ConditionIR
from rule_migration_runtime_v1 import RuleMigrationRuntime
from activation_ledger_v1 import ActivationLedger


class ProbabilisticTriggerRuntime:
    def __init__(self, rules: Iterable[Any] = (), activation_ledger: ActivationLedger | None = None):
        self.rules = list(rules or [])
        self._migration = RuleMigrationRuntime()
        self.activation_ledger = activation_ledger or ActivationLedger()

    def bind_state(self, state: Any) -> None:
        ledger = getattr(state, "activation_ledger", None)
        if ledger is not None:
            self.activation_ledger = ledger

    def reset_turn(self):
        if self.activation_ledger is not None:
            self.activation_ledger.reset()

    @staticmethod
    def _conditions_met(rule, ctx):
        for condition in getattr(rule, "conditions", []) or []:
            raw = condition.to_dict() if hasattr(condition, "to_dict") else dict(condition)
            op = str(raw.pop("type", raw.pop("op", "unknown")))
            if not ConditionRuntime.evaluate(ConditionIR(op, raw), ctx):
                return False
        return True

    def _eligible(self, rule, ctx):
        if self.activation_ledger is not None:
            return self.activation_ledger.eligible(
                rule, ctx, turn_cap=getattr(rule, "metadata", {}).get("turn_cap")
            )
        return self.activation_ledger.eligible(
            rule, ctx, turn_cap=(getattr(rule, "metadata", {}) or {}).get("turn_cap")
        )

    def _consume(self, rule, ctx):
        if self.activation_ledger is not None:
            self.activation_ledger.consume(rule, ctx)
            return

    def fire(self, event: str, ctx: dict) -> list[dict]:
        ctx = dict(ctx or {})
        state = ctx.get("state")
        if state is not None:
            self.bind_state(state)
        out = []
        for rule in self.rules:
            if str(getattr(rule, "event", "")) != str(event):
                continue
            if not self._eligible(rule, ctx) or not self._conditions_met(rule, ctx):
                continue

            # Generic rules are executed through the common Rule IR boundary.
            safe, _ = self._migration.migration_safe(rule)
            if safe:
                rows = self._migration.fire_migrated([rule], event, ctx)
                out.extend(rows)
                continue

            # Specialized/deferred effects still need a branch-local event
            # payload, but must not invoke the retired TriggerRuntime.
            self._consume(rule, ctx)
            for effect in getattr(rule, "effects", []) or []:
                payload = effect.to_dict() if hasattr(effect, "to_dict") else dict(effect)
                out.append({
                    "rule_id": str(getattr(rule, "id", "")),
                    "owner_id": str(getattr(rule, "owner_id", "")),
                    "source_text": str(getattr(rule, "source_text", "")),
                    "effect": payload,
                    "activation": int(getattr(rule, "activations", 0)),
                    "metadata": dict(getattr(rule, "metadata", {}) or {}),
                    "probabilistic_deferred": True,
                })
        return out
