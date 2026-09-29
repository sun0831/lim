from dataclasses import dataclass
from enum import Enum
import json, re

class AuditKind(str, Enum):
    SKILL_RECLASSIFY='skill_reclassify'
    CONDITION='condition'
    TARGET_SELECTOR='target_selector'
    STATUS_OR_EFFECT='status_or_effect'
    ACTION_TRIGGER='action_trigger'
    RESOURCE_STATE='resource_state'
    SKILL_TRANSFORM='skill_transform'
    COIN_POWER_TRANSFORM='coin_power_transform'
    SPECIAL_STATE='special_state'
    INITIAL_STATE='initial_state'
    IMMUNITY_MODIFIER='immunity_modifier'
    OUT_OF_SCOPE='out_of_scope'
    UNRESOLVED='unresolved'

@dataclass
class Finding:
    index:int
    text:str
    kind:str
    confidence:str
    evidence:list[str]


def classify(x):
    t=x['text']
    # deterministic, conservative rules; no semantic claim where text is incomplete
    if '전투 BGM' in t or '누군가처럼 공간' in t:
        return AuditKind.OUT_OF_SCOPE,'high',['non_damage_flavor_or_bgm']
    if '스킬로 취급됨' in t:
        return AuditKind.SKILL_RECLASSIFY,'high',['skill_is_treated_as']
    if '상시 적용' in t and re.search(r'\d+개?\s*보유|가지고 시작',t):
        return AuditKind.INITIAL_STATE,'high',['explicit_starting_resource']
    if '가지고 시작' in t:
        return AuditKind.INITIAL_STATE,'high',['explicit_starting_state']
    if '스킬 종료 시' in t or '피격 시' in t or '전투에 등장할 때' in t or '전투 종료 시' in t or '처음으로' in t:
        return AuditKind.ACTION_TRIGGER,'medium',['event_timing_fragment']
    if '가장 낮은' in t or '가장 빠른' in t or '우선 적용' in t or '가장 왼쪽 슬롯' in t:
        return AuditKind.TARGET_SELECTOR,'high',['explicit_target_selection']
    if '강화됨' in t or '변경됨' in t or '변경' in t and '스킬' in t:
        return AuditKind.SKILL_TRANSFORM,'medium',['skill_transform_language']
    if '코인' in t or '위력' in t:
        if '적용됨' in t or '영향을 받지 않음' in t or '변경' in t:
            return AuditKind.COIN_POWER_TRANSFORM,'medium',['coin_power_clause']
    if '취급' in t or '상태일 때' in t or '상태가 될 때' in t or '보유 시' in t or '조건' in t:
        return AuditKind.CONDITION,'medium',['state_condition_fragment']
    if '충전' in t or '탄환' in t or '연료' in t or '보유' in t:
        return AuditKind.RESOURCE_STATE,'medium',['resource_state_fragment']
    if '피해량' in t or '정신력 감소' in t or '효과' in t:
        return AuditKind.STATUS_OR_EFFECT,'medium',['effect_or_modifier_fragment']
    if '퇴각 불가' in t or '신속을 얻을 수 없음' in t or '영향을 받지 않음' in t:
        return AuditKind.IMMUNITY_MODIFIER,'medium',['restriction_or_immunity']
    return AuditKind.UNRESOLVED,'low',['no_safe_pattern']


def audit(path):
    d=json.load(open(path,encoding='utf-8'))
    xs=[x for x in d['clauses'] if x['kind']=='unresolved']
    out=[Finding(i,x['text'],*classify(x)) for i,x in enumerate(xs)]
    return out

if __name__=='__main__':
    import sys
    xs=audit(sys.argv[1])
    from collections import Counter
    print(Counter(x.kind for x in xs))
