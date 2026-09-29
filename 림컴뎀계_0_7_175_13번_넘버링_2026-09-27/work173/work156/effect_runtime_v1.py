"""Common Effect IR dispatcher foundation.

Effects are normalized into commands. Execution remains owned by existing
runtimes until a handler is explicitly registered.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Callable, Dict, Iterable, Optional
from rule_ir_v1 import EffectIR

EFFECT_CATEGORIES = {
    "state": {
        "set_state", "state_change", "flag", "set_flag",
    "register_fatal_prevention", "register_damage_modifier_highest_poise", "sp_gain",
    },
    "resource": {
        "resource_gain", "resource_consume", "resource_set", "resource_convert", "resource_spend_charge_barrier_lowest_hp_2", "kill_charge_barrier_self_random_ally",
        "resource_gain_affiliation_count", "resource_gain_lowest_allies", "resource_gain_from_charge_potency", "resource_gain_from_charge_potency_plus", "next_turn_resource_gain", "next_turn_charge_barrier_from_charge", "resource_gain_lowest_hp_ally",
    },
    "status": {
        "status_gain", "status_lose", "status_set", "status_convert", "status_transform", "resource_threshold_status_gain", "resource_threshold_status_gain", "status_transform",
    "amplitude_conversion", "amplitude_entanglement",
    "status_gain_affiliation", "status_gain_affiliation_ordered",
    "sinking_deluge",
        "poise_gain_lowest_ally", "poise_gain_lowest_affiliation", "poise_gain_self_bonus",
        "heal_lowest_ally",
        "status_gain_affiliation", "status_gain_affiliation_ordered",
        "enemy_status_count_gain", "hongmaehwa_crit", "poise_gain",
        "support_poise_gain", "support_poise_count_bonus",
    },
    "buff_debuff": {"buff_apply", "debuff_apply", "buff_remove", "debuff_remove"},
    "modifier": {
        "damage_percent", "damage_flat", "critical_damage_percent", "skill_power",
        "coin_power", "vulnerability", "extra_damage_scale", "status_potency_damage",
    },
    "action": {"support_action", "extra_action", "trigger_action", "assist_action", "queue_action"},
    "legacy": {
        "legacy_gimmick",
    },
}

# Effects whose semantics are fully owned by the common EffectExecutor.
# Keep this explicit so category membership alone never silently migrates a
# specialized gimmick.
GENERIC_EXECUTABLE_EFFECTS = frozenset({
    "buff_apply", "debuff_apply", "buff_remove", "debuff_remove",
    "set_state", "state_change", "flag", "set_flag",
    "resource_gain", "resource_consume", "resource_set", "resource_convert", "resource_spend_charge_barrier_lowest_hp_2", "kill_charge_barrier_self_random_ally", "resource_gain_affiliation_count", "resource_gain_lowest_allies", "resource_gain_from_charge_potency", "resource_gain_from_charge_potency_plus", "next_turn_resource_gain", "next_turn_charge_barrier_from_charge", "resource_gain_lowest_hp_ally", "resource_gain_from_charge_potency", "resource_gain_from_charge_potency_plus", "next_turn_resource_gain", "next_turn_charge_barrier_from_charge", "resource_gain_lowest_hp_ally",
    "status_gain", "status_lose", "status_set", "status_convert", "status_transform", "resource_threshold_status_gain",
    "amplitude_conversion", "amplitude_entanglement",
    "status_gain_affiliation", "status_gain_affiliation_ordered",
    "sinking_deluge",
        "poise_gain_lowest_ally", "poise_gain_lowest_affiliation", "poise_gain_self_bonus",
        "heal_lowest_ally",
    "damage_percent", "damage_flat", "critical_damage_percent",
    "skill_power", "coin_power", "vulnerability", "extra_damage_scale",
    "status_potency_damage",
    "register_fatal_prevention", "register_damage_modifier_highest_poise", "sp_gain",
    "support_poise_gain", "support_poise_count_bonus", "hongmaehwa_crit", "enemy_status_count_gain", "poise_gain",
    "queue_action", "support_action", "assist_action", "extra_action", "trigger_action",
    "hongmaehwa_crit", "enemy_status_count_gain",
    "poise_gain_lowest_ally", "poise_gain_lowest_affiliation", "poise_gain_self_bonus", "heal_lowest_ally",
})



@dataclass(frozen=True)
class EffectCommand:
    kind: str
    params: Dict[str,Any]
    rule_id: str = ''
    category: str = 'unknown'

class EffectRuntime:
    def __init__(self): self._handlers: Dict[str,Callable[[EffectCommand,Dict[str,Any]],Any]] = {}
    def register(self, kind: str, handler: Callable[[EffectCommand,Dict[str,Any]],Any]) -> None:
        if not callable(handler): raise TypeError('handler must be callable')
        self._handlers[str(kind)] = handler
    @staticmethod
    def category_for(kind: str) -> str:
        k=str(kind)
        for category, kinds in EFFECT_CATEGORIES.items():
            if k in kinds: return category
        return 'unknown'

    @staticmethod
    def is_generic_executable(kind: str) -> bool:
        return str(kind) in GENERIC_EXECUTABLE_EFFECTS
    def resolve(self, effect: EffectIR, ctx: Optional[Dict[str,Any]]=None, rule_id: str='') -> EffectCommand:
        kind=str(effect.kind)
        return EffectCommand(kind, dict(effect.params or {}), str(rule_id), self.category_for(kind))
    def dispatch(self, effect: EffectIR, ctx: Optional[Dict[str,Any]]=None, rule_id: str='') -> Any:
        command=self.resolve(effect,ctx,rule_id); handler=self._handlers.get(command.kind)
        if handler is None: return command
        return handler(command, dict(ctx or {}))
    def dispatch_all(self, effects: Iterable[EffectIR], ctx: Optional[Dict[str,Any]]=None, rule_id: str='') -> list[Any]:
        return [self.dispatch(e,ctx,rule_id) for e in effects]
