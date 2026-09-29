"""Small self-contained clash executor used by the v29 one-turn package.

The v29 release previously referenced this module without shipping it.  This
implementation keeps clash resolution deliberately separate from the damage
engine and delegates the actual surviving-coin damage to DamageEngine.
"""
from __future__ import annotations
from typing import Any, Optional, Sequence
from copy import deepcopy
from limbus_damage_engine_v29 import ClashData, EventType

class ClashAwareExecutor:
    def __init__(self, machine):
        self.machine = machine

    def execute(self, state, identity, skill, defender: ClashData,
                attacker_faces: Optional[Sequence[str]] = None,
                defender_faces: Optional[Sequence[str]] = None,
                attacker_context=None, defender_context=None,
                is_crit: bool = False):
        engine = self.machine.engine
        af = list(attacker_faces or ["H"] * len(skill.coins))
        df = list(defender_faces or ["H"] * len(defender.coins))
        result = engine.resolve_clash(skill, defender, af, df)
        outcome = "win" if result["defender_remaining_coins"] == 0 and result["attacker_remaining_coins"] > 0 else "lose"
        if result["attacker_remaining_coins"] == 0 and result["defender_remaining_coins"] == 0:
            outcome = "tie"

        # Never mutate catalog SkillData with the transient result of this
        # particular clash. The same skill object may be reused by later
        # requested actions or branch simulations.
        resolved_skill = deepcopy(skill)
        resolved_skill.clash_result = outcome
        state.event_log.append({"event":"clash", "identity":identity.id,
                                "skill":skill.id, "outcome":outcome,
                                "exchanges":result["exchanges"]})
        self.machine.events.emit(EventType.CLASH_START, state, {"identity":identity,"skill":skill})
        self.machine.events.emit(EventType.CLASH_WIN if outcome == "win" else EventType.CLASH_LOSE,
                                 state, {"identity":identity,"skill":skill})

        # Clash-result effects are part of the skill lifecycle and must happen
        # before the surviving coins are resolved. This keeps deterministic
        # Clash execution aligned with the probabilistic branch executor.
        clash_effects = (resolved_skill.effects_on_clash_win if outcome == "win"
                         else resolved_skill.effects_on_clash_lose)
        for effect in clash_effects:
            if engine.condition_met(state, identity, effect.get("condition"), resolved_skill):
                engine.apply_effect(state, identity.id, effect.get("target", "self"), effect)
        trigger_name = "Clash Win" if outcome == "win" else "Clash Lose"
        for passive in getattr(identity, "passives", []) or []:
            if passive.get("trigger") == trigger_name:
                engine.apply_trigger_effects(state, identity, passive.get("effects", []), resolved_skill)

        # A won clash proceeds to damage. A lost clash only allows explicitly
        # unbreakable coins to survive; ordinary losing coins do not deal damage.
        if outcome == "lose":
            surviving = [i for i,c in enumerate(skill.coins) if c.unbreakable]
        else:
            surviving = list(range(len(skill.coins)))

        before = state.turn_damage
        prior_heads = 0
        for i, coin in enumerate(skill.coins):
            if i not in surviving or state.enemy.hp <= 0:
                continue
            face = af[i] if i < len(af) else "H"
            engine.simulate_coin(state, identity, resolved_skill, coin, face, is_crit, i+1, prior_heads)
            if face.upper() == "H": prior_heads += 1

        # Skill-level hit effects are evaluated after the attack's surviving
        # coins, matching the normal skill lifecycle.
        if state.enemy.hp > 0:
            for effect in getattr(resolved_skill, "effects_on_hit", []) or []:
                if engine.condition_met(state, identity, effect.get("condition"), resolved_skill):
                    engine.apply_effect(state, identity.id, effect.get("target", "self"), effect)
        return {"outcome": outcome, "damage": state.turn_damage-before,
                "clash": result}
