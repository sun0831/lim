"""Common contract for skill-transform clauses.

This is a normalization/audit layer. It deliberately does not execute skills.
Skill changes are represented as SKILL_SWAP plus timing/selection parameters;
reclassification, forced follow-up actions, and coin/power changes are routed
to their existing runtimes instead of creating a monolithic skill-transform runtime.
"""
from __future__ import annotations
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Any, Optional

class SkillTransformRoute(str, Enum):
    SKILL_SWAP = "skill_swap"
    SKILL_RECLASSIFY = "skill_reclassify"
    SKILL_EVENT_TRIGGER = "skill_event_trigger"
    FORCED_ACTION = "forced_action"
    COIN_POWER_TRANSFORM = "coin_power_transform"
    SPECIAL_STATE = "special_state"
    UNRESOLVED = "unresolved"

@dataclass(frozen=True)
class SkillSwapSpec:
    source_skill: str
    target_skill: str
    timing: str = "immediate"
    slot_policy: str = "any_matching_slot"
    retry_if_invalidated: bool = False
    activation_limit: Optional[int] = None
    params: dict[str, Any] = field(default_factory=dict)

    def to_dict(self):
        return asdict(self)


def validate_skill_swap(spec: SkillSwapSpec) -> None:
    if not spec.source_skill or not spec.target_skill:
        raise ValueError("skill swap requires source_skill and target_skill")
    if spec.timing not in {"immediate", "turn_start", "next_turn_start", "turn_end_deferred", "action_start", "action_end"}:
        raise ValueError(f"unsupported skill swap timing: {spec.timing}")
    if spec.slot_policy not in {"any_matching_slot", "leftmost_below", "leftmost_above", "specific_slot", "all_matching"}:
        raise ValueError(f"unsupported slot policy: {spec.slot_policy}")
    if spec.activation_limit is not None and spec.activation_limit < 1:
        raise ValueError("activation_limit must be >= 1")


def route_from_e23_kind(kind: str) -> SkillTransformRoute:
    mapping = {
        "true_skill_swap": SkillTransformRoute.SKILL_SWAP,
        "next_turn_skill_swap": SkillTransformRoute.SKILL_SWAP,
        "skill_reclassify": SkillTransformRoute.SKILL_RECLASSIFY,
        "conditional_skill_trigger": SkillTransformRoute.SKILL_EVENT_TRIGGER,
        "forced_or_followup_skill": SkillTransformRoute.FORCED_ACTION,
        "coin_or_skill_parameter_transform": SkillTransformRoute.COIN_POWER_TRANSFORM,
        "special_state_not_skill_transform": SkillTransformRoute.SPECIAL_STATE,
        "unresolved": SkillTransformRoute.UNRESOLVED,
    }
    return mapping.get(kind, SkillTransformRoute.UNRESOLVED)


def swap_spec_from_clause(kind: str, source_skill: str, target_skill: str, **params: Any) -> SkillSwapSpec:
    route = route_from_e23_kind(kind)
    if route is not SkillTransformRoute.SKILL_SWAP:
        raise ValueError(f"clause kind {kind} is not a skill swap")
    timing = "next_turn_start" if kind == "next_turn_skill_swap" else params.pop("timing", "immediate")
    spec = SkillSwapSpec(source_skill=source_skill, target_skill=target_skill, timing=timing, **params)
    validate_skill_swap(spec)
    return spec
