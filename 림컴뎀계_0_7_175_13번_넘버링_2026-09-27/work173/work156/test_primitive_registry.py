"""E34 Primitive Registry regression tests."""
import json
from pathlib import Path

from primitive_registry_v1 import (
    DEFAULT_REGISTRY,
    PrimitiveFamily,
    PrimitiveRegistry,
    get_primitive,
    resolve_effect_primitive,
)
from resource_primitive_v1 import ResourcePrimitive


def test_e34_registry_contains_all_frozen_resource_primitives():
    registered = {c.primitive_id for c in DEFAULT_REGISTRY.all()}
    expected = {p.value for p in ResourcePrimitive}
    assert expected <= registered
    assert len(expected) == 13


def test_e34_registry_has_no_duplicate_ids():
    ids = [c.primitive_id for c in DEFAULT_REGISTRY.all()]
    assert len(ids) == len(set(ids))


def test_e34_resource_conversion_resolves_through_existing_mapper():
    c = resolve_effect_primitive(
        "resource_convert",
        {"source": "A", "source_amount": 2, "target": "B", "target_amount": 1, "conversion_mode": "fixed"},
    )
    assert c is not None
    assert c.primitive_id == "resource_conversion"
    assert c.owner == "ResourceRuntime"


def test_e34_resource_triggered_skill_swap_is_composed_not_new_runtime():
    c = get_primitive("resource_triggered_skill_swap")
    assert c.family is PrimitiveFamily.SKILL
    assert "ConditionRuntime" in c.owner
    assert "SkillTransformContract" in c.owner


def test_e34_highest_and_lowest_share_target_owner():
    assert get_primitive("highest_resource_selector").owner == "TargetRuntime"
    assert get_primitive("lowest_resource_selector").owner == "TargetRuntime"


def test_e34_unknown_primitive_is_rejected():
    try:
        DEFAULT_REGISTRY.require("does_not_exist")
        assert False
    except KeyError:
        pass


def test_e34_contract_freeze_matches_registry():
    p = Path(__file__).with_name("PRIMITIVE_CONTRACT_FREEZE_E34.json")
    frozen = json.loads(p.read_text(encoding="utf-8"))
    assert frozen["stage"] == "E34"
    assert frozen["new_runtime_count"] == 0
    assert set(frozen["primitive_ids"]) == {p.value for p in ResourcePrimitive}
    assert set(frozen.get("common_contract_ids", [])) <= {c.primitive_id for c in DEFAULT_REGISTRY.all()}


def test_e34_common_contracts_have_existing_owners():
    expected = {
        "condition_threshold": "ConditionRuntime",
        "explicit_target": "TargetRuntime",
        "random_target": "TargetRuntime",
        "status_effect": "StatusEffectRuntime",
        "buff_debuff_effect": "BuffDebuffRuntime",
        "action_queue_effect": "ActionQueue+EffectRuntime",
        "trigger_event": "TriggerRuntime",
        "probabilistic_trigger": "ProbabilisticTriggerRuntime",
        "skill_swap_timed": "SkillTransformContract",
        "coin_power_transform": "CoinExecutionCore+DamageModifierRuntime",
    }
    for primitive_id, owner in expected.items():
        assert DEFAULT_REGISTRY.require(primitive_id).owner == owner


def test_e34_common_contracts_do_not_create_new_runtime_family():
    allowed = {
        "ConditionRuntime", "ConditionRuntime+StatusEffectRuntime",
        "ConditionRuntime+ResourceRuntime", "TriggerRuntime",
        "TargetRuntime", "AffiliationRuntime+TargetRuntime",
        "EffectRuntime", "EffectRuntime+ResourceRuntime",
        "StatusEffectRuntime", "BuffDebuffRuntime",
        "DamageModifierRuntime+EffectRuntime", "ActionQueue+EffectRuntime",
        "ProbabilisticTriggerRuntime", "TriggerRuntime+ActionQueue",
        "SkillTransformContract", "ActionQueue+TriggerRuntime",
        "CoinExecutionCore+DamageModifierRuntime",
        "StatusEffectLifecycle+StatusEffectRuntime", "OneTurnCoreV23+TriggerRuntime",
        "ResourceRuntime", "DamageModifierRuntime", "ConditionRuntime+SkillTransformContract",
    }
    assert {c.owner for c in DEFAULT_REGISTRY.all()} <= allowed
