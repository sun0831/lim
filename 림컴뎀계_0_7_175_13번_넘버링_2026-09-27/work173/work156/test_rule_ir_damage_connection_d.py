"""D-stage RuleIR -> DamageEngine integration contracts.

These tests verify the actual combat boundary rather than only inspecting the
intermediate EffectCommand. A migrated RuleIR modifier must be registered on
the actor's canonical identity bucket and subsequently be consumed by the
DamageEngine at coin timing.
"""
from limbus_damage_engine_v29 import BattleState, EnemyState, FighterState, IdentityData, SkillData, CoinData, DamageEngine
from rule_ir_v1 import EffectIR
from effect_runtime_v1 import EffectRuntime
from effect_executor_v1 import EffectExecutor
from rule_runtime_v1 import RuleRuntime
from trigger_rule_model_v1 import TriggerRule, TriggerEffect, TriggerCondition


def _fixture():
    coin = CoinData(5, "slash", "lust")
    skill = SkillData("S1", "S1", 10, [coin], "slash", "lust")
    identity = IdentityData("A", "A", 0, {"S1": skill})
    state = BattleState(
        EnemyState(1000, 1000, level=60),
        {"A": FighterState(level=60)},
    )
    return state, identity, skill, coin


def test_rule_ir_damage_modifier_reaches_damage_engine():
    state, identity, skill, coin = _fixture()
    base = DamageEngine().calculate_coin_damage(state, identity, skill, coin, "H", False, coin_index=0)[0]

    command = EffectRuntime().resolve(
        EffectIR("damage_percent", {"amount": 0.20, "identity_id": "A"}),
        {"state": state, "identity_id": "A", "rule_owner_id": "A"},
        "d-damage-percent",
    )
    result = EffectExecutor().execute(
        command,
        {"state": state, "identity_id": "A", "rule_owner_id": "A"},
    )

    assert result["target_identity_id"] == "A"
    assert state.runtime["damage_modifiers"][-1]["target_identity_id"] == "A"
    boosted = DamageEngine().calculate_coin_damage(state, identity, skill, coin, "H", False, coin_index=0)[0]
    assert boosted > base


def test_rule_runtime_trigger_rule_modifier_changes_real_coin_damage():
    state, identity, skill, coin = _fixture()
    base = DamageEngine().calculate_coin_damage(state, identity, skill, coin, "H", False, coin_index=0)[0]
    rule = TriggerRule(
        "d-direct-rule", "A", "after_skill",
        [TriggerCondition("always")],
        [TriggerEffect("damage_percent", {"amount": 0.20, "identity_id": "A"})],
        1,
    )
    out = RuleRuntime().execute_trigger_rules(
        [rule], "after_skill",
        {"state": state, "identity_id": "A", "rule_owner_id": "A"},
    )
    assert out and out[0]["target_identity_id"] == "A"
    damage = DamageEngine().calculate_coin_damage(state, identity, skill, coin, "H", False, coin_index=0)[0]
    assert damage > base


def test_rule_runtime_activation_and_damage_modifier_are_single_step():
    state, identity, skill, coin = _fixture()
    rule = TriggerRule(
        "d-single-step", "A", "after_skill",
        [TriggerCondition("always")],
        [TriggerEffect("damage_flat", {"amount": 3, "identity_id": "A"})],
        1,
    )
    ctx = {"state": state, "identity_id": "A", "rule_owner_id": "A"}
    first = RuleRuntime().execute_trigger_rules([rule], "after_skill", ctx)
    second = RuleRuntime().execute_trigger_rules([rule], "after_skill", ctx)
    assert len(first) == 1
    assert second == []
    base = 15.0
    damage = DamageEngine().calculate_coin_damage(state, identity, skill, coin, "H", False, coin_index=0)[0]
    assert damage == base + 3
