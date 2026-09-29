"""Adapters between the new Rule IR and the legacy trigger/gimmick rule types.

The bridge is intentionally loss-aware: fields that have no exact IR equivalent
are retained in ``metadata`` instead of being silently discarded.
"""
from __future__ import annotations
from typing import Any, Iterable, List
import hashlib
from rule_ir_v1 import RuleIR, ConditionIR, EffectIR, TargetIR


def condition_from_legacy(condition: Any) -> ConditionIR:
    if hasattr(condition, "to_dict"):
        raw = condition.to_dict()
    elif isinstance(condition, dict):
        raw = dict(condition)
    else:
        raw = {"type": str(condition)}
    op = str(raw.pop("type", raw.pop("op", "unknown")))
    return ConditionIR(op=op, args=raw)


def effect_from_legacy(effect: Any) -> EffectIR:
    if hasattr(effect, "to_dict"):
        raw = effect.to_dict()
    elif isinstance(effect, dict):
        raw = dict(effect)
    else:
        raw = {"type": str(effect)}
    kind = str(raw.pop("type", raw.pop("kind", "unknown")))
    return EffectIR(kind=kind, params=raw)


def trigger_rule_to_ir(rule: Any) -> RuleIR:
    """Convert a legacy TriggerRule-like object without changing the object."""
    meta = dict(getattr(rule, "metadata", {}) or {})
    target = None
    target_raw = meta.get("target")
    if isinstance(target_raw, dict):
        target = TargetIR(
            side=str(target_raw.get("side", "self")),
            selector=str(target_raw.get("selector", "self")),
            count=int(target_raw.get("count", 1)),
            filters=dict(target_raw.get("filters", {})),
        )
    effects = tuple(effect_from_legacy(e) for e in getattr(rule, "effects", []) or [])
    conditions = tuple(condition_from_legacy(c) for c in getattr(rule, "conditions", []) or [])
    return RuleIR(
        rule_id=str(getattr(rule, "id", "")),
        owner_id=str(getattr(rule, "owner_id", "")),
        trigger=str(getattr(rule, "event", "")),
        conditions=conditions,
        target=target,
        effects=effects,
        timing=str(meta.get("timing", "immediate")),
        activation_limit=getattr(rule, "max_activations", None),
        source_text=str(getattr(rule, "source_text", "")),
        dependencies=tuple(str(x) for x in meta.get("dependencies", ()) or ()),
        status=str(meta.get("status", "implemented")),
        activation_scope=str(meta.get("activation_scope", getattr(rule, "activation_scope", "global"))),
        metadata=meta,
    )


def gimmick_rule_to_ir(rule: Any) -> RuleIR:
    """Convert the compatibility GimmickRule into the common IR.

    Gimmick-specific fields are preserved under EffectIR params so the adapter
    is reversible enough for migration/debugging while the legacy runtime stays
    untouched.
    """
    params = {
        "kind": str(getattr(rule, "kind", "unknown")),
        "trigger_skill_names": list(getattr(rule, "trigger_skill_names", ()) or ()),
        "actor_hint": getattr(rule, "actor_hint", None),
        "skill_hint": getattr(rule, "skill_hint", None),
        "require_start_not_staggered": bool(getattr(rule, "require_start_not_staggered", False)),
        "require_end_staggered": bool(getattr(rule, "require_end_staggered", False)),
        "extra_scale": float(getattr(rule, "extra_scale", 0.0)),
        "activation_scope": str(getattr(rule, "activation_scope", "global")),
        "module": getattr(rule, "module", None),
    }
    source_text = str(getattr(rule, "source_text", ""))
    stable_key = "|".join((
        str(getattr(rule, "owner_id", "")),
        str(getattr(rule, "kind", "")),
        source_text,
    ))
    digest = hashlib.sha1(stable_key.encode("utf-8")).hexdigest()[:16]
    conditions = []
    if bool(getattr(rule, "require_start_not_staggered", False)):
        conditions.append(ConditionIR("action_start_not_staggered"))
    if bool(getattr(rule, "require_end_staggered", False)):
        conditions.append(ConditionIR("action_end_staggered"))
    skills = tuple(getattr(rule, "trigger_skill_names", ()) or ())
    if skills:
        conditions.append(ConditionIR("skill_name_any", {"value": list(skills)}))
    if getattr(rule, "actor_hint", None):
        conditions.append(ConditionIR("actor_id", {"value": getattr(rule, "actor_hint")}))
    if getattr(rule, "skill_hint", None):
        conditions.append(ConditionIR("skill_name_contains", {"value": getattr(rule, "skill_hint")}))
    return RuleIR(
        rule_id=f"gimmick:{getattr(rule, 'owner_id', '')}:{getattr(rule, 'kind', '')}:{digest}",
        owner_id=str(getattr(rule, "owner_id", "")),
        trigger=str(getattr(rule, "kind", "")),
        conditions=tuple(conditions),
        effects=(EffectIR("legacy_gimmick", params),),
        timing="event",
        activation_limit=getattr(rule, "max_activations", None),
        source_text=source_text,
        status="legacy",
        activation_scope=str(getattr(rule, "activation_scope", "global")),
    )


def compile_trigger_rules(rules: Iterable[Any]) -> List[RuleIR]:
    """Compile legacy TriggerRule objects into the common IR without mutation."""
    return [trigger_rule_to_ir(rule) for rule in rules]


def compile_gimmick_rules(rules: Iterable[Any]) -> List[RuleIR]:
    """Compile legacy GimmickRule objects into the common IR without mutation."""
    return [gimmick_rule_to_ir(rule) for rule in rules]
