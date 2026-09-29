from __future__ import annotations
from dataclasses import dataclass, asdict
from enum import Enum
import re
from typing import Any, Iterable

class TargetCluster(str, Enum):
    RANDOM='random_target'; LOWEST_RESOURCE='lowest_resource_target'; HIGHEST_RESOURCE='highest_resource_target'
    SPEED='speed_target'; HP='hp_target'; STATUS='status_target'; FORMATION='formation_target'
    EXPLICIT_IDENTITY='specific_identity_target'; AFFILIATION='affiliation_target'; ALL_TARGETS='all_targets'
    MAIN_TARGET='main_target'; TARGET_RELATION='target_relation'; MULTI_TARGET_COUNT='multi_target_count'
    OUT_OF_AXIS='non_target_clause'; UNRESOLVED='unresolved_target_clause'
class Match(str, Enum):
    EXISTING_TARGET_SELECTOR='existing_target_selector'; EXISTING_RESOURCE_SELECTOR='existing_resource_selector'
    EXISTING_RANDOM='existing_random_selector'; EXISTING_AFFILIATION='existing_affiliation_resolver'
    EXISTING_ACTION_TARGET='existing_action_target'; PARTIAL='partial_common_primitives'; NEW='new_primitive_candidate'; UNRESOLVED='unresolved'
@dataclass(frozen=True)
class Hit:
    cluster: TargetCluster; confidence: str; evidence: tuple[str,...]; match: Match; missing: tuple[str,...]=()
_RANDOM=re.compile(r'무작위|랜덤'); _LOW=re.compile(r'가장 적게|가장 낮은|최소|가장 적은'); _HIGH=re.compile(r'가장 많이|가장 높은|최대|가장 많은')
_SPEED=re.compile(r'속도가 가장 빠른|속도가 가장 느린|가장 빠른|가장 느린'); _HP=re.compile(r'최대 체력이 가장|체력.*가장|현재 체력 비율이 가장')
_STATUS=re.compile(r'위력이|횟수|Count|스택|충전|탄환|호흡|침잠|화상|출혈|진동|파열|생체 재료|정신력'); _FORM=re.compile(r'편성 순서가 가장|가장 왼쪽 슬롯|가장 오른쪽 슬롯|첫 번째 슬롯|후방|전방|대기 인원|출전 중')
_ALL=re.compile(r'모든 아군|모든 적|각 대상|전체 아군|전체 적'); _MAIN=re.compile(r'메인 타겟|주 대상|타겟으로 지정'); _AFF=re.compile(r'소속|협회|사무소|거미집|중지|흑운회|피쿼드|검계|세븐|리우|W사|N사|LCCB|약지|라만차|검지|소지|흑수|가씨')
_ID=re.compile(r'이상|파우스트|돈키호테|히스클리프|이스마엘|싱클레어|홍루|료슈|뫼르소|로쟈|그레고르|오티스|특정 인격|특정 아군'); _REL=re.compile(r'자신을 제외|자신 포함|자신 또는|다른 아군|다른 인격|아군 중|적 중'); _COUNT=re.compile(r'\d+명|\d+명당|최대 \d+명|\d+명까지')
def split_clauses(text:str)->list[str]:
    out=[]
    for b in re.split(r'\n+|\s+/-\s+',text or ''):
        b=b.strip(' /-•')
        if b: out += [x.strip() for x in re.split(r'(?<=다)\.\s+|(?<=음)\.\s+',b) if x.strip()]
    return out
def _resource(s): return bool(_STATUS.search(s))
def classify_clause(text:str)->tuple[Hit,...]:
    s=text.strip(); h=[]
    rnd=bool(_RANDOM.search(s)); low=bool(_LOW.search(s)); high=bool(_HIGH.search(s)); res=_resource(s)
    if rnd: h.append(Hit(TargetCluster.RANDOM,'high',('random marker',),Match.EXISTING_RANDOM))
    if low and res: h.append(Hit(TargetCluster.LOWEST_RESOURCE,'high',('resource+lowest',),Match.EXISTING_RESOURCE_SELECTOR))
    elif high and res: h.append(Hit(TargetCluster.HIGHEST_RESOURCE,'high',('resource+highest',),Match.EXISTING_RESOURCE_SELECTOR))
    if _SPEED.search(s): h.append(Hit(TargetCluster.SPEED,'high',('speed selector',),Match.EXISTING_TARGET_SELECTOR))
    if _HP.search(s): h.append(Hit(TargetCluster.HP,'high',('hp selector',),Match.EXISTING_TARGET_SELECTOR))
    if _STATUS.search(s) and (low or high) and not (low and res) and not (high and res): h.append(Hit(TargetCluster.STATUS,'high',('status comparison',),Match.EXISTING_TARGET_SELECTOR))
    if _FORM.search(s):
        m=Match.EXISTING_TARGET_SELECTOR if ('가장 왼쪽' in s or '가장 오른쪽' in s) else Match.PARTIAL
        h.append(Hit(TargetCluster.FORMATION,'high' if m is Match.EXISTING_TARGET_SELECTOR else 'medium',('formation selector',),m,() if m is Match.EXISTING_TARGET_SELECTOR else ('generic formation policy',)))
    if _ALL.search(s): h.append(Hit(TargetCluster.ALL_TARGETS,'high',('all-target marker',),Match.PARTIAL,('all-ally/all-enemy selector',)))
    if _MAIN.search(s): h.append(Hit(TargetCluster.MAIN_TARGET,'high',('main-target marker',),Match.EXISTING_ACTION_TARGET))
    if _COUNT.search(s) and ('아군' in s or '적' in s or rnd or _ALL.search(s)): h.append(Hit(TargetCluster.MULTI_TARGET_COUNT,'medium',('target count',),Match.PARTIAL,('count-constrained selector',)))
    if _AFF.search(s): h.append(Hit(TargetCluster.AFFILIATION,'high',('affiliation marker',),Match.EXISTING_AFFILIATION))
    if _ID.search(s): h.append(Hit(TargetCluster.EXPLICIT_IDENTITY,'medium',('identity reference',),Match.PARTIAL,('identity-specific predicate',)))
    if _REL.search(s): h.append(Hit(TargetCluster.TARGET_RELATION,'high',('relative target predicate',),Match.PARTIAL,('owner/participant relation',)))
    if not h:
        h.append(Hit(TargetCluster.UNRESOLVED if re.search(r'대상|아군|적에게|인격에게|타겟',s) else TargetCluster.OUT_OF_AXIS,'low' if re.search(r'대상|아군|적에게|인격에게|타겟',s) else 'high',('target marker',) if re.search(r'대상|아군|적에게|인격에게|타겟',s) else ('no target marker',),Match.UNRESOLVED if re.search(r'대상|아군|적에게|인격에게|타겟',s) else Match.PARTIAL,('selector semantics',) if re.search(r'대상|아군|적에게|인격에게|타겟',s) else ('handled by another axis',)))
    return tuple(h)
def audit_records(records:Iterable[dict[str,Any]])->dict[str,Any]:
    records=list(records); rows=[]; cc={x.value:0 for x in TargetCluster}; mc={x.value:0 for x in Match}; total=0
    for i,r in enumerate(records):
        for text in split_clauses(r.get('source_text','')):
            total+=1
            for x in classify_clause(text):
                cc[x.cluster.value]+=1; mc[x.match.value]+=1; rows.append({'record_index':i,'identity_id':r.get('identity_id'),'identity_name':r.get('identity_name'),'passive_name':r.get('passive_name'),'text':text,**asdict(x),'cluster':x.cluster.value,'match':x.match.value})
    return {'record_count':len(records),'clause_count':total,'cluster_counts':cc,'match_counts':mc,'rows':rows}
