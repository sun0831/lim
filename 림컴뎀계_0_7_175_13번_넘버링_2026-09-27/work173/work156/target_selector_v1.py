"""Deterministic target-selection primitives for one-turn simulation.

The current engine still uses an aggregate enemy state by default. This module
normalizes explicit target-selection requests and can select from a list of
enemy slot dictionaries when a scenario provides per-target data. It never
guesses a target when the requested selector cannot be evaluated.
"""
from __future__ import annotations
from typing import Any, Dict, List, Optional
import random

ALIASES = {
    "fastest": "speed_max", "slowest": "speed_min",
    "fastest_ally": "speed_max", "slowest_ally": "speed_min",
    "highest_hp": "hp_max", "lowest_hp": "hp_min",
    "highest_hp_percent": "hp_percent_max", "lowest_hp_percent": "hp_percent_min",
    "leftmost": "formation_min", "rightmost": "formation_max",
    "fastest_formation_ally": "formation_min", "slowest_formation_ally": "formation_max",
    "earliest_ally": "formation_min", "latest_ally": "formation_max",
    "random": "random", "event_target": "explicit",
    "main": "explicit", "lowest_hp_staggered": "lowest_hp_staggered", "primary": "explicit",
    "highest_tremor_count": "highest_status_count:Tremor", "lowest_tremor_count": "lowest_status_count:Tremor",
    "highest_taunt": "taunt_max", "highest_provoke": "taunt_max",
    "faster_roster_allies": "formation_before_owner",
    "slower_roster_allies": "formation_after_owner",
    "lowest_charge_among_faster_allies": "formation_before_owner_charge_min",
    "lowest_charge_holder": "charge_positive_min",
    "formation_1": "formation_slot:1",
    "formation_2": "formation_slot:2",
    "formation_3": "formation_slot:3",
    "lowest_sp_among_fanatics": "status_present_sp_min:광신",
}


def normalize(policy: Any) -> Optional[str]:
    if policy is None:
        return None
    p = str(policy).strip().lower()
    return ALIASES.get(p, p)


def _num(obj: Dict[str, Any], key: str, default: Any = 0) -> float:
    try:
        return float(obj.get(key, default))
    except (TypeError, ValueError):
        return float(default)


def _status_obj(target: Dict[str, Any], name: str) -> Dict[str, Any]:
    sts = target.get("statuses", {}) or {}
    st = sts.get(name, {})
    if st != {}:
        return st
    lname = str(name).lower()
    for k, v in sts.items():
        if str(k).lower() == lname:
            return v
    return {}


def _id_set(raw: Any) -> set[str]:
    if raw is None:
        return set()
    if isinstance(raw, (list, tuple, set)):
        return {str(x) for x in raw}
    return {str(raw)}


def _apply_filters(targets: List[Dict[str, Any]], filters: Dict[str, Any]) -> List[Dict[str, Any]]:
    if not filters:
        return list(targets)
    out = list(targets)

    include_ids = _id_set(filters.get("include_ids"))
    if include_ids:
        out = [t for t in out if str(t.get("id", t.get("index", ""))) in include_ids]

    exclude_ids = _id_set(filters.get("exclude_ids"))
    if filters.get("exclude_self") and filters.get("owner_id") is not None:
        exclude_ids.add(str(filters.get("owner_id")))
    if exclude_ids:
        out = [t for t in out if str(t.get("id", t.get("index", ""))) not in exclude_ids]

    if bool(filters.get("alive_only")):
        out = [t for t in out if _num(t, "hp", t.get("max_hp", 0)) > 0]

    status_present = filters.get("status_present")
    if status_present is not None:
        names = status_present if isinstance(status_present, (list, tuple, set)) else [status_present]
        out = [
            t for t in out
            if any(_status_obj(t, str(name)) for name in names)
        ]

    status_absent = filters.get("status_absent")
    if status_absent is not None:
        names = status_absent if isinstance(status_absent, (list, tuple, set)) else [status_absent]
        out = [
            t for t in out
            if all(not _status_obj(t, str(name)) for name in names)
        ]

    owner_formation_index = filters.get("owner_formation_index")
    if owner_formation_index is not None:
        try:
            owner_slot = int(owner_formation_index)
            if bool(filters.get("formation_before_owner")):
                out = [t for t in out if int(_num(t, "formation_index", t.get("index", 0))) < owner_slot]
            if bool(filters.get("formation_after_owner")):
                out = [t for t in out if int(_num(t, "formation_index", t.get("index", 0))) > owner_slot]
        except (TypeError, ValueError):
            return []

    return out


def _resolve_structured_policy(
    targets: List[Dict[str, Any]],
    policy: Dict[str, Any],
    count: int,
    rng: Optional[random.Random],
) -> List[Dict[str, Any]]:
    requested_count = max(1, int(policy.get("count", count)))
    base = _apply_filters(targets, dict(policy.get("filters") or {}))
    selector = policy.get("selector", policy.get("policy"))

    priority = list(policy.get("priority") or [])
    for p in priority:
        if isinstance(p, dict):
            cands = _apply_filters(base, dict(p.get("filters") or {}))
            selected = select_targets(
                cands,
                p.get("selector", p.get("policy")),
                count=int(p.get("count", requested_count)),
                rng=rng,
            )
        else:
            selected = select_targets(base, p, count=requested_count, rng=rng)
        if selected:
            return selected[:requested_count]

    selected = select_targets(base, selector, count=requested_count, rng=rng) if selector is not None else base[:requested_count]
    if selected:
        return selected[:requested_count]

    fallback = policy.get("fallback")
    if fallback is not None:
        selected = select_targets(base, fallback, count=requested_count, rng=rng)
        if selected:
            return selected[:requested_count]

    if policy.get("fallback_to_unfiltered"):
        selected = select_targets(targets, fallback or selector, count=requested_count, rng=rng)
        return selected[:requested_count]

    return []


def select_targets(
    targets: List[Dict[str, Any]],
    policy: Any,
    count: int = 1,
    target_index: Optional[int] = None,
    target_ids: Optional[List[str]] = None,
    rng: Optional[random.Random] = None,
) -> List[Dict[str, Any]]:
    if not targets:
        return []
    if target_ids:
        wanted = {str(x) for x in target_ids}
        return [t for t in targets if str(t.get("id", t.get("index", ""))) in wanted][:max(1, int(count))]
    if target_index is not None:
        i = int(target_index)
        return [targets[i]] if 0 <= i < len(targets) else []

    if isinstance(policy, dict):
        return _resolve_structured_policy(targets, policy, count, rng)

    p = normalize(policy)
    if not p or p in ("explicit", "selected"):
        return targets[:max(1, int(count))]

    if p.startswith("formation_slot:"):
        try:
            slot = int(p.split(":", 1)[1])
        except (TypeError, ValueError):
            return []
        if slot < 1:
            return []
        out = [t for t in targets if int(_num(t, "formation_index", t.get("index", 0))) == slot]
        return out[:max(1, int(count))]

    if p == "lowest_hp_staggered":
        candidates = []
        for t in targets:
            st = t.get("state")
            staggered = bool(getattr(st, "staggered", False)) if st is not None else bool(t.get("staggered", False))
            if not staggered:
                continue
            abnormality = bool(t.get("is_abnormality", getattr(st, "is_abnormality", False) if st is not None else False))
            is_part = bool(t.get("is_part", t.get("part", False)))
            candidates.append((0 if (abnormality and not is_part) else 1, _num(t, "hp", t.get("max_hp", 0)), _num(t, "formation_index", t.get("index", 0)), t))
        if not candidates:
            return []
        candidates.sort(key=lambda x: (x[0], x[1], x[2]))
        return [candidates[0][3]]

    if p == "random":
        chooser = rng if rng is not None else random
        alive = [t for t in targets if _num(t, "hp", t.get("max_hp", 0)) > 0]
        pool = alive or list(targets)
        n = min(max(1, int(count)), len(pool))
        return chooser.sample(pool, n)

    if p == "taunt_max":
        def key(t):
            return _num(t, "taunt", t.get("taunt_value", t.get("provoke", 0)))
    elif p == "speed_max":
        key = lambda t: _num(t, "speed")
    elif p == "speed_min":
        key = lambda t: _num(t, "speed")
    elif p == "hp_max":
        key = lambda t: _num(t, "hp", t.get("max_hp", 0))
    elif p == "hp_min":
        key = lambda t: _num(t, "hp", t.get("max_hp", 0))
    elif p == "hp_percent_max":
        key = lambda t: _num(t, "hp", 0) / max(_num(t, "max_hp", 1), 1)
    elif p == "hp_percent_min":
        key = lambda t: _num(t, "hp", 0) / max(_num(t, "max_hp", 1), 1)
    elif p == "sp_max":
        key = lambda t: _num(t, "sp", 0)
    elif p == "sp_min":
        key = lambda t: _num(t, "sp", 0)
    elif p == "charge_positive_min":
        eligible = [t for t in targets if _num(t, "charge", 0) > 0]
        if not eligible:
            return []
        targets = eligible
        key = lambda t: _num(t, "charge", 0)
    elif p == "formation_min":
        key = lambda t: _num(t, "formation_index", t.get("index", 0))
    elif p == "formation_max":
        key = lambda t: _num(t, "formation_index", t.get("index", 0))
    elif p == "poise_potency_max":
        name = "Poise"
        def key(t):
            st = _status_obj(t, name)
            return _num(st, "potency", 0) if isinstance(st, dict) else _num(st, "potency", getattr(st, "potency", 0))
    elif p == "poise_potency_min":
        name = "Poise"
        def key(t):
            st = _status_obj(t, name)
            return _num(st, "potency", 0) if isinstance(st, dict) else _num(st, "potency", getattr(st, "potency", 0))
    elif p == "poise_count_max":
        name = "Poise"
        def key(t):
            st = _status_obj(t, name)
            return _num(st, "count", 0) if isinstance(st, dict) else _num(st, "count", getattr(st, "count", 0))
    elif p == "poise_count_min":
        name = "Poise"
        def key(t):
            st = _status_obj(t, name)
            return _num(st, "count", 0) if isinstance(st, dict) else _num(st, "count", getattr(st, "count", 0))
    elif p.startswith("highest_status:"):
        name = p.split(":", 1)[1]
        def key(t):
            st = _status_obj(t, name)
            if isinstance(st, dict):
                return _num(st, "potency", 0)
            return _num(st, "potency", getattr(st, "potency", 0))
    elif p.startswith("lowest_status:"):
        name = p.split(":", 1)[1]
        def key(t):
            st = _status_obj(t, name)
            if isinstance(st, dict):
                return _num(st, "potency", 0)
            return _num(st, "potency", getattr(st, "potency", 0))
    elif p.startswith("highest_status_count:"):
        name = p.split(":", 1)[1]
        def key(t):
            st = _status_obj(t, name)
            if isinstance(st, dict):
                return _num(st, "count", 0)
            return _num(st, "count", getattr(st, "count", 0))
    elif p.startswith("lowest_status_count:"):
        name = p.split(":", 1)[1]
        def key(t):
            st = _status_obj(t, name)
            if isinstance(st, dict):
                return _num(st, "count", 0)
            return _num(st, "count", getattr(st, "count", 0))
    elif p.startswith("highest_status_total:"):
        name = p.split(":", 1)[1]
        def key(t):
            st = _status_obj(t, name)
            if isinstance(st, dict):
                return _num(st, "potency", 0) + _num(st, "count", 0)
            return _num(st, "potency", getattr(st, "potency", 0)) + _num(st, "count", getattr(st, "count", 0))
    elif p.startswith("status_present_sp_min:"):
        name = p.split(":", 1)[1]
        targets = [t for t in targets if _status_obj(t, name)]
        if not targets:
            return []
        key = lambda t: _num(t, "sp", 0)
    elif p.startswith("status_present_sp_max:"):
        name = p.split(":", 1)[1]
        targets = [t for t in targets if _status_obj(t, name)]
        if not targets:
            return []
        key = lambda t: _num(t, "sp", 0)
    elif p.startswith("lowest_status_total:"):
        name = p.split(":", 1)[1]
        def key(t):
            st = _status_obj(t, name)
            if isinstance(st, dict):
                return _num(st, "potency", 0) + _num(st, "count", 0)
            return _num(st, "potency", getattr(st, "potency", 0)) + _num(st, "count", getattr(st, "count", 0))
    else:
        return []

    reverse = p.endswith("_max") or p in ("speed_max", "hp_max", "hp_percent_max", "sp_max", "formation_max", "taunt_max") or p.startswith("highest_status:") or p.startswith("highest_status_count:") or p.startswith("highest_status_total:")
    return sorted(targets, key=key, reverse=reverse)[:max(1, int(count))]
