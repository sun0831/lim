"""E34 Primitive Registry.

The registry is a declarative index of primitives already justified by the
E17-E33 audits.  It does not introduce a new execution runtime.  Runtime
ownership remains with the existing Condition/Target/Effect/Action/Trigger
implementations.

A registry entry records the stable primitive id, its semantic family, the
existing execution owner, and the minimal contract required by the primitive.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Iterable, Mapping, Optional, Tuple

from resource_primitive_v1 import ResourcePrimitive, ResourcePrimitiveSpec, primitive_from_effect


class PrimitiveFamily(str, Enum):
    RESOURCE = "resource"
    CONDITION = "condition"
    TARGET = "target"
    EFFECT = "effect"
    ACTION = "action"
    TRIGGER = "trigger"
    SKILL = "skill"
    STATUS = "status"
    DAMAGE_MODIFIER = "damage_modifier"
    LIFECYCLE = "lifecycle"


@dataclass(frozen=True)
class PrimitiveContract:
    """Frozen metadata for one registry primitive.

    ``owner`` names the existing runtime/IR layer that executes the primitive;
    it is deliberately not a new Runtime class.
    """

    primitive_id: str
    family: PrimitiveFamily
    owner: str
    inputs: Tuple[str, ...] = ()
    outputs: Tuple[str, ...] = ()
    aliases: Tuple[str, ...] = ()
    notes: str = ""


# E34 contract freeze: primitives already justified by E17-E33 are listed as
# canonical contracts.  Repeated audit clusters map onto these entries rather
# than becoming one runtime per audit axis.  The common contracts below are
# declarative routing contracts: they do not introduce new Runtime classes.
_CONTRACTS: Tuple[PrimitiveContract, ...] = (
    PrimitiveContract("resource_gain_on_trigger", PrimitiveFamily.RESOURCE, "ResourceRuntime", ("resource", "trigger"), ("resource_gain",)),
    PrimitiveContract("affiliation_count_scaled_gain", PrimitiveFamily.RESOURCE, "ResourceRuntime", ("resource", "affiliation", "per_count"), ("resource_gain",)),
    PrimitiveContract("cumulative_resource_gain", PrimitiveFamily.RESOURCE, "ResourceRuntime", ("resource", "threshold", "reward"), ("resource_gain",)),
    PrimitiveContract("resource_scaled_modifier", PrimitiveFamily.DAMAGE_MODIFIER, "DamageModifierRuntime", ("resource", "multiplier", "modifier"), ("damage_modifier",)),
    PrimitiveContract("resource_zero", PrimitiveFamily.CONDITION, "ConditionRuntime", ("resource",), ("condition",)),
    PrimitiveContract("lowest_resource_selector", PrimitiveFamily.TARGET, "TargetRuntime", ("resource", "target_side"), ("target_set",)),
    PrimitiveContract("highest_resource_selector", PrimitiveFamily.TARGET, "TargetRuntime", ("resource", "target_side"), ("target_set",)),
    PrimitiveContract("random_target_count_scaled", PrimitiveFamily.TARGET, "TargetRuntime", ("affiliation", "per_count", "target_side"), ("target_set",)),
    PrimitiveContract("skill_reclassify", PrimitiveFamily.SKILL, "SkillTransformContract", ("skill_tag",), ("skill_classification",)),
    PrimitiveContract("resource_consume_trigger", PrimitiveFamily.RESOURCE, "ResourceRuntime", ("resource", "trigger"), ("trigger",)),
    PrimitiveContract("skill_swap", PrimitiveFamily.SKILL, "SkillTransformContract", ("source_skill", "target_skill"), ("skill_selection",)),
    PrimitiveContract("resource_triggered_skill_swap", PrimitiveFamily.SKILL, "ConditionRuntime+SkillTransformContract", ("resource", "trigger", "source_skill", "target_skill"), ("skill_selection",)),
    PrimitiveContract("resource_conversion", PrimitiveFamily.RESOURCE, "ResourceRuntime", ("resource", "reward", "conversion_mode"), ("resource_transform",)),

    # Common contracts confirmed by E24-E33 against existing runtimes.
    PrimitiveContract("condition_threshold", PrimitiveFamily.CONDITION, "ConditionRuntime", ("field", "operator", "value"), ("condition",)),
    PrimitiveContract("condition_identity_relation", PrimitiveFamily.CONDITION, "ConditionRuntime", ("identity_id", "relation"), ("condition",)),
    PrimitiveContract("condition_status_predicate", PrimitiveFamily.CONDITION, "ConditionRuntime+StatusEffectRuntime", ("status", "operator", "value"), ("condition",)),
    PrimitiveContract("condition_hp_stagger_predicate", PrimitiveFamily.CONDITION, "ConditionRuntime", ("hp_or_stagger", "operator", "value"), ("condition",)),
    PrimitiveContract("condition_resource_predicate", PrimitiveFamily.CONDITION, "ConditionRuntime+ResourceRuntime", ("resource", "operator", "value"), ("condition",)),
    PrimitiveContract("condition_resonance_predicate", PrimitiveFamily.CONDITION, "ConditionRuntime", ("resonance", "operator", "value"), ("condition",)),
    PrimitiveContract("condition_action_state", PrimitiveFamily.CONDITION, "ConditionRuntime", ("action_state",), ("condition",)),
    PrimitiveContract("activation_limit", PrimitiveFamily.CONDITION, "TriggerRuntime", ("scope", "limit"), ("activation_guard",)),
    PrimitiveContract("explicit_target", PrimitiveFamily.TARGET, "TargetRuntime", ("target_id_or_index",), ("target_set",)),
    PrimitiveContract("random_target", PrimitiveFamily.TARGET, "TargetRuntime", ("count", "rng"), ("target_set",)),
    PrimitiveContract("target_count", PrimitiveFamily.TARGET, "TargetRuntime", ("count",), ("target_set",)),
    PrimitiveContract("speed_target_selector", PrimitiveFamily.TARGET, "TargetRuntime", ("direction",), ("target_set",)),
    PrimitiveContract("hp_target_selector", PrimitiveFamily.TARGET, "TargetRuntime", ("metric", "direction"), ("target_set",)),
    PrimitiveContract("formation_target_selector", PrimitiveFamily.TARGET, "TargetRuntime", ("direction",), ("target_set",)),
    PrimitiveContract("status_target_selector", PrimitiveFamily.TARGET, "TargetRuntime", ("status", "direction"), ("target_set",)),
    PrimitiveContract("affiliation_target_selector", PrimitiveFamily.TARGET, "AffiliationRuntime+TargetRuntime", ("affiliation", "side"), ("target_set",)),
    PrimitiveContract("specific_identity_target", PrimitiveFamily.TARGET, "TargetRuntime", ("identity_id", "side"), ("target_set",)),
    PrimitiveContract("target_relation_selector", PrimitiveFamily.TARGET, "TargetRuntime", ("relation",), ("target_set",)),
    PrimitiveContract("state_effect", PrimitiveFamily.EFFECT, "EffectRuntime", ("state_or_flag", "value"), ("state_change",)),
    PrimitiveContract("resource_effect", PrimitiveFamily.EFFECT, "EffectRuntime+ResourceRuntime", ("resource", "operation", "amount"), ("resource_change",)),
    PrimitiveContract("status_effect", PrimitiveFamily.STATUS, "StatusEffectRuntime", ("status", "operation", "potency", "count"), ("status_change",)),
    PrimitiveContract("buff_debuff_effect", PrimitiveFamily.STATUS, "BuffDebuffRuntime", ("name", "kind", "operation"), ("buff_debuff_change",)),
    PrimitiveContract("damage_modifier_effect", PrimitiveFamily.DAMAGE_MODIFIER, "DamageModifierRuntime+EffectRuntime", ("modifier", "value"), ("damage_modifier",)),
    PrimitiveContract("action_queue_effect", PrimitiveFamily.ACTION, "ActionQueue+EffectRuntime", ("action", "timing", "target"), ("queued_action",)),
    PrimitiveContract("trigger_event", PrimitiveFamily.TRIGGER, "TriggerRuntime", ("event", "conditions", "effects"), ("trigger_result",)),
    PrimitiveContract("probabilistic_trigger", PrimitiveFamily.TRIGGER, "ProbabilisticTriggerRuntime", ("event", "probability", "outcome"), ("trigger_result",)),
    PrimitiveContract("trigger_chain", PrimitiveFamily.TRIGGER, "TriggerRuntime+ActionQueue", ("source_event", "generated_action"), ("queued_action",)),
    PrimitiveContract("skill_swap_timed", PrimitiveFamily.SKILL, "SkillTransformContract", ("source_skill", "target_skill", "timing", "slot_policy"), ("skill_selection",)),
    PrimitiveContract("forced_followup_action", PrimitiveFamily.ACTION, "ActionQueue+TriggerRuntime", ("skill_or_action", "trigger"), ("queued_action",)),
    PrimitiveContract("coin_power_transform", PrimitiveFamily.SKILL, "CoinExecutionCore+DamageModifierRuntime", ("coin_or_power", "operation", "value"), ("coin_power_change",)),
    PrimitiveContract("status_lifecycle", PrimitiveFamily.LIFECYCLE, "StatusEffectLifecycle+StatusEffectRuntime", ("lifecycle",), ("status_state",)),
    PrimitiveContract("turn_lifecycle", PrimitiveFamily.LIFECYCLE, "OneTurnCoreV23+TriggerRuntime", ("timing",), ("lifecycle_event",)),
)


class PrimitiveRegistry:
    """Immutable-by-default lookup registry for E34 contracts."""

    def __init__(self, contracts: Iterable[PrimitiveContract] = _CONTRACTS):
        items = tuple(contracts)
        ids = [c.primitive_id for c in items]
        if len(ids) != len(set(ids)):
            raise ValueError("duplicate primitive_id")
        self._contracts: Dict[str, PrimitiveContract] = {c.primitive_id: c for c in items}
        self._aliases: Dict[str, str] = {}
        for c in items:
            for alias in c.aliases:
                if alias in self._aliases and self._aliases[alias] != c.primitive_id:
                    raise ValueError(f"duplicate primitive alias: {alias}")
                self._aliases[alias] = c.primitive_id

    def get(self, primitive_id: str) -> Optional[PrimitiveContract]:
        canonical = self._aliases.get(primitive_id, primitive_id)
        return self._contracts.get(canonical)

    def require(self, primitive_id: str) -> PrimitiveContract:
        contract = self.get(primitive_id)
        if contract is None:
            raise KeyError(f"unknown primitive: {primitive_id}")
        return contract

    def all(self) -> Tuple[PrimitiveContract, ...]:
        return tuple(self._contracts.values())

    def by_family(self, family: PrimitiveFamily) -> Tuple[PrimitiveContract, ...]:
        return tuple(c for c in self._contracts.values() if c.family is family)

    def resolve_effect(self, kind: str, params: Mapping[str, Any] | None = None) -> Optional[PrimitiveContract]:
        """Resolve an existing declarative Effect kind through the E17-E25 mapper."""
        spec = primitive_from_effect(kind, dict(params or {}))
        if spec is None:
            return None
        return self.get(spec.primitive.value)

    def validate_spec(self, spec: ResourcePrimitiveSpec) -> PrimitiveContract:
        contract = self.get(spec.primitive.value)
        if contract is None:
            raise KeyError(f"primitive is not registered: {spec.primitive.value}")
        return contract

    def snapshot(self) -> Dict[str, Dict[str, Any]]:
        return {
            c.primitive_id: {
                "family": c.family.value,
                "owner": c.owner,
                "inputs": list(c.inputs),
                "outputs": list(c.outputs),
                "aliases": list(c.aliases),
                "notes": c.notes,
            }
            for c in self._contracts.values()
        }


DEFAULT_REGISTRY = PrimitiveRegistry()


def get_primitive(primitive_id: str) -> PrimitiveContract:
    return DEFAULT_REGISTRY.require(primitive_id)


def resolve_effect_primitive(kind: str, params: Mapping[str, Any] | None = None) -> Optional[PrimitiveContract]:
    return DEFAULT_REGISTRY.resolve_effect(kind, params)


def registry_snapshot() -> Dict[str, Dict[str, Any]]:
    return DEFAULT_REGISTRY.snapshot()
