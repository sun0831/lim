"""Common buff/debuff runtime foundation.

Stores declarative timed modifiers separately from identity-specific gimmicks.
The runtime is intentionally small: it owns lifecycle/stack/duration and exposes
resolved modifiers; damage/effect runtimes remain responsible for applying the
numerical result.
"""
from __future__ import annotations
from copy import deepcopy
from typing import Any, Dict, Optional, Mapping
from status_effect_lifecycle_v1 import StatusLifecycle, classify_status_effect, lifecycle_profile

KEY = "buff_debuffs"

class BuffDebuffRuntime:
    KEY = KEY

    @classmethod
    def _store(cls, state) -> Dict[str, Dict[str, Any]]:
        return state.runtime.setdefault(cls.KEY, {})

    @classmethod
    def apply(cls, state, *, target_id: str, name: str, kind: str = "buff",
              potency: int = 0, count: int = 0, duration: Optional[int] = None,
              modifiers: Optional[Dict[str, float]] = None, source_id: str = "",
              rule_id: str = "", stack_mode: str = "add", max_count: Optional[int] = None,
              timing: str = "always", conditions: Optional[Dict[str, Any]] = None,
              modifier_policy: Optional[Dict[str, Any]] = None, priority: int = 0,
              stack_group: Optional[str] = None, consume_on: Optional[str] = None,
              lifecycle: Optional[str] = None, rule_expiry: Optional[Dict[str, Any]] = None,
              value_semantics: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        if kind not in {"buff", "debuff"}:
            raise ValueError("kind must be 'buff' or 'debuff'")
        profile = lifecycle_profile(str(name), {"consume_on": consume_on, "lifecycle": lifecycle} if (consume_on or lifecycle) else {})
        lifecycle_value = str(lifecycle or profile["lifecycle"])
        if lifecycle_value not in {x.value for x in StatusLifecycle}:
            raise ValueError(f"unsupported status lifecycle: {lifecycle_value}")
        key = f"{kind}:{target_id}:{name}"
        store = cls._store(state)
        old = deepcopy(store.get(key))
        item = deepcopy(old) if old else {
            "target_id": str(target_id), "name": str(name), "kind": kind,
            "potency": 0, "count": 0, "duration": duration,
            "modifiers": {}, "source_id": str(source_id), "rule_id": str(rule_id),
            "timing": str(timing or "always"), "conditions": deepcopy(conditions or {}),
            "modifier_policy": deepcopy(modifier_policy or {}), "priority": int(priority),
            "stack_group": str(stack_group or name), "consume_on": consume_on,
            "lifecycle": lifecycle_value, "rule_expiry": deepcopy(rule_expiry or {}),
            "value_semantics": deepcopy(value_semantics or profile.get("value_semantics") or {}),
            "status_category": str(profile.get("category", "unspecified")),
            "value_mode": str(profile.get("value_mode", "unspecified")),
            "consumption": str(profile.get("consumption", "none")),
            "expiration": str(profile.get("expiration", "unspecified")),
        }
        old_count = int(item.get("count", 0)) if old is not None else 0
        requested_count = int(count)
        if stack_mode == "replace" or old is None:
            item["potency"] = int(potency); item["count"] = requested_count
        elif stack_mode == "max":
            item["potency"] = max(int(item.get("potency", 0)), int(potency))
            item["count"] = max(int(item.get("count", 0)), requested_count)
        else:
            item["potency"] = int(item.get("potency", 0)) + int(potency)
            item["count"] = old_count + requested_count
        if max_count is not None:
            item["count"] = min(item["count"], int(max_count))
        accepted_count = max(0, int(item.get("count", 0)) - old_count) if stack_mode == "add" and old is not None else int(item.get("count", 0))
        if modifiers:
            incoming = {str(k): float(v) for k, v in modifiers.items()}
            if stack_mode == "replace" or old is None:
                item["modifiers"] = incoming
            elif stack_mode == "max":
                for k, v in incoming.items():
                    item["modifiers"][k] = max(float(item["modifiers"].get(k, v)), v)
            else:
                if max_count is not None and requested_count > 0 and accepted_count < requested_count:
                    ratio = accepted_count / requested_count
                    incoming = {k: v * ratio for k, v in incoming.items()}
                for k, v in incoming.items():
                    item["modifiers"][k] = float(item["modifiers"].get(k, 0.0)) + v
        if duration is not None:
            item["duration"] = int(duration)
        item["source_id"] = str(source_id or item.get("source_id", ""))
        item["rule_id"] = str(rule_id or item.get("rule_id", ""))
        if timing:
            item["timing"] = str(timing)
        if conditions is not None:
            item["conditions"] = deepcopy(conditions)
        if modifier_policy is not None:
            item["modifier_policy"] = deepcopy(modifier_policy)
        item["priority"] = int(priority)
        if stack_group is not None:
            item["stack_group"] = str(stack_group)
        if consume_on is not None:
            item["consume_on"] = str(consume_on)
        if lifecycle is not None:
            item["lifecycle"] = lifecycle_value
        if rule_expiry is not None:
            item["rule_expiry"] = deepcopy(rule_expiry)
        if value_semantics is not None:
            item["value_semantics"] = deepcopy(value_semantics)
        item["status_category"] = str(profile.get("category", item.get("status_category", "unspecified")))
        item["value_mode"] = str(profile.get("value_mode", item.get("value_mode", "unspecified")))
        item["consumption"] = str(profile.get("consumption", item.get("consumption", "none")))
        item["expiration"] = str(profile.get("expiration", item.get("expiration", "unspecified")))
        store[key] = item
        return deepcopy(item)

    @classmethod
    def remove(cls, state, *, target_id: str, name: str, kind: Optional[str] = None) -> int:
        store = cls._store(state)
        keys = [k for k, v in store.items() if str(v.get("target_id")) == str(target_id)
                and str(v.get("name")) == str(name)
                and (kind is None or str(v.get("kind")) == str(kind))]
        for k in keys: del store[k]
        return len(keys)

    @classmethod
    def has(cls, state, *, target_id: str, name: str, kind: Optional[str] = None) -> bool:
        return any(str(v.get("target_id")) == str(target_id) and str(v.get("name")) == str(name)
                   and (kind is None or str(v.get("kind")) == str(kind))
                   for v in cls._store(state).values())

    @classmethod
    def _condition_met(cls, state, item: Mapping[str, Any], context: Optional[Mapping[str, Any]]) -> bool:
        cond = item.get("conditions") or {}
        if not cond:
            return True
        ctx = dict(context or {})
        enemy = getattr(state, "enemy", None)
        target_id = str(item.get("target_id", ""))
        fighter = getattr(state, "fighters", {}).get(target_id)
        if "generated" in cond and bool(ctx.get("generated", False)) != bool(cond["generated"]):
            return False
        if "coin_index" in cond and int(ctx.get("coin_index", -1)) != int(cond["coin_index"]):
            return False
        if "coin_index_gte" in cond and int(ctx.get("coin_index", -1)) < int(cond["coin_index_gte"]):
            return False
        if "coin_index_lte" in cond and int(ctx.get("coin_index", -1)) > int(cond["coin_index_lte"]):
            return False
        if "enemy_staggered" in cond and bool(getattr(enemy, "staggered", False)) != bool(cond["enemy_staggered"]):
            return False
        if "actual_damage_gte" in cond and float(ctx.get("actual_damage", 0)) < float(cond["actual_damage_gte"]):
            return False
        if "actual_damage_lte" in cond and float(ctx.get("actual_damage", 0)) > float(cond["actual_damage_lte"]):
            return False
        for prefix, obj in (("enemy", enemy), ("self", fighter)):
            if obj is None:
                continue
            hp = float(getattr(obj, "hp", 0)); max_hp = float(getattr(obj, "max_hp", hp))
            if f"{prefix}_hp_pct_lte" in cond and max_hp and hp / max_hp * 100.0 > float(cond[f"{prefix}_hp_pct_lte"]):
                return False
            if f"{prefix}_hp_pct_gte" in cond and max_hp and hp / max_hp * 100.0 < float(cond[f"{prefix}_hp_pct_gte"]):
                return False
        status_name = cond.get("status")
        if status_name:
            target = enemy if cond.get("status_target", "enemy") == "enemy" else fighter
            st = getattr(target, "statuses", {}).get(str(status_name)) if target is not None else None
            field = str(cond.get("status_field", "potency"))
            value = float(getattr(st, field, 0)) if st is not None else 0.0
            if "status_gte" in cond and value < float(cond["status_gte"]): return False
            if "status_lte" in cond and value > float(cond["status_lte"]): return False
            if cond.get("status_present") is True and st is None: return False
            if cond.get("status_present") is False and st is not None: return False
        flag = cond.get("flag")
        if flag is not None:
            flags = getattr(state, "runtime", {}).get("condition_flags", {})
            if bool(flags.get(str(flag), False)) != bool(cond.get("flag_value", True)):
                return False
        return True

    @classmethod
    def _aggregate_modifier(cls, current: Optional[float], value: float, policy: str,
                             priority: int, order: int, meta: Dict[str, Any], key: str) -> tuple[float, Dict[str, Any]]:
        policy = str(policy or "add")
        if current is None:
            return value, {"priority": priority, "order": order, "policy": policy}
        prev = meta.get(key, {})
        prev_priority = int(prev.get("priority", 0))
        if policy == "max":
            return max(current, value), prev
        if policy == "min":
            return min(current, value), prev
        if policy == "replace":
            if priority >= prev_priority:
                return value, {"priority": priority, "order": order, "policy": policy}
            return current, prev
        if policy == "multiply_scale":
            # Values are represented as additive percentage scales (0.20 = +20%).
            # Convert each factor into a multiplicative scale without changing the
            # default additive behavior of existing modifiers.
            prev_factor = 1.0 + current
            factor = 1.0 + value
            return prev_factor * factor - 1.0, prev
        if policy != "add":
            raise ValueError(f"unsupported modifier aggregation policy: {policy}")
        return current + value, prev

    @classmethod
    def resolve(cls, state, *, target_id: str, kind: Optional[str] = None,
                timing: str = "always", context: Optional[Mapping[str, Any]] = None,
                scope: str = "all") -> Dict[str, float]:
        out: Dict[str, float] = {}
        meta: Dict[str, Any] = {}
        scope = str(scope or "all")
        outgoing_only = {"Damage Up", "Damage Down"}
        incoming_only = {"Protection", "Fragile", "Damage Taken Up", "Vulnerable", "Defense Level Down", "Defense Down"}
        for order, item in enumerate(cls._store(state).values()):
            if str(item.get("target_id")) != str(target_id): continue
            if kind is not None and str(item.get("kind")) != str(kind): continue
            name = str(item.get("name", ""))
            if scope == "outgoing" and name in incoming_only: continue
            if scope == "incoming" and name not in incoming_only: continue
            item_timing = str(item.get("timing", "always"))
            if item_timing not in {"always", str(timing)}: continue
            if not cls._condition_met(state, item, context): continue
            policy_map = item.get("modifier_policy") or {}
            skill_scope = policy_map.get("skill_scope")
            if skill_scope:
                skill_is_defense = bool((context or {}).get("skill_is_defense", False))
                if str(skill_scope) == "attack" and skill_is_defense:
                    continue
                if str(skill_scope) == "defense" and not skill_is_defense:
                    continue
            default_policy = str(policy_map.get("default", "add"))
            priority = int(item.get("priority", 0))
            local_meta = {"order": order}
            for key, raw_value in (item.get("modifiers") or {}).items():
                key = str(key); value = float(raw_value)
                policy = str(policy_map.get(key, default_policy))
                out[key], _ = cls._aggregate_modifier(out.get(key), value, policy, priority, order, meta, key)
                if key not in meta or policy == "replace" and priority >= int(meta[key].get("priority", 0)):
                    meta[key] = {"priority": priority, "order": order, "policy": policy}
        return out

    @classmethod
    def consume_on_event(cls, state, *, event: str, target_id: Optional[str] = None,
                         context: Optional[Mapping[str, Any]] = None) -> list[Dict[str, Any]]:
        """Consume count-based buffs/debuffs whose declarative lifecycle matches an event.

        Consumption is opt-in via ``consume_on``; existing effects are therefore
        behavior-preserving. Conditions are evaluated before consumption, and the
        returned records are suitable for EventLog/trigger attribution.
        """
        event = str(event)
        if state is None or not hasattr(state, "runtime"):
            return []
        consumed: list[Dict[str, Any]] = []
        store = cls._store(state)
        for key, item in list(store.items()):
            if str(item.get("consume_on") or "") != event:
                continue
            if target_id is not None and str(item.get("target_id")) != str(target_id):
                continue
            if not cls._condition_met(state, item, context):
                continue
            before = int(item.get("count", 0))
            if before <= 0:
                continue
            amount = max(1, int((context or {}).get("consume_count", 1)))
            after = max(0, before - amount)
            item["count"] = after
            rec = {"event": "buff_debuff_consumed", "lifecycle_event": event,
                   "target_id": str(item.get("target_id")), "name": str(item.get("name")),
                   "kind": str(item.get("kind")), "before": before, "consumed": before-after,
                   "after": after, "rule_id": str(item.get("rule_id", "")),
                   "source_id": str(item.get("source_id", ""))}
            consumed.append(rec)
            state.event_log.append(rec)
            if after <= 0:
                del store[key]
        return consumed

    @classmethod
    def resolve_rule_expiry(cls, state, *, event: str, target_id: Optional[str] = None,
                            context: Optional[Mapping[str, Any]] = None) -> list[Dict[str, Any]]:
        """Apply declarative RULE lifecycle expiry/transition hooks.

        RULE effects are not treated as count-based consumption.  A rule can
        explicitly request removal on an event; richer conversions remain an
        EffectRuntime responsibility.
        """
        event = str(event)
        store = cls._store(state)
        removed: list[Dict[str, Any]] = []
        for key, item in list(store.items()):
            if str(item.get("lifecycle", "")) != StatusLifecycle.RULE.value:
                continue
            if target_id is not None and str(item.get("target_id")) != str(target_id):
                continue
            rule = item.get("rule_expiry") or {}
            if str(rule.get("event", "")) != event:
                continue
            if not cls._condition_met(state, item, context):
                continue
            rec = {"event": "buff_debuff_rule_expired", "lifecycle_event": event,
                   "target_id": str(item.get("target_id")), "name": str(item.get("name")),
                   "kind": str(item.get("kind")), "rule_id": str(item.get("rule_id", "")),
                   "source_id": str(item.get("source_id", ""))}
            removed.append(rec)
            state.event_log.append(rec)
            del store[key]
        return removed

    @classmethod
    def snapshot(cls, state, *, target_id: Optional[str] = None) -> Dict[str, Any]:
        items = cls._store(state).values()
        return {f"{x['kind']}:{x['name']}": deepcopy(x) for x in items
                if target_id is None or str(x.get("target_id")) == str(target_id)}

    @classmethod
    def end_turn(cls, state) -> list[Dict[str, Any]]:
        store = cls._store(state); expired=[]
        for key, item in list(store.items()):
            d=item.get("duration")
            if d is None: continue
            d=int(d)-1
            if d <= 0:
                expired.append(deepcopy(item)); del store[key]
            else: item["duration"] = d
        return expired
