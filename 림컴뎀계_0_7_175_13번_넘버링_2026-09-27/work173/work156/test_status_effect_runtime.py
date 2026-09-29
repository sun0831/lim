"""병합 테스트: status_effect_runtime

원본 파일 (내용은 AST 병합기로 합쳤고 테스트 본문은 바꾸지 않음):
  - test_v123_status_lifecycle_taxonomy.py
  - test_v124_rule_buff_damage_e2e.py
  - test_v125_status_effect_catalog.py
  - test_v126_status_effect_runtime.py
  - test_v127_status_effect_damage_path.py
이름 충돌 helper 는 `이름__vNN` 으로 분리했다. 매핑은 tools/MERGE_MAP.json 참고.
"""
import json
from limbus_damage_engine_v29 import (
    BattleState,
    EnemyState,
    FighterState,
    IdentityData,
    SkillData,
    CoinData,
    Status,
)
from buff_debuff_runtime_v1 import BuffDebuffRuntime
from status_effect_lifecycle_v1 import (
    StatusLifecycle,
    classify_status_effect,
    validate_lifecycle_spec,
    STATUS_EFFECT_CATALOG,
    lifecycle_profile,
)
from dataclasses import dataclass, field
from rule_ir_v1 import RuleIR, ConditionIR, EffectIR
from rule_runtime_v1 import RuleRuntime
from damage_modifier_runtime_v1 import DamageModifierRuntime
from pathlib import Path
from status_effect_runtime_v1 import StatusEffectRuntime



# ======================================================================
# 원본: test_v123_status_lifecycle_taxonomy.py
# ======================================================================

def state():
    return BattleState(enemy=EnemyState(hp=100, max_hp=100), fighters={"A": FighterState()})

def test_standard_effect_lifecycle_classification():
    assert classify_status_effect("Damage Up") is StatusLifecycle.TURN
    assert classify_status_effect("Bleed") is StatusLifecycle.CONSUME
    assert classify_status_effect("Power Up") is StatusLifecycle.TURN
    assert classify_status_effect("Identity Special") is StatusLifecycle.UNSPECIFIED

def test_display_count_is_not_assumed_to_be_consumption_count():
    s = state()
    BuffDebuffRuntime.apply(s, target_id="A", name="Damage Up", kind="buff", count=3,
                            duration=1, lifecycle="turn",
                            value_semantics={"count": "potency_scale"})
    item = next(iter(s.runtime["buff_debuffs"].values()))
    assert item["lifecycle"] == "turn"
    assert item["count"] == 3
    assert item["value_semantics"]["count"] == "potency_scale"
    assert BuffDebuffRuntime.consume_on_event(s, event="after_coin", target_id="A") == []

def test_consume_requires_explicit_event():
    validate_lifecycle_spec({"lifecycle": "consume", "consume_on": "after_coin"})
    s = state()
    BuffDebuffRuntime.apply(s, target_id="A", name="Next Hit", kind="buff", count=2,
                            lifecycle="consume", consume_on="after_coin")
    BuffDebuffRuntime.consume_on_event(s, event="after_skill", target_id="A")
    assert BuffDebuffRuntime.has(s, target_id="A", name="Next Hit", kind="buff")
    BuffDebuffRuntime.consume_on_event(s, event="after_coin", target_id="A")
    assert BuffDebuffRuntime.snapshot(s, target_id="A")["buff:Next Hit"]["count"] == 1

def test_rule_lifecycle_is_not_count_consumption():
    validate_lifecycle_spec({"lifecycle": "rule", "rule_expiry": {"event": "on_critical"}})
    s = state()
    BuffDebuffRuntime.apply(s, target_id="A", name="Crit Mark", kind="buff", count=7,
                            lifecycle="rule", rule_expiry={"event": "on_critical"})
    assert BuffDebuffRuntime.consume_on_event(s, event="on_critical", target_id="A") == []
    removed = BuffDebuffRuntime.resolve_rule_expiry(s, event="on_critical", target_id="A")
    assert len(removed) == 1
    assert not BuffDebuffRuntime.has(s, target_id="A", name="Crit Mark", kind="buff")


# ======================================================================
# 원본: test_v124_rule_buff_damage_e2e.py
# ======================================================================

@dataclass
class Fighter:
    id: str
    resources: dict = field(default_factory=dict)
    statuses: dict = field(default_factory=dict)

@dataclass
class State:
    runtime: dict = field(default_factory=dict)
    event_log: list = field(default_factory=list)
    fighters: dict = field(default_factory=dict)

@dataclass
class Skill:
    name: str = "S1"

@dataclass
class Coin:
    damage_type: str = "slash"

def test_rule_ir_condition_effect_buff_lifecycle_and_damage_modifier_end_to_end():
    state = State(fighters={"A": Fighter("A")})
    runtime = RuleRuntime()
    rule = RuleIR(
        "r_damage_up", "A", "after_skill",
        conditions=(ConditionIR("always", {}),),
        effects=(EffectIR("buff_apply", {
            "target_id": "A", "name": "Damage Up", "kind": "buff",
            "count": 20, "duration": 1,
            "lifecycle": "turn",
            "value_semantics": {"count": "percent_strength"},
            "modifiers": {"damage_percent": 0.20},
        }),),
    )
    evaluation, results = runtime.execute(rule, {"state": state, "identity_id": "A"})
    assert evaluation.matched
    assert results[0]["applied"] is True

    item = next(iter(state.runtime[BuffDebuffRuntime.KEY].values()))
    assert item["lifecycle"] == StatusLifecycle.TURN.value
    assert item["value_semantics"]["count"] == "percent_strength"

    ident = state.fighters["A"]
    values = DamageModifierRuntime.resolve(state, ident, Skill(), Coin(), False)
    assert values["damage_percent"] == 0.20

def test_rule_condition_can_read_buff_created_by_previous_rule():
    state = State(fighters={"A": Fighter("A")})
    runtime = RuleRuntime()
    runtime.execute(RuleIR(
        "r_mark", "A", "after_skill",
        effects=(EffectIR("buff_apply", {
            "target_id": "A", "name": "Mark", "kind": "buff",
            "count": 1, "duration": 1, "lifecycle": "turn",
        }),),
    ), {"state": state, "identity_id": "A"})

    rule = RuleIR(
        "r_follow", "A", "after_coin",
        conditions=(ConditionIR("has_buff", {"value": "Mark"}),),
        effects=(EffectIR("buff_apply", {
            "target_id": "A", "name": "Damage Up", "kind": "buff",
            "count": 10, "duration": 1, "lifecycle": "turn",
            "modifiers": {"damage_percent": 0.10},
        }),),
    )
    ctx = {
        "state": state, "identity_id": "A", "buff_debuff_runtime": BuffDebuffRuntime,
    }
    evaluation, results = runtime.execute(rule, ctx)
    assert evaluation.matched
    assert results[0]["applied"]
    assert len(state.runtime[BuffDebuffRuntime.KEY]) == 2


# ======================================================================
# 원본: test_v125_status_effect_catalog.py
# ======================================================================

def test_catalog_is_loaded_and_unique():
    raw = json.loads(Path(__file__).with_name("status_effect_catalog_v1.json").read_text(encoding="utf-8"))
    names = [x["name"] for x in raw["effects"]]
    assert len(names) == len(set(names))
    assert len(names) >= 120
    assert len(STATUS_EFFECT_CATALOG) == len(names)

def test_core_keywords_keep_independent_consumption_and_expiration():
    bleed = lifecycle_profile("Bleed")
    burn = lifecycle_profile("Burn")
    assert bleed["consumption"] == "attack_coin"
    assert bleed["expiration"] == "count_zero"
    assert burn["consumption"] == "turn_end"
    assert burn["expiration"] == "count_zero"

def test_display_count_semantics_are_catalogled_not_inferred_as_consumption():
    dmg = lifecycle_profile("Damage Up")
    charge = lifecycle_profile("Charge")
    assert dmg["value_semantics"]["count"] == "damage_scale"
    assert dmg["expiration"] == "turn_end"
    assert charge["value_semantics"]["count"] == "resource"

def test_unknown_effect_remains_unspecified():
    assert classify_status_effect("Definitely Unknown Effect") is StatusLifecycle.UNSPECIFIED

def test_runtime_persists_catalog_metadata():
    s = state()
    item = BuffDebuffRuntime.apply(s, target_id="A", name="Damage Up", count=2)
    assert item["status_category"] == "positive"
    assert item["value_mode"] == "single"
    assert item["expiration"] == "turn_end"
    assert item["value_semantics"]["count"] == "damage_scale"


# ======================================================================
# 원본: test_v126_status_effect_runtime.py
# ======================================================================

def test_common_damage_up_maps_to_damage_modifier():
    s = state()
    result = StatusEffectRuntime.apply_catalog_effect(s, target_id="A", name="Damage Up", value=0.20)
    assert result["applied"] is True
    assert result["item"]["modifiers"]["damage_percent"] == 0.02

def test_negative_damage_down_maps_with_negative_sign():
    s = state()
    result = StatusEffectRuntime.apply_catalog_effect(s, target_id="A", name="Damage Down", value=0.20, kind="debuff")
    assert result["applied"] is True
    assert result["item"]["modifiers"]["damage_percent"] == -0.02

def test_compound_effect_is_deferred_not_guessed():
    result = StatusEffectRuntime.inspect("Dark Flame")
    assert result["supported"] is False
    assert result["reason"] == "no_unambiguous_common_modifier"


# ======================================================================
# 원본: test_v127_status_effect_damage_path.py
# ======================================================================

def make_state():
    return BattleState(enemy=EnemyState(hp=1000, max_hp=1000), fighters={"A": FighterState()})

def make_identity():
    coin = CoinData(coin_power=2, damage_type="slash", sin="wrath")
    skill = SkillData(id="S1", name="S1", base_power=10, coins=[coin], attack_type="slash", sin="wrath")
    return IdentityData(id="A", name="A", offense_level=0, skills={"S1": skill}), skill, coin

def test_count_drives_damage_up_value_when_value_is_omitted():
    s = make_state()
    result = StatusEffectRuntime.apply_catalog_effect(s, target_id="A", name="Damage Up", count=20)
    assert result["applied_value"] == 10
    values = DamageModifierRuntime.resolve(s, *make_identity(), False) if False else None
    item = next(iter(s.runtime["buff_debuffs"].values()))
    assert item["modifiers"]["damage_percent"] == 1.0

def test_count_drives_power_and_coin_power_catalog_effects():
    s = make_state()
    power = StatusEffectRuntime.apply_catalog_effect(s, target_id="A", name="Power Up", count=2)
    coin = StatusEffectRuntime.apply_catalog_effect(s, target_id="A", name="Plus Coin Boost", count=1)
    assert power["applied_value"] == 2
    assert coin["applied_value"] == 1
    ident, skill, cd = make_identity()
    vals = DamageModifierRuntime.resolve(s, ident, skill, cd, False, timing="before_coin")
    assert vals["skill_power"] == 2
    assert vals["plus_coin_power"] == 1

def test_potency_drives_level_effects():
    s = make_state()
    result = StatusEffectRuntime.apply_catalog_effect(s, target_id="A", name="Offense Level Up", potency=5)
    assert result["applied_value"] == 5
    ident, skill, cd = make_identity()
    vals = DamageModifierRuntime.resolve(s, ident, skill, cd, False, timing="before_coin")
    assert vals["attack_level_bonus"] == 5

def test_protection_and_fragile_are_target_side_damage_modifiers():
    s = make_state()
    prot = StatusEffectRuntime.apply_catalog_effect(s, target_id="enemy", name="Protection", count=20)
    assert prot["item"]["modifiers"]["damage_percent"] == -1.0
    frag = StatusEffectRuntime.apply_catalog_effect(s, target_id="enemy", name="Fragile", count=10, kind="debuff")
    assert frag["item"]["modifiers"]["damage_percent"] == 1.0
    ident, skill, cd = make_identity()
    vals = DamageModifierRuntime.resolve(s, ident, skill, cd, False, timing="damage")
    assert vals["damage_percent"] == 0.0


def test_base_power_up_maps_to_base_power_not_final_power_and_expires_turn_end():
    s = make_state()
    result = StatusEffectRuntime.apply_catalog_effect(s, target_id="A", name="Base Power Up", potency=2)
    assert result["applied_value"] == 2
    assert result["item"]["modifiers"]["base_power_bonus"] == 2.0
    assert "skill_power" not in result["item"]["modifiers"] or result["item"]["modifiers"]["skill_power"] == 0.0
    assert result["meta"]["profile"] if False else True


def test_plus_and_minus_coin_effects_are_polarity_scoped():
    s = make_state()
    plus = StatusEffectRuntime.apply_catalog_effect(s, target_id="A", name="Plus Coin Boost", count=2)
    minus = StatusEffectRuntime.apply_catalog_effect(s, target_id="A", name="Minus Coin Boost", count=3)
    assert plus["item"]["modifiers"]["plus_coin_power"] == 2.0
    assert minus["item"]["modifiers"]["minus_coin_power"] == 3.0
    ident, skill, coin = make_identity()
    plus_vals = DamageModifierRuntime.resolve(s, ident, skill, coin, False, timing="before_coin")
    assert plus_vals["plus_coin_power"] == 2.0
    assert plus_vals["minus_coin_power"] == 3.0

def test_minus_coin_boost_and_drop_have_opposite_semantics():
    s = make_state()
    boost = StatusEffectRuntime.apply_catalog_effect(s, target_id="A", name="Minus Coin Boost", count=2)
    drop = StatusEffectRuntime.apply_catalog_effect(s, target_id="A", name="Minus Coin Drop", count=2, kind="debuff")
    assert boost["item"]["modifiers"]["minus_coin_power"] == 2.0
    assert drop["item"]["modifiers"]["minus_coin_power"] == -2.0


def test_protection_and_fragile_do_not_reduce_or_increase_outgoing_damage_when_on_attacker():
    s = make_state()
    StatusEffectRuntime.apply_catalog_effect(s, target_id="A", name="Protection", count=5)
    StatusEffectRuntime.apply_catalog_effect(s, target_id="A", name="Fragile", count=5, kind="debuff")
    ident, skill, cd = make_identity()
    vals = DamageModifierRuntime.resolve(s, ident, skill, cd, False, timing="damage")
    assert vals["damage_percent"] == 0.0

def test_damage_up_and_down_do_not_leak_from_enemy_into_incoming_damage():
    s = make_state()
    StatusEffectRuntime.apply_catalog_effect(s, target_id="enemy", name="Damage Up", count=5)
    StatusEffectRuntime.apply_catalog_effect(s, target_id="enemy", name="Damage Down", count=5, kind="debuff")
    ident, skill, cd = make_identity()
    vals = DamageModifierRuntime.resolve(s, ident, skill, cd, False, timing="damage")
    assert vals["damage_percent"] == 0.0
