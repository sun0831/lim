"""Measurable migration boundary from legacy rules to Rule IR.

This module is intentionally read-only: it compiles rules for inspection,
coverage reports, golden tests, and gradual runtime migration. It does not
replace the authoritative combat mutation path.
"""
from __future__ import annotations
from typing import Any, Dict, Iterable, List
from rule_ir_bridge_v1 import compile_trigger_rules, compile_gimmick_rules
from rule_ir_v1 import RuleIR


def migration_report(trigger_rules: Iterable[Any] = (), gimmick_rules: Iterable[Any] = ()) -> Dict[str, Any]:
    triggers = list(trigger_rules)
    gimmicks = list(gimmick_rules)
    trigger_ir = compile_trigger_rules(triggers)
    gimmick_ir = compile_gimmick_rules(gimmicks)
    all_ir: List[RuleIR] = trigger_ir + gimmick_ir
    status = {}
    for rule in all_ir:
        status[rule.status] = status.get(rule.status, 0) + 1
    condition_count = sum(len(r.conditions) for r in all_ir)
    target_count = sum(r.target is not None for r in all_ir)
    effect_count = sum(len(r.effects) for r in all_ir)
    return {
        "legacy_trigger_rules": len(triggers),
        "legacy_gimmick_rules": len(gimmicks),
        "compiled_rules": len(all_ir),
        "compiled_conditions": condition_count,
        "compiled_targets": target_count,
        "compiled_effects": effect_count,
        "status_counts": status,
        "lossless_boundary": all(getattr(r, "source_text", "") != "" for r in all_ir),
    }
