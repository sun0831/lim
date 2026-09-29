from amplitude_runtime_v1 import AmplitudeRuntime
from limbus_damage_engine_v29 import EnemyState, FighterState, BattleState, Status
from passive_runtime_v29_base import HasAmplitudeState, AmplitudePotencyThreshold, PassiveEvent, PassiveTrigger


def _state():
    enemy = EnemyState(100, 100, statuses={"Tremor": Status(potency=12, count=7)})
    fighter = FighterState()
    return BattleState(enemy=enemy, fighters={"i": fighter}, runtime={}), enemy


def test_amplitude_is_a_target_status_not_runtime_mirror():
    state, enemy = _state()
    AmplitudeRuntime().set_state(state, enemy, "작열", "conversion", owner_id="i")
    assert "Amplitude" in enemy.statuses
    assert "amplitude_states" not in state.runtime
    assert enemy.statuses["Amplitude"].data["states"][0]["amplitude"] == "작열"


def test_conversion_replaces_conversion_but_entanglement_coexists():
    state, enemy = _state()
    rt = AmplitudeRuntime()
    rt.set_state(state, enemy, "작열", "conversion")
    rt.set_state(state, enemy, "사슬", "conversion")
    rt.set_state(state, enemy, "반향", "entanglement")
    states = rt.get_states(enemy)
    assert {(x["amplitude"], x["mode"]) for x in states} == {("사슬", "conversion"), ("반향", "entanglement")}


def test_generic_conditions_read_status_backed_amplitude():
    state, enemy = _state()
    AmplitudeRuntime().set_state(state, enemy, "작열", "conversion")
    event = PassiveEvent(PassiveTrigger.HIT, {"target": enemy})
    assert HasAmplitudeState("enemy").check(event, state, "i")
    assert HasAmplitudeState("enemy", "작열", "conversion").check(event, state, "i")
    assert AmplitudePotencyThreshold("작열", 10).check(event, state, "i")
