"""E35-7 conservative contract lowering for single opaque fragments.

Only high-confidence lexical contracts are lowered. Unknown prose is returned as
None so the caller can preserve it as unsupported/partial instead of guessing.
"""
from __future__ import annotations
import re
from typing import Optional
from rule_ir_v1 import RuleIR, ConditionIR, TargetIR, EffectIR

_RESOURCE = r"충전|탄환|호흡|정신력|원한 문신|분노|색욕|나태|탐식|우울|오만|질투"
_STATUS = r"출혈|화상|진동|침잠|파열|호흡|충전|보호막|신속|위력|방어|공격|피해량"

def _trigger(text: str):
    if re.search(r"전투\s*시작(?:\s*시)?", text): return "turn_start"
    if re.search(r"전투\s*종료(?:\s*시)?", text): return "turn_end"
    if re.search(r"턴\s*시작(?:\s*시)?", text): return "turn_start"
    if re.search(r"턴\s*종료(?:\s*시)?", text): return "turn_end"
    if re.search(r"공격\s*(?:종료|후)(?:\s*시)?", text): return "attack_end"
    if re.search(r"스킬\s*(?:종료|후)(?:\s*시)?", text): return "skill_end"
    if re.search(r"적중\s*시|명중\s*시", text): return "hit"
    if re.search(r"피격\s*시", text): return "hit_received"
    if re.search(r"처치\s*시|사망\s*시", text): return "unit_death"
    return None

def _condition(text: str):
    # Resource/status threshold with explicit numeric comparator.
    m = re.search(rf"({_RESOURCE}|{_STATUS})\s*(?:이|가|을|를)?\s*(\d+)\s*(이상|이하|초과|미만|일 때|일경우)", text)
    if m:
        op = {"이상":"gte","이하":"lte","초과":"gt","미만":"lt","일 때":"equals","일경우":"equals"}[m.group(3)]
        key=m.group(1); val=int(m.group(2))
        prim="condition_resource_predicate" if key in {"충전","탄환","호흡","정신력"} else "condition_threshold"
        return ConditionIR(op=op,args={"value":val,"resource_or_status":key,"primitive_id":prim})
    if re.search(r"(?:자신|아군|적).*(?:흐트러짐|사망)", text):
        return ConditionIR(op="event_state",args={"value":text,"primitive_id":"condition_action_state"})
    return None

def _effect(text: str):
    # Explicit resource gain/consume/set. Keep Korean resource name intact.
    m = re.search(rf"({_RESOURCE})\s*(\d+)\s*(?:을|를)?\s*(얻|획득|증가|충전|회복|소모|소비|감소|잃음|잃는다)", text)
    if m:
        word=m.group(3); mode="consume" if word in {"소모","소비","감소","잃음","잃는다"} else "gain"
        return EffectIR("resource_effect",{"resource":m.group(1),"amount":int(m.group(2)),"mode":mode,"primitive_id":"resource_effect"})
    # Status/potency change with explicit numeric amount.
    m = re.search(rf"({_STATUS})\s*(\d+)\s*(?:을|를)?\s*(부여|얻음|증가|감소|부여함|얻는다)", text)
    if m:
        word=m.group(3); mode="decrease" if word=="감소" else "gain"
        return EffectIR("status_effect",{"status":m.group(1),"amount":int(m.group(2)),"mode":mode,"primitive_id":"status_effect"})
    # Damage/power modifier, only when an explicit signed percentage is present.
    m = re.search(r"(피해량|피해|위력|코인 위력|방어 위력)\s*([+-]?\d+)\s*%", text)
    if m:
        return EffectIR("damage_modifier",{"kind":m.group(1),"percent":int(m.group(2)),"primitive_id":"damage_modifier_effect"})
    return None

def lower_contract_clause(text: str, owner_id: str, rule_id: str) -> Optional[RuleIR]:
    text=str(text).strip()
    trig=_trigger(text)
    # Require an explicit trigger or a clear effect; this prevents generic prose from being promoted.
    c=_condition(text)
    e=_effect(text)
    if not (trig or e):
        return None
    # A condition-bearing single clause may be a trigger+condition+effect contract.
    if not e:
        return None
    target=TargetIR(side="enemy" if re.search(r"적에게|적의", text) else "self", selector="self" if not re.search(r"적에게", text) else "context", count=1)
    unknown=[]
    # If a strong condition marker exists but condition extraction failed, remain opaque.
    if re.search(r"(이상|이하|초과|미만|일 때|일경우|이면|경우)", text) and c is None:
        return None
    return RuleIR(rule_id=rule_id, owner_id=str(owner_id), trigger=trig or "always",
        conditions=(c,) if c else (), target=target, effects=(e,), source_text=text,
        status="implemented", activation_scope="owner",
        timing="turn_end" if "턴 종료" in text else "immediate",
        metadata={"compiler":"E35-7","lowering":"contract_lexical","primitive_contracts":[e.params.get("primitive_id")],"unknown_fragments":unknown,
                  "deferred_turns": 1 if "다음 턴" in text else 0})
