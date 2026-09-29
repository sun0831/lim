from __future__ import annotations
from typing import Iterable, Tuple
from battle_core_v29 import BattleStateMachineV23
from limbus_damage_engine_v29 import EventType, IdentityData, SkillData
from passive_runtime_v29 import PassiveRuntimeV13, PassiveTrigger

EVENT_MAP = {
    EventType.ENCOUNTER_START: PassiveTrigger.ENCOUNTER_START,
    EventType.COMBAT_START: PassiveTrigger.COMBAT_START,
    EventType.TURN_START: PassiveTrigger.TURN_START,
    EventType.BEFORE_USE: PassiveTrigger.BEFORE_USE,
    EventType.ON_USE: PassiveTrigger.ON_USE,
    EventType.SKILL_START: PassiveTrigger.SKILL_START,
    EventType.CLASH_START: PassiveTrigger.CLASH_START,
    EventType.CLASH_WIN: PassiveTrigger.CLASH_WIN,
    EventType.CLASH_LOSE: PassiveTrigger.CLASH_LOSE,
    EventType.COIN_START: PassiveTrigger.COIN_START,
    EventType.BEFORE_HIT: PassiveTrigger.COIN_HIT,
    EventType.HEADS_HIT: PassiveTrigger.HEADS_HIT,
    EventType.TAILS_HIT: PassiveTrigger.TAILS_HIT,
    EventType.HIT: PassiveTrigger.HIT,
    EventType.DAMAGE: PassiveTrigger.DAMAGE,
    EventType.STAGGER_CHECK: PassiveTrigger.STAGGER_CHECK,
    EventType.STAGGER: PassiveTrigger.STAGGER,
    EventType.SKILL_END: PassiveTrigger.SKILL_END,
    EventType.ATTACK_END: PassiveTrigger.ATTACK_END,
    EventType.ON_KILL: PassiveTrigger.ON_KILL,
    EventType.UNIT_DEATH: PassiveTrigger.UNIT_DEATH,
    EventType.TURN_END: PassiveTrigger.TURN_END,
    EventType.COMBAT_END: PassiveTrigger.COMBAT_END,
    EventType.BEFORE_ATTACK: PassiveTrigger.BEFORE_ATTACK,
    EventType.ON_UNOPPOSED_ATTACK: PassiveTrigger.UNOPPOSED,
    EventType.HIT_AFTER_CLASH_WIN: PassiveTrigger.HIT_AFTER_CLASH_WIN,
}

class PassiveAwareBattleStateMachineV23(BattleStateMachineV23):
    def __init__(self, engine=None, events=None, identities: Iterable[IdentityData] = ()):
        super().__init__(engine=engine, events=events)
        self.passive_runtime = PassiveRuntimeV13()
        self.engine.passive_runtime = self.passive_runtime
        for event_type, trigger in EVENT_MAP.items():
            self.engine.bus.subscribe(event_type, self._passive_handler(trigger))
        for ident in identities:
            self.register_identity_passives(ident)

    def _passive_handler(self, trigger):
        def handler(ctx):
            state = ctx.get('state') if isinstance(ctx, dict) else None
            if state is None: return
            if trigger == PassiveTrigger.TURN_START:
                self.passive_runtime.reset_scope('turn')
            self.passive_runtime.emit(trigger, ctx, state)
        return handler

    def register_identity_passives(self, identity: IdentityData):
        self.passive_runtime.register_many(identity.passives)

    def start(self, state):
        self.passive_runtime.reset_activations()
        self.passive_runtime.trace.clear()
        super().start(state)
        # BattleStateMachine.start emits lifecycle events through the gameplay
        # hub, not the engine bus.  Emit those lifecycle triggers directly so
        # start-of-turn/start-of-combat passives actually execute in one-turn mode.
        self.passive_runtime.emit(PassiveTrigger.ENCOUNTER_START, {"state": state}, state)
        self.passive_runtime.emit(PassiveTrigger.COMBAT_START, {"state": state}, state)
        self.passive_runtime.emit(PassiveTrigger.TURN_START, {"state": state, "turn": 0}, state)

    def start_next_turn(self, state, turn_index=1):
        """Advance passive lifecycle by one turn and apply effects scheduled for this turn."""
        self.passive_runtime.reset_activations()
        applied = self.passive_runtime.apply_deferred_turn_start(state)
        self.passive_runtime.emit(PassiveTrigger.TURN_START, {"state": state, "turn": int(turn_index)}, state)
        state.event_log.append({"event":"turn_start_processed", "turn":int(turn_index),
                                "deferred_effects_applied":len(applied)})
        return applied

    def execute_skill(self, state, identity, skill, outcomes: Tuple[Tuple[str,bool], ...]):
        if self.phase == self.phase.FINISHED or state.enemy.hp <= 0:
            return 0.0
        self.phase = self.phase.CLASH if skill.clash_result in ('win','lose') else self.phase.EXECUTE
        self.engine.bus.emit(EventType.BEFORE_USE, {'state':state,'identity':identity,'skill':skill})
        self.engine.bus.emit(EventType.ON_USE, {'state':state,'identity':identity,'skill':skill})
        before = state.turn_damage
        self.engine.simulate_skill(state, identity, skill, outcomes)
        self.engine.bus.emit(EventType.ATTACK_END, {'state':state,'identity':identity,'skill':skill})
        return state.turn_damage - before
