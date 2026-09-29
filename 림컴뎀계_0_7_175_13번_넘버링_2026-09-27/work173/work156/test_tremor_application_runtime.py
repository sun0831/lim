from limbus_damage_engine_v29 import BattleState, EnemyState, FighterState, Status
from keyword_runtime_v1 import KeywordRuntime
from passive_runtime_v29_base import AddStatus, Const, PassiveEvent, PassiveTrigger, EventTarget
from effect_executor_v1 import EffectExecutor
from effect_runtime_v1 import EffectCommand


def test_tremor_application_tracks_potency_and_count_together():
    enemy = EnemyState(100, 100, statuses={'Tremor': Status(potency=3, count=2)})
    state = BattleState(enemy=enemy, fighters={'A': FighterState()})
    KeywordRuntime.add_tremor(enemy, 5, 4, state=state, source_id='A')
    assert enemy.statuses['Tremor'].potency == 8
    assert enemy.statuses['Tremor'].count == 6
    assert state.event_log[-1]['event'] == 'keyword_gain'


def test_tremor_application_context_bonus_is_applied_at_mutation_boundary():
    enemy = EnemyState(100, 100)
    state = BattleState(enemy=enemy, fighters={'A': FighterState()})
    event = PassiveEvent(PassiveTrigger.COIN_HIT, {'tremor_potency_bonus': 1, 'tremor_count_bonus': 2})
    KeywordRuntime.add_tremor(enemy, 3, 1, state=state, event=event, source_id='A')
    assert enemy.statuses['Tremor'].potency == 4
    assert enemy.statuses['Tremor'].count == 3


def test_add_status_tremor_uses_shared_keyword_runtime():
    enemy = EnemyState(100, 100)
    state = BattleState(enemy=enemy, fighters={'A': FighterState()})
    effect = AddStatus('Tremor', potency=Const(4), count=Const(2))
    event = PassiveEvent(PassiveTrigger.COIN_HIT, {})
    effect.apply(event, state, 'A', [enemy])
    assert enemy.statuses['Tremor'].potency == 4
    assert enemy.statuses['Tremor'].count == 2


def test_effect_executor_status_gain_tremor_supports_potency_and_count():
    enemy = EnemyState(100, 100)
    state = BattleState(enemy=enemy, fighters={'A': FighterState()})
    cmd = EffectCommand('status_gain', {'status': 'Tremor', 'potency': 6, 'count': 3}, 'r1', 'status')
    result = EffectExecutor().execute(cmd, {'state': state, 'target': enemy, 'identity_id': 'A'})
    assert result['applied'] is True
    assert enemy.statuses['Tremor'].potency == 6
    assert enemy.statuses['Tremor'].count == 3
