"""Non-mutating parity helpers for Legacy TriggerRule -> Rule IR migration.

The parity layer deliberately compares normalized rule semantics only. It does
not execute either side, so it can be used before a rule is migrated into the
live combat path.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Any, Iterable

from rule_ir_bridge_v1 import trigger_rule_to_ir
from rule_runtime_v1 import RuleRuntime
from rule_ir_v1 import RuleIR


@dataclass(frozen=True)
class RuleParityResult:
    rule_id: str
    event: str
    legacy_effects: tuple[dict, ...]
    ir_effects: tuple[dict, ...]
    conditions: tuple[dict, ...]
    target: dict | None
    effects_match: bool
    status: str
    reason: str = ""


class MigrationParityRuntime:
    """Compare legacy and IR representations without changing combat state."""

    @staticmethod
    def _legacy_effects(rule: Any) -> tuple[dict, ...]:
        out = []
        for effect in getattr(rule, "effects", []) or []:
            if hasattr(effect, "to_dict"):
                out.append(dict(effect.to_dict()))
            elif isinstance(effect, dict):
                out.append(dict(effect))
            else:
                out.append({"type": str(effect)})
        return tuple(out)

    @staticmethod
    def _ir_effects(rule: RuleIR) -> tuple[dict, ...]:
        return tuple({"type": e.kind, **dict(e.params)} for e in rule.effects)

    @staticmethod
    def _conditions(rule: RuleIR) -> tuple[dict, ...]:
        return tuple({"type": c.op, **dict(c.args)} for c in rule.conditions)

    @staticmethod
    def _target(rule: RuleIR) -> dict | None:
        if rule.target is None:
            return None
        return {
            "side": rule.target.side,
            "selector": rule.target.selector,
            "count": rule.target.count,
            "filters": dict(rule.target.filters),
        }

    def compare(self, legacy: Any) -> RuleParityResult:
        ir = trigger_rule_to_ir(legacy)
        legacy_effects = self._legacy_effects(legacy)
        ir_effects = self._ir_effects(ir)
        match = legacy_effects == ir_effects
        if match:
            status, reason = "exact", "effect payload preserved"
        else:
            status, reason = "loss", "legacy effect payload differs after IR normalization"
        return RuleParityResult(
            rule_id=ir.rule_id,
            event=ir.trigger,
            legacy_effects=legacy_effects,
            ir_effects=ir_effects,
            conditions=self._conditions(ir),
            target=self._target(ir),
            effects_match=match,
            status=status,
            reason=reason,
        )

    def audit(self, rules: Iterable[Any]) -> dict:
        rows = [self.compare(r) for r in rules]
        exact = sum(r.status == "exact" for r in rows)
        return {
            "total_rules": len(rows),
            "exact_rules": exact,
            "loss_rules": len(rows) - exact,
            "exact_ratio": (exact / len(rows)) if rows else 1.0,
            "records": [asdict(r) for r in rows],
        }

    def evaluate_parity(self, legacy: Any, ctx: dict) -> dict:
        """Compare match/condition/target decisions without executing effects."""
        ir = trigger_rule_to_ir(legacy)
        runtime = RuleRuntime()
        evaluation = runtime.evaluate(ir, ctx)
        # Legacy eligibility/condition evaluation is intentionally delegated to
        # TriggerRuntime in the live path; this method reports only IR-side
        # evaluation plus representation parity, avoiding state mutation.
        row = self.compare(legacy)
        return {
            "rule_id": row.rule_id,
            "ir_matched": evaluation.matched,
            "ir_reason": evaluation.reason,
            "effects_match": row.effects_match,
            "representation": row.status,
        }
