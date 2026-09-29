"""Generic resource runtime for 림컴뎀계 0.5.11.

Keeps identity-specific resources separate from the core damage formula while
providing one consistent lifecycle: set -> gain/loss -> clamp -> threshold
checks -> event log.  Initial/preheated values are explicit scenario input;
this module never invents prior-turn preparation.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

@dataclass
class ResourceSpec:
    name: str
    minimum: int = 0
    maximum: Optional[int] = None
    threshold_variants: Dict[str, int] = field(default_factory=dict)
    threshold_operators: Dict[str, str] = field(default_factory=dict)
    turn_reset: Optional[int] = None

    def threshold_met(self, value: int, variant: str) -> bool:
        if variant not in self.threshold_variants:
            return False
        op = self.threshold_operators.get(variant, ">=")
        target = int(self.threshold_variants[variant])
        if op == ">=": return value >= target
        if op == ">": return value > target
        if op == "<=": return value <= target
        if op == "<": return value < target
        if op == "==": return value == target
        raise ValueError(f"unsupported resource threshold operator: {op}")

    def clamp(self, value: int) -> int:
        value = max(self.minimum, int(value))
        if self.maximum is not None:
            value = min(value, int(self.maximum))
        return value

class ResourceRuntime:
    def __init__(self, specs: Optional[Dict[str, ResourceSpec]] = None):
        self.specs = dict(specs or {})

    @classmethod
    def from_scenario(cls, scenario: Dict[str, Any]):
        specs: Dict[str, ResourceSpec] = {}
        raw = scenario.get("resource_specs", {}) or {}
        for name, cfg in raw.items():
            cfg = cfg if isinstance(cfg, dict) else {"maximum": cfg}
            specs[str(name)] = ResourceSpec(
                str(name), int(cfg.get("minimum", 0)),
                None if cfg.get("maximum") is None else int(cfg.get("maximum")),
                {str(k): int(v) for k, v in (cfg.get("threshold_variants", {}) or {}).items()},
                {str(k): str(v) for k, v in (cfg.get("threshold_operators", {}) or {}).items()},
                None if cfg.get("turn_reset") is None else int(cfg.get("turn_reset")))
        return cls(specs)

    def register(self, name: str, minimum: int = 0, maximum: Optional[int] = None,
                 threshold_variants: Optional[Dict[str, int]] = None,
                 threshold_operators: Optional[Dict[str, str]] = None, turn_reset: Optional[int] = None) -> ResourceSpec:
        spec = ResourceSpec(str(name), int(minimum), None if maximum is None else int(maximum),
                            dict(threshold_variants or {}), dict(threshold_operators or {}),
                            None if turn_reset is None else int(turn_reset))
        self.specs[spec.name] = spec
        return spec

    @staticmethod
    def _core_resource_attr(name: str):
        return {"충전": "charge", "충전 위력": "charge_potency", "탄환": "ammo", "호흡": "poise_potency"}.get(str(name))

    def get(self, fighter, name: str, default: int = 0) -> int:
        name = str(name)
        attr = self._core_resource_attr(name)
        if attr == "charge":
            return int(getattr(fighter, "charge", default))
        if attr == "charge_potency":
            return int(getattr(fighter, "charge_potency", default))
        if attr == "ammo":
            return int(getattr(fighter, "ammo", default))
        if attr == "poise_potency":
            return int(getattr(getattr(fighter, "poise", None), "potency", default))
        return int(fighter.resources.get(name, default))

    def set(self, fighter, name: str, value: int, state=None, reason: str = "set") -> int:
        name = str(name)
        spec = self.specs.get(name)
        requested = int(value)
        value = spec.clamp(requested) if spec else requested
        before = self.get(fighter, name)
        # Preserve overflow as an explicit lifecycle event instead of silently
        # discarding it. Charge-over-cap mechanics can consume this event and
        # convert the excess into another resource on the next turn.
        if spec is not None and spec.maximum is not None and requested > int(spec.maximum):
            overflow = requested - int(spec.maximum)
            owner_id = str(getattr(fighter, 'id', '') or '')
            if not owner_id and state is not None:
                for iid, ff in getattr(state, 'fighters', {}).items():
                    if ff is fighter:
                        owner_id = str(iid); break
            skill_id = ''
            if str(reason).startswith('skill:'):
                parts = str(reason).split(':', 2)
                if len(parts) >= 2:
                    skill_id = str(parts[1])
            self._log(state, {
                'event': 'resource_overflow', 'resource': name,
                'identity_id': owner_id, 'skill_id': skill_id,
                'requested': requested, 'maximum': int(spec.maximum),
                'overflow': overflow, 'before': before, 'after': int(value),
                'reason': reason,
            })
        attr = self._core_resource_attr(name)
        if attr == "charge":
            fighter.charge = value
        elif attr == "charge_potency":
            fighter.charge_potency = value
        elif attr == "ammo":
            fighter.ammo = value
        elif attr == "poise_potency":
            if getattr(fighter, "poise", None) is None:
                return value
            fighter.poise.potency = value
        else:
            fighter.resources[name] = value
        event={"event":"resource_change", "resource":name, "reason":reason,
               "delta":value-before, "before":before, "after":value}
        self._log(state, event)
        # Emit a distinct threshold-crossing event so higher layers can react
        # without reverse-engineering the resource_change log.  This does not
        # itself execute a game effect.
        if spec:
            for variant, threshold in spec.threshold_variants.items():
                op=spec.threshold_operators.get(variant, ">=")
                crossed = self._threshold_crossed(before, value, int(threshold), op)
                if crossed:
                    self._log(state, {"event":"resource_threshold_reached", "resource":name,
                                      "variant":variant, "threshold":int(threshold),
                                      "operator":op, "before":before, "after":value, "reason":reason})
        return value

    def change(self, fighter, name: str, delta: int, state=None, reason: str = "effect", track_cumulative: bool = True) -> int:
        before = self.get(fighter, name)
        new_value = self.set(fighter, name, before + int(delta), state=state, reason=reason)
        # Keep an encounter-scoped cumulative consumption counter for mechanics such as
        # "전투 중 누적으로 X를 10 소모할 때마다 Y 1 얻음". The counter records
        # explicit resource consumption only; lifecycle decay (e.g. Charge -1 at
        # turn end) can opt out with track_cumulative=False.
        if int(delta) < 0 and state is not None and track_cumulative:
            consumed = min(before, -int(delta))
            if consumed > 0:
                bucket = state.runtime.setdefault('cumulative_resource_consumed', {})
                key = (str(getattr(fighter, 'id', '')), name)
                # FighterState does not require an id field; resolve the owner by identity map when possible.
                if not key[0]:
                    for iid, ff in getattr(state, 'fighters', {}).items():
                        if ff is fighter:
                            key = (str(iid), name); break
                total_before = int(bucket.get(key, 0))
                total_after = total_before + consumed
                bucket[key] = total_after
                self._log(state, {'event':'resource_cumulative_consumed', 'identity_id':key[0],
                                   'resource':name, 'amount':consumed,
                                   'cumulative_before':total_before, 'cumulative_after':total_after,
                                   'reason':reason})
        return new_value

    def meets(self, fighter, name: str, threshold: int, op: str = ">=") -> bool:
        value = self.get(fighter, name)
        if op == ">=": return value >= int(threshold)
        if op == ">": return value > int(threshold)
        if op == "<=": return value <= int(threshold)
        if op == "<": return value < int(threshold)
        if op == "==": return value == int(threshold)
        raise ValueError(f"unsupported resource operator: {op}")

    def variant_ready(self, fighter, name: str, variant: str) -> bool:
        spec = self.specs.get(str(name))
        if not spec or variant not in spec.threshold_variants:
            return False
        return spec.threshold_met(self.get(fighter, name), variant)

    @staticmethod
    def _threshold_crossed(before: int, after: int, threshold: int, op: str) -> bool:
        if op == ">=": return before < threshold <= after
        if op == ">": return before <= threshold < after
        if op == "<=": return before > threshold >= after
        if op == "<": return before >= threshold > after
        if op == "==": return after == threshold and before != threshold
        raise ValueError(f"unsupported resource threshold operator: {op}")

    def reset_turn(self, fighter, state=None) -> None:
        """Apply explicit per-turn reset values declared by ResourceSpec."""
        for name, spec in self.specs.items():
            if spec.turn_reset is None:
                continue
            before = self.get(fighter, name)
            self.set(fighter, name, spec.turn_reset, state=state, reason="turn_reset")
            if state is not None:
                state.event_log.append({"event":"resource_turn_reset", "resource":name,
                                        "before":before, "after":self.get(fighter,name)})

    def reset_turn_all(self, state, identity_map=None) -> None:
        """Apply declared turn resets to every fighter that owns the resource.

        Resource specs are global by scenario; missing resources are treated as
        zero and are initialized only when a non-zero reset is declared.
        """
        fighters = getattr(state, 'fighters', {}) if state is not None else {}
        for fighter in fighters.values():
            self.reset_turn(fighter, state=state)

    def consume(self, fighter, name: str, amount: int, state=None, reason: str = "consume", track_cumulative: bool = True) -> int:
        if int(amount) < 0:
            raise ValueError("consume amount must be non-negative")
        return self.change(fighter, name, -int(amount), state=state, reason=reason, track_cumulative=track_cumulative)

    def gain_charge_barrier(self, fighter, amount: int, state=None, reason: str = "charge_barrier_gain") -> int:
        """Gain Charge Barrier and materialize its shield immediately.

        Charge Barrier is a separate resource axis from Charge Count/Potency.
        Each stack grants 3 Shield, or 5 for W Corp employees. The shield is
        tracked separately so Turn End can expire only the shield originating
        from Charge Barrier.
        """
        amount = max(0, int(amount))
        # Explicit catalog substitution: some identities convert every Charge
        # Barrier acquisition into another named resource. The substitution is
        # checked before Charge Barrier shield materialization so no barrier
        # or shield is created in that case.
        substitutions = ((getattr(state, 'runtime', {}) or {}).get('charge_barrier_substitution', {})
                         if state is not None else {})
        target = substitutions.get(str(getattr(fighter, 'id', '') or ''))
        if target:
            after = self.gain(fighter, target, amount, state=state, reason=f'{reason}:substitution')
            if state is not None:
                state.event_log.append({'event':'resource_substitution',
                    'source':'충전 역장','target':target,'identity_id':str(getattr(fighter,'id','') or ''),
                    'amount':amount,'reason':reason})
            return self.get(fighter, '충전 역장', 0)
        before = self.get(fighter, "충전 역장", 0)
        after = self.set(fighter, "충전 역장", before + amount, state=state, reason=reason)
        gained = max(0, after - before)
        scale = 5 if bool(getattr(fighter, "is_wcorp", False)) else 3
        shield = gained * scale
        fighter.shield = float(getattr(fighter, "shield", 0.0)) + shield
        fighter.charge_barrier_shield = float(getattr(fighter, "charge_barrier_shield", 0.0)) + shield
        if state is not None:
            state.event_log.append({"event":"charge_barrier_gain", "identity_id":str(getattr(fighter,'id','') or ''),
                                    "amount":gained, "shield_gain":shield, "scale":scale,
                                    "before":before, "after":after, "shield_after":fighter.shield,
                                    "reason":reason})
        return after

    def consume_shield(self, fighter, amount: float, state=None, reason: str = "shield_damage") -> float:
        """Consume shield and reduce Charge Barrier after its shield unit is spent."""
        raw = max(0.0, float(amount))
        shield_before = float(getattr(fighter, "shield", 0.0))
        actual = min(raw, shield_before)
        if actual <= 0:
            return 0.0
        fighter.shield = shield_before - actual
        barrier_shield_before = float(getattr(fighter, "charge_barrier_shield", 0.0))
        barrier_spent = min(actual, barrier_shield_before)
        fighter.charge_barrier_shield = barrier_shield_before - barrier_spent
        scale = 5 if bool(getattr(fighter, "is_wcorp", False)) else 3
        barrier_loss = int(barrier_spent // scale)
        if barrier_loss > 0:
            before = self.get(fighter, "충전 역장", 0)
            self.set(fighter, "충전 역장", max(0, before - barrier_loss), state=state, reason="charge_barrier_shield_spent")
            fighter.charge_barrier_shield = max(0.0, fighter.charge_barrier_shield)
        if state is not None:
            state.event_log.append({"event":"shield_consumed", "identity_id":str(getattr(fighter,'id','') or ''),
                                    "amount":actual, "shield_before":shield_before, "shield_after":fighter.shield,
                                    "charge_barrier_shield_before":barrier_shield_before,
                                    "charge_barrier_shield_after":fighter.charge_barrier_shield,
                                    "charge_barrier_lost":barrier_loss, "reason":reason})
        return actual

    def gain(self, fighter, name: str, amount: int, state=None, reason: str = "gain") -> int:
        if int(amount) < 0:
            raise ValueError("gain amount must be non-negative")
        return self.change(fighter, name, int(amount), state=state, reason=reason)

    @staticmethod
    def _log(state, event):
        if state is not None:
            state.event_log.append(event)
