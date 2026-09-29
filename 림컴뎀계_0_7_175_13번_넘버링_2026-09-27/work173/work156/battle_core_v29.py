from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Callable, Dict, List, Optional, Tuple
from limbus_damage_engine_v29 import BattleState, IdentityData, SkillData, CoinData, EventType, DamageEngine

class BattlePhase(Enum): WAIT=auto(); EXECUTE=auto(); CLASH=auto(); FINISHED=auto()
@dataclass
class BattleEvent:
    type: EventType; state: BattleState; payload: Dict[str,Any]=field(default_factory=dict)
class GameplayEventHub:
    def __init__(self): self._handlers={}; self.history=[]
    def subscribe(self,event_type,handler): self._handlers.setdefault(event_type,[]).append(handler)
    def emit(self,event_type,state,payload=None):
        e=BattleEvent(event_type,state,payload or {}); self.history.append(e)
        for h in tuple(self._handlers.get(event_type,())): h(e)
    def clear_history(self): self.history.clear()
class BattleStateMachineV23:
    def __init__(self,engine=None,events=None):
        self.engine=engine or DamageEngine(); self.events=events or GameplayEventHub(); self.phase=BattlePhase.WAIT; self.turn=0
        for et in EventType: self.engine.bus.subscribe(et,self._bridge(et))
    def _bridge(self,et):
        def h(ctx):
            if isinstance(ctx,dict) and ctx.get('state') is not None: self.events.emit(et,ctx['state'],dict(ctx))
        return h
    def start(self,state): self.turn=0; self.phase=BattlePhase.EXECUTE; self.events.emit(EventType.ENCOUNTER_START,state); self.events.emit(EventType.COMBAT_START,state); self.events.emit(EventType.TURN_START,state,{'turn':0})
    def execute_coin(self,state,identity,skill,coin,result,is_crit,coin_index,prior_heads=0):
        if self.phase==BattlePhase.FINISHED or state.enemy.hp<=0:return 0.0
        return self.engine.simulate_coin(state,identity,skill,coin,result,is_crit,coin_index,prior_heads)
    def end_turn(self,state):
        if self.phase==BattlePhase.FINISHED:return
        self.engine.turn_end(state)
        # Declarative Buff/Debuff lifecycle is finalized after native turn-end
        # status processing.  Existing entries without consume/duration semantics
        # remain untouched.
        from buff_debuff_runtime_v1 import BuffDebuffRuntime
        expired = BuffDebuffRuntime.end_turn(state)
        if expired:
            for item in expired:
                state.event_log.append({"event": "buff_debuff_expired",
                                        "target_id": str(item.get("target_id")),
                                        "name": str(item.get("name")),
                                        "kind": str(item.get("kind")),
                                        "rule_id": str(item.get("rule_id", ""))})
        self.events.emit(EventType.COMBAT_END if state.enemy.hp<=0 else EventType.TURN_END,state,{'turn':self.turn})
        self.phase=BattlePhase.FINISHED if state.enemy.hp<=0 else BattlePhase.WAIT


from passive_battle_core_v29 import PassiveAwareBattleStateMachineV23
from clash_core_v24 import ClashAwareExecutor
class ClashAwareBattleStateMachineV23(PassiveAwareBattleStateMachineV23):
    def __init__(self,engine=None,events=None,identities=()):
        super().__init__(engine=engine,events=events,identities=identities); self.clash_executor=ClashAwareExecutor(self)
    def execute_clash(self,state,identity,skill,defender,attacker_faces=None,defender_faces=None,attacker_context=None,defender_context=None,is_crit=False):
        return self.clash_executor.execute(state,identity,skill,defender,attacker_faces,defender_faces,attacker_context,defender_context,is_crit)
