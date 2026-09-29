from limbus_damage_engine_v29 import BattleState, EnemyState, FighterState, Status
from rule_ir_compiler_v1 import compile_text
from rule_runtime_v1 import RuleRuntime
from amplitude_runtime_v1 import AmplitudeRuntime


def test_compiled_amplitude_conversion_executes_through_rule_ir():
    enemy = EnemyState(100, 100, statuses={"Tremor": Status(potency=12, count=5)})
    state = BattleState(enemy=enemy, fighters={"i": FighterState()}, runtime={})
    rules, reasons, unsupported = compile_text("대상에게 진동 - 작열로 진폭 변환", "i", "amp")
    assert not unsupported
    assert rules and rules[0].effects
    assert rules[0].effects[0].kind == "amplitude_conversion"
    assert rules[0].effects[0].params["primitive_id"] == "status_effect"
    rr = RuleRuntime()
    evaluation, results = rr.execute(rules[0], {
        "state": state,
        "identity_id": "i",
        "rule_owner_id": "i",
        "enemy": enemy,
        "targets": [{"id": "enemy"}],
    })
    assert evaluation.matched
    assert results and results[0]["applied"] is True
    assert AmplitudeRuntime().has_state(enemy, "작열", "conversion")
    assert "amplitude_conversion" in [e["event"] for e in state.event_log]


def test_rule_ir_amplitude_conversion_replaces_previous_conversion_and_preserves_tremor():
    enemy = EnemyState(100, 100, statuses={"Tremor": Status(potency=20, count=9)})
    state = BattleState(enemy=enemy, fighters={"i": FighterState()}, runtime={})
    rt = AmplitudeRuntime()
    rt.set_state(state, enemy, "사슬", "conversion")
    rules, _, _ = compile_text("대상에게 진동 - 작열로 진폭 변환", "i", "amp")
    RuleRuntime().execute(rules[0], {"state": state, "identity_id": "i", "rule_owner_id": "i", "targets": [{"id": "enemy"}]})
    states = rt.get_states(enemy)
    assert {x["amplitude"] for x in states if x["mode"] == "conversion"} == {"작열"}
    assert enemy.statuses["Tremor"].potency == 20
    assert enemy.statuses["Tremor"].count == 9


def test_compiled_amplitude_entanglement_executes_through_rule_ir_and_coexists():
    enemy = EnemyState(100, 100, statuses={"Tremor": Status(potency=8, count=4)})
    state = BattleState(enemy=enemy, fighters={"i": FighterState()}, runtime={})
    rt = AmplitudeRuntime()
    rt.set_state(state, enemy, "작열", "conversion")
    rules, _, unsupported = compile_text("대상에게 진동 - 사슬로 진폭 얽힘", "i", "amp-ent")
    assert not unsupported
    assert rules[0].effects[0].kind == "amplitude_entanglement"
    evaluation, results = RuleRuntime().execute(rules[0], {
        "state": state, "identity_id": "i", "rule_owner_id": "i", "targets": [{"id": "enemy"}]
    })
    assert evaluation.matched and results[0]["applied"] is True
    states = rt.get_states(enemy)
    assert ("작열", "conversion") in {(x["amplitude"], x["mode"]) for x in states}
    assert ("사슬", "entanglement") in {(x["amplitude"], x["mode"]) for x in states}


def test_catalog_style_amplitude_conversion_uses_target_status_and_per_target_limit():
    enemy_a = EnemyState(100, 100, statuses={"Tremor": Status(potency=10, count=5)})
    enemy_b = EnemyState(100, 100, statuses={"Tremor": Status(potency=10, count=5)})
    state = BattleState(enemy=enemy_a, fighters={"i": FighterState()}, runtime={})
    rules, _, unsupported = compile_text(
        "진동 - 작열이 없으면, 진동 - 작열로 진폭 변환 (대상별 1회)", "i", "catalog"
    )
    assert not unsupported and len(rules) == 1
    rule = rules[0]
    assert rule.activation_limit == 1
    assert rule.activation_scope == "per_target"
    assert rule.conditions[0].op == "not"
    assert rule.target.selector == "event_target"

    rr = RuleRuntime()
    ctx = {"state": state, "identity_id": "i", "rule_owner_id": "i", "targets": [{"id": "enemy"}], "target_id": "enemy"}
    evaluation, results = rr.execute(rule, ctx)
    assert evaluation.matched and results[0]["applied"] is True
    assert AmplitudeRuntime().has_state(enemy_a, "작열", "conversion")

    # The same target is blocked after its one activation, while a different
    # target remains eligible through the shared per-target ledger contract.
    evaluation2, _ = rr.execute(rule, ctx)
    assert not evaluation2.matched and evaluation2.reason == "activation_limit"

def test_catalog_style_amplitude_condition_is_target_backed():
    enemy = EnemyState(100, 100, statuses={"Tremor": Status(potency=20, count=3)})
    state = BattleState(enemy=enemy, fighters={"i": FighterState()}, runtime={})
    rules, _, unsupported = compile_text(
        "[적중시] 대상이 진폭 변환 상태가 아니면, 진동 - 붕괴로 진폭 변환", "i", "catalog"
    )
    assert not unsupported
    rr = RuleRuntime()
    evaluation, results = rr.execute(rules[0], {
        "state": state, "identity_id": "i", "rule_owner_id": "i",
        "targets": [{"id": "enemy"}], "target_id": "enemy"
    })
    assert evaluation.matched and results[0]["applied"] is True
    assert AmplitudeRuntime().has_state(enemy, "붕괴", "conversion")

    evaluation2, _ = rr.execute(rules[0], {
        "state": state, "identity_id": "i", "rule_owner_id": "i",
        "targets": [{"id": "enemy"}], "target_id": "enemy"
    })
    assert not evaluation2.matched and evaluation2.reason == "condition_failed"
