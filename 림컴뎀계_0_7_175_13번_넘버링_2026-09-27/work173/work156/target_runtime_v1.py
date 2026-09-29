"""Rule-IR target resolution boundary.

This layer translates TargetIR into concrete target records when a scenario
provides candidate lists. It intentionally delegates deterministic selection to
``target_selector_v1`` and does not mutate battle state.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from rule_ir_v1 import TargetIR
from target_selector_v1 import select_targets

@dataclass(frozen=True)
class TargetResolution:
    requested: Optional[TargetIR]
    targets: tuple[Dict[str, Any], ...]
    resolved: bool
    reason: str

class TargetRuntime:
    """Resolve declarative targets without guessing missing combat data."""

    def resolve(self, target: Optional[TargetIR], ctx: Dict[str, Any]) -> TargetResolution:
        if target is None:
            return TargetResolution(None, tuple(), True, "no_target_required")

        side = str(target.side or "self")
        candidates = self._candidates(side, target, ctx)
        if not candidates:
            # Self is a useful special case even when no candidate list exists.
            if target.selector in ("self", "actor"):
                actor = ctx.get("actor") or ctx.get("identity")
                if isinstance(actor, dict):
                    return TargetResolution(target, (actor,), True, "self")
            return TargetResolution(target, tuple(), False, "no_candidates")

        # Apply eligibility filters before ranking/counting. Otherwise a dead
        # or ineligible top-ranked target can consume the requested slot count.
        candidates = [x for x in candidates if self._filters_match(x, target.filters)]
        if not candidates:
            return TargetResolution(target, tuple(), False, "selector_or_filter_no_match")
        selector = target.selector or "explicit"
        target_ids = target.filters.get("target_ids") or target.filters.get("identity_ids")
        target_index = target.filters.get("target_index")
        selected = select_targets(
            list(candidates), selector, max(1, int(target.count or 1)),
            target_index=target_index, target_ids=target_ids,
        )
        if not selected:
            return TargetResolution(target, tuple(), False, "selector_or_filter_no_match")
        return TargetResolution(target, tuple(selected), True, "resolved")

    @staticmethod
    def _candidates(side: str, target: TargetIR, ctx: Dict[str, Any]) -> List[Dict[str, Any]]:
        if str(target.selector) == "event_target":
            raw = ctx.get("targets") or ctx.get("target_candidates") or ctx.get("target")
            if isinstance(raw, dict):
                return [raw]
            if isinstance(raw, list):
                return [x for x in raw if isinstance(x, dict)]
            if isinstance(raw, tuple):
                return [x for x in raw if isinstance(x, dict)]
            return []
        side_key = {
            "ally": "allies", "allies": "allies", "self": "self_candidates",
            "enemy": "enemies", "enemies": "enemies", "target": "targets",
        }.get(side.lower(), side)
        raw = ctx.get(side_key, [])
        if isinstance(raw, dict):
            raw = list(raw.values())
        if not isinstance(raw, list):
            raw = list(raw) if isinstance(raw, tuple) else []
        return [x for x in raw if isinstance(x, dict)]

    @staticmethod
    def _filters_match(target: Dict[str, Any], filters: Dict[str, Any]) -> bool:
        if not filters:
            return True
        if filters.get("alive_only") and float(target.get("hp", target.get("max_hp", 0)) or 0) <= 0:
            return False
        if filters.get("dead_only") and float(target.get("hp", 0) or 0) > 0:
            return False
        if filters.get("exclude_identity_id") is not None:
            if str(target.get("identity_id", target.get("id", ""))) == str(filters["exclude_identity_id"]):
                return False
        if filters.get("affiliation"):
            aff = target.get("affiliations", target.get("combat_affiliations", [])) or []
            if isinstance(aff, str): aff = [aff]
            if str(filters["affiliation"]) not in {str(x) for x in aff}:
                return False
        if filters.get("status"):
            statuses = target.get("statuses", {}) or {}
            if str(filters["status"]) not in statuses:
                return False
        return True
