"""Migration planning and safe execution helpers for legacy trigger rules.

The planner does not guess semantics. It only measures whether a legacy rule
can cross the Rule IR boundary using the currently implemented generic
Condition/Target/Effect runtimes.  Specialized effects remain explicitly
classified as deferred.
"""
from __future__ import annotations
from collections import Counter
from dataclasses import dataclass, asdict
from typing import Any, Iterable, List

from rule_ir_bridge_v1 import trigger_rule_to_ir
from effect_runtime_v1 import EffectRuntime
from condition_runtime_v1 import ConditionRuntime
from rule_ir_v1 import ConditionIR
from rule_runtime_v1 import RuleRuntime


@dataclass(frozen=True)
class RuleMigrationRecord:
    rule_id: str
    event: str
    effects: int
    generic_effects: int
    deferred_effects: int
    unknown_effects: int
    status: str


class RuleMigrationRuntime:
    """Measure and execute the subset of legacy rules that is already generic.

    Migration safety is stricter than effect-category membership: every IR
    condition operator must also be implemented by the common condition runtime.
    """

    SUPPORTED_CONDITIONS = ConditionRuntime.SUPPORTED_OPS

    @classmethod
    def condition_safety(cls, rule):
        unsupported = tuple(sorted({str(c.op) for c in rule.conditions if str(c.op) not in cls.SUPPORTED_CONDITIONS}))
        return (not unsupported, unsupported)

    def migration_safe(self, legacy):
        ir = trigger_rule_to_ir(legacy)
        condition_ok, unsupported = self.condition_safety(ir)
        effect_ok = all(self._effect_state(e.kind) == "generic" for e in ir.effects)
        reasons = []
        if not effect_ok:
            reasons.append("deferred_effect")
        reasons.extend(f"unsupported_condition:{x}" for x in unsupported)
        return effect_ok and condition_ok, tuple(reasons)

    def __init__(self, rule_runtime: RuleRuntime | None = None):
        self.runtime = rule_runtime or RuleRuntime()

    def reset_turn(self) -> None:
        """Reset activation state owned by the production RuleRuntime."""
        self.runtime.reset_turn()

    @staticmethod
    def _effect_state(kind: str) -> str:
        category = EffectRuntime.category_for(kind)
        if category in {"state", "resource", "status", "modifier", "action"}:
            # Category membership is intentionally not enough: some entries
            # are still specialized even though they live in a generic bucket.
            if EffectRuntime.is_generic_executable(kind):
                return "generic"
            return "deferred"
        if category == "unknown":
            return "unknown"
        return "deferred"

    def analyze(self, rules: Iterable[Any]) -> dict:
        records: List[RuleMigrationRecord] = []
        effect_counts = Counter()
        state_counts = Counter()
        unsafe_condition_counts = Counter()
        for legacy in rules:
            rule = trigger_rule_to_ir(legacy)
            states = [self._effect_state(e.kind) for e in rule.effects]
            _, unsupported_conditions = self.condition_safety(rule)
            for op in unsupported_conditions:
                unsafe_condition_counts[op] += 1
            for e, state in zip(rule.effects, states):
                effect_counts[e.kind] += 1
                state_counts[state] += 1
            if not states:
                status = "generic"
            elif all(s == "generic" for s in states):
                status = "generic"
            elif any(s == "unknown" for s in states):
                status = "unknown"
            else:
                status = "deferred"
            records.append(RuleMigrationRecord(
                rule_id=rule.rule_id,
                event=rule.trigger,
                effects=len(states),
                generic_effects=states.count("generic"),
                deferred_effects=states.count("deferred"),
                unknown_effects=states.count("unknown"),
                status=status,
            ))
        total = len(records)
        return {
            "total_rules": total,
            "fully_generic_rules": sum(r.status == "generic" for r in records),
            "deferred_rules": sum(r.status == "deferred" for r in records),
            "unknown_rules": sum(r.status == "unknown" for r in records),
            "effect_state_counts": dict(state_counts),
            "effect_kind_counts": dict(effect_counts),
            "unsupported_condition_counts": dict(unsafe_condition_counts),
            "records": [asdict(r) for r in records],
        }

    def partition(self, rules: Iterable[Any], event: str) -> tuple[list[Any], list[Any]]:
        """Partition an event into IR-owned rules and legacy-only rules.

        This is the single migration boundary used by production callers.
        A rule that is migration-safe is never returned in the legacy bucket.
        """
        safe, deferred = [], []
        for rule in rules:
            if str(getattr(rule, "event", "")) != str(event):
                continue
            ok, _ = self.migration_safe(rule)
            (safe if ok else deferred).append(rule)
        return safe, deferred

    def production_fire(self, rules: Iterable[Any], event: str, ctx: dict) -> tuple[list[dict], int]:
        """Execute the production IR boundary without a legacy execution hop.

        Production callers must not silently fall back to ``TriggerRuntime``.
        Deferred rules are reported to the caller as a migration boundary error;
        the compatibility runtime remains available only to explicit legacy/test
        callers.  This makes accidental reintroduction of Legacy execution a
        fail-fast condition instead of a hidden performance/maintenance cost.
        """
        safe, deferred = self.partition(rules, event)
        if deferred:
            ids = tuple(str(getattr(r, "id", "")) for r in deferred)
            raise RuntimeError(
                f"production Rule IR boundary received deferred rules for {event}: {ids}"
            )
        fired = self.fire_migrated(safe, event, ctx) if safe else []
        # In a real production combat context an ActionQueue is the authoritative
        # execution boundary.  If a generic effect could not execute there, do
        # not silently hand it back to special_gimmick_v2 for manual handling.
        # Compatibility callers without a live queue are still allowed to
        # receive the historical deferred payload (for isolated/unit tests).
        if ctx.get("action_queue") is not None:
            deferred = [x for x in fired if x.get("migration_execution_deferred")]
            if deferred:
                ids = tuple(str(x.get("rule_id", "")) for x in deferred)
                raise RuntimeError(
                    f"production Rule IR execution deferred inside live ActionQueue context for {event}: {ids}"
                )
        return fired, 0

    def fire_migrated(self, rules: Iterable[Any], event: str, ctx: dict) -> list[dict]:
        """Delegate migrated execution to the common RuleRuntime boundary.

        RuleMigrationRuntime remains responsible for classification and safety
        checks; it no longer owns a second copy of Condition/Target/Effect
        execution semantics.
        """
        selected = []
        for legacy in rules:
            if str(getattr(legacy, "event", "")) != str(event):
                continue
            generic, _reasons = self.migration_safe(legacy)
            if generic:
                selected.append(legacy)
            else:
                for effect in getattr(legacy, "effects", []) or []:
                    selected.append(legacy)
                    break
        return self.runtime.execute_legacy_rules(selected, event, ctx, require_generic=True)

    def execute_generic(self, rules: Iterable[Any], event: str, ctx: dict) -> list[Any]:
        """Execute only rules whose every effect is already generic-safe.

        This is deliberately opt-in. Existing callers can continue using the
        legacy TriggerRuntime until parity/golden tests exist for a rule.
        """
        selected = []
        for legacy in rules:
            if str(getattr(legacy, "event", "")) != str(event):
                continue
            ir = trigger_rule_to_ir(legacy)
            if all(EffectRuntime.is_generic_executable(e.kind) for e in ir.effects):
                selected.append(legacy)
        return self.runtime.execute_trigger_rules(selected, event, ctx, legacy_fallback=False)
