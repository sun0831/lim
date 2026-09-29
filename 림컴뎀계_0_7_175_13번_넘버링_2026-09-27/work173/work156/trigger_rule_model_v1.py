"""Declarative trigger rule definition shared by Runtime and production code.

Activation state is intentionally not stored on TriggerRule.  The canonical
runtime owner is ActivationLedger; the legacy constructor keeps positional
argument compatibility for old data/tests but ignores the retired mutable
counter arguments.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

@dataclass(frozen=True)
class TriggerCondition:
    type: str
    value: Any = None
    field: Optional[str] = None
    negate: bool = False
    def to_dict(self):
        d={"type":self.type}
        if self.value is not None: d["value"]=self.value
        if self.field is not None: d["field"]=self.field
        if self.negate: d["negate"]=True
        return d

@dataclass(frozen=True)
class TriggerEffect:
    type: str
    params: Dict[str, Any] = field(default_factory=dict)
    def to_dict(self): return {"type":self.type, **self.params}

@dataclass(init=False)
class TriggerRule:
    """Rule definition only; activation state lives in ActivationLedger."""
    id: str
    owner_id: str
    event: str
    conditions: List[TriggerCondition]
    effects: List[TriggerEffect]
    max_activations: int
    activation_scope: str
    source_text: str
    metadata: Dict[str, Any]

    def __init__(self, id: str, owner_id: str, event: str,
                 conditions: Optional[List[TriggerCondition]] = None,
                 effects: Optional[List[TriggerEffect]] = None,
                 max_activations: int = 1,
                 _legacy_activations: int = 0,
                 activation_scope: str = 'global',
                 _legacy_activation_buckets: Optional[Dict[str, int]] = None,
                 source_text: str = "",
                 metadata: Optional[Dict[str, Any]] = None):
        self.id = id
        self.owner_id = owner_id
        self.event = event
        self.conditions = list(conditions or [])
        self.effects = list(effects or [])
        self.max_activations = int(max_activations)
        self.activation_scope = activation_scope
        self.source_text = source_text
        self.metadata = dict(metadata or {})

    def to_dict(self):
        return {"id":self.id,"owner_id":self.owner_id,"event":self.event,
                "conditions":[c.to_dict() for c in self.conditions],
                "effects":[e.to_dict() for e in self.effects],
                "max_activations":self.max_activations,"activation_scope":self.activation_scope,
                "source_text":self.source_text,"metadata":dict(self.metadata)}
