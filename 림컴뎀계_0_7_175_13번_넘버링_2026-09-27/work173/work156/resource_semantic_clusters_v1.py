from __future__ import annotations
import re
from dataclasses import dataclass
from enum import Enum
from typing import Iterable

class SemanticCluster(str, Enum):
    TRIGGER_TO_GAIN = 'trigger_to_gain'
    AFFILIATION_SCALED = 'affiliation_scaled_resource'
    CUMULATIVE_SPEND = 'cumulative_spend_to_gain'
    RESOURCE_SCALED_MODIFIER = 'resource_scaled_modifier'
    RESOURCE_ZERO_STATE = 'resource_zero_state_transition'
    RESOURCE_BASED_TARGET = 'resource_based_target_selection'
    RANDOM_COUNT_SCALING = 'random_target_count_scaling'
    SKILL_RESOURCE_TRANSFORM = 'resource_skill_transform'
    RESOURCE_CONVERSION = 'resource_conversion_or_exchange'
    RESOURCE_THRESHOLD = 'resource_threshold_condition'
    RESOURCE_CONSUMPTION = 'resource_consumption_trigger'
    SPECIAL_STATE = 'resource_special_state'
    UNRESOLVED = 'unresolved_resource_semantics'

@dataclass(frozen=True)
class ClusterHit:
    cluster: SemanticCluster
    confidence: str
    evidence: tuple[str, ...]

@dataclass(frozen=True)
class ClusteredRecord:
    identity_id: str
    identity_name: str
    passive_name: str
    source_text: str
    hits: tuple[ClusterHit, ...]

def _hit(out, c, conf, *ev):
    out.append(ClusterHit(c, conf, tuple(ev)))

def classify(text: str) -> tuple[ClusterHit, ...]:
    s=text.replace('×','x').replace('＊','*')
    out=[]
    if re.search(r'누적으로.{0,30}소모할 때마다',s):
        _hit(out,SemanticCluster.CUMULATIVE_SPEND,'high','누적으로 소모할 때마다')
    if re.search(r'소속.{0,30}(\d+)명당|소속.{0,30}수.{0,15}x\s*\d+',s):
        _hit(out,SemanticCluster.AFFILIATION_SCALED,'high','소속 인원 수에 따른 배수/구간')
    if re.search(r'가장 적게 보유|가장 낮은.{0,15}(충전|자원|수치)|수치가 가장 낮은',s):
        _hit(out,SemanticCluster.RESOURCE_BASED_TARGET,'high','자원 보유량 최솟값 대상 선택')
    if re.search(r'무작위.{0,30}(\d+)명|무작위.{0,30}수치|무작위 적',s) and re.search(r'(당|따라|만큼|추가)',s):
        _hit(out,SemanticCluster.RANDOM_COUNT_SCALING,'medium','무작위 대상 + 수치/인원 스케일링')
    if re.search(r'자신의 [^\n]{0,20}(수치|횟수|위력|자원).{0,30}(당|x|%)',s) or re.search(r'(충전|호흡|오혈|연료|생체 재료|예지안|앙갚음 장부|원한 문신|지령의 가호).{0,35}(당|x).{0,20}피해량',s):
        _hit(out,SemanticCluster.RESOURCE_SCALED_MODIFIER,'medium','보유 자원량에 따른 피해/수치 변동')
    if re.search(r'0이 되면|없으면.{0,30}변경|0이.{0,20}변경',s) and re.search(r'(다음 턴|변경|해제|과열|상태)',s):
        _hit(out,SemanticCluster.RESOURCE_ZERO_STATE,'high','자원 0/소진 상태 전환')
    if re.search(r'(자원|충전|탄환|생체 재료|예지안|지령).{0,50}(스킬.*변경|변경.*스킬|스킬로 변경)',s):
        _hit(out,SemanticCluster.SKILL_RESOURCE_TRANSFORM,'high','자원 상태가 스킬 변환을 유발')
    if re.search(r'(자원|충전|탄환|생체 재료|호흡|예지안|연료|오혈|문신|지령).{0,60}(변경|전환|바뀜|대체)',s):
        _hit(out,SemanticCluster.RESOURCE_CONVERSION,'medium','자원/상태의 변환')
    if re.search(r'(이상|이하|미만|초과|도달|넘으면|없으면|0이 되면).{0,20}(충전|자원|수치|위력|횟수)| (충전|자원).{0,20}(이상|이하|미만|초과)',s):
        _hit(out,SemanticCluster.RESOURCE_THRESHOLD,'medium','자원 임계값 조건')
    if re.search(r'(소모|사용).{0,20}(하면|할 때|시)',s) and re.search(r'(충전|탄환|자원|연료|생체 재료|횟수)',s):
        _hit(out,SemanticCluster.RESOURCE_CONSUMPTION,'medium','자원 소비가 트리거')
    if re.search(r'(얻음|얻는다|증가|부여).{0,25}(피격|적중|처치|턴 시작|전투 시작|공격 종료|사망|합 승리)',s):
        _hit(out,SemanticCluster.TRIGGER_TO_GAIN,'medium','이벤트 발생 후 자원/효과 획득')
    if re.search(r'(원호|전가|무적|퇴각 불가|체력.{0,10}1|패닉|침식|BGM|특수|과열|불안정)',s) and re.search(r'(자원|횟수|수치|얻|소모|변경)',s):
        _hit(out,SemanticCluster.SPECIAL_STATE,'low','자원과 결합된 특수 상태')
    if not out:
        _hit(out,SemanticCluster.UNRESOLVED,'low','현재 공통 패턴으로 안정적 분해 불가')
    return tuple(out)

def cluster_records(records: Iterable[dict]) -> list[ClusteredRecord]:
    out=[]
    for r in records:
        out.append(ClusteredRecord(r.get('identity_id',''),r.get('identity_name',''),r.get('passive_name',''),r.get('source_text',''),classify(r.get('source_text',''))))
    return out
