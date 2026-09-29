"""Common seven-keyword runtime.

Owns the generic lifecycle rules for Burn, Bleed, Tremor, Rupture, Sinking,
Poise and Charge.  Identity-specific variants stay outside this module.
"""
from __future__ import annotations
from typing import Any, Dict

KEYWORDS = ("Burn", "Bleed", "Tremor", "Rupture", "Sinking", "Poise", "Charge")

class KeywordRuntime:
    @staticmethod
    def _status(unit, name):
        return getattr(unit, "statuses", {}).get(name)

    @staticmethod
    def _keyword_damage_multiplier(enemy, keyword: str) -> float:
        """Return target-side damage multiplier for a keyword effect.

        1.0 = unchanged, 0.5 = 50% damage, 0 = immune.
        This modifier is deliberately separate from Sin/Gloom affinity resistance.
        """
        mods = getattr(enemy, "keyword_damage_modifiers", {}) or {}
        for key in (keyword, keyword.lower(), keyword.capitalize()):
            if key in mods:
                try:
                    return max(0.0, float(mods[key]))
                except (TypeError, ValueError):
                    return 1.0
        return 1.0

    @staticmethod
    def _gloom_multiplier(enemy) -> float:
        """Convert Gloom affinity resistance to a damage multiplier."""
        try:
            value = float((getattr(enemy, "sin_res", {}) or {}).get("gloom", 1.0))
        except (TypeError, ValueError):
            value = 1.0
        if value < 1.0:
            return max(0.0, 1.0 + (value - 1.0) / 2.0)
        return max(0.0, value)

    @classmethod
    def _sinking_gloom_damage(cls, enemy, raw: float) -> tuple[float, float]:
        """Apply Sinking keyword damage modifier and Gloom affinity resistance."""
        multiplier = cls._keyword_damage_multiplier(enemy, "Sinking")
        gloom_multiplier = cls._gloom_multiplier(enemy)
        return raw * multiplier * gloom_multiplier, multiplier * gloom_multiplier

    @staticmethod
    def consume(statuses, name: str, amount: int = 1):
        st = statuses.get(name)
        if not st:
            return 0
        consumed = min(max(0, int(amount)), max(0, int(st.count)))
        st.count -= consumed
        if st.count <= 0:
            statuses.pop(name, None)
        return consumed

    @classmethod
    def on_target_hit(cls, state) -> Dict[str, Any]:
        """Resolve generic enemy-side hit-triggered keyword effects."""
        out = {"rupture_damage": 0.0, "sinking_sp": 0, "events": []}
        enemy = state.enemy
        rupture = enemy.statuses.get("Rupture")
        if rupture and rupture.count > 0 and rupture.potency > 0 and enemy.hp > 0:
            raw = float(rupture.potency)
            actual = min(raw, enemy.hp)
            enemy.hp -= actual; state.turn_damage += actual
            cls.consume(enemy.statuses, "Rupture")
            out["rupture_damage"] = actual
            out["events"].append({"event":"rupture","raw_damage":raw,"actual_damage":actual})

        sinking = enemy.statuses.get("Sinking")
        if sinking and sinking.count > 0 and sinking.potency > 0:
            potency = int(sinking.potency)
            if bool(getattr(enemy, "is_abnormality", False)):
                # Non-SP/Abnormality targets take Gloom-affinity HP damage
                # instead of ordinary SP damage when Sinking activates.
                raw = float(potency)
                modified, total_multiplier = cls._sinking_gloom_damage(enemy, raw)
                actual = min(modified, enemy.hp)
                enemy.hp -= actual
                state.turn_damage += actual
                cls.consume(enemy.statuses, "Sinking")
                out["sinking_gloom_damage"] = actual
                out["events"].append({"event":"sinking_gloom","raw_damage":raw,
                                       "modified_damage":modified,
                                       "actual_damage":actual,
                                       "keyword_damage_multiplier":cls._keyword_damage_multiplier(enemy, "Sinking"),
                                       "gloom_resistance_multiplier":cls._gloom_multiplier(enemy),
                                       "total_multiplier":total_multiplier,
                                       "hp_after":enemy.hp,
                                       "potency":potency})
            else:
                before = enemy.sp
                enemy.sp = max(-45, min(45, enemy.sp - potency))
                cls.consume(enemy.statuses, "Sinking")
                out["sinking_sp"] = enemy.sp - before
                out["events"].append({"event":"sinking","potency":potency,
                                       "sp_before":before,"sp_after":enemy.sp})
        for event in out["events"]:
            state.event_log.append(event)
        return out

    @classmethod
    def sinking_deluge(cls, state, target=None) -> Dict[str, Any]:
        """Explicit Sinking Deluge activation; never auto-triggers on hit.

        For SP targets, Deluge deals SP damage equal to Potency*Count; any
        amount that would pass below -45 becomes Gloom HP damage. For
        Non-SP/Abnormality targets, the full amount is Gloom HP damage.
        Sinking is removed after activation.
        """
        enemy = target if target is not None else state.enemy
        sinking = enemy.statuses.get("Sinking")
        if not sinking or sinking.count <= 0 or sinking.potency <= 0:
            return {"applied": False, "gloom_damage": 0.0, "sp_damage": 0, "removed": False}
        potency = int(sinking.potency)
        count = int(sinking.count)
        raw = potency * count
        out = {"applied": True, "raw": raw, "gloom_damage": 0.0, "sp_damage": 0,
               "removed": True, "events": []}
        if bool(getattr(enemy, "is_abnormality", False)):
            modified, total_multiplier = cls._sinking_gloom_damage(enemy, float(raw))
            actual = min(modified, enemy.hp)
            enemy.hp -= actual
            state.turn_damage += actual
            out["gloom_damage"] = actual
            out["events"].append({"event":"sinking_deluge_gloom", "raw_damage":raw,
                                   "modified_damage":modified, "actual_damage":actual,
                                   "keyword_damage_multiplier":cls._keyword_damage_multiplier(enemy, "Sinking"),
                                   "gloom_resistance_multiplier":cls._gloom_multiplier(enemy),
                                   "total_multiplier":total_multiplier, "potency":potency, "count":count})
        else:
            before_sp = int(enemy.sp)
            # The source rule routes Deluge overflow below -45 SP into Gloom HP damage.
            # This is not an optional mode: the overflow is part of the canonical rule.
            keyword_mult = cls._keyword_damage_multiplier(enemy, "Sinking")
            effective_sp_damage = max(0, int(raw * keyword_mult))
            target_sp = before_sp - effective_sp_damage
            overflow = max(0, -45 - target_sp)
            if overflow > 0:
                modified, total_multiplier = cls._sinking_gloom_damage(enemy, float(overflow))
                actual = min(modified, enemy.hp)
                enemy.hp -= actual
                state.turn_damage += actual
                out["gloom_damage"] = actual
            enemy.sp = max(-45, target_sp)
            out["sp_damage"] = before_sp - enemy.sp
            out["events"].append({"event":"sinking_deluge", "raw_damage":raw,
                                   "effective_sp_damage":effective_sp_damage,
                                   "sp_before":before_sp, "sp_after":enemy.sp,
                                   "sp_damage":out["sp_damage"],
                                   "gloom_damage":out["gloom_damage"],
                                   "keyword_damage_multiplier":keyword_mult,
                                   "overflow_to_hp":bool(overflow > 0),
                                   "potency":potency, "count":count})
        enemy.statuses.pop("Sinking", None)
        for event in out["events"]:
            state.event_log.append(event)
        return out

    @staticmethod
    def critical_chance_percent(fighter) -> float:
        poise = getattr(fighter, "poise", None)
        potency = max(0, int(getattr(poise, "potency", 0))) if poise is not None else 0
        return min(100.0, potency * 5.0)

    @classmethod
    def on_critical(cls, state, identity_id: str, successful: bool = True) -> Dict[str, Any]:
        """Consume exactly one Poise Count for one successful logical critical.

        Secondary target resolution must call this only once for the logical
        coin, so Poise is not consumed once per target.
        """
        fighter = state.fighters[identity_id]
        poise = getattr(fighter, "poise", None)
        before = int(getattr(poise, "count", 0)) if poise is not None else 0
        if not successful or poise is None or before <= 0:
            return {"consumed": 0, "before": before, "after": before}
        poise.count = max(0, before - 1)
        event = {"event": "poise_consume_critical", "identity_id": identity_id,
                 "before": before, "after": poise.count, "consumed": 1}
        state.event_log.append(event)
        return {"consumed": 1, "before": before, "after": poise.count, "event": event}

    @classmethod
    def turn_end(cls, state) -> Dict[str, Any]:
        """Resolve generic turn-end keyword effects exactly once."""
        out = {"burn_damage": 0.0, "expired": [], "poise_expired": [], "charge_consumed": {}}
        enemy = state.enemy
        burn = enemy.statuses.get("Burn")
        if burn and burn.count > 0 and burn.potency > 0 and enemy.hp > 0:
            raw = float(burn.potency); actual = min(raw, enemy.hp)
            enemy.hp -= actual; state.turn_damage += actual
            cls.consume(enemy.statuses, "Burn")
            out["burn_damage"] = actual
            event = {"event":"turn_end_burn","raw_damage":raw,"actual_damage":actual,
                     "enemy_hp_after":enemy.hp,"burn_potency":burn.potency,
                     "burn_count_after":enemy.statuses.get("Burn").count if enemy.statuses.get("Burn") else 0}
            state.event_log.append(event)
        # Tremor Count is a turn-lifecycle value as well as a Burst resource.
        # A Burst consumes its own Count immediately; any remaining Tremor Count
        # still loses 1 at Turn End. Keep this here so non-Burst turns also
        # follow the generic Tremor lifecycle.
        tremor = enemy.statuses.get("Tremor")
        if tremor and tremor.count > 0:
            before = int(tremor.count)
            tremor.count = max(0, before - 1)
            event = {"event": "tremor_turn_end", "before": before,
                     "after": tremor.count, "potency": int(tremor.potency)}
            state.event_log.append(event)
            if tremor.count == 0:
                enemy.statuses.pop("Tremor", None)
                out["expired"].append("Tremor")

        # Poise Count is a turn-lifecycle value.  Consume it here once; the
        # DamageEngine must not repeat the same mutation after this bridge.
        for identity_id, fighter in state.fighters.items():
            poise = getattr(fighter, "poise", None)
            if poise is not None and poise.count > 0:
                before = int(poise.count)
                poise.count = max(0, before - 1)
                event = {"event": "poise_turn_end", "identity_id": str(identity_id),
                         "before": before, "after": poise.count}
                state.event_log.append(event)
                if poise.count == 0:
                    out["poise_expired"].append(str(identity_id))

            # Charge is a generic keyword resource.  Do not touch unrelated
            # identity resources such as Bio Material merely because they are
            # represented on the same ResourceRuntime axis.
            # Charge Count decays independently of Charge Barrier.
            charge_before = int(getattr(fighter, "charge", 0))
            if charge_before > 0:
                from resource_runtime_v1 import ResourceRuntime
                rr = state.runtime.get("resource_runtime")
                if rr is None:
                    rr = ResourceRuntime()
                charge_after = rr.consume(fighter, "충전", 1, state=state, reason="keyword_turn_end", track_cumulative=False)
                out["charge_consumed"][str(identity_id)] = charge_before - charge_after

            # Charge Barrier lifecycle: each remaining stack becomes one Charge
            # Count, then the Barrier and its generated Shield expire completely.
            from resource_runtime_v1 import ResourceRuntime
            rr = state.runtime.get("resource_runtime") or ResourceRuntime()
            barrier = rr.get(fighter, "충전 역장", 0)
            if barrier > 0:
                rr.gain(fighter, "충전", barrier, state=state, reason="charge_barrier_turn_end")
                before_barrier = barrier
                rr.set(fighter, "충전 역장", 0, state=state, reason="charge_barrier_turn_end_expire")
                generated = float(getattr(fighter, "charge_barrier_shield", 0.0))
                fighter.shield = max(0.0, float(getattr(fighter, "shield", 0.0)) - generated)
                fighter.charge_barrier_shield = 0.0
                state.event_log.append({"event":"charge_barrier_turn_end", "identity_id":str(identity_id),
                                       "barrier_before":before_barrier, "charge_gained":before_barrier,
                                       "generated_shield_expired":generated, "shield_after":fighter.shield})
        return out

    @classmethod
    def burst(cls, state, name: str = "Tremor", count_cost: int = 1) -> Dict[str, Any]:
        st = state.enemy.statuses.get(name)
        if not st or st.potency <= 0 or st.count <= 0:
            return {"applied": False, "damage": 0.0, "stagger_threshold_raised": 0}
        if name != "Tremor":
            return {"applied": False, "damage": 0.0, "stagger_threshold_raised": 0}
        amount = int(st.potency)
        state.enemy.stagger_thresholds = [x + amount for x in state.enemy.stagger_thresholds]
        cls.consume(state.enemy.statuses, name, count_cost)
        event = {"event":"tremor_burst", "status":name,
                 "stagger_threshold_raised":amount,
                 "count_after":state.enemy.statuses.get(name).count if state.enemy.statuses.get(name) else 0,
                 "stagger_thresholds_after":list(state.enemy.stagger_thresholds)}
        state.event_log.append(event)
        return {"applied": True, "damage": 0.0, "stagger_threshold_raised": amount, "event": event}

    @classmethod
    def add(cls, unit, name: str, potency: int = 0, count: int = 0, *, state=None, event=None, source_id=None):
        """Apply a keyword status through the canonical keyword mutation boundary.

        Tremor is represented by two independent axes: Potency and Count.  The
        caller may therefore provide either or both.  Optional event/state
        context is deliberately accepted here so future declarative Tremor
        application modifiers can be applied at the exact mutation boundary
        without identity-specific status writers.
        """
        statuses = getattr(unit, 'statuses', {})
        st = statuses.get(name)
        if st is None:
            from limbus_damage_engine_v29 import Status
            st = Status(); statuses[name] = st
        p = int(potency); c = int(count)
        if name in {'Tremor', 'Burn'}:
            ctx = getattr(event, 'ctx', {}) if event is not None else {}
            # Context modifiers are additive and scoped to this exact status
            # application. Burn uses the same common mutation boundary as Tremor.
            p += int(ctx.get(f'{name.lower()}_potency_bonus', 0) or 0)
            c += int(ctx.get(f'{name.lower()}_count_bonus', 0) or 0)
            if potency > 0: p = max(0, p)
            if count > 0: c = max(0, c)
        before = (int(getattr(st, 'potency', 0)), int(getattr(st, 'count', 0)))
        st.potency += p; st.count += c
        if state is not None and hasattr(state, 'event_log'):
            state.event_log.append({
                'event': 'keyword_gain', 'keyword': name,
                'source_id': str(source_id or ''),
                'potency_added': p, 'count_added': c,
                'before': before,
                'after': (int(st.potency), int(st.count)),
            })
        return st

    @classmethod
    def add_tremor(cls, unit, potency=0, count=0, *, state=None, event=None, source_id=None):
        """Canonical Tremor application entry point."""
        return cls.add(unit, 'Tremor', potency, count, state=state, event=event, source_id=source_id)
