from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
import re

class SkillTransformClass(str, Enum):
    TRUE_SWAP='true_skill_swap'
    SKILL_RECLASSIFY='skill_reclassify'
    CONDITIONAL_TRIGGERED_SKILL='conditional_skill_trigger'
    COIN_MODIFICATION='coin_or_skill_parameter_transform'
    FOLLOWUP_ACTION='forced_or_followup_skill'
    NEXT_TURN_SWAP='next_turn_skill_swap'
    SPECIAL_STATE='special_state_not_skill_transform'
    UNRESOLVED='unresolved'

@dataclass(frozen=True)
class Audit:
    classification: SkillTransformClass
    evidence: tuple[str,...]
    confidence: str

RE_SWAP=re.compile(r'(?:스킬|기본 스킬|반격 스킬).*?(?:변경|교체|바뀜|변환)')
RE_RECLASS=re.compile(r'(?:스킬.*?)(?:취급|간주)')
RE_COIN=re.compile(r'(?:코인|파괴 불가 코인|최종 위력|위력).*?(?:변경|증가|감소|적용)')
RE_FOLLOW=re.compile(r'(?:일방 공격|원호 공격|반격).*?(?:사용|발동|공격)')
RE_NEXT=re.compile(r'(?:다음 턴|다음 턴 시작).*?(?:스킬|기본 스킬).*?(?:변경|사용)')

def classify(text:str)->Audit:
    t=text.strip()
    if RE_RECLASS.search(t):
        return Audit(SkillTransformClass.SKILL_RECLASSIFY, ('취급/간주 표현',),'high')
    if RE_NEXT.search(t) and RE_SWAP.search(t):
        return Audit(SkillTransformClass.NEXT_TURN_SWAP, ('다음 턴 + 스킬 변경',),'high')
    if RE_SWAP.search(t):
        return Audit(SkillTransformClass.TRUE_SWAP, ('스킬 변경/교체 표현',),'high')
    if RE_COIN.search(t):
        return Audit(SkillTransformClass.COIN_MODIFICATION, ('코인/위력 변경 표현',),'medium')
    if RE_FOLLOW.search(t):
        return Audit(SkillTransformClass.FOLLOWUP_ACTION, ('추가 공격/발동 표현',),'medium')
    if any(x in t for x in ('얻음','부여','증가','감소')) and '스킬' not in t:
        return Audit(SkillTransformClass.SPECIAL_STATE, ('스킬 자체가 아닌 상태 변화',),'medium')
    return Audit(SkillTransformClass.UNRESOLVED, (), 'low')
