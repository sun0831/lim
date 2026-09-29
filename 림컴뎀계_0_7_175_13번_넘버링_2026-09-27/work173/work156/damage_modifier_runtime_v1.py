"""Generic combat damage modifier runtime.

Affiliation/identity modules register declarative modifiers here; the damage
engine only resolves applicable modifiers at the exact coin timing.
"""
from __future__ import annotations
from typing import Any, Dict

from buff_debuff_runtime_v1 import BuffDebuffRuntime


class DamageModifierRuntime:
    KEY = "damage_modifiers"

    @classmethod
    def register(cls, state, *, target_identity_id: str, kind: str, amount: float,
                 source_identity_id: str = "", attack_type: str | None = None,
                 critical_only: bool = False, skill_name: str | None = None,
                 reason: str = "", rule_id: str | None = None) -> Dict[str, Any]:
        mod = {
            "source_identity_id": str(source_identity_id),
            "target_identity_id": str(target_identity_id),
            "kind": str(kind),
            "amount": float(amount),
            "attack_type": attack_type,
            "critical_only": bool(critical_only),
            "skill_name": skill_name,
            "reason": str(reason),
            "rule_id": rule_id,
        }
        state.runtime.setdefault(cls.KEY, []).append(mod)
        return mod

    @classmethod
    def resolve(cls, state, identity, skill, coin, is_crit: bool, *, timing: str = "damage", context: Dict[str, Any] | None = None) -> Dict[str, float]:
        out = {
            "damage_percent": 0.0,
            "critical_damage_percent": 0.0,
            "flat_damage": 0.0,
            "skill_power": 0.0,
            "clash_power": 0.0,
            "base_power_bonus": 0.0,
            "coin_power": 0.0,
            "plus_coin_power": 0.0,
            "minus_coin_power": 0.0,
            "attack_level_bonus": 0.0,
            "defense_level_bonus": 0.0,
            "vulnerability": 0.0,
            "extra_damage_scale": 0.0,
        }
        for mod in state.runtime.get(cls.KEY, []) or []:
            if str(mod.get("target_identity_id", "")) != str(identity.id):
                continue
            if mod.get("attack_type") and str(mod["attack_type"]) != str(getattr(coin, "damage_type", "")):
                continue
            if mod.get("skill_name") and str(mod["skill_name"]) != str(getattr(skill, "name", "")):
                continue
            if mod.get("critical_only") and not is_crit:
                continue
            kind = str(mod.get("kind", ""))
            if kind in out:
                out[kind] += float(mod.get("amount", 0.0))

        # Buff/Debuff Runtime is the declarative lifecycle owner.  Resolve both
        # actor-scoped modifiers and modifiers attached to the enemy target so
        # vulnerability/debuff effects can participate in the same damage path.
        # Fast path: most legacy calculations have no declarative B/D state.
        buff_store = getattr(state, "runtime", {}).get(BuffDebuffRuntime.KEY)
        if buff_store:
            actor_values = BuffDebuffRuntime.resolve(state, target_id=str(identity.id), timing=timing, context=context, scope="outgoing")
            enemy_values = BuffDebuffRuntime.resolve(state, target_id="enemy", timing=timing, context=context, scope="incoming")
            for values in (actor_values, enemy_values):
                for key, amount in values.items():
                    key = str(key)
                    amount = float(amount)
                    if key in out:
                        out[key] += amount
                    elif key in {"damage_taken_up", "vulnerability_percent"}:
                        out["vulnerability"] += amount
                    elif key == "defense_level_down":
                        out["defense_level_bonus"] -= amount

        # Vulnerability is a target-side damage multiplier; expose it through
        # the same dynamic percentage channel without double-registering it.
        out["damage_percent"] += out["vulnerability"]
        return out
