"""Conservative second-pass classification for E19 trigger catch-all clauses.

The classifier is an audit aid: it separates trigger clauses by their *effect/output*
shape. It does not claim game-rule execution coverage. Ambiguous clauses remain
unresolved rather than being guessed.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
from enum import Enum
import re
from typing import Any, Dict, Iterable, List

class TriggerOutput(str, Enum):
    RESOURCE_GAIN = "resource_gain"
    STATUS_EFFECT = "status_effect"
    ACTION_TRIGGER = "action_trigger"
    CONDITION_ONLY = "condition_only"
    UNRESOLVED = "unresolved"

@dataclass(frozen=True)
class TriggerClassification:
    output: TriggerOutput
    text: str
    evidence: tuple[str, ...]
    confidence: str = "medium"

_RESOURCE = re.compile(r"충전|탄환|호흡|침잠|화상|출혈|진동|파열|침전|생체 재료|장부|원한 문신|예지안|잔영|지령|대행|조망|횟수|공명|자원")
_GAIN = re.compile(r"얻음|얻는다|획득|증가|회복|충전.*증가|횟수.*증가")
_STATUS = re.compile(r"부여|버프|디버프|강화|약화|보호막|피해량 증가|공격 레벨 증가|방어 레벨 증가|해제|제거|변경됨")
_ACTION = re.compile(r"일방 공격|공격함|공격함|스킬.*사용|사용함|발동|스킬 발동|스킬로|시전|변경")
_CONDITION = re.compile(r"이면|하면|할 때|일 때|상태면|상태인 경우|적용|조건|없으면|있으면")


def classify_trigger(text: str) -> TriggerClassification:
    s = text.strip()
    if not s:
        return TriggerClassification(TriggerOutput.UNRESOLVED, s, ("empty",), "low")

    has_resource = bool(_RESOURCE.search(s))
    has_gain = bool(_GAIN.search(s))
    has_status = bool(_STATUS.search(s))
    has_action = bool(_ACTION.search(s))
    has_condition = bool(_CONDITION.search(s))

    # Resource gain is selected only when the gain target is plausibly a resource.
    if has_resource and has_gain:
        return TriggerClassification(TriggerOutput.RESOURCE_GAIN, s,
            ("resource-marker", "gain-marker"), "high")
    # Explicit skill/attack execution is an action trigger, even when a condition is present.
    if has_action and not (has_status and has_resource and has_gain):
        return TriggerClassification(TriggerOutput.ACTION_TRIGGER, s,
            ("action-marker",), "medium")
    # Status/effect output is separated from resource gain.
    if has_status:
        return TriggerClassification(TriggerOutput.STATUS_EFFECT, s,
            ("status-marker",), "medium")
    # Pure predicates with no detectable output remain conditions.
    if has_condition and not (has_gain or has_status or has_action):
        return TriggerClassification(TriggerOutput.CONDITION_ONLY, s,
            ("condition-marker",), "medium")
    return TriggerClassification(TriggerOutput.UNRESOLVED, s,
        ("no-safe-output-shape",), "low")


def reclassify_records(records: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
    rows: List[Dict[str, Any]] = []
    counts = {k.value: 0 for k in TriggerOutput}
    for r in records:
        c = classify_trigger(r.get("text", ""))
        row = {k: r.get(k) for k in ("identity_id", "identity_name", "passive_name")}
        row.update(asdict(c)); row["output"] = c.output.value
        rows.append(row); counts[c.output.value] += 1
    unique = {}
    for r in rows:
        unique.setdefault(r["text"], r["output"])
    return {"record_count": len(rows), "unique_source_texts": len(unique),
            "counts": counts, "records": rows}
