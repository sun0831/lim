"""Generic one-turn requested/triggered action queue for 림컴뎀계 0.5.6.

The queue deliberately separates:
- RequestedAction: the order chosen by the user at turn setup.
- TriggeredAction: an action generated during execution by a passive, skill,
  stagger event, assist rule, or another triggered action.

A triggered action is inserted immediately after its source action, while the
remaining requested actions retain their original requested_index.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, Iterator, List, Optional


@dataclass
class ActionRequest:
    identity_id: str
    skill_id: str
    requested_index: int
    faces: Optional[List[str]] = None
    target_count: int = 1
    crit: bool = False
    clash: Optional[Dict[str, Any]] = None
    bleed_clash_probability: Optional[Dict[str, Any]] = None
    generated: bool = False
    reason: Optional[str] = None
    source_action_index: Optional[int] = None
    source_event: Optional[str] = None
    trigger_chain: List[str] = field(default_factory=list)
    depth: int = 0
    suppress_kill_reuse: bool = False
    target_policy: Optional[str] = None
    target_index: Optional[int] = None
    target_ids: Optional[List[str]] = None
    # Explicit user override for selectors such as random. This is distinct from
    # the selector policy so the UI can say 'random, but force these targets'.
    target_override_ids: Optional[List[str]] = None
    # Optional per-coin target assignment. Example: ['A', 'B'] means coin 1 -> A, coin 2 -> B.
    coin_target_ids: Optional[List[Any]] = None
    trigger_kind: Optional[str] = None

    @classmethod
    def from_raw(cls, raw: Dict[str, Any], requested_index: int) -> "ActionRequest":
        return cls(
            identity_id=str(raw["identity_id"]),
            skill_id=str(raw["skill_id"]),
            requested_index=int(raw.get("_requested_index", requested_index)),
            faces=None if raw.get("faces") is None else [str(x).upper() for x in raw["faces"]],
            target_count=int(raw.get("target_count", 1)),
            crit=bool(raw.get("crit", False)),
            clash=raw.get("clash"),
            bleed_clash_probability=raw.get("bleed_clash_probability"),
            generated=bool(raw.get("_generated", False)),
            reason=raw.get("_reason"),
            source_action_index=raw.get("_source_action_index"),
            source_event=raw.get("_source_event"),
            trigger_chain=list(raw.get("_trigger_chain", [])),
            depth=int(raw.get("_depth", 0)),
            suppress_kill_reuse=bool(raw.get("_suppress_kill_reuse", False)),
            target_policy=raw.get('target_policy', raw.get('_target_policy')),
            target_index=raw.get('target_index', raw.get('_target_index')),
            target_ids=None if raw.get('target_ids', raw.get('_target_ids')) is None else [str(x) for x in raw.get('target_ids', raw.get('_target_ids'))],
            target_override_ids=None if raw.get('target_override_ids', raw.get('_target_override_ids')) is None else [str(x) for x in raw.get('target_override_ids', raw.get('_target_override_ids'))],
            coin_target_ids=None if raw.get('coin_target_ids', raw.get('coin_target_indices', raw.get('_coin_target_ids'))) is None else list(raw.get('coin_target_ids', raw.get('coin_target_indices', raw.get('_coin_target_ids')))),
            trigger_kind=raw.get('trigger_kind', raw.get('_trigger_kind')),
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "identity_id": self.identity_id,
            "skill_id": self.skill_id,
            "requested_index": self.requested_index,
            "faces": self.faces,
            "target_count": self.target_count,
            "crit": self.crit,
            "clash": self.clash,
            "bleed_clash_probability": self.bleed_clash_probability,
            "generated": self.generated,
            "reason": self.reason,
            "source_action_index": self.source_action_index,
            "source_event": self.source_event,
            "trigger_chain": list(self.trigger_chain),
            "depth": self.depth,
            "suppress_kill_reuse": self.suppress_kill_reuse,
            "target_policy": self.target_policy,
            "target_index": self.target_index,
            "target_ids": list(self.target_ids) if self.target_ids is not None else None,
            "target_override_ids": list(self.target_override_ids) if self.target_override_ids is not None else None,
            "coin_target_ids": list(self.coin_target_ids) if self.coin_target_ids is not None else None,
            "trigger_kind": self.trigger_kind,
        }


class ActionQueue:
    """FIFO queue with immediate-after-source insertion semantics."""
    def __init__(self, requests: Optional[List[ActionRequest]] = None, max_depth: int = 16):
        self.items: List[ActionRequest] = list(requests or [])
        self.position = 0
        self.max_depth = int(max_depth)
        self.executed: List[ActionRequest] = []

    @classmethod
    def from_scenario(cls, actions: List[Dict[str, Any]], max_depth: int = 16) -> "ActionQueue":
        return cls([ActionRequest.from_raw(a, i) for i, a in enumerate(actions, 1)], max_depth=max_depth)

    def __bool__(self):
        return self.position < len(self.items)

    def pop(self) -> ActionRequest:
        if not self:
            raise IndexError("action queue is empty")
        action = self.items[self.position]
        self.position += 1
        self.executed.append(action)
        return action

    def enqueue_triggered(self, action: ActionRequest) -> bool:
        if action.depth > self.max_depth:
            return False
        # Insert at the current cursor: this is immediately after the source
        # action and before the next planned player action.
        self.items.insert(self.position, action)
        return True

    def triggered_from(self, source: ActionRequest, identity_id: str, skill_id: str,
                       reason: str, source_event: str = "trigger", faces=None,
                       suppress_kill_reuse: bool = False, target_policy=None, target_index=None, target_ids=None, target_override_ids=None, coin_target_ids=None, trigger_kind=None) -> ActionRequest:
        chain = list(source.trigger_chain)
        chain.append(f"{source.identity_id}:{source.skill_id}")
        return ActionRequest(
            identity_id=str(identity_id), skill_id=str(skill_id),
            requested_index=source.requested_index, faces=faces,
            generated=True, reason=reason,
            source_action_index=source.requested_index,
            source_event=source_event, trigger_chain=chain,
            depth=source.depth + 1,
            suppress_kill_reuse=bool(suppress_kill_reuse),
            target_policy=target_policy, target_index=target_index,
            target_ids=None if target_ids is None else [str(x) for x in target_ids],
            target_override_ids=None if target_override_ids is None else [str(x) for x in target_override_ids],
            coin_target_ids=None if coin_target_ids is None else list(coin_target_ids),
            trigger_kind=trigger_kind or source_event,
        )

    def enqueue_generated(self, source: ActionRequest, identity_id: str, skill_id: str,
                          reason: str, source_event: str = "trigger", faces=None,
                          *, target_policy=None, target_index=None, target_ids=None,
                          target_override_ids=None, coin_target_ids=None,
                          trigger_kind=None, suppress_kill_reuse=False,
                          inherit_target=True) -> tuple[ActionRequest, bool]:
        """Create and queue one generated action at the common ActionQueue boundary.

        ``inherit_target`` preserves the source action's explicit target only when
        the generated rule does not provide a more specific selector.  Keeping
        this policy here prevents individual trigger/event handlers from drifting
        into different target-inheritance semantics.
        """
        explicit_target = (target_policy not in (None, '', 'main') or
                           target_index is not None or target_ids is not None or
                           target_override_ids is not None or coin_target_ids is not None)
        use_source = bool(inherit_target and not explicit_target and source.target_policy is not None)
        generated = self.triggered_from(
            source, str(identity_id), str(skill_id), str(reason),
            source_event=source_event, faces=faces,
            suppress_kill_reuse=suppress_kill_reuse,
            target_policy=(source.target_policy if use_source else target_policy),
            target_index=(source.target_index if use_source else target_index),
            target_ids=(source.target_ids if use_source else target_ids),
            target_override_ids=(source.target_override_ids if use_source else target_override_ids),
            coin_target_ids=(source.coin_target_ids if use_source else coin_target_ids),
            trigger_kind=trigger_kind,
        )
        return generated, self.enqueue_triggered(generated)

    def requested_plan(self) -> List[Dict[str, Any]]:
        return [x.to_dict() for x in self.items if not x.generated]
