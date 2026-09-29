"""Small shared helper for legacy condition trees.

This module only owns the structural ``and``/``or`` part of a legacy
condition.  Actual leaf-condition semantics remain in each runtime because
their state models are different.
"""
from __future__ import annotations
from typing import Any, Callable, Dict, Optional


def evaluate_composite_condition(
    condition: Optional[Dict[str, Any]],
    evaluator: Callable[[Dict[str, Any]], bool],
) -> Optional[bool]:
    """Evaluate a legacy ``and``/``or`` node, or return None for leaf nodes."""
    if not condition:
        return None
    kind = condition.get("type")
    children = condition.get("conditions") or []
    if kind == "or":
        return any(evaluator(child) for child in children)
    if kind == "and":
        return all(evaluator(child) for child in children)
    return None
