"""Shared lifecycle/value taxonomy for Limbus status effects.

Lifecycle and value semantics are deliberately separate.  A status may both
consume a value on an event and expire by turn progression (e.g. core keywords),
so the catalog exposes independent ``consumption`` and ``expiration`` fields.
The legacy single ``lifecycle`` classification remains available for backwards
compatibility and is derived conservatively.
"""
from __future__ import annotations
from enum import Enum
from pathlib import Path
from typing import Any, Mapping
import json


class StatusLifecycle(str, Enum):
    CONSUME = "consume"
    TURN = "turn"
    RULE = "rule"
    UNSPECIFIED = "unspecified"


_CATALOG_PATH = Path(__file__).with_name("status_effect_catalog_v1.json")
try:
    _CATALOG = json.loads(_CATALOG_PATH.read_text(encoding="utf-8"))
    STATUS_EFFECT_CATALOG = {x["name"]: x for x in _CATALOG.get("effects", [])}
except Exception:
    STATUS_EFFECT_CATALOG = {}


def get_status_effect_spec(name: str) -> dict[str, Any] | None:
    item = STATUS_EFFECT_CATALOG.get(str(name))
    return dict(item) if item else None


def classify_status_effect(name: str, spec: Mapping[str, Any] | None = None) -> StatusLifecycle:
    """Return the legacy primary lifecycle without guessing unknown effects.

    Explicit lifecycle wins.  Otherwise the catalog's independent consumption
    and expiration fields are collapsed only for compatibility: rule expiry has
    priority, then event/resource consumption, then turn expiry.
    """
    incoming = dict(spec or {})
    catalog = get_status_effect_spec(str(name)) or {}
    merged = {**catalog, **incoming}
    explicit = merged.get("lifecycle")
    if explicit:
        return StatusLifecycle(str(explicit))
    expiration = str(merged.get("expiration", ""))
    consumption = str(merged.get("consumption", ""))
    if expiration.startswith("rule") or expiration in {"death", "death_or_rule", "skill_or_rule"}:
        return StatusLifecycle.RULE
    if consumption and consumption not in {"none", "turn_end"}:
        return StatusLifecycle.CONSUME
    if expiration.startswith("turn") or expiration in {"count_zero", "stack_zero"}:
        return StatusLifecycle.TURN
    if merged.get("consume_on") or merged.get("resource_consumer"):
        return StatusLifecycle.CONSUME
    return StatusLifecycle.UNSPECIFIED


def lifecycle_profile(name: str, spec: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Return normalized catalog semantics for runtime consumers."""
    catalog = get_status_effect_spec(str(name)) or {}
    merged = {**catalog, **dict(spec or {})}
    return {
        "lifecycle": classify_status_effect(name, spec).value,
        "consumption": merged.get("consumption", "none"),
        "expiration": merged.get("expiration", "unspecified"),
        "value_mode": merged.get("value_mode", "unspecified"),
        "value_semantics": dict(merged.get("value_semantics") or {}),
        "category": merged.get("category", "unspecified"),
    }


def validate_lifecycle_spec(spec: Mapping[str, Any]) -> None:
    lifecycle = StatusLifecycle(str(spec.get("lifecycle", "unspecified")))
    if lifecycle is StatusLifecycle.CONSUME and not spec.get("consume_on") and not spec.get("resource_consumer"):
        # Catalog-backed effects may declare a consumption mode instead of an
        # event name; retain the old strict contract for hand-authored rules.
        if not spec.get("consumption"):
            raise ValueError("CONSUME lifecycle requires consume_on/resource_consumer/consumption")
    if lifecycle is StatusLifecycle.TURN and spec.get("duration") is None and not spec.get("turn_end_expiry", False) and not spec.get("expiration"):
        raise ValueError("TURN lifecycle requires duration, turn_end_expiry, or expiration")
    if lifecycle is StatusLifecycle.RULE and not (spec.get("rule_expiry") or spec.get("rule_trigger") or spec.get("conversion_rule") or spec.get("expiration")):
        raise ValueError("RULE lifecycle requires rule_expiry, rule_trigger, conversion_rule, or expiration")
