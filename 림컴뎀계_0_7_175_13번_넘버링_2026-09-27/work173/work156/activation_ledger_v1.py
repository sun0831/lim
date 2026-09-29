"""Single owner for turn-scoped rule activation state.

Production Rule/Trigger objects describe activation limits; this ledger owns the
mutable counts.  It is intentionally small and deepcopy-friendly so probability
branches can fork the complete activation state with the rest of TurnState.
"""
from __future__ import annotations
from copy import deepcopy
from typing import Any, Dict, Iterable, Mapping, Tuple


class ActivationLedger:
    def __init__(self, counts: Mapping[str, int] | None = None,
                 buckets: Mapping[Tuple[str, str], int] | None = None):
        self.counts: Dict[str, int] = {str(k): int(v) for k, v in (counts or {}).items()}
        self.buckets: Dict[Tuple[str, str], int] = {
            (str(k[0]), str(k[1])): int(v) for k, v in (buckets or {}).items()
        }

    def clone(self) -> "ActivationLedger":
        return deepcopy(self)

    def reset(self) -> None:
        self.counts.clear()
        self.buckets.clear()

    @staticmethod
    def scope_key(rule: Any, ctx: Mapping[str, Any] | None = None) -> str:
        ctx = ctx or {}
        scope = str(getattr(rule, "activation_scope", None)
                    or ctx.get("activation_scope", "global"))
        if scope == "per_identity":
            return str(ctx.get("trigger_identity_id", ctx.get("identity_id", "")))
        if scope == "per_actor":
            return str(ctx.get("trigger_identity_id", ctx.get("actor_id", ctx.get("identity_id", ""))))
        if scope == "per_skill":
            return str(ctx.get("skill_id", ctx.get("skill_name", "")))
        if scope == "per_target":
            return str(ctx.get("target_id", ctx.get("target_index", "")))
        if scope in ("per_identity_target", "per_actor_target"):
            actor = ctx.get("trigger_identity_id", ctx.get("actor_id", ctx.get("identity_id", "")))
            target = ctx.get("target_id", ctx.get("target_index", ""))
            return f"{actor}|{target}"
        return "__global__"

    def count(self, rule_or_id: Any, ctx: Mapping[str, Any] | None = None) -> int:
        rule_id = str(rule_or_id if isinstance(rule_or_id, str) else getattr(rule_or_id, "rule_id", getattr(rule_or_id, "id", "")))
        scope = str(getattr(rule_or_id, "activation_scope", "global")) if not isinstance(rule_or_id, str) else "global"
        if scope == "global":
            return self.counts.get(rule_id, 0)
        return self.buckets.get((rule_id, self.scope_key(rule_or_id, ctx)), 0)

    def total_count(self, rule_or_id: Any) -> int:
        rule_id = str(rule_or_id if isinstance(rule_or_id, str) else getattr(rule_or_id, "rule_id", getattr(rule_or_id, "id", "")))
        return self.counts.get(rule_id, 0)

    def eligible(self, rule: Any, ctx: Mapping[str, Any] | None = None,
                 *, turn_cap: int | None = None) -> bool:
        limit = getattr(rule, "activation_limit", None)
        if limit is None:
            limit = getattr(rule, "max_activations", None)
        if limit is None or int(limit) < 0:
            return True
        limit = int(limit)
        scope = str(getattr(rule, "activation_scope", "global") or "global")
        total = self.counts.get(str(getattr(rule, "rule_id", getattr(rule, "id", ""))), 0)
        if turn_cap is not None and total >= int(turn_cap):
            return False
        if scope == "global":
            return total < limit
        key = (str(getattr(rule, "rule_id", getattr(rule, "id", ""))), self.scope_key(rule, ctx))
        return self.buckets.get(key, 0) < limit

    def consume(self, rule: Any, ctx: Mapping[str, Any] | None = None) -> None:
        rule_id = str(getattr(rule, "rule_id", getattr(rule, "id", "")))
        self.counts[rule_id] = self.counts.get(rule_id, 0) + 1
        scope = str(getattr(rule, "activation_scope", "global") or "global")
        if scope != "global":
            key = (rule_id, self.scope_key(rule, ctx))
            self.buckets[key] = self.buckets.get(key, 0) + 1

    def release(self, rule: Any, ctx: Mapping[str, Any] | None = None) -> None:
        rule_id = str(getattr(rule, "rule_id", getattr(rule, "id", "")))
        current = self.counts.get(rule_id, 0)
        if current > 0:
            self.counts[rule_id] = current - 1
        scope = str(getattr(rule, "activation_scope", "global") or "global")
        if scope != "global":
            key = (rule_id, self.scope_key(rule, ctx))
            bucket = self.buckets.get(key, 0)
            if bucket > 0:
                self.buckets[key] = bucket - 1

    def snapshot(self) -> dict:
        return {
            "counts": dict(self.counts),
            "buckets": {f"{rid}\x1f{key}": int(v) for (rid, key), v in self.buckets.items()},
        }

    @classmethod
    def from_snapshot(cls, snapshot: Mapping[str, Any] | None) -> "ActivationLedger":
        snapshot = snapshot or {}
        buckets = {}
        for raw, value in (snapshot.get("buckets", {}) or {}).items():
            rid, sep, key = str(raw).partition("\x1f")
            if sep:
                buckets[(rid, key)] = int(value)
        return cls(snapshot.get("counts", {}), buckets)
