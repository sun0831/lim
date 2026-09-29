"""E27 conservative cross-identity clause decomposition and primitive-gap audit.

Cross-identity is treated as an analysis axis, not a standalone runtime. A clause may
hit multiple semantic clusters. This module deliberately leaves ambiguous clauses
unresolved rather than inventing identity-specific semantics.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
from enum import Enum
import re
from typing import Any, Iterable

class CrossCluster(str, Enum):
    AFFILIATION_MEMBERSHIP_COUNT = "affiliation_membership_count"
    CROSS_IDENTITY_EVENT_TRIGGER = "cross_identity_event_trigger"
    CROSS_IDENTITY_TARGET_SELECTION = "cross_identity_target_selection"
    CROSS_IDENTITY_RESOURCE_EFFECT = "cross_identity_resource_effect"
    CROSS_IDENTITY_STATUS_EFFECT = "cross_identity_status_effect"
    CROSS_IDENTITY_SKILL_ACTION = "cross_identity_skill_action"
    OWNER_PARTICIPANT_RELATION = "owner_participant_relation"
    FORMATION_PRIORITY_SELECTOR = "formation_priority_selector"
    SPECIFIC_IDENTITY_REFERENCE = "specific_identity_reference"
    OUT_OF_AXIS = "non_cross_identity_clause"
    UNRESOLVED = "unresolved_cross_identity"

class Match(str, Enum):
    EXISTING_AFFILIATION = "existing_affiliation_resolver"
    EXISTING_TARGET = "existing_target_selector"
    EXISTING_TRIGGER = "existing_trigger_runtime"
    EXISTING_RESOURCE = "existing_resource_runtime"
    EXISTING_STATUS = "existing_status_runtime"
    EXISTING_ACTION = "existing_action_runtime"
    PARTIAL = "partial_common_primitives"
    NEW = "new_primitive_candidate"
    UNRESOLVED = "unresolved"

@dataclass(frozen=True)
class Clause:
    record_index: int
    identity_id: str
    identity_name: str
    passive_name: str
    text: str

@dataclass(frozen=True)
class Hit:
    cluster: CrossCluster
    confidence: str
    evidence: tuple[str, ...]
    match: Match
    missing: tuple[str, ...] = ()

_AFF = re.compile(r"소속|가문|협회|사무소|거미집|중지|흑운회|피쿼드호|검계|세븐|리우|W사|N사|LCCB|마침표|약지|라만차|흑수|가씨")
_COUNT = re.compile(r"\d+명당|\d+명 이상|\d+명 이하|\d+명 사망|\d+명|인원|몇 명|명일 때")
_EVENT = re.compile(r"피격|적중|처치|사망|사망한|공격 종료|공격당|공격하여|스킬 사용|스킬을 사용|대기해제|복귀|등장|전투 시작|턴 시작|턴 종료|합 승리|발동")
_TARGET = re.compile(r"가장 (낮|높|빠르|느리)|정신력이 가장|속도가 가장|최대 체력이 가장|탄환을 가장|충전 횟수가 가장|진동 횟수가 가장|도발치가 가장|편성 순서|특정.*아군")
_RESOURCE = re.compile(r"충전|탄환|호흡|침잠|화상|출혈|진동|파열|생체 재료|혈찬|앙갚음|원한 문신|오혈|조망|정신력|자원|횟수")
_STATUS = re.compile(r"부여|얻음|증가|감소|회복|보호막|버프|디버프|피해량 증가|공격 레벨|방어 레벨|해제|강화|약화")
_ACTION = re.compile(r"일방 공격|공격함|공격한다|스킬.*사용|사용함|발동함|발동|명령|스킬로 변경|변경")
_OWNER = re.compile(r"자신을 제외|자신 포함|자신 또는|자신이|자신의|다른 아군|아군 인격|동료")
_SPECIFIC = re.compile(r"\[[^\]]+\]|‘[^’]+’|E\.G\.O|홍루|히스클리프|료슈|돈키호테|이스마엘|싱클레어|파우스트|이상|로쟈|그레고르|뫼르소")
_FORMATION = re.compile(r"편성 순서|가장 빠른 슬롯|가장 왼쪽|후방|대기 인원|출전 중|출전")

def split_clauses(text: str) -> list[str]:
    # Preserve bullets while splitting on sentence-like boundaries.
    parts=[]
    for block in re.split(r"\n+|\s+/-\s+", text or ""):
        block=block.strip(" /-•")
        if not block: continue
        # Keep Korean rule sentences together unless separated by explicit punctuation.
        subs=re.split(r"(?<=다)\.\s+|(?<=음)\.\s+", block)
        parts.extend(s.strip() for s in subs if s.strip())
    return parts

def classify_clause(text: str) -> tuple[Hit, ...]:
    s=text.strip(); hits=[]
    has_aff=bool(_AFF.search(s)); has_event=bool(_EVENT.search(s)); has_target=bool(_TARGET.search(s))
    has_resource=bool(_RESOURCE.search(s)); has_status=bool(_STATUS.search(s)); has_action=bool(_ACTION.search(s))
    has_owner=bool(_OWNER.search(s)); has_specific=bool(_SPECIFIC.search(s)); has_formation=bool(_FORMATION.search(s))
    if (has_aff or has_owner) and has_event and has_resource:
        hits.append(Hit(CrossCluster.CROSS_IDENTITY_RESOURCE_EFFECT,"high",("affiliation+event+resource",),Match.EXISTING_RESOURCE))
    if (has_aff or has_owner) and has_event and has_status and not has_resource:
        hits.append(Hit(CrossCluster.CROSS_IDENTITY_STATUS_EFFECT,"medium",("affiliation+event+status",),Match.EXISTING_STATUS))
    if (has_aff or has_owner) and has_event and has_action:
        hits.append(Hit(CrossCluster.CROSS_IDENTITY_SKILL_ACTION,"high",("affiliation+event+action",),Match.EXISTING_ACTION))
    if (has_aff or has_owner) and has_event and not (has_resource or has_status or has_action):
        hits.append(Hit(CrossCluster.CROSS_IDENTITY_EVENT_TRIGGER,"medium",("affiliation+event",),Match.EXISTING_TRIGGER))
    if has_target and (has_aff or has_owner or "아군" in s):
        missing=[]
        if "속도" in s: missing.append("generic speed-based selector")
        if "정신력" in s: missing.append("generic sanity selector")
        hits.append(Hit(CrossCluster.CROSS_IDENTITY_TARGET_SELECTION,"high",("affiliation+target-selector",),Match.EXISTING_TARGET,tuple(missing)))
    if has_aff and has_formation:
        hits.append(Hit(CrossCluster.FORMATION_PRIORITY_SELECTOR,"medium",("formation/slot selector",),Match.PARTIAL,("formation-priority selector" ,)))
    if has_aff and bool(_COUNT.search(s)):
        hits.append(Hit(CrossCluster.AFFILIATION_MEMBERSHIP_COUNT,"high",("affiliation+count",),Match.EXISTING_AFFILIATION))
    if has_owner and has_aff and ("자신을 제외" in s or "자신 포함" in s or "자신 또는" in s):
        hits.append(Hit(CrossCluster.OWNER_PARTICIPANT_RELATION,"high",("owner/participant relation",),Match.PARTIAL,("explicit owner/participant predicate",)))
    if has_specific and has_aff:
        hits.append(Hit(CrossCluster.SPECIFIC_IDENTITY_REFERENCE,"medium",("specific identity/name reference",),Match.PARTIAL,("identity-reference condition",)))
    if not hits:
        cross_marker = has_aff or has_owner or "아군" in s or "동료" in s or "다른 인격" in s or "다른 아군" in s
        if not cross_marker:
            hits.append(Hit(CrossCluster.OUT_OF_AXIS,"high",("no-cross-identity-marker",),Match.PARTIAL,("handled by another axis",)))
        else:
            # A cross-identity clause may still be a generic effect whose target/trigger
            # semantics are already owned by common runtimes. Keep it here rather than
            # manufacturing an identity-specific primitive.
            if has_target:
                hits.append(Hit(CrossCluster.CROSS_IDENTITY_TARGET_SELECTION,"medium",("generic target selector",),Match.EXISTING_TARGET))
            elif has_action:
                hits.append(Hit(CrossCluster.CROSS_IDENTITY_SKILL_ACTION,"medium",("generic action",),Match.EXISTING_ACTION))
            elif has_resource:
                hits.append(Hit(CrossCluster.CROSS_IDENTITY_RESOURCE_EFFECT,"medium",("generic resource effect",),Match.EXISTING_RESOURCE))
            elif has_status:
                hits.append(Hit(CrossCluster.CROSS_IDENTITY_STATUS_EFFECT,"medium",("generic status/effect",),Match.EXISTING_STATUS))
            elif "우선 적용" in s or "가장" in s:
                hits.append(Hit(CrossCluster.CROSS_IDENTITY_TARGET_SELECTION,"medium",("priority-target predicate",),Match.PARTIAL,("generic priority selector",)))
            elif "버릴 때" in s or "사용한" in s or "사용할 때" in s:
                hits.append(Hit(CrossCluster.CROSS_IDENTITY_EVENT_TRIGGER,"medium",("action-event predicate",),Match.PARTIAL,("generic action-event condition",)))
            elif "속도 차이" in s:
                hits.append(Hit(CrossCluster.CROSS_IDENTITY_STATUS_EFFECT,"medium",("speed-difference modifier",),Match.PARTIAL,("generic comparison modifier",)))
            elif "퇴각 상태" in s:
                hits.append(Hit(CrossCluster.OWNER_PARTICIPANT_RELATION,"medium",("owner state predicate",),Match.PARTIAL,("owner state condition",)))
            elif "기본 공격 스킬로 메인 타겟" in s:
                hits.append(Hit(CrossCluster.CROSS_IDENTITY_EVENT_TRIGGER,"medium",("shared-target predicate",),Match.PARTIAL,("target relation condition",)))
            elif "검지 소속" in s:
                hits.append(Hit(CrossCluster.SPECIFIC_IDENTITY_REFERENCE,"high",("specific affiliation reference",),Match.PARTIAL,("affiliation-specific condition",)))
            elif "스킬을 장착한 아군당" in s:
                hits.append(Hit(CrossCluster.AFFILIATION_MEMBERSHIP_COUNT,"high",("ally skill-metadata count",),Match.PARTIAL,("count of qualifying allies",)))
            else:
                hits.append(Hit(CrossCluster.UNRESOLVED,"low",("cross-marker-without-safe-semantic-shape",),Match.UNRESOLVED,("semantic context",)))
    return tuple(hits)

# bug-safe helper used above
has_count = lambda s: bool(_COUNT.search(s))

def audit_records(records: Iterable[dict[str,Any]]) -> dict[str,Any]:
    rows=[]; counts={c.value:0 for c in CrossCluster}; match_counts={m.value:0 for m in Match}
    total_clauses=0
    for i,r in enumerate(records):
        clauses=split_clauses(r.get("source_text", ""))
        for text in clauses:
            total_clauses+=1
            hits=classify_clause(text)
            for h in hits:
                counts[h.cluster.value]+=1; match_counts[h.match.value]+=1
                rows.append({"record_index":i,"identity_id":r.get("identity_id"),"identity_name":r.get("identity_name"),"passive_name":r.get("passive_name"),"text":text,**asdict(h),"cluster":h.cluster.value,"match":h.match.value})
    return {"record_count":len(list(records)) if not isinstance(records,list) else len(records),"clause_count":total_clauses,"cluster_counts":counts,"match_counts":match_counts,"rows":rows}
