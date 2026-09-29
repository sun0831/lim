"""Probability helpers for declarative coin-reuse rules.

This module deliberately separates probability calculation from state mutation.
It can calculate an expected number of reuse attempts for a bounded geometric
rule, while the authoritative battle state remains deterministic until a full
branching executor is enabled.
"""
from __future__ import annotations
from typing import Any, Dict


def negative_effect_count(statuses: Dict[str, Any]) -> int:
    """Count currently present negative statuses (positive potency/count)."""
    n = 0
    for name, st in (statuses or {}).items():
        if name in {"Offense Level Up", "Defense Level Up", "Damage Up", "Protection"}:
            continue
        if isinstance(st, dict):
            active = float(st.get("potency", 0)) > 0 or float(st.get("count", 0)) > 0
        else:
            active = float(getattr(st, "potency", 0)) > 0 or float(getattr(st, "count", 0)) > 0
        if active:
            n += 1
    return n


def reuse_probability(rule: Dict[str, Any], statuses: Dict[str, Any] | None = None) -> float:
    # Identity-level probabilistic reuse is modeled at the high-point assumption:
    # once its declarative activation condition reaches the execution layer,
    # treat the reuse chance as 100%. E.G.O probability is intentionally out of
    # scope for the current calculator and will be handled separately later.
    if rule.get("high_point_assumption") or rule.get("mode") == "probabilistic":
        return 1.0
    p = float(rule.get("probability", 0.0))
    bonus = float(rule.get("negative_status_bonus", 0.0)) * negative_effect_count(statuses or {})
    return max(0.0, min(1.0, p + bonus))


def expected_reuses(rule: Dict[str, Any], statuses: Dict[str, Any] | None = None) -> float:
    """Expected bounded reuse count when p is evaluated at the same state."""
    p = reuse_probability(rule, statuses)
    m = max(0, int(rule.get("max_reuses", 0)))
    return sum(p ** k for k in range(1, m + 1))


def bounded_reuse_distribution(rule: Dict[str, Any], statuses: Dict[str, Any] | None = None) -> Dict[int, float]:
    """Return exact stop/reuse-count probabilities for a bounded Bernoulli reuse rule.

    k means exactly k additional executions. The remaining probability mass is the
    stop event (including the event that the first reuse fails). The distribution is
    normalized and never mutates battle state.
    """
    p = reuse_probability(rule, statuses)
    m = max(0, int(rule.get("max_reuses", 0)))
    if m <= 0:
        return {0: 1.0}
    out = {}
    for k in range(m):
        out[k] = (p ** k) * (1.0 - p)
    out[m] = p ** m
    total = sum(out.values()) or 1.0
    return {k: v / total for k, v in out.items()}
