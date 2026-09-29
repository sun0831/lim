"""Declarative resource primitives for the common Rule IR.

This module is intentionally a schema/normalization layer, not an identity-specific
runtime.  It turns recurring resource-rule shapes into small composable primitives.
Execution remains owned by the existing Condition/Target/Effect runtimes.
"""
from __future__ import annotations
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Any, Dict, Optional, Tuple


class ResourcePrimitive(str, Enum):
    TRIGGER_GAIN = "resource_gain_on_trigger"
    AFFILIATION_SCALED_GAIN = "affiliation_count_scaled_gain"
    CUMULATIVE_SPEND_GAIN = "cumulative_resource_gain"
    RESOURCE_SCALED_MODIFIER = "resource_scaled_modifier"
    RESOURCE_ZERO_CONDITION = "resource_zero"
    LOWEST_RESOURCE_TARGET = "lowest_resource_selector"
    HIGHEST_RESOURCE_TARGET = "highest_resource_selector"
    RANDOM_COUNT_SCALED = "random_target_count_scaled"
    SKILL_RECLASSIFY = "skill_reclassify"
    RESOURCE_CONSUME_TRIGGER = "resource_consume_trigger"
    SKILL_SWAP = "skill_swap"
    RESOURCE_TRIGGERED_SKILL_SWAP = "resource_triggered_skill_swap"
    RESOURCE_CONVERSION = "resource_conversion"


@dataclass(frozen=True)
class ResourceRef:
    name: str
    amount: Optional[float] = None


@dataclass(frozen=True)
class ResourcePrimitiveSpec:
    primitive: ResourcePrimitive
    resource: Optional[ResourceRef] = None
    trigger: Optional[str] = None
    threshold: Optional[float] = None
    reward: Optional[ResourceRef] = None
    affiliation: Optional[str] = None
    per_count: Optional[int] = None
    modifier: Optional[str] = None
    multiplier: Optional[float] = None
    target_selector: Optional[str] = None
    target_side: str = "self"
    effect: Optional[str] = None
    skill_tag: Optional[str] = None
    source_skill: Optional[str] = None
    target_skill: Optional[str] = None
    conversion_mode: Optional[str] = None
    params: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        out = asdict(self)
        out["primitive"] = self.primitive.value
        return out


def compose(*specs: ResourcePrimitiveSpec) -> Tuple[ResourcePrimitiveSpec, ...]:
    """Return an immutable primitive sequence for one rule clause."""
    return tuple(specs)


def validate(spec: ResourcePrimitiveSpec) -> None:
    """Reject malformed primitive declarations without guessing missing semantics."""
    p = spec.primitive
    if p is ResourcePrimitive.TRIGGER_GAIN:
        if not spec.resource or not spec.trigger:
            raise ValueError("trigger gain requires resource and trigger")
    elif p is ResourcePrimitive.AFFILIATION_SCALED_GAIN:
        if not spec.resource or not spec.affiliation or not spec.per_count:
            raise ValueError("affiliation scaled gain requires resource, affiliation, per_count")
    elif p is ResourcePrimitive.CUMULATIVE_SPEND_GAIN:
        if not spec.resource or not spec.threshold or not spec.reward:
            raise ValueError("cumulative gain requires resource, threshold, reward")
    elif p is ResourcePrimitive.RESOURCE_SCALED_MODIFIER:
        if not spec.resource or spec.multiplier is None or not spec.modifier:
            raise ValueError("resource scaled modifier requires resource, multiplier, modifier")
    elif p is ResourcePrimitive.RESOURCE_ZERO_CONDITION:
        if not spec.resource:
            raise ValueError("resource zero requires resource")
    elif p in {ResourcePrimitive.LOWEST_RESOURCE_TARGET, ResourcePrimitive.HIGHEST_RESOURCE_TARGET}:
        if not spec.resource:
            raise ValueError("resource selector requires resource")
    elif p is ResourcePrimitive.RANDOM_COUNT_SCALED:
        if not spec.affiliation or not spec.per_count:
            raise ValueError("random count scaled requires affiliation and per_count")
    elif p is ResourcePrimitive.SKILL_RECLASSIFY:
        if not spec.skill_tag:
            raise ValueError("skill reclassify requires skill_tag")
    elif p is ResourcePrimitive.RESOURCE_CONSUME_TRIGGER:
        if not spec.resource or not spec.trigger:
            raise ValueError("resource consume trigger requires resource and trigger")
    elif p in {ResourcePrimitive.SKILL_SWAP, ResourcePrimitive.RESOURCE_TRIGGERED_SKILL_SWAP}:
        if not spec.source_skill or not spec.target_skill:
            raise ValueError("skill swap requires source_skill and target_skill")
    elif p is ResourcePrimitive.RESOURCE_CONVERSION:
        if not spec.resource or not spec.reward:
            raise ValueError("resource conversion requires source and target resources")
        if spec.conversion_mode not in {"fixed", "proportional", "substitution", "transfer"}:
            raise ValueError("resource conversion requires a supported conversion_mode")


def primitive_from_effect(kind: str, params: Dict[str, Any]) -> Optional[ResourcePrimitiveSpec]:
    """Map already-declarative EffectIR kinds to a resource primitive.

    Unknown or identity-specific effects deliberately return None rather than
    being guessed into a generic primitive.
    """
    p = dict(params or {})
    if kind in {"resource_gain", "kill_resource_gain", "target_death_resource_gain"}:
        spec = ResourcePrimitiveSpec(ResourcePrimitive.TRIGGER_GAIN,
            resource=ResourceRef(str(p.get("resource", "")), p.get("amount")),
            trigger=str(p.get("trigger") or kind),
            params=p)
    elif kind == "cumulative_resource_gain":
        spec = ResourcePrimitiveSpec(ResourcePrimitive.CUMULATIVE_SPEND_GAIN,
            resource=ResourceRef(str(p.get("source_resource") or p.get("resource", ""))),
            threshold=float(p.get("threshold", p.get("consume_amount", 0)) or 0),
            reward=ResourceRef(str(p.get("reward_resource") or p.get("target_resource", "")), p.get("reward_amount")),
            params=p)
    elif kind == "resource_gain_affiliation_count":
        spec = ResourcePrimitiveSpec(ResourcePrimitive.AFFILIATION_SCALED_GAIN,
            resource=ResourceRef(str(p.get("resource", "")), p.get("amount")),
            affiliation=str(p.get("affiliation", "")), per_count=int(p.get("per_count", p.get("count", 0)) or 0),
            params=p)
    elif kind in {"resource_scaled_damage_bonus", "resource_scaled_modifier"}:
        spec = ResourcePrimitiveSpec(ResourcePrimitive.RESOURCE_SCALED_MODIFIER,
            resource=ResourceRef(str(p.get("resource", ""))),
            modifier=str(p.get("modifier", "damage_percent")),
            multiplier=float(p.get("multiplier", p.get("scale", 0)) or 0), params=p)
    elif kind == "resource_zero_transform":
        spec = ResourcePrimitiveSpec(ResourcePrimitive.RESOURCE_ZERO_CONDITION,
            resource=ResourceRef(str(p.get("resource", ""))), effect=str(p.get("effect", "")), params=p)
    elif kind in {"lowest_resource_selector", "resource_gain_lowest_allies"}:
        spec = ResourcePrimitiveSpec(ResourcePrimitive.LOWEST_RESOURCE_TARGET,
            resource=ResourceRef(str(p.get("resource", ""))), target_selector="lowest", target_side=str(p.get("target_side", "ally")), effect=str(p.get("effect", kind)), params=p)
    elif kind in {"highest_resource_selector", "resource_gain_highest_allies"}:
        spec = ResourcePrimitiveSpec(ResourcePrimitive.HIGHEST_RESOURCE_TARGET,
            resource=ResourceRef(str(p.get("resource", ""))), target_selector="highest", target_side=str(p.get("target_side", "ally")), effect=str(p.get("effect", kind)), params=p)
    elif kind == "random_target_count_scaled":
        spec = ResourcePrimitiveSpec(ResourcePrimitive.RANDOM_COUNT_SCALED,
            affiliation=str(p.get("affiliation", "")), per_count=int(p.get("per_count", p.get("count_per", 0)) or 0), target_selector="random", target_side=str(p.get("target_side", "enemy")), effect=str(p.get("effect", "")), params=p)
    elif kind == "skill_reclassify":
        spec = ResourcePrimitiveSpec(ResourcePrimitive.SKILL_RECLASSIFY,
            skill_tag=str(p.get("skill_tag", p.get("tag", ""))), params=p)
    elif kind == "resource_consume_trigger":
        spec = ResourcePrimitiveSpec(ResourcePrimitive.RESOURCE_CONSUME_TRIGGER,
            resource=ResourceRef(str(p.get("resource", "")), p.get("amount")),
            trigger=str(p.get("trigger", "")), effect=str(p.get("effect", "consume")), params=p)
    elif kind == "skill_swap":
        spec = ResourcePrimitiveSpec(ResourcePrimitive.SKILL_SWAP,
            source_skill=str(p.get("source_skill", p.get("from_skill", ""))),
            target_skill=str(p.get("target_skill", p.get("to_skill", ""))), params=p)
    elif kind == "resource_triggered_skill_swap":
        spec = ResourcePrimitiveSpec(ResourcePrimitive.RESOURCE_TRIGGERED_SKILL_SWAP,
            resource=ResourceRef(str(p.get("resource", ""))) if p.get("resource") else None,
            trigger=str(p.get("trigger", "")) or None,
            source_skill=str(p.get("source_skill", p.get("from_skill", ""))),
            target_skill=str(p.get("target_skill", p.get("to_skill", ""))), params=p)
    elif kind == "resource_convert":
        spec = ResourcePrimitiveSpec(ResourcePrimitive.RESOURCE_CONVERSION,
            resource=ResourceRef(str(p.get("source", p.get("source_resource", ""))), p.get("source_amount", p.get("amount"))),
            reward=ResourceRef(str(p.get("target", p.get("target_resource", ""))), p.get("target_amount", p.get("reward_amount"))),
            conversion_mode=str(p.get("conversion_mode", "fixed")), params=p)
    elif kind == "resource_gain_from_consumed":
        spec = ResourcePrimitiveSpec(ResourcePrimitive.RESOURCE_CONVERSION,
            resource=ResourceRef(str(p.get("source", p.get("source_resource", ""))), p.get("source_per", p.get("consume_per"))),
            reward=ResourceRef(str(p.get("target", p.get("target_resource", ""))), p.get("target_amount", p.get("reward_amount"))),
            conversion_mode="proportional", params=p)
    else:
        return None
    validate(spec)
    return spec
