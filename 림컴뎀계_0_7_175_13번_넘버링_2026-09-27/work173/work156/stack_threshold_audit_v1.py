"""E29 semantic audit for the stack_threshold gap axis.

This is an audit/normalization layer, not a new StackThresholdRuntime. The
existing ConditionRuntime already exposes generic numeric comparisons plus
resource/status-specific threshold operators. The audit maps clauses to those
existing contracts and leaves genuinely composite timing/action semantics to
those runtimes instead of inventing a new axis-specific runtime.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import List
import re

@dataclass(frozen=True)
class ThresholdRoute:
    route: str
    confidence: str
    reason: str


def route_clause(text: str) -> List[ThresholdRoute]:
    routes: List[ThresholdRoute] = []
    if re.search(r"누적.*(?:소모|얻)|\d+.*(?:소모할 때마다|이상|이하|미만)|수치가? 0|횟수 \d+", text):
        routes.append(ThresholdRoute("numeric_or_resource_threshold", "high", "generic numeric/resource threshold or threshold crossing"))
    if re.search(r"충전|생체 재료|예지안|경혈|꽃잎|적안|참회|사랑/증오|지령의 가호|호흡(?: 위력| 횟수)?|연료|주살|공명", text):
        routes.append(ThresholdRoute("resource_or_stack_threshold", "high", "resource/stack-like value is thresholded"))
    if re.search(r"출혈.*\d+|화상.*\d+|침잠.*\d+|진동.*\d+|잔향.*\d+|도발치.*\d+", text):
        routes.append(ThresholdRoute("status_threshold", "high", "status potency/count threshold"))
    if re.search(r"정신력.*(?:\d+|이상|미만)|정신력이? 0", text):
        routes.append(ThresholdRoute("mental_threshold", "high", "mental/SP threshold; generic comparison"))
    if re.search(r"(?:체력|잃은 체력).*\d+%|체력이? \d+%|체력 비율", text):
        routes.append(ThresholdRoute("hp_threshold", "high", "HP percentage threshold"))
    if re.search(r"속도.*\d+|속도가?.*(?:가장 빠른|가장 느린)", text):
        routes.append(ThresholdRoute("speed_threshold", "high", "speed comparison/selector condition"))
    if re.search(r"공명 수", text):
        routes.append(ThresholdRoute("resonance_threshold", "high", "resonance-count threshold"))
    if re.search(r"턴당|전투당|최대 \d+회|스킬당 \d+회", text):
        routes.append(ThresholdRoute("activation_limit", "high", "activation cap belongs to trigger/ledger, not threshold primitive"))
    if not routes:
        routes.append(ThresholdRoute("contextual_recheck", "low", "threshold semantics need surrounding clause context"))
    # Deduplicate route labels while preserving order.
    seen=set(); out=[]
    for r in routes:
        if r.route not in seen:
            seen.add(r.route); out.append(r)
    return out
