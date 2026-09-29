"""Common Buff/Debuff event lifecycle bridge.

The bridge keeps state-transition ownership in BuffDebuffRuntime while allowing
both deterministic and probabilistic execution paths to feed the same lifecycle
contract.  It does not fire identity-specific triggers or calculate damage.
"""
from __future__ import annotations
from typing import Any, Dict, Mapping, Optional
from buff_debuff_runtime_v1 import BuffDebuffRuntime


class BuffDebuffEventBridge:
    """Apply declarative buff/debuff lifecycle transitions for one event."""

    @staticmethod
    def dispatch(state: Any, *, event: str, target_id: Optional[str] = None,
                 context: Optional[Mapping[str, Any]] = None) -> Dict[str, Any]:
        ctx = dict(context or {})
        consumed = BuffDebuffRuntime.consume_on_event(
            state, event=str(event), target_id=target_id, context=ctx
        )
        return {
            "event": str(event),
            "target_id": None if target_id is None else str(target_id),
            "consumed": consumed,
            "count": len(consumed),
        }

    @staticmethod
    def end_turn(state: Any) -> Dict[str, Any]:
        expired = BuffDebuffRuntime.end_turn(state)
        for item in expired:
            record = {
                "event": "buff_debuff_expired",
                "target_id": str(item.get("target_id", "")),
                "name": str(item.get("name", "")),
                "kind": str(item.get("kind", "")),
                "rule_id": str(item.get("rule_id", "")),
                "source_id": str(item.get("source_id", "")),
            }
            if hasattr(state, "event_log"):
                state.event_log.append(record)
        return {"event": "turn_end", "expired": expired, "count": len(expired)}
