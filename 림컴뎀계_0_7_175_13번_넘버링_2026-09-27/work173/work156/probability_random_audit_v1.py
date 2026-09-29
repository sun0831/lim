"""E32 audit: probability_random gap-axis against existing primitives.

This is an audit/normalization layer, not a new battle runtime.  It separates
random target selection, Bernoulli probability triggers, bounded reuse, and
per-coin random outcomes so RuleIR can route each clause to an existing
primitive or mark a genuine semantic gap.
"""
from __future__ import annotations
import json, re
from pathlib import Path
from typing import Any, Dict, Iterable, List

RANDOM_RE = re.compile(r"무작위|랜덤")
PERCENT_RE = re.compile(r"(\d+(?:\.\d+)?)\s*%\s*확률")
PER_COIN_RE = re.compile(r"각\s*탄환마다|코인마다|각\s*코인")
TARGET_RE = re.compile(r"무작위\s*(?:대상|적|아군|인격)\s*\d*명?")
REUSE_RE = re.compile(r"추가로|추가.*발동|재발동|다시.*발동|횟수.*확률")


def load_axis_records(path: str | Path) -> List[dict]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return [r for r in data.get("gaps", []) if "probability_random" in (r.get("categories") or [])]


def classify_text(text: str) -> str:
    s = text or ""
    if TARGET_RE.search(s) and not PERCENT_RE.search(s):
        return "random_target"
    if PER_COIN_RE.search(s) and PERCENT_RE.search(s):
        return "per_coin_random_outcome"
    if PERCENT_RE.search(s) and REUSE_RE.search(s):
        return "probabilistic_trigger_or_reuse"
    if PERCENT_RE.search(s):
        return "probabilistic_effect"
    if RANDOM_RE.search(s):
        return "random_choice_without_explicit_probability"
    return "non_probability_clause_overlap"


def audit(records: Iterable[dict]) -> Dict[str, Any]:
    rows=[]
    for r in records:
        text=r.get("source_text","")
        rows.append({
            "identity_id": r.get("identity_id"),
            "identity_name": r.get("identity_name"),
            "passive_name": r.get("passive_name"),
            "classification": classify_text(text),
            "source_text": text,
            "existing_primitive": {
                "random_target": "TargetSelector.random",
                "probabilistic_trigger_or_reuse": "reuse_probability / ProbabilisticTriggerRuntime",
                "probabilistic_effect": "ProbabilisticTriggerRuntime + Effect/Condition",
                "per_coin_random_outcome": "requires per-coin RNG outcome contract; no dedicated runtime confirmed",
                "random_choice_without_explicit_probability": "TargetSelector.random or generic random-choice parameter",
                "non_probability_clause_overlap": "existing Condition/Action/Effect primitive",
            }[classify_text(text)],
        })
    unique={r["source_text"] for r in rows}
    from collections import Counter
    counts=Counter(r["classification"] for r in rows)
    return {
        "axis":"probability_random",
        "record_count":len(rows),
        "unique_source_text_count":len(unique),
        "classification_counts":dict(counts),
        "new_dedicated_runtime_confirmed":False,
        "important_contract_gap":"per_coin_random_outcome" if counts.get("per_coin_random_outcome",0) else None,
        "rows":rows,
    }
