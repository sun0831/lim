"""Conservative audit of resource-consumption clauses.

This module classifies clauses; it does not claim end-to-end game-rule execution.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
from enum import Enum
from typing import Iterable
import re

class ConsumptionClass(str, Enum):
    CUMULATIVE_SPEND_REWARD = "cumulative_spend_reward"
    CONSUME_TRIGGER = "consume_trigger"
    CONSUME_DURING_ACTION = "consume_during_action"
    DIRECT_CONSUME_EFFECT = "direct_consume_effect"
    CONSUME_CONVERSION = "consume_conversion"
    CONSUME_TRACKING_MODIFIER = "consume_tracking_modifier"
    CONSUME_CONDITION = "consume_condition"
    UNRESOLVED = "unresolved"

@dataclass(frozen=True)
class ConsumptionAudit:
    text: str
    classification: ConsumptionClass
    evidence: tuple[str, ...]
    primitive: str | None

_CUM = re.compile(r"누적.*소모.*때마다")
_TRIGGER = re.compile(r"소모(?:할|하면|했다면|할 때|하는|한).*?(?:얻|부여|증가|감소|추가|발동|피해|회복|문신|호흡|재장전)")
_CONVERSION = re.compile(r"소모.*?(?:얻음|얻고|보급|재장전|변경|변환)")
_TRACK = re.compile(r"소모한.*?(?:피해량|수치|합|만큼|비례)")
_CONDITION = re.compile(r"(?:소모.*?경우|소모.*?없으면|소모.*?이상이면|소모.*?0이면|소모.*?적용)")

def classify_consumption_clause(text: str) -> ConsumptionAudit:
    t = text.strip()
    if _CUM.search(t):
        return ConsumptionAudit(t, ConsumptionClass.CUMULATIVE_SPEND_REWARD, ("cumulative-spend marker",), "cumulative_resource_gain")
    if _CONDITION.search(t) and not _TRIGGER.search(t):
        return ConsumptionAudit(t, ConsumptionClass.CONSUME_CONDITION, ("consumption used as predicate/fallback",), None)
    if _CONVERSION.search(t) and any(x in t for x in ("얻", "보급", "재장전", "변경", "변환")):
        # Conversion is still an effect of consumption, but deserves a separate audit bucket.
        if "소모한" in t or "소모하여" in t or "소모되면" in t or "소모하면" in t:
            return ConsumptionAudit(t, ConsumptionClass.CONSUME_CONVERSION, ("consumption-to-new-state/resource",), "resource_consume_trigger")
    if _TRACK.search(t):
        return ConsumptionAudit(t, ConsumptionClass.CONSUME_TRACKING_MODIFIER, ("consumed amount reused as parameter",), "resource_consume_trigger")
    if _TRIGGER.search(t):
        return ConsumptionAudit(t, ConsumptionClass.CONSUME_TRIGGER, ("consumption event causes downstream effect",), "resource_consume_trigger")
    if "소모" in t and any(x in t for x in ("전부 소모", "소모하여", "소모하고")):
        return ConsumptionAudit(t, ConsumptionClass.DIRECT_CONSUME_EFFECT, ("direct consume operation",), None)
    if "소모" in t:
        return ConsumptionAudit(t, ConsumptionClass.CONSUME_DURING_ACTION, ("consumption tied to action/coin",), None)
    return ConsumptionAudit(t, ConsumptionClass.UNRESOLVED, (), None)

def audit_clauses(clauses: Iterable[dict]) -> list[dict]:
    out=[]
    for c in clauses:
        a=classify_consumption_clause(c.get("text", ""))
        row=dict(c)
        row.update({"classification": a.classification.value, "evidence": list(a.evidence), "primitive": a.primitive})
        out.append(row)
    return out
