"""Conservative clause-level decomposition for resource_transform gap records.

This is an audit/normalization layer. It never claims that a whole source sentence
is one primitive: one clause can yield several primitive candidates. Low-confidence
or unsupported clauses remain unresolved.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
from enum import Enum
import re
from typing import Iterable, List, Dict, Any

class CandidateKind(str, Enum):
    TRIGGER = "trigger"
    RESOURCE_GAIN = "resource_gain"
    RESOURCE_CONSUME = "resource_consume"
    RESOURCE_TRANSFORM = "resource_transform"
    AFFILIATION_COUNT = "affiliation_count"
    RESOURCE_SCALED_MODIFIER = "resource_scaled_modifier"
    RESOURCE_ZERO = "resource_zero"
    LOWEST_RESOURCE_TARGET = "lowest_resource_selector"
    RANDOM_TARGET = "random_target"
    COUNT_SCALING = "count_scaling"
    SKILL_TRANSFORM = "skill_transform"
    STATUS_EFFECT = "status_effect"
    UNRESOLVED = "unresolved"

@dataclass(frozen=True)
class PrimitiveCandidate:
    kind: CandidateKind
    text: str
    confidence: str = "medium"
    evidence: tuple[str, ...] = ()

_TRIGGER = re.compile(r"피격|적중|처치|사망|공격 종료|턴 시작|턴 종료|전투 시작|사용 시|사용할 때|합 승리|크리티컬|흐트러짐")
_GAIN = re.compile(r"얻음|획득|증가|부여|회복")
_CONSUME = re.compile(r"소모|소비|차감")
_ZERO = re.compile(r"(?:0|없으면|없을 경우|없을 때|부족하면)")
_AFF = re.compile(r"소속|아군 인격|적 인격|편성된")
_LOW = re.compile(r"가장 적|가장 낮|최저|가장 느린|가장 높은|최대 체력")
_RANDOM = re.compile(r"무작위|랜덤")
_SCALE = re.compile(r"당|마다|비례|\b\d+\b|\d+%|×|x")
_MOD = re.compile(r"피해량|피해|공격 위력|공격 레벨|방어 레벨|코인 위력|크리티컬 피해량")
_SKILL = re.compile(r"스킬.*변경|변경.*스킬|스킬로 변경|간주")
_STATUS = re.compile(r"부여|제거|해제|버프|디버프")

def decompose_clause(text: str) -> List[PrimitiveCandidate]:
    s=text.strip().lstrip("-· ")
    if not s: return []
    out=[]
    def add(kind,evidence,confidence="medium"):
        out.append(PrimitiveCandidate(kind,s,confidence,tuple(evidence)))
    if _TRIGGER.search(s): add(CandidateKind.TRIGGER,["trigger-marker"])
    if _GAIN.search(s): add(CandidateKind.RESOURCE_GAIN,["gain-marker"])
    if _CONSUME.search(s): add(CandidateKind.RESOURCE_CONSUME,["consume-marker"])
    if _ZERO.search(s) and re.search(r"충전|재료|조망|예지안|장부|원한|탄환|횟수|자원|재료",s):
        add(CandidateKind.RESOURCE_ZERO,["zero-marker"])
    if _AFF.search(s): add(CandidateKind.AFFILIATION_COUNT,["affiliation-marker"])
    if _LOW.search(s): add(CandidateKind.LOWEST_RESOURCE_TARGET,["selector-marker"])
    if _RANDOM.search(s): add(CandidateKind.RANDOM_TARGET,["random-marker"])
    if _SCALE.search(s): add(CandidateKind.COUNT_SCALING,["scaling-marker"])
    if _MOD.search(s) and _GAIN.search(s): add(CandidateKind.RESOURCE_SCALED_MODIFIER,["modifier+gain"])
    if _SKILL.search(s): add(CandidateKind.SKILL_TRANSFORM,["skill-transform-marker"])
    # Status effects are deliberately a candidate, not a forced classification.
    if _STATUS.search(s) and not (_GAIN.search(s) and re.search(r"자원|충전|재료|장부|원한|탄환",s)):
        add(CandidateKind.STATUS_EFFECT,["status-marker"])
    if not out: add(CandidateKind.UNRESOLVED,["no-safe-pattern"],"low")
    return out

def decompose_records(records: Iterable[Dict[str,Any]]) -> Dict[str,Any]:
    records=list(records)
    clauses=[]; counts={k.value:0 for k in CandidateKind}; unresolved=[]
    for r in records:
        for raw in re.split(r"\n+",r.get("source_text", "")):
            for c in decompose_clause(raw):
                item={"identity_id":r.get("identity_id"),"identity_name":r.get("identity_name"),"passive_name":r.get("passive_name"),**asdict(c)}
                item["kind"]=c.kind.value
                clauses.append(item); counts[c.kind.value]+=1
                if c.kind is CandidateKind.UNRESOLVED: unresolved.append(item)
    return {"record_count":len(records),"clause_candidate_count":len(clauses),"candidate_counts":counts,"unresolved_count":len(unresolved),"clauses":clauses}
