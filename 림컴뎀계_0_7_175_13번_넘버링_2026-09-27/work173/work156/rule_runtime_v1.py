"""Execution shell for the common Rule IR."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict, List
from condition_runtime_v1 import ConditionRuntime
from activation_runtime_v1 import ActivationRuntime
from effect_runtime_v1 import EffectCommand, EffectRuntime
from rule_ir_v1 import RuleIR
from rule_ir_bridge_v1 import trigger_rule_to_ir
from target_runtime_v1 import TargetResolution, TargetRuntime
from effect_executor_v1 import EffectExecutor

@dataclass(frozen=True)
class RuleEvaluation:
    rule_id: str
    matched: bool
    reason: str
    commands: tuple[EffectCommand, ...] = ()
    target: TargetResolution | None = None

class RuleRuntime:
    def __init__(self, effect_runtime: EffectRuntime | None = None, target_runtime: TargetRuntime | None = None, activation_runtime: ActivationRuntime | None = None, effect_executor: EffectExecutor | None = None):
        self.effects = effect_runtime or EffectRuntime()
        self.targets = target_runtime or TargetRuntime()
        self.activations = activation_runtime or ActivationRuntime()
        self.executor = effect_executor or EffectExecutor()

    def reset_turn(self) -> None:
        self.activations.reset()

    def bind_state(self, state: Any) -> None:
        """Bind production activation ownership to the current TurnState."""
        ledger = getattr(state, "activation_ledger", None)
        if ledger is not None:
            self.activations.bind(ledger)

    def evaluate(self, rule: RuleIR, ctx: Dict[str, Any]) -> RuleEvaluation:
        state = ctx.get("state") if isinstance(ctx, dict) else None
        if state is not None:
            self.bind_state(state)
        if rule.status == 'disabled':
            return RuleEvaluation(rule.rule_id, False, 'disabled')
        if not self.activations.eligible(rule, ctx):
            return RuleEvaluation(rule.rule_id, False, 'activation_limit')
        if not ConditionRuntime.all(rule.conditions, ctx):
            return RuleEvaluation(rule.rule_id, False, 'condition_failed')
        target = self.targets.resolve(rule.target, ctx) if rule.target else None
        if target is not None and not target.resolved:
            return RuleEvaluation(rule.rule_id, False, target.reason, (), target)
        commands = tuple(self.effects.resolve(e, ctx, rule.rule_id) for e in rule.effects)
        self.activations.consume(rule, ctx)
        return RuleEvaluation(rule.rule_id, True, 'matched', commands, target)

    def execute(self, rule: RuleIR, ctx: Dict[str, Any]) -> tuple[RuleEvaluation, list[Any]]:
        """Evaluate and concretely execute generic effects; specialized actions stay deferred."""
        evaluation = self.evaluate(rule, ctx)
        if not evaluation.matched:
            return evaluation, []
        exec_ctx = dict(ctx, target=(evaluation.target.targets[0] if evaluation.target and evaluation.target.targets else ctx.get("target")))
        if rule.target is not None:
            exec_ctx["target_side"] = rule.target.side
        results = self.executor.execute_all(evaluation.commands, exec_ctx)
        # A rule with only deferred effects did not actually execute.  Restore
        # its activation reservation so compatibility/unit callers can retry
        # once a live ActionQueue context is available.
        if results and all(isinstance(result, dict) and result.get("deferred") for result in results):
            self.activations.release(rule, exec_ctx)
        return evaluation, results

    def evaluate_all(self, rules: List[RuleIR], ctx: Dict[str, Any]) -> List[RuleEvaluation]:
        return [self.evaluate(r, ctx) for r in rules]

    def execute_legacy_rules(self, rules: List[Any], event: str, ctx: Dict[str, Any], *, require_generic: bool = True) -> List[Any]:
        """Execute legacy-shaped rules through the single common RuleRuntime path.

        Legacy objects are treated only as an input representation.  Evaluation,
        activation accounting, target resolution, command construction, and
        concrete effect execution all delegate to ``evaluate``/``execute`` so
        there is no second copy of the engine hidden behind the migration
        boundary.  ``require_generic`` is a migration safety gate, not a
        separate execution implementation.
        """
        out: List[Any] = []
        for legacy in rules:
            if str(getattr(legacy, "event", "")) != str(event):
                continue
            ir = trigger_rule_to_ir(legacy)
            if require_generic and not all(self.effects.is_generic_executable(e.kind) for e in ir.effects):
                for effect in getattr(legacy, "effects", []) or []:
                    out.append({"rule_id": legacy.id, "owner_id": legacy.owner_id,
                                "source_text": legacy.source_text, "effect": effect.to_dict(),
                                "activation": getattr(legacy, "activations", 0),
                                "metadata": dict(getattr(legacy, "metadata", {}) or {}),
                                "migration_deferred": True})
                continue

            exec_ctx = dict(ctx)
            exec_ctx["rule_owner_id"] = str(getattr(legacy, "owner_id", ""))
            evaluation, results = self.execute(ir, exec_ctx)
            if not evaluation.matched:
                if evaluation.reason in {"target_unresolved", "target_not_found", "no_candidates", "selector_or_filter_no_match"}:
                    for effect in getattr(legacy, "effects", []) or []:
                        marker = {"rule_id": legacy.id, "owner_id": legacy.owner_id,
                                  "source_text": legacy.source_text,
                                  "effect": effect.to_dict(),
                                  "activation": getattr(legacy, "activations", 0),
                                  "metadata": dict(getattr(legacy, "metadata", {}) or {}),
                                  "migration_target_unresolved": True,
                                  "migration_target_reason": evaluation.reason}
                        out.append(marker)
                    # Target failure is observable even when the caller is not
                    # using a UI trace. Do not consume the activation budget.
                    log = getattr(ctx.get("state"), "event_log", None)
                    if isinstance(log, list):
                        log.append({"event": "migration_target_unresolved",
                                    "rule_id": legacy.id,
                                    "owner_id": legacy.owner_id,
                                    "reason": evaluation.reason,
                                    "source_text": legacy.source_text})
                continue

            # ``execute`` owns activation consumption. Keep the legacy object's
            # counter synchronized only when the compatibility object exposes a
            # historical consume() surface; this is accounting, not execution.
            deferred = any(isinstance(result, dict) and result.get("deferred") for result in results)
            if callable(getattr(legacy, "consume", None)) and not (results and all(isinstance(result, dict) and result.get("deferred") for result in results)):
                legacy.consume(exec_ctx)

            for effect, result in zip(getattr(legacy, "effects", []) or [], results):
                entry = {"rule_id": legacy.id, "owner_id": legacy.owner_id,
                         "source_text": legacy.source_text, "effect": effect.to_dict(),
                         "activation": getattr(legacy, "activations", 0),
                         "metadata": dict(getattr(legacy, "metadata", {}) or {}),
                         "execution_result": result}
                if deferred:
                    entry["migration_execution_deferred"] = True
                else:
                    entry["executed_generic"] = True
                out.append(entry)
        return out

    def execute_trigger_rules(self, rules: List[Any], event: str, ctx: Dict[str, Any], *, legacy_fallback: bool = False) -> List[Any]:
        """Execute legacy TriggerRule objects through the common Rule IR boundary.

        Generic effects are concretely executed here. Effects that still belong
        to specialized legacy runtimes are returned as deferred commands/results
        when ``legacy_fallback`` is False; with the explicit ``legacy_fallback=True`` opt-in, callers can temporarily preserve
        the old TriggerRuntime behavior for those effects.
        """
        results: List[Any] = []
        for legacy in rules:
            if str(getattr(legacy, "event", "")) != str(event):
                continue
            rule = trigger_rule_to_ir(legacy)
            evaluation, executed = self.execute(rule, ctx)
            if evaluation.matched:
                results.extend(executed)
            elif not evaluation.matched and legacy_fallback:
                # Do not silently mutate the legacy object here; the caller can
                # continue using TriggerRuntime for rules that are not yet IR-safe.
                continue
        return results
