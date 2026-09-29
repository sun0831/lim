"""Golden-result comparison helpers.

Keeps comparison deterministic and intentionally ignores volatile fields unless
explicitly requested. The solver remains responsible for producing results.
"""
from __future__ import annotations
import json
from typing import Any, Dict, Iterable

DEFAULT_PATHS=("total_damage","damage_by_identity","damage_by_skill","next_turn_state")

def project(result: Dict[str,Any], paths: Iterable[str]=DEFAULT_PATHS) -> Dict[str,Any]:
    return {p: result.get(p) for p in paths}

def canonical(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",",":"))

def compare(expected: Dict[str,Any], actual: Dict[str,Any], paths: Iterable[str]=DEFAULT_PATHS) -> Dict[str,Any]:
    e=project(expected,paths); a=project(actual,paths)
    diffs={p:{"expected":e[p],"actual":a[p]} for p in e if canonical(e[p]) != canonical(a[p])}
    return {"ok": not diffs, "diffs": diffs}
