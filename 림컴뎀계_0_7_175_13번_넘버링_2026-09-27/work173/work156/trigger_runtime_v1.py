"""Compatibility Trigger runtime backed by the canonical ActivationLedger.

This module is retained only for legacy/compatibility callers. TriggerRule is a
pure definition; mutable activation state is never stored on the rule itself.
"""
from __future__ import annotations
from typing import Any, Dict, List, Optional
from trigger_rule_model_v1 import TriggerCondition, TriggerEffect, TriggerRule
from activation_ledger_v1 import ActivationLedger

class TriggerRuntime:
    """Evaluate declarative rules against a normalized event context."""
    def __init__(self, rules: Optional[List[TriggerRule]]=None, activation_ledger: ActivationLedger | None = None):
        self.rules=list(rules or [])
        self.ledger=activation_ledger or ActivationLedger()

    def reset_turn(self):
        self.ledger.reset()

    @classmethod
    def condition_met(cls, condition: TriggerCondition, ctx: Dict[str,Any]) -> bool:
        from condition_runtime_v1 import ConditionRuntime
        from rule_ir_v1 import ConditionIR
        args = condition.to_dict()
        args.pop('type', None)
        return ConditionRuntime.evaluate(ConditionIR(condition.type, args), ctx)

    def fire(self, event: str, ctx: Dict[str,Any]) -> List[Dict[str,Any]]:
        fired=[]
        for rule in self.rules:
            if rule.event!=event or not self.ledger.eligible(rule, ctx, turn_cap=(rule.metadata or {}).get('turn_cap')):
                continue
            if not all(self.condition_met(c,ctx) for c in rule.conditions):
                continue
            self.ledger.consume(rule, ctx)
            for effect in rule.effects:
                fired.append({"rule_id":rule.id,"owner_id":rule.owner_id,
                              "source_text":rule.source_text,"effect":effect.to_dict(),
                              "activation":self.ledger.total_count(rule),"metadata":dict(rule.metadata)})
        return fired
