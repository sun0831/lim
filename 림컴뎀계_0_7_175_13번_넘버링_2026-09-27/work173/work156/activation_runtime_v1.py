"""Common activation-budget runtime for Rule IR.

Activation is separated from condition/effect semantics so once-per-turn,
per-identity, per-skill, and per-target limits can be reused by migrated rules
without duplicating counters in every gimmick module.
"""
from __future__ import annotations
from typing import Any, Dict
from rule_ir_v1 import RuleIR
from activation_ledger_v1 import ActivationLedger


class ActivationRuntime:
    def __init__(self, ledger: ActivationLedger | None = None):
        self.ledger = ledger or ActivationLedger()
        # Compatibility views; production ownership is the ledger.
        self.counts = self.ledger.counts
        self.buckets = self.ledger.buckets

    def bind(self, ledger: ActivationLedger) -> None:
        self.ledger = ledger
        self.counts = ledger.counts
        self.buckets = ledger.buckets

    def reset(self) -> None:
        self.ledger.reset()

    def eligible(self, rule: RuleIR, ctx: Dict[str, Any]) -> bool:
        turn_cap = (getattr(rule, "metadata", {}) or {}).get("turn_cap")
        return self.ledger.eligible(rule, ctx, turn_cap=turn_cap)

    def consume(self, rule: RuleIR, ctx: Dict[str, Any]) -> None:
        self.ledger.consume(rule, ctx)
    def release(self, rule: RuleIR, ctx: Dict[str, Any]) -> None:
        """Undo one activation reservation when execution was deferred.

        Evaluation reserves the activation before effect execution so normal
        RuleRuntime callers remain atomic.  If every concrete effect is
        deferred (for example a generated action outside a live ActionQueue),
        the rule did not actually fire and its budget must be restored.
        """
        self.ledger.release(rule, ctx)

