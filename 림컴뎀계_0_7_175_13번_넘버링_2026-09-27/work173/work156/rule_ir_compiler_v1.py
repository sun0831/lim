"""E35 Clause -> RuleIR compiler.

Compiles clauses through the canonical passive compiler (v29) and lowers the
resulting executable definitions into the shared RuleIR. The lowering is
loss-aware: unsupported/opaque values are retained in metadata instead of
being silently discarded.
"""
from __future__ import annotations

from dataclasses import fields, is_dataclass
from enum import Enum
from typing import Any, Mapping, Optional
import re

from passive_compiler_v29 import compile_one, split_clauses
from passive_runtime_v29_base import PassiveDefinition
from primitive_registry_v1 import DEFAULT_REGISTRY
from rule_ir_v1 import RuleIR, ConditionIR, EffectIR, TargetIR

_TRIGGER_MAP = {
    "EncounterStart": "encounter_start", "CombatStart": "combat_start",
    "TurnStart": "turn_start", "BeforeUse": "before_use", "OnUse": "on_use",
    "SkillStart": "skill_start", "ClashStart": "clash_start", "ClashWin": "clash_win",
    "ClashLose": "clash_lose", "CoinStart": "coin_start", "CoinRoll": "coin_roll",
    "CoinHit": "coin_hit", "HeadsHit": "heads_hit", "TailsHit": "tails_hit",
    "Hit": "hit", "Damage": "damage", "StaggerCheck": "stagger_check",
    "Stagger": "stagger", "SkillEnd": "skill_end", "AttackEnd": "attack_end",
    "OnKill": "on_kill", "UnitDeath": "unit_death", "TurnEnd": "turn_end",
    "CombatEnd": "combat_end", "BeforeAttack": "before_attack",
    "OnUnopposedAttack": "on_unopposed_attack", "HitAfterClashWin": "hit_after_clash_win",
}


def _plain(value: Any) -> Any:
    """Serialize parser objects without losing their structural data."""
    if isinstance(value, Enum):
        return value.value
    if is_dataclass(value):
        return {f.name: _plain(getattr(value, f.name)) for f in fields(value)}
    if isinstance(value, Mapping):
        return {str(k): _plain(v) for k, v in value.items()}
    if isinstance(value, (tuple, list)):
        return [_plain(v) for v in value]
    if isinstance(value, set):
        return sorted(_plain(v) for v in value)
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    if hasattr(value, "__dict__"):
        return {str(k): _plain(v) for k, v in vars(value).items()}
    return str(value)


def _primitive_for_condition(condition: Any) -> str:
    name = type(condition).__name__
    mapping = {
        "Always": "condition_action_state",
        "And": "condition_threshold",
        "ContextCompare": "condition_threshold",
        "HpPercent": "condition_hp_stagger_predicate",
        "StatusThreshold": "condition_status_predicate",
        "HasStatus": "condition_status_predicate",
        "ResourceThreshold": "condition_resource_predicate",
        "ChargeAtLeast": "condition_resource_predicate",
        "AmmoAtLeast": "condition_resource_predicate",
        "AllyRankCondition": "condition_identity_relation",
        "SpeedAtLeast": "condition_threshold",
        "SpeedDifferenceAtLeast": "condition_threshold",
        "SpeedRelation": "condition_identity_relation",
        "TargetCountAtLeast": "condition_threshold",
        "SkillCondition": "condition_action_state",
        "AttackTypeIs": "condition_action_state",
        "IsCrit": "condition_action_state",
        "AllAlliesFasterThanEnemy": "condition_identity_relation",
        "TargetWeakToAttackType": "condition_status_predicate",
        "SinIs": "condition_action_state",
        "HasAmplitudeState": "condition_status_predicate",
        "AmplitudePotencyThreshold": "condition_status_predicate",
    }
    return mapping.get(name, "condition_action_state")


def _condition_ir(condition: Any) -> ConditionIR:
    raw = _plain(condition)
    op = type(condition).__name__
    if op == "Always":
        return ConditionIR(op="always", args={"value": {}, "primitive_id": "condition_action_state"})
    if op in {"Not", "And", "Or"}:
        children = getattr(condition, "condition", None) if op == "Not" else getattr(condition, "conditions", ())
        if op == "Not":
            child_ir = _condition_ir(children)
            return ConditionIR(op="not", args={"condition": {"op": child_ir.op, "args": child_ir.args}})
        return ConditionIR(op=op.lower(), args={"conditions": [{"op": c.op, "args": c.args} for c in (_condition_ir(x) for x in children)]})
    if op == "HasAmplitudeState":
        op = "has_amplitude_state"
        raw = dict(raw)
        raw["target"] = getattr(condition, "target", "enemy")
        raw["amplitude"] = getattr(condition, "amplitude", None)
        raw["mode"] = getattr(condition, "mode", None)
    elif op == "AmplitudePotencyThreshold":
        op = "amplitude_potency_gte"
        raw = dict(raw)
        raw["target"] = getattr(condition, "target", "enemy")
        raw["amplitude"] = getattr(condition, "amplitude", None)
        raw["mode"] = getattr(condition, "mode", None)
        raw["threshold"] = getattr(condition, "value", 0)
    elif isinstance(raw, dict) and set(raw) == {"conditions"}:
        op = "and"
    return ConditionIR(op=op, args={"value": raw, "primitive_id": _primitive_for_condition(condition), **(raw if op in {"has_amplitude_state", "amplitude_potency_gte"} else {})})


def _primitive_for_effect(effect: Any) -> str:
    name = type(effect).__name__
    mapping = {
        "EnsureAmmoAtLeast": "resource_effect", "AddCharge": "resource_effect",
        "AddAmmo": "resource_effect", "AddPoise": "resource_effect",
        "AddSinResource": "resource_effect", "ConsumeCharge": "resource_effect",
        "ConsumeAmmo": "resource_effect", "ConsumeStatus": "status_effect",
        "AddStatus": "status_effect", "AddPersistentModifier": "buff_debuff_effect",
        "AmplitudeStateEffect": "status_effect",
        "ModifyContext": "damage_modifier_effect", "AddDefenseLevel": "damage_modifier_effect",
    }
    return mapping.get(name, "state_effect")


def _effect_ir(effect: Any) -> EffectIR:
    kind = type(effect).__name__
    params = {"value": _plain(effect), "primitive_id": _primitive_for_effect(effect)}
    if kind == "AmplitudeStateEffect":
        mode = str(getattr(effect, "mode", "conversion"))
        kind = "amplitude_entanglement" if mode == "entanglement" else "amplitude_conversion"
    return EffectIR(kind=kind, params=params)


def _target_ir(target: Any) -> TargetIR:
    name = type(target).__name__
    selector = {
        "SelfTarget": "self", "EnemyTarget": "explicit_enemy", "EventTarget": "event_target",
        "AllAlliesTarget": "all_allies", "SelfPlusAllyTarget": "self_plus_ally",
        "AllySelectorTarget": "ally_selector",
    }.get(name, name)
    raw = _plain(target)
    count = int(raw.get("count", 1)) if isinstance(raw, dict) and isinstance(raw.get("count", 1), int) else 1
    side = "enemy" if name == "EnemyTarget" else "ally" if "Ally" in name else "self"
    return TargetIR(side=side, selector=selector, count=count, filters=raw if isinstance(raw, dict) else {"value": raw})




def _direct_lowering(text: str, owner_id: str, rule_id: str) -> Optional[RuleIR]:
    """Conservative E35-4 lowering for high-frequency compound clauses.

    This layer only emits declarative RuleIR. It never claims that the target
    runtime can execute a newly invented semantic. Patterns are deliberately
    narrow; unmatched prose remains unsupported.
    """
    t = str(text).strip()
    if not t:
        return None

    # Skill swap: preserve slot policy and retry/next-turn timing as contract data.
    m = re.search(r"(?:기본\s*스킬|스킬)\s*(?:하나를|을|를)\s*[‘'\"]([^‘’'\"]+)[’'\"]\s*(?:으로|로)\s*변경", t)
    if m:
        slot = "leftmost_below" if "가장 왼쪽 슬롯의 아래" in t else "leftmost_above" if "가장 왼쪽 슬롯의 위" in t else "any_matching_slot"
        timing = "next_turn_start" if "다음 턴" in t else "immediate"
        return RuleIR(
            rule_id=rule_id, owner_id=str(owner_id), trigger="turn_start" if "턴 시작" in t else "always",
            target=TargetIR(side="self", selector="self", count=1),
            effects=(EffectIR("skill_swap", {"source_skill": "basic_skill", "target_skill": m.group(1),
                                              "primitive_id": "skill_swap_timed", "slot_policy": slot,
                                              "timing": timing, "retry_if_invalidated": "다시 발동" in t}),),
            timing=timing, source_text=t, status="implemented", activation_scope="owner",
            metadata={"compiler":"E35-4", "lowering":"skill_swap_contract", "primitive_contracts":["skill_swap_timed"]},
        )

    # Explicit forced / support / assist follow-up attacks.
    m = re.search(r"(?:사용 전|공격 종료 시|스킬 종료 시|턴 종료 시|전투 시작 시).*?[‘'\"]([^‘’'\"]+)['’\"](?:로|을|를)?\s*(?:일방 공격|원호 공격|원호 방어|사용)", t)
    if m:
        action_kind = "assist_action" if "원호" in t else "forced_followup_action"
        return RuleIR(
            rule_id=rule_id, owner_id=str(owner_id), trigger="attack_end" if "공격 종료" in t else "skill_end" if "스킬 종료" in t else "turn_end" if "턴 종료" in t else "combat_start",
            target=TargetIR(side="enemy", selector="explicit_or_context", count=1),
            effects=(EffectIR(action_kind, {"skill_or_action": m.group(1), "primitive_id": "forced_followup_action" if action_kind=="forced_followup_action" else "action_queue_effect", "queued": True}),),
            source_text=t, status="implemented", activation_scope="owner",
            metadata={"compiler":"E35-4", "lowering":"forced_followup_contract", "primitive_contracts":["forced_followup_action" if action_kind=="forced_followup_action" else "action_queue_effect"]},
        )

    # Lowest-resource ally / affiliation target selectors.
    resource = None
    for k in ("탄환", "충전", "호흡", "정신력"):
        if k in t: resource = k; break
    if resource and re.search(r"(?:가장\s*적게|가장\s*낮은|가장\s*부족한).*?아군", t):
        affiliation = re.search(r"([가-힣A-Za-z·\[\] -]+?)\s*소속", t)
        filters = {"resource": resource, "direction": "min", "side": "ally"}
        if affiliation: filters["affiliation"] = affiliation.group(1).strip()
        return RuleIR(
            rule_id=rule_id, owner_id=str(owner_id), trigger="action_start" if "사용할 때" in t or "사용 시" in t else "always",
            target=TargetIR(side="ally", selector="lowest_resource", count=1, filters=filters),
            effects=(EffectIR("compound_effect", {"primitive_id":"lowest_resource_selector", "source_text":t}),),
            source_text=t, status="implemented", activation_scope="owner",
            metadata={"compiler":"E35-4", "lowering":"lowest_resource_target_contract", "primitive_contracts":["lowest_resource_selector"]},
        )

    # Generic affiliation target selection, preserving target side/count.
    m = re.search(r"(?:편성된|전장에 있는|출전 중인|살아있는)?\s*([가-힣A-Za-z·]+)\s*소속\s*(?:아군\s*)?(?:인격|대상)?", t)
    if m and "소속" in t and ("아군" in t or "적" in t):
        count = 1
        cm = re.search(r"(\d+)명", t)
        if cm: count = int(cm.group(1))
        side = "enemy" if "소속 적" in t else "ally"
        return RuleIR(
            rule_id=rule_id, owner_id=str(owner_id), trigger="turn_start" if "턴 시작" in t else "always",
            target=TargetIR(side=side, selector="affiliation", count=count, filters={"affiliation":m.group(1)}),
            effects=(EffectIR("compound_effect", {"primitive_id":"affiliation_target_selector", "source_text":t}),),
            source_text=t, status="implemented", activation_scope="owner",
            metadata={"compiler":"E35-4", "lowering":"affiliation_target_contract", "primitive_contracts":["affiliation_target_selector"]},
        )

    # Death-triggered resource/status effects.
    if re.search(r"(?:아군|대상|자신).*?사망(?:시|하면)", t):
        effect = "status_effect" if re.search(r"(?:얻음|부여|증가).*(?:버프|보호막|위력|횟수|상태)", t) else "resource_effect"
        primitive = "status_effect" if effect == "status_effect" else "resource_effect"
        return RuleIR(
            rule_id=rule_id, owner_id=str(owner_id), trigger="unit_death",
            target=TargetIR(side="self", selector="self", count=1),
            effects=(EffectIR(effect, {"primitive_id":primitive, "source_text":t}),),
            source_text=t, status="implemented", activation_scope="owner",
            metadata={"compiler":"E35-4", "lowering":"death_trigger_contract", "primitive_contracts":[primitive]},
        )

    # Independent RNG: preserve probability granularity rather than inventing
    # an aggregate probability.
    if "확률은 각" in t and ("개별적으로" in t or "각각" in t):
        return RuleIR(
            rule_id=rule_id, owner_id=str(owner_id), trigger="coin_roll",
            target=TargetIR(side="enemy", selector="context", count=1),
            effects=(EffectIR("probabilistic_effect", {"primitive_id":"probabilistic_trigger", "rng_scope":"per_coin", "source_text":t}),),
            source_text=t, status="implemented", activation_scope="owner",
            metadata={"compiler":"E35-4", "lowering":"independent_rng_contract", "primitive_contracts":["probabilistic_trigger"]},
        )
    return None


def compile_passive_definition(rule: PassiveDefinition) -> RuleIR:
    trigger = getattr(rule.trigger, "value", str(rule.trigger))
    trigger = _TRIGGER_MAP.get(trigger, trigger)
    conditions = tuple(_condition_ir(c) for c in rule.conditions)
    effects = tuple(_effect_ir(e) for e in rule.effects)
    target = _target_ir(rule.target)
    source_text = str(rule.source_text)
    metadata = {
        "compiler": "E35",
        "source_type": "passive_compiler_v29.PassiveDefinition",
        "supported": bool(getattr(rule, "supported", True)),
        "deferred_turns": int(getattr(rule, "deferred_turns", 0) or (1 if "다음 턴" in source_text else 0)),
        "primitive_contracts": sorted({
            *(c.args.get("primitive_id") for c in conditions if isinstance(c.args, dict) and c.args.get("primitive_id")),
            *(e.params.get("primitive_id") for e in effects if isinstance(e.params, dict) and e.params.get("primitive_id")),
        }),
    }
    target_activation = re.search(r'대상별\s*(?:최대\s*)?(\d+)회', source_text)
    activation_scope = "per_target" if target_activation else "global"
    activation_limit = rule.max_activations
    if target_activation:
        activation_limit = int(target_activation.group(1))
        metadata["activation_scope_source"] = "source_text:대상별"
    return RuleIR(
        rule_id=str(rule.id), owner_id=str(rule.owner_id), trigger=trigger,
        conditions=conditions, target=target, effects=effects,
        timing="turn_end" if getattr(rule, "deferred_turns", 0) else "immediate",
        activation_limit=activation_limit, source_text=source_text,
        status="implemented" if getattr(rule, "supported", True) else "unsupported",
        activation_scope=activation_scope, metadata=metadata,
    )


def compile_clause(text: str, owner_id: str, rule_id: str = "clause") -> list[RuleIR]:
    """Compile one prose clause through the canonical v29 compiler."""
    record = {"id": rule_id, "name": rule_id, "effect": str(text)}
    out, reasons, unsupported = compile_record(record, str(owner_id), 0)
    for ir in out:
        ir.metadata["parse_reasons"] = list(reasons)
        ir.metadata["unsupported_reasons"] = list(unsupported)
    return out


def compile_record(record: Mapping[str, Any], owner_id: str, index: int = 0) -> tuple[list[RuleIR], list[str], list[str]]:
    text_value = str(record.get("effect", ""))
    # E35-4 lowering takes precedence for explicitly recognized contracts so
    # canonical v29 self-target fallbacks do not hide a more precise target.
    direct: list[RuleIR] = []
    for j, clause in enumerate(split_clauses(text_value)):
        rid = f"{record.get('id') or 'clause'}:e35:{index}:{j}"
        lowered = _direct_lowering(clause, str(owner_id), rid)
        if lowered is not None:
            direct.append(lowered)
    if direct:
        return direct, ["e35_direct_lowering"], []
    # Preserve the canonical v29 parser as the first fallback. E35-7 only
    # handles clauses that v29 cannot lower, so existing RuleIR semantics are
    # never shadowed by the lexical contract layer.
    rules, reasons, unsupported = compile_one(dict(record), str(owner_id), int(index))
    out = [compile_passive_definition(r) for r in rules]
    if out:
        return out, list(reasons), list(unsupported)
    contract_rules=[]
    for j, clause in enumerate(split_clauses(text_value)):
        rid=f"{record.get('id') or 'clause'}:e35_7:{index}:{j}"
        lowered=lower_contract_clause(clause, str(owner_id), rid)
        if lowered is not None:
            contract_rules.append(lowered)
    if contract_rules:
        return contract_rules, list(reasons)+["e35_contract_lowering"], []
    return out, list(reasons), list(unsupported)


def compile_text(text: str, owner_id: str, rule_prefix: str = "clause") -> tuple[list[RuleIR], list[str], list[str]]:
    all_rules: list[RuleIR] = []
    reasons: list[str] = []
    unsupported: list[str] = []
    for i, clause in enumerate(split_clauses(str(text))):
        rs, rr, uu = compile_record({"id": f"{rule_prefix}:{i}", "name": rule_prefix, "effect": clause}, owner_id, i)
        all_rules.extend(rs); reasons.extend(rr); unsupported.extend(uu)
    return all_rules, reasons, unsupported

# E35-6: conservative multi-node lowering for compound clauses.
# Only converts fragments when their semantics map to already-existing IR
# vocabulary. Unknown fragments keep the whole rule partial/unsupported.
from rule_ir_decomposition_v1 import decompose_clause
from rule_ir_contract_lowering_v1 import lower_contract_clause

_RESOURCE_NAMES = ("충전", "탄환", "호흡", "정신력", "분노", "색욕", "나태", "탐식", "우울", "오만", "질투")

def _text_condition_ir(text: str):
    m = re.search(r"(정신력|충전|탄환|호흡|분노|색욕|나태|탐식|우울|오만|질투)(?:이|가|을|를)?\s*(-?\d+)\s*(이상|이하|초과|미만)", text)
    if m:
        op_map = {"이상":"gte", "이하":"lte", "초과":"gt", "미만":"lt"}
        return ConditionIR(op=op_map[m.group(3)], args={"resource_or_status":m.group(1), "value":int(m.group(2)), "primitive_id":"condition_resource_predicate" if m.group(1) in _RESOURCE_NAMES[:4] else "condition_threshold"})
    if re.search(r"(아군|적|자신).*(사망|흐트러짐)", text):
        return ConditionIR(op="event_state", args={"value":text, "primitive_id":"condition_action_state"})
    return None

def _text_effect_ir(text: str):
    m = re.search(r"(충전|탄환|호흡|정신력)\s*(\d+)\s*(?:을|를)?\s*(얻|획득|소모|소비)", text)
    if m:
        mode = "gain" if m.group(3) in ("얻", "획득") else "consume"
        return EffectIR("resource_effect", {"resource":m.group(1), "amount":int(m.group(2)), "mode":mode, "primitive_id":"resource_effect"})
    m = re.search(r"(보호막|버프|위력|횟수|출혈|화상|진동|침잠|파열|충전|호흡).*?(\d+)\s*(?:부여|얻음|증가|감소)", text)
    if m:
        return EffectIR("status_effect", {"status":m.group(1), "amount":int(m.group(2)), "primitive_id":"status_effect"})
    return None

def compile_compound_clause(text: str, owner_id: str, rule_id: str = "compound") -> Optional[RuleIR]:
    d = decompose_clause(text)
    if not d.needs_compound_lowering or len(d.fragments) < 2:
        return None
    conditions = []
    effects = []
    trigger = "always"
    target = None
    unknown = []
    for f in d.fragments:
        if f.role == "trigger":
            if "턴 시작" in f.text: trigger = "turn_start"
            elif "턴 종료" in f.text: trigger = "turn_end"
            elif "공격 종료" in f.text: trigger = "attack_end"
            elif "스킬 종료" in f.text: trigger = "skill_end"
            elif "사망" in f.text: trigger = "unit_death"
            else: trigger = "event"
            # Korean clauses frequently combine trigger + condition in one fragment.
            c = _text_condition_ir(f.text)
            if c: conditions.append(c)
        elif f.role == "condition":
            c = _text_condition_ir(f.text)
            if c: conditions.append(c)
            else: unknown.append(f.text)
        elif f.role == "target":
            # Reuse E35-4 direct lowering for known target selectors.
            r = _direct_lowering(f.text, owner_id, rule_id + ":target")
            if r: target = r.target
            else: unknown.append(f.text)
        elif f.role == "effect":
            e = _text_effect_ir(f.text)
            if e: effects.append(e)
            else:
                r = _direct_lowering(f.text, owner_id, rule_id + ":effect")
                if r: effects.extend(r.effects)
                else: unknown.append(f.text)
        else:
            unknown.append(f.text)
    if not conditions and not effects and not target and trigger == "always" and not unknown:
        return None
    status = "implemented" if not unknown and effects else "partial"
    return RuleIR(rule_id=rule_id, owner_id=str(owner_id), trigger=trigger,
        conditions=tuple(conditions), target=target or TargetIR(side="self", selector="self", count=1),
        effects=tuple(effects), source_text=str(text), status=status, activation_scope="owner",
        metadata={"compiler":"E35-6", "lowering":"compound_multi_node", "unknown_fragments":unknown,
                  "fragment_count":len(d.fragments), "primitive_contracts":sorted({p for x in effects for p in [x.params.get("primitive_id")] if p})})
