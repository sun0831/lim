"""Catalog-driven status-effect adapter.

This layer does not invent mechanics for identity-specific effects.  It only
translates catalog entries whose value semantics have an unambiguous mapping to
existing DamageModifierRuntime fields.  Unsupported/compound effects remain
explicitly deferred for dedicated Rule/Keyword runtimes.
"""
from __future__ import annotations
from typing import Any, Dict, Mapping

from status_effect_lifecycle_v1 import get_status_effect_spec, lifecycle_profile
from buff_debuff_runtime_v1 import BuffDebuffRuntime

# Catalog value-semantic -> common modifier field.
SEMANTIC_TO_MODIFIER = {
    "damage_scale": "damage_percent",
    "damage_taken_scale": "damage_percent",
    "final_power": "skill_power",
    "clash_power": "clash_power",
    "base_power": "base_power_bonus",
    "offense_level": "attack_level_bonus",
    "defense_level": "defense_level_bonus",
    "crit_damage_scale": "critical_damage_percent",
    # Weak-resist DMG Boost is target-resistance conditional and must not be
    # collapsed into unconditional damage_percent. It remains deferred until
    # the damage resolver can prove the target is weak to the attack type.
    "plus_coin_power": "plus_coin_power",
    "minus_coin_power": "minus_coin_power",
}

class StatusEffectRuntime:
    """Apply catalog-backed common status semantics without guessing special rules."""

    @classmethod
    def _modifier_for(cls, name: str, *, value: float, kind: str) -> tuple[Dict[str, float], Dict[str, Any]]:
        spec = get_status_effect_spec(name)
        if not spec:
            return {}, {"supported": False, "reason": "unknown_catalog_effect"}
        semantics = dict(spec.get("value_semantics") or {})
        category = str(spec.get("category", "unspecified"))
        modifiers: Dict[str, float] = {}
        mapped = []
        for semantic, modifier in SEMANTIC_TO_MODIFIER.items():
            if semantic not in semantics.values():
                continue
            # Positive effects increase the mapped value; negative effects
            # decrease it.  Damage-taken effects use the same signed channel:
            # positive Protection reduces incoming damage, Fragile increases it.
            sign = 1.0 if category == "positive" else -1.0 if category == "negative" else 1.0
            if semantic == "damage_taken_scale":
                sign *= -1.0
            amount = float(value)
            if semantic in {"damage_scale", "damage_taken_scale", "crit_damage_scale"}:
                # Source definitions use X*10% per stack for these common
                # percentage effects; runtime stores decimal multipliers.
                amount /= 10.0
            modifiers[modifier] = modifiers.get(modifier, 0.0) + sign * amount
            mapped.append({"semantic": semantic, "modifier": modifier, "sign": sign})
        if not mapped:
            return {}, {"supported": False, "reason": "no_unambiguous_common_modifier"}
        return modifiers, {"supported": True, "mapped": mapped, "profile": lifecycle_profile(name)}

    @classmethod
    def apply_catalog_effect(cls, state, *, target_id: str, name: str, kind: str = "buff",
                             value: float | None = None, potency: int = 0, count: int = 0,
                             source_id: str = "", rule_id: str = "", **kwargs) -> Dict[str, Any]:
        spec = get_status_effect_spec(name) or {}
        semantics = dict(spec.get("value_semantics") or {})
        max_count = spec.get("max_count")
        if max_count is not None:
            count = min(int(count), int(max_count))
        if value is None:
            # The catalog's *key* (potency/count/stack/value) is authoritative
            # for where the numeric strength comes from.  Looking only at the
            # semantic value is unsafe because e.g. Power Up uses Count while
            # Power Down uses Potency even though both mean final_power.
            value = 1.0
            for source_key, source_value in semantics.items():
                if source_key == "count":
                    value = float(count); break
                if source_key in {"potency", "stack"}:
                    value = float(potency); break
                if source_key == "value":
                    value = float(count if count else potency); break
        modifiers, meta = cls._modifier_for(name, value=float(value), kind=kind)
        if not meta.get("supported"):
            return {"applied": False, "deferred": True, "name": name, **meta}
        modifier_policy = dict(kwargs.pop("modifier_policy", {}) or {})
        skill_scope = spec.get("skill_scope")
        if skill_scope:
            modifier_policy["skill_scope"] = str(skill_scope)
        item = BuffDebuffRuntime.apply(
            state, target_id=str(target_id), name=str(name), kind=kind,
            potency=int(potency), count=int(count), modifiers=modifiers,
            modifier_policy=modifier_policy,
            max_count=(int(max_count) if max_count is not None else None),
            source_id=str(source_id), rule_id=str(rule_id), **kwargs
        )
        return {"applied": True, "deferred": False, "applied_value": float(value), "item": item, **meta}

    @classmethod
    def inspect(cls, name: str) -> Dict[str, Any]:
        spec = get_status_effect_spec(name)
        if not spec:
            return {"name": name, "supported": False, "reason": "unknown_catalog_effect"}
        modifiers, meta = cls._modifier_for(name, value=1.0, kind="buff")
        return {"name": name, "supported": bool(meta.get("supported")),
                "candidate_modifiers": modifiers, **meta}
