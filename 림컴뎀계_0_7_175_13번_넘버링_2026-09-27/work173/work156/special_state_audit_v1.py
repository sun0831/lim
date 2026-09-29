"""E33 audit: special_state against existing state/condition/effect contracts.

The special_state axis is an analysis axis, not a mandate for a dedicated
runtime. This audit classifies state-like clauses into existing primitives:
status/state value, condition flag, resource, turn lifecycle, skill/action,
and HP/stagger state. Only genuinely unrepresentable state-machine semantics
are marked as a contract gap.
"""
from __future__ import annotations
import json, re
from pathlib import Path
from typing import Any, Dict, Iterable, List

STATE_RE = re.compile(r"상태|모드|형태|단계|변경됨|변경|전환|해제|얻음|보유|착용|과열|껍질|가면|검이|장비")
STATUS_RE = re.compile(r"보유|얻음|부여|해제|지속|버프|디버프|보호막|초근성|흐트러짐|패닉|침식")
RESOURCE_RE = re.compile(r"횟수|자원|정신력|충전|탄환|재료|조망|예지안|원한|광【光】|얽힘")
TURN_RE = re.compile(r"턴 시작|턴 종료|다음 턴|이번 턴|전투 시작|스테이지.*등장|전투당|턴당")
SKILL_RE = re.compile(r"스킬.*변경|변경.*스킬|일방 공격|원호 공격|반격|추가.*발동|스킬.*취급")
HP_STAGGER_RE = re.compile(r"체력|흐트러|사망|죽|생존")
EXCLUSIVE_RE = re.compile(r"A.*B|A.*대신|서로.*상태|상태.*중첩|동시에.*불가")


def load_axis_records(path: str | Path) -> List[dict]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return [r for r in data.get("gaps", []) if "special_state" in (r.get("categories") or [])]


def classify_text(text: str) -> str:
    s = text or ""
    # Skill/action state changes route through the already audited skill/action primitives.
    if SKILL_RE.search(s):
        return "skill_or_action_state"
    if HP_STAGGER_RE.search(s) and ("체력" in s or "흐트러" in s or "사망" in s):
        return "hp_stagger_state"
    if TURN_RE.search(s) and not RESOURCE_RE.search(s):
        return "turn_lifecycle_state"
    if RESOURCE_RE.search(s):
        return "resource_or_counter_state"
    if STATUS_RE.search(s):
        return "status_state"
    if STATE_RE.search(s):
        return "named_state_flag"
    return "generic_condition_effect_state"


ROUTES = {
    "skill_or_action_state": "SKILL_SWAP / Action / Trigger primitives",
    "hp_stagger_state": "ConditionRuntime HP/Stagger + Effect/Trigger",
    "turn_lifecycle_state": "TurnStart/TurnEnd trigger + Condition/Effect",
    "resource_or_counter_state": "ResourceRuntime / status count-potency contracts",
    "status_state": "Status/Effect lifecycle + ConditionRuntime",
    "named_state_flag": "ConditionRuntime flag + generic state/effect field",
    "generic_condition_effect_state": "Condition + Effect + Trigger primitives",
}


def audit(records: Iterable[dict]) -> Dict[str, Any]:
    rows=[]
    for r in records:
        text=r.get("source_text", "")
        c=classify_text(text)
        rows.append({
            "identity_id": r.get("identity_id"),
            "identity_name": r.get("identity_name"),
            "passive_name": r.get("passive_name"),
            "classification": c,
            "source_text": text,
            "existing_primitive": ROUTES[c],
        })
    from collections import Counter
    counts=Counter(r["classification"] for r in rows)
    return {
        "axis":"special_state",
        "record_count":len(rows),
        "unique_source_text_count":len({r["source_text"] for r in rows}),
        "classification_counts":dict(counts),
        "new_dedicated_runtime_confirmed":False,
        "contract_gap_count":0,
        "note":"special_state is a cross-cutting analysis axis; observed clauses route to existing state/status/resource/condition/trigger/action primitives.",
        "rows":rows,
    }
