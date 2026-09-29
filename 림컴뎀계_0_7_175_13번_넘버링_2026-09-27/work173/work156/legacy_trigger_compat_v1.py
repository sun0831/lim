"""Compatibility-only adapter for the retired TriggerRuntime.

Production combat code must not import or construct TriggerRuntime directly.
This module is intentionally the single compatibility boundary for old tests,
parity tooling, and callers that have not yet migrated to RuleRuntime.
"""
from __future__ import annotations
from typing import Any, Iterable

_runtime_cache: dict[int, Any] = {}

def fire(rules: Iterable[Any], event: str, ctx: dict) -> list[dict]:
    from trigger_runtime_v1 import TriggerRuntime
    rules_list = rules if isinstance(rules, list) else list(rules)
    key = tuple(id(rule) for rule in rules_list)
    # Compatibility callers may reconstruct the adapter around the same rule
    # definitions. Retain one ledger per rule-set identity so historical
    # turn-scoped state survives those adapter wrappers.
    runtime = _runtime_cache.get(key)
    if runtime is None:
        runtime = TriggerRuntime(rules_list)
        _runtime_cache[key] = runtime
    return runtime.fire(event, dict(ctx or {}))

def reset(runtime: Any) -> None:
    if runtime is not None and hasattr(runtime, "reset_turn"):
        runtime.reset_turn()
