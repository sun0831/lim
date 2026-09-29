"""Concrete executor for the common EffectCommand layer.

This is the first mutation boundary for migrated Rule IR effects.  It handles
only effects whose semantics are generic enough to be shared safely:
state/flag, resource, status, and damage modifiers.  Action/legacy effects are
returned as deferred commands so existing combat runtimes remain authoritative.
"""
from __future__ import annotations
from typing import Any, Dict, Iterable, List

from effect_runtime_v1 import EffectCommand
from resource_runtime_v1 import ResourceRuntime
from damage_modifier_runtime_v1 import DamageModifierRuntime
from support_runtime_v1 import SupportActionResolver, command_from_effect
from target_runtime_v1 import TargetRuntime
from limbus_damage_engine_v29 import Status
from buff_debuff_runtime_v1 import BuffDebuffRuntime
from amplitude_runtime_v1 import AmplitudeRuntime


class EffectExecutor:
    def __init__(self, resource_runtime: ResourceRuntime | None = None):
        self.resources = resource_runtime or ResourceRuntime()
        self.targets = TargetRuntime()

    def execute(self, command: EffectCommand, ctx: Dict[str, Any]) -> Any:
        kind = command.kind
        p = dict(command.params or {})
        if kind in {"buff_apply", "debuff_apply", "buff_remove", "debuff_remove"}:
            return self._buff_debuff(command, ctx)
        if kind in {"amplitude_conversion", "amplitude_entanglement"}:
            return self._amplitude(command, ctx)
        if kind == "status_transform":
            return self._status_legacy(command, ctx)
        if kind == "resource_threshold_status_gain":
            state=ctx.get("state")
            tid=str(p.get("identity_id") or ctx.get("rule_owner_id") or ctx.get("identity_id") or "")
            fighter=(getattr(state,"fighters",{}) or {}).get(tid) if state is not None else None
            if fighter is None:
                return {"deferred":True,"reason":"resource_threshold_target_missing","command":command}
            resource=str(p.get("resource","")); threshold=int(p.get("threshold",0)); status=str(p.get("status",""))
            gain_amount=int(p.get("gain_amount",0)); current=int(getattr(fighter,"resources",{}).get(resource,0))
            before=current-gain_amount
            # The effect is ordered after the cumulative resource gain in the same
            # rule, so this observes the post-conversion value.  The source wording
            # says "became >= threshold", not merely "is >= threshold".
            if current < threshold or before >= threshold:
                return {"applied":False,"reason":"threshold_not_crossed","before":before,"current":current,"threshold":threshold,"command":command}
            st=fighter.statuses.get(status)
            if st is None:
                st=Status(potency=0,count=0); fighter.statuses[status]=st
            st.potency=max(1,int(getattr(st,"potency",0))); st.count=max(1,int(getattr(st,"count",0)))
            ev={"event":"resource_threshold_status_gain","identity_id":tid,"resource":resource,"current":current,"threshold":threshold,"status":status,"trigger_rule_id":command.rule_id}
            if hasattr(state,"event_log"): state.event_log.append(ev)
            return {"applied":True,"event":ev,"command":command}
        if kind == "sp_gain":
            state=ctx.get("state")
            tid=str(p.get("identity_id") or ctx.get("rule_owner_id") or ctx.get("identity_id") or "")
            fighter=(getattr(state,"fighters",{}) or {}).get(tid) if state is not None else None
            if fighter is None:
                return {"deferred":True,"reason":"sp_gain_target_missing","command":command}
            before=float(getattr(fighter,"sp",0)); amount=float(p.get("amount",0)); max_sp=float(getattr(fighter,"max_sp",45)); after=min(max_sp,before+amount); fighter.sp=after
            ev={"event":"sp_gain","identity_id":tid,"amount":after-before,"before":before,"after":after,"trigger_rule_id":command.rule_id}
            if hasattr(state,"event_log"): state.event_log.append(ev)
            if p.get("max_sp_followup") and after >= max_sp and before < max_sp:
                pending=state.runtime.setdefault("pending_next_turn_statuses",{})
                bucket=pending.setdefault(tid,{})
                st=bucket.setdefault("Slash Damage Up",{"potency":0,"count":0})
                st["potency"]=int(st.get("potency",0))+10
                if hasattr(state,"event_log"): state.event_log.append({"event":"next_turn_status_gain","identity_id":tid,"status":"Slash Damage Up","potency":10,"count":0,"trigger_rule_id":command.rule_id})
            return {"applied":True,"event":ev,"command":command}
        if kind in {"set_state", "state_change", "flag", "set_flag", "register_fatal_prevention", "register_damage_modifier_highest_poise"}:
            return self._state(command, ctx)
        if kind in {"resource_gain_lowest_allies", "resource_gain_lowest_hp_ally"}:
            return self._targeted_effect(command, ctx)
        if kind == "resource_spend_charge_barrier_lowest_hp_2":
            state=ctx.get("state"); fighters=getattr(state,"fighters",{}) if state is not None else {}
            spent=int((ctx.get("consumed_resources",{}) or {}).get("충전",0)); minimum=int(p.get("min_consumed",10)); count=int(p.get("count",2))
            if state is None or spent < minimum: return {"applied":False,"reason":"consumed_charge_below_threshold","command":command}
            ids=list((ctx.get("available_identity_ids") or fighters.keys())); cand=[]
            for fid in ids:
                f=fighters.get(str(fid))
                if f is None or float(getattr(f,"hp",0))<=0: continue
                mx=max(float(getattr(f,"max_hp",1)),1.0); hp=float(getattr(f,"hp",0)); cand.append((hp/mx,hp,ids.index(fid),str(fid),f))
            cand.sort(key=lambda x:(x[0],x[1],x[2])); amount=spent//2; rr=state.runtime.get("resource_runtime")
            events=[]
            for _,_,_,tid,f in cand[:count]:
                if rr is not None: rr.gain_charge_barrier(f,amount,state=state,reason=command.rule_id or kind)
                else: f.resources["충전 역장"]=int(f.resources.get("충전 역장",0))+amount
                events.append({"event":"charge_barrier_lowest_hp_distribution","identity_id":tid,"resource":"충전 역장","amount":amount,"source_identity_id":str(ctx.get("identity_id",ctx.get("owner_id",""))),"consumed_charge":spent,"trigger_rule_id":command.rule_id})
            for ev in events: state.event_log.append(ev)
            return {"applied":True,"targets":[e["identity_id"] for e in events],"amount":amount,"events":events,"command":command}
        if kind == "kill_charge_barrier_self_random_ally":
            state=ctx.get("state"); fighters=getattr(state,"fighters",{}) if state is not None else {}; spent=int((ctx.get("consumed_resources",{}) or {}).get("충전",0)); minimum=int(p.get("min_consumed",15))
            if state is None or spent < minimum: return {"applied":False,"reason":"consumed_charge_below_threshold","command":command}
            owner_id=str(p.get("identity_id") or ctx.get("identity_id") or ctx.get("owner_id") or ""); owner=fighters.get(owner_id)
            if owner is None: return {"applied":False,"reason":"owner_not_found","command":command}
            amount=int(p.get("amount",7)); rr=state.runtime.get("resource_runtime")
            if rr is not None: rr.gain_charge_barrier(owner,amount,state=state,reason=command.rule_id or kind)
            else: owner.resources["충전 역장"]=int(owner.resources.get("충전 역장",0))+amount
            import random
            ids=list(ctx.get("available_identity_ids") or fighters.keys()); allies=[str(fid) for fid in ids if str(fid)!=owner_id and (f:=fighters.get(str(fid))) is not None and float(getattr(f,"hp",0))>0]
            chosen=None
            if allies:
                rng=ctx.get("target_rng") or random.Random(ctx.get("random_seed",0)); chosen=rng.choice(allies); f=fighters[chosen]
                if rr is not None: rr.gain_charge_barrier(f,amount,state=state,reason=command.rule_id or kind)
                else: f.resources["충전 역장"]=int(f.resources.get("충전 역장",0))+amount
            ev={"event":"kill_charge_barrier_gain","identity_id":owner_id,"resource":"충전 역장","amount":amount,"source_identity_id":owner_id,"consumed_charge":spent,"random_ally_id":chosen,"trigger_rule_id":command.rule_id}
            state.event_log.append(ev)
            return {"applied":True,"target":chosen,"owner":owner_id,"amount":amount,"event":ev,"command":command}
        if kind in {"next_turn_resource_gain", "next_turn_charge_barrier_from_charge"}:
            return self._resource(command, ctx)
        if kind.startswith("resource_"):
            return self._resource(command, ctx)
        if kind in {"status_gain", "status_lose", "status_set", "status_convert",
                    "status_gain_affiliation", "status_gain_affiliation_ordered",
                    "enemy_status_count_gain", "support_poise_gain", "support_poise_count_bonus",
                    "hongmaehwa_crit", "poise_gain"}:
            return self._status(command, ctx)
        if kind == "sinking_deluge":
            state = ctx.get("state")
            target = ctx.get("target")
            if state is None:
                return {"deferred": True, "reason": "missing_state_context", "command": command}
            from keyword_runtime_v1 import KeywordRuntime
            return KeywordRuntime.sinking_deluge(state, target=target)
        if kind in {"queue_action", "assist_action", "extra_action", "trigger_action"}:
            return self._queue_action(self._normalize_generated_action(command), ctx)
        if kind == "support_action":
            return self._support_action(command, ctx)
        if kind in {"resource_gain_lowest_allies", "poise_gain_lowest_ally", "poise_gain_lowest_affiliation", "poise_gain_self_bonus", "heal_lowest_ally"}:
            return self._targeted_effect(command, ctx)
        if kind in {"damage_percent", "damage_flat", "critical_damage_percent",
                    "skill_power", "coin_power", "vulnerability", "extra_damage_scale",
                    "status_potency_damage"}:
            return self._modifier(command, ctx)
        # Support/assist/extra actions and legacy effects deliberately remain
        # deferred; their specialized runtimes own action-queue semantics.
        return {"deferred": True, "command": command}


    @staticmethod
    def _normalize_generated_action(command: EffectCommand) -> EffectCommand:
        """Normalize historical generated-action effect names into one queue command.

        ``assist_action``, ``extra_action`` and ``trigger_action`` were legacy
        spellings for the same generated-action boundary.  Their execution
        semantics are now owned by ActionQueue; the aliases are retained only
        as declarative input compatibility.
        """
        if command.kind == "queue_action":
            return command
        params = dict(command.params or {})
        params.setdefault("trigger_kind", command.kind)
        return EffectCommand("queue_action", params, command.rule_id, "action")

    def _queue_action(self, command: EffectCommand, ctx: Dict[str, Any]) -> Any:
        """Materialize a generic queue_action effect into the shared ActionQueue.

        The executor owns only queue materialization; skill selection and damage
        remain solver concerns.  If the current caller is outside a live combat
        queue, return a deferred result rather than pretending the action fired.
        """
        queue = ctx.get("action_queue")
        source = ctx.get("source_action")
        if queue is None or source is None:
            return {"deferred": True, "reason": "missing_action_queue_context", "command": command}
        p = dict(command.params or {})
        identity_id = p.get("identity_id") or p.get("target_identity_id")
        skill_id = p.get("skill_id")
        skill_name = p.get("skill_name")
        if not identity_id:
            identity_id = ctx.get("rule_owner_id") or ctx.get("identity_id")
        if not skill_id and skill_name:
            identity_map = ctx.get("identity_map") or {}
            ident = identity_map.get(str(identity_id))
            if ident is None:
                # Catalog effects historically use display names for generated
                # actions. Resolve those names without changing the canonical
                # identity_id representation used by ActionQueue.
                for candidate in identity_map.values():
                    names = (getattr(candidate, "name", ""), getattr(candidate, "full_name", ""))
                    if any(str(identity_id) and str(identity_id) in str(name) for name in names):
                        ident = candidate
                        identity_id = getattr(candidate, "id", identity_id)
                        break
            if ident is not None:
                for skill in (getattr(ident, "skills", {}) or {}).values():
                    if str(skill_name) in str(getattr(skill, "name", "")):
                        skill_id = getattr(skill, "id", None)
                        break
        if not identity_id or not skill_id:
            return {"deferred": True, "reason": "action_skill_unresolved", "command": command}
        generated = queue.triggered_from(
            source, str(identity_id), str(skill_id),
            str(p.get("reason") or command.rule_id or "rule_queue_action"),
            source_event=str(p.get("source_event") or p.get("trigger_kind") or ctx.get("event") or "trigger"),
            faces=p.get("faces"),
            suppress_kill_reuse=bool(p.get("suppress_kill_reuse", False)),
            target_policy=p.get("target_policy"),
            target_index=p.get("target_index"),
            target_ids=p.get("target_ids"),
            target_override_ids=p.get("target_override_ids"),
            coin_target_ids=p.get("coin_target_ids"),
            trigger_kind=p.get("trigger_kind"),
        )
        queued = queue.enqueue_triggered(generated)
        return {"queued": bool(queued), "action": generated.to_dict(), "command": command}

    def _support_action(self, command: EffectCommand, ctx: Dict[str, Any]) -> Any:
        """Resolve a support command through the shared SupportActionResolver and queue it.

        ``requested_next`` intentionally remains a solver-level skill placeholder:
        the selected ally is resolved here, while the solver resolves that ally's
        next requested action exactly as the legacy support bridge did.
        """
        queue = ctx.get("action_queue")
        source = ctx.get("source_action")
        if queue is None or source is None:
            return {"deferred": True, "reason": "missing_action_queue_context", "command": command}
        p = dict(command.params or {})
        source_id = str(p.get("source_identity_id") or ctx.get("identity_id") or ctx.get("rule_owner_id") or "")
        identity_map = ctx.get("identity_map") or {}
        identities = list(identity_map.values())
        available = ctx.get("available_identity_ids") or list(identity_map.keys())
        resolver = SupportActionResolver(identities, available)
        support_command = command_from_effect(p, source_id)
        target = resolver.resolve_identity(support_command, source_id)
        if target is None or str(getattr(target, "id", "")) not in [str(x) for x in available]:
            return {"deferred": True, "reason": "support_identity_unresolved", "command": command}

        if support_command.skill_policy == "requested_next" or support_command.skill_name == "__support_default__":
            skill_id = "__support_default__"
        else:
            skill = resolver.resolve_skill(target, support_command)
            if skill is None:
                return {"deferred": True, "reason": "support_skill_unresolved", "command": command}
            skill_id = str(getattr(skill, "id", ""))
            if not skill_id:
                return {"deferred": True, "reason": "support_skill_missing_id", "command": command}

        generated = queue.triggered_from(
            source, str(target.id), skill_id,
            str(p.get("reason") or command.rule_id or "rule_support_action"),
            source_event=str(p.get("source_event") or support_command.trigger_kind or ctx.get("event") or "support"),
            faces=p.get("faces"),
            suppress_kill_reuse=bool(p.get("suppress_kill_reuse", False)),
            target_policy=support_command.target_policy,
            target_index=p.get("target_index"),
            target_ids=p.get("target_ids"),
            target_override_ids=p.get("target_override_ids"),
            coin_target_ids=p.get("coin_target_ids"),
            trigger_kind=support_command.trigger_kind,
        )
        queued = queue.enqueue_triggered(generated)
        return {"queued": bool(queued), "action": generated.to_dict(), "command": command}


    def _targeted_effect(self, command: EffectCommand, ctx: Dict[str, Any]) -> Any:
        """Execute deterministic ally/affiliation target effects.

        Selection is delegated to the shared TargetRuntime boundary; mutation
        remains here so EffectExecutor is the single generic-effect mutation
        point.  These handlers preserve the legacy tie-break rules: formation
        order after the primary lowest-value metric.
        """
        kind = command.kind
        p = dict(command.params or {})
        state = ctx.get("state")
        if state is None:
            return {"deferred": True, "reason": "missing_state_context", "command": command}
        fighters = getattr(state, "fighters", {}) or {}
        available = [str(x) for x in (ctx.get("available_identity_ids") or list(fighters.keys()))]
        owner_id = str(p.get("owner_id") or ctx.get("rule_owner_id") or ctx.get("identity_id") or "")
        def live_ids(exclude_owner=False):
            return [iid for iid in available if (not exclude_owner or iid != owner_id) and iid in fighters and float(getattr(fighters[iid], "hp", 0)) > 0]
        def formation(iid):
            try: return available.index(str(iid))
            except ValueError: return 10**9
        def poise(iid):
            st=getattr(fighters[iid], "poise", None)
            metric=str(p.get("metric", "potency"))
            return int(getattr(st, "count" if metric == "count" else "potency", 0)) if st is not None else 0

        if kind == "poise_gain_self_bonus":
            affiliation = str(p.get("affiliation", ""))
            resolver = ctx.get("affiliation_resolver")
            if resolver is None:
                return {"deferred": True, "reason": "missing_affiliation_resolver", "command": command}
            total = resolver.count(affiliation, include_dead=True, state=state)
            alive = resolver.count(affiliation, include_dead=False, state=state)
            dead_count = max(0, total - alive)
            if dead_count < int(p.get("member_count_threshold", 0)):
                return {"applied": False, "reason": "dead_threshold_not_met", "command": command}
            amount = int(p.get("amount_high", p.get("amount", 1))) if dead_count >= int(p.get("dead_threshold", 10**9)) else int(p.get("amount", 1))
            f = fighters.get(owner_id)
            if f is None: return {"deferred": True, "reason": "owner_not_found", "command": command}
            before = (int(getattr(f.poise, "potency", 0)), int(getattr(f.poise, "count", 0)))
            f.poise.potency += amount
            if p.get("use_count", True): f.poise.count += amount
            event = {"event":"poise_gain","identity_id":owner_id,"amount":amount,"count_amount":amount if p.get("use_count",True) else 0,"before":before,"after":(int(f.poise.potency),int(f.poise.count)),"trigger_rule_id":command.rule_id}
            state.event_log.append(event)
            return {"applied": True, "identity_id": owner_id, "amount": amount, "event": event, "command": command}

        if kind == "poise_gain_lowest_affiliation":
            affiliation = str(p.get("affiliation", "")); resolver = ctx.get("affiliation_resolver")
            if resolver is None:
                return {"deferred": True, "reason": "missing_affiliation_resolver", "command": command}
            amount = int(p.get("amount", 1))
            if resolver.count(affiliation, include_dead=False, state=state) >= int(p.get("member_count_threshold", 10**9)):
                amount = int(p.get("amount_high", amount))
            members = resolver.select_lowest_n(affiliation, int(p.get("count", 1)), lambda ident, iid: poise(iid), include_dead=False, state=state, exclude_ids=[owner_id] if p.get("exclude_owner") else [])
            events=[]
            for member in members:
                f=fighters.get(str(member.identity_id))
                if f is None: continue
                before=(int(f.poise.potency),int(f.poise.count)); f.poise.potency += amount
                if p.get("use_count", True): f.poise.count += amount
                event={"event":"poise_gain","identity_id":str(member.identity_id),"amount":amount,"count_amount":amount if p.get("use_count",True) else 0,"before":before,"after":(int(f.poise.potency),int(f.poise.count)),"trigger_rule_id":command.rule_id}
                state.event_log.append(event); events.append(event)
            return {"applied": True, "targets":[e["identity_id"] for e in events], "events":events, "command":command}

        ids = live_ids(exclude_owner=(kind == "poise_gain_lowest_ally"))
        if kind == "poise_gain_lowest_ally":
            if not ids: return {"applied": False, "reason":"no_eligible_ally", "command":command}
            tid=min(ids, key=lambda iid:(poise(iid),formation(iid))); f=fighters[tid]
            amount=int(p.get("amount",1)); before=(int(f.poise.potency),int(f.poise.count)); f.poise.potency += amount
            if p.get("use_count",True): f.poise.count += amount
            event={"event":"poise_gain","identity_id":tid,"amount":amount,"count_amount":amount if p.get("use_count",True) else 0,"before":before,"after":(int(f.poise.potency),int(f.poise.count)),"trigger_rule_id":command.rule_id}
            state.event_log.append(event); return {"applied":True,"target":tid,"event":event,"command":command}

        if kind == "heal_lowest_ally":
            ids=live_ids(False)
            if not ids: return {"applied":False,"reason":"no_eligible_ally","command":command}
            def hp_key(iid):
                # Source wording here is "체력이 가장 낮은 아군": current HP,
                # not current-HP percentage.  Percentage selectors are separate.
                f=fighters[iid]; hp=float(getattr(f,"hp",0)); return (hp,formation(iid))
            tid=min(ids,key=hp_key); f=fighters[tid]; before=float(getattr(f,"hp",0)); amount=int(p.get("amount",0)); mx=float(getattr(f,"max_hp",before)); after=min(mx,before+amount); f.hp=after; actual=after-before
            event={"event":"kill_heal","identity_id":tid,"amount":actual,"requested_amount":amount,"before":before,"after":after,"trigger_rule_id":command.rule_id}; state.event_log.append(event)
            return {"applied":True,"target":tid,"event":event,"command":command}

        if kind == "resource_gain_lowest_hp_ally":
            resource=str(p.get("resource","충전 역장")); amount=int(p.get("amount",0)); exclude_owner=bool(p.get("exclude_owner",True))
            ids=live_ids(exclude_owner=exclude_owner)
            if not ids: return {"applied":False,"reason":"no_eligible_ally","command":command}
            def hp_key(iid):
                f=fighters[iid]; mx=max(float(getattr(f,"max_hp",1)),1.0); hp=float(getattr(f,"hp",0)); return (hp/mx,hp,formation(iid))
            tid=min(ids,key=hp_key); f=fighters[tid]
            before=self.resources.get(f,resource)
            if resource=='충전 역장': after=self.resources.gain_charge_barrier(f,amount,state=state,reason=command.rule_id or 'rule')
            else: after=self.resources.gain(f,resource,amount,state=state,reason=command.rule_id or 'rule')
            ev={"event":"resource_gain_lowest_hp_ally","identity_id":tid,"resource":resource,"amount":amount,"before":before,"after":after,"trigger_rule_id":command.rule_id}; state.event_log.append(ev)
            return {"applied":True,"target":tid,"amount":amount,"event":ev,"command":command}

        if kind == "resource_gain_lowest_allies":
            resource=str(p.get("resource","충전")); count=int(p.get("count",1)); base=int(p.get("amount_base",0)); expr_resource=str(p.get("amount_resource",resource)); cap=p.get("cap")
            owner=fighters.get(owner_id)
            if owner is None: return {"deferred":True,"reason":"owner_not_found","command":command}
            def resource_value(f): return self.resources.get(f, resource)
            def expr_value(f): return self.resources.get(f, expr_resource)
            current_expr=expr_value(owner); amount=base+current_expr;
            if cap is not None: amount=min(amount,int(cap))
            ids=live_ids(False)
            # Legacy semantics: owner is always selected, then `count` lowest allies.
            selected=[owner_id] if owner_id in ids else []
            rest=[iid for iid in ids if iid != owner_id]
            if resource == "충전":
                # Preserve legacy preference for charge-capable allies when present.
                identity_map=ctx.get("identity_map") or {}
                def capable(iid):
                    ident=identity_map.get(iid);
                    if ident is None: return 0
                    blob='\n'.join(str(x) for sk in (getattr(ident,'skills',{}) or {}).values() for x in ((getattr(sk,'effects',[]) or []) + (getattr(sk,'_source_effects',[]) or [])))
                    import re
                    return int(bool(re.search(r'충전(?: 횟수)?\s*(?:\d+\s*)?(?:소모|감소)|충전(?: 횟수)?\s*(?:\d+\s*)?(?:증가|얻음|획득)',blob)))
                rest.sort(key=lambda iid:(-capable(iid),resource_value(fighters[iid]),formation(iid)))
            else: rest.sort(key=lambda iid:(resource_value(fighters[iid]),formation(iid)))
            selected.extend(rest[:count]); events=[]
            for tid in selected:
                f=fighters[tid]; before=self.resources.get(f,resource); after=self.resources.gain_charge_barrier(f,amount,state=state,reason=command.rule_id or "rule") if resource=="충전 역장" else self.resources.change(f,resource,amount,state=state,reason="resource_distribution");
                event={"event":"kill_resource_distribution","identity_id":tid,"resource":resource,"amount":amount,"before":before,"after":after,"trigger_rule_id":command.rule_id,"source_identity_id":owner_id}; state.event_log.append(event); events.append(event)
            return {"applied":True,"targets":selected,"amount":amount,"events":events,"command":command}

        return {"deferred":True,"reason":"unsupported_targeted_effect","command":command}

    def _amplitude(self, command: EffectCommand, ctx: Dict[str, Any]) -> Any:
        state = ctx.get("state")
        if state is None:
            return {"deferred": True, "reason": "missing_state_context", "command": command}
        p = dict(command.params or {})
        raw = p.get("value", p)
        if not isinstance(raw, dict):
            raw = {}
        amplitude = raw.get("amplitude") or raw.get("value", {}).get("amplitude") if isinstance(raw.get("value"), dict) else raw.get("amplitude")
        mode = "conversion" if command.kind == "amplitude_conversion" else "entanglement"
        if not amplitude:
            return {"applied": False, "reason": "missing_amplitude", "command": command}
        target = ctx.get("target_unit") or ctx.get("target")
        if isinstance(target, dict):
            tid = target.get("identity_id") or target.get("id")
            if tid is not None:
                target = (getattr(state, "fighters", {}) or {}).get(str(tid))
                if target is None and str(tid).lower() in {"enemy", "target", "event_target"}:
                    target = getattr(state, "enemy", None)
            elif str(ctx.get("target_side", "")).lower() == "enemy":
                target = getattr(state, "enemy", None)
        if target is None and str(ctx.get("target_side", "")).lower() == "enemy":
            target = getattr(state, "enemy", None)
        if target is None:
            target = self._resolve_actor(ctx, {})
        if target is None:
            return {"deferred": True, "reason": "target_not_found", "command": command}
        owner_id = str(ctx.get("rule_owner_id") or ctx.get("identity_id") or "")
        rt = AmplitudeRuntime()
        before = rt.get_states(target)
        if amplitude == "current_tremor" and mode == "entanglement":
            rt.entangle_current_tremor(state, target, owner_id=owner_id)
        else:
            rt.set_state(state, target, str(amplitude), mode, source="Tremor", owner_id=owner_id)
        after = rt.get_states(target)
        event = {"event": command.kind, "target": "enemy" if target is getattr(state, "enemy", None) else str(getattr(target, "id", "")), "amplitude": str(amplitude), "mode": mode, "before": before, "after": after, "trigger_rule_id": command.rule_id}
        log = getattr(state, "event_log", None)
        if isinstance(log, list):
            log.append(event)
        return {"applied": True, "target": target, "amplitude": str(amplitude), "mode": mode, "event": event, "command": command}

    def execute_all(self, commands: Iterable[EffectCommand], ctx: Dict[str, Any]) -> List[Any]:
        return [self.execute(c, ctx) for c in commands]

    @staticmethod
    def _actor(ctx: Dict[str, Any]):
        return ctx.get("actor") or ctx.get("identity") or ctx.get("fighter")

    @classmethod
    def _resolve_actor(cls, ctx: Dict[str, Any], params: Dict[str, Any]):
        """Resolve an explicit effect target before falling back to event actor."""
        state = ctx.get("state")
        target_id = params.get("identity_id") or params.get("target_identity_id") or ctx.get("rule_owner_id")
        if target_id is not None and state is not None:
            fighters = getattr(state, "fighters", {}) or {}
            target = fighters.get(str(target_id))
            if target is not None:
                return target
        return cls._actor(ctx)

    def _register_damage_modifier(self, state, target_id, command, p):
        DamageModifierRuntime.register(state, target_identity_id=str(target_id),
            source_identity_id=str(p.get("source_identity_id") or command.rule_id),
            kind=str(p.get("kind", "critical_damage_percent")),
            amount=float(p.get("amount", 0.0)), attack_type=p.get("attack_type"),
            critical_only=bool(p.get("critical_only", False)), skill_name=p.get("skill_name"),
            reason=str(p.get("reason", "")), rule_id=command.rule_id)
        state.event_log.append({"event":"damage_modifier_registered", "target_identity_id":str(target_id),
            "source_identity_id":str(p.get("source_identity_id") or command.rule_id),
            "kind":str(p.get("kind", "critical_damage_percent")), "amount":float(p.get("amount",0.0)),
            "reason":str(p.get("reason", "")), "rule_id":command.rule_id})

    def _buff_debuff(self, command: EffectCommand, ctx: Dict[str, Any]) -> Any:
        state = ctx.get("state")
        if state is None:
            return {"deferred": True, "reason": "missing_state_context", "command": command}
        p = dict(command.params or {})
        target_id = str(p.get("target_id") or ctx.get("target_id") or ctx.get("identity_id") or "")
        if not target_id:
            return {"deferred": True, "reason": "missing_target_id", "command": command}
        if command.kind in {"buff_remove", "debuff_remove"}:
            kind = "buff" if command.kind == "buff_remove" else "debuff"
            removed = BuffDebuffRuntime.remove(state, target_id=target_id, name=str(p.get("name", "")), kind=kind)
            return {"applied": removed > 0, "removed": removed, "command": command}
        kind = "buff" if command.kind == "buff_apply" else "debuff"
        item = BuffDebuffRuntime.apply(state, target_id=target_id, name=str(p.get("name", "")), kind=kind,
            potency=int(p.get("potency", 0)), count=int(p.get("count", 0)), duration=p.get("duration"),
            modifiers=p.get("modifiers") or {}, source_id=str(p.get("source_id") or ctx.get("identity_id") or ""),
            rule_id=command.rule_id, stack_mode=str(p.get("stack_mode", "add")),
            timing=str(p.get("timing", "always")), conditions=p.get("conditions"),
            modifier_policy=p.get("modifier_policy"), priority=int(p.get("priority", 0)),
            stack_group=p.get("stack_group"), consume_on=p.get("consume_on"),
            lifecycle=p.get("lifecycle"), rule_expiry=p.get("rule_expiry"),
            value_semantics=p.get("value_semantics"))
        return {"applied": True, "item": item, "command": command}

    def _state(self, command: EffectCommand, ctx: Dict[str, Any]) -> Any:
        p = command.params
        state = ctx.get("state")
        if state is None:
            return {"deferred": True, "reason": "missing_state_context", "command": command}
        if command.kind == "register_fatal_prevention":
            target_id=str(p.get("identity_id") or p.get("owner_id") or ctx.get("rule_owner_id") or ctx.get("identity_id") or "")
            if target_id not in getattr(state,"fighters",{}):
                return {"deferred": True, "reason":"owner_not_found", "command":command}
            uses=int(p.get("uses",1)); state.runtime.setdefault("fatal_prevention",{})[target_id]=uses
            state.event_log.append({"event":"fatal_prevention_registered","identity_id":target_id,"uses":uses,"reason":p.get("reason",""),"trigger_rule_id":command.rule_id})
            return {"applied":True,"identity_id":target_id,"uses":uses,"command":command}
        if command.kind == "register_damage_modifier_highest_poise":
            fighters=getattr(state,"fighters",{}) or {}; resolver=ctx.get("affiliation_resolver"); affiliation=str(p.get("affiliation",""))
            if affiliation and resolver is not None:
                members=list(resolver.members(affiliation,include_dead=False,state=state))
            else:
                available=[str(x) for x in (ctx.get("available_identity_ids") or fighters.keys())]
                members=[type("M",(),{"identity_id":iid,"formation_index":i}) for i,iid in enumerate(available) if iid in fighters and float(getattr(fighters[iid],"hp",0))>0]
            metric=str(p.get("metric", "potency"))
            field="count" if metric == "count" else "potency"
            members.sort(key=lambda m:(-int(getattr(getattr(fighters.get(str(m.identity_id)),"poise",None),field,0)),int(getattr(m,"formation_index",10**9))))
            if not members:
                return {"applied":False,"reason":"no_eligible_target","command":command}
            target=str(members[0].identity_id)
            self._register_damage_modifier(state,target,command,p)
            return {"applied":True,"target":target,"command":command}
        key = str(p.get("key", p.get("field", p.get("flag", ""))))
        if not key:
            return {"applied": False, "reason": "missing_state_key"}
        value = p.get("value", p.get("amount"))
        target = self._actor(ctx)
        container = state.runtime if hasattr(state, "runtime") else (state if isinstance(state, dict) else None)
        if command.kind in {"flag", "set_flag"}:
            flags = (container.setdefault("condition_flags", {}) if container is not None else ctx.setdefault("condition_flags", {}))
            flags[key] = bool(value)
            return flags[key]
        if isinstance(target, dict): target[key] = value; return value
        if target is not None: setattr(target, key, value); return value
        if container is not None: container[key] = value; return value
        return {"applied": False, "reason": "no_state_target"}

    def _resource(self, command: EffectCommand, ctx: Dict[str, Any]) -> Any:
        p = command.params
        actor = self._resolve_actor(ctx, p)
        if actor is None or not hasattr(actor, "resources"):
            return {"applied": False, "reason": "actor_has_no_resources"}
        p = command.params
        name = str(p.get("resource", p.get("name", "")))
        amount = int(p.get("amount", p.get("value", 0)))
        state = ctx.get("state")
        if command.kind == "resource_gain":
            if name == '충전 역장':
                return self.resources.gain_charge_barrier(actor, amount, state=state, reason=command.rule_id or 'rule')
            return self.resources.gain(actor, name, amount, state=state, reason=command.rule_id or "rule")
        if command.kind in {'resource_gain_from_charge_potency','resource_gain_from_charge_potency_plus'}:
            potency=int(getattr(actor,'charge_potency',0)); base=int(p.get('base',0)); cap=int(p.get('cap',99)); computed=min(cap,potency+base)
            if name == '충전 역장':
                return self.resources.gain_charge_barrier(actor, computed, state=state, reason=command.rule_id or 'rule')
            return self.resources.gain(actor, name, computed, state=state, reason=command.rule_id or 'rule')
        if command.kind == 'next_turn_resource_gain':
            if state is None: return {'deferred':True,'reason':'missing_state_context','command':command}
            target_id=str(p.get('identity_id') or getattr(actor,'id','') or ctx.get('identity_id') or ctx.get('rule_owner_id') or '')
            nxt=state.runtime.setdefault('next_turn_state',{}).setdefault('fighters',{}).setdefault(target_id,{})
            before=int(nxt.get(name,0)); nxt[name]=before+amount
            state.event_log.append({'event':'next_turn_resource_gain','resource':name,'identity_id':target_id,'amount':amount,'before':before,'after':nxt[name],'trigger_rule_id':command.rule_id})
            return nxt[name]
        if command.kind == 'next_turn_charge_barrier_from_charge':
            if state is None: return {'deferred':True,'reason':'missing_state_context','command':command}
            target_id=str(p.get('identity_id') or getattr(actor,'id','') or ctx.get('identity_id') or ctx.get('rule_owner_id') or '')
            source=str(p.get('source_resource','충전')); per=max(1,int(p.get('per',5))); cap=int(p.get('cap',4)); per_amount=int(p.get('amount',1))
            current=int(getattr(actor,'charge',0)) if source=='충전' else int(actor.resources.get(source,0)); computed=min(cap,current//per)*per_amount
            nxt=state.runtime.setdefault('next_turn_state',{}).setdefault('fighters',{}).setdefault(target_id,{})
            before=int(nxt.get(name,0)); nxt[name]=before+computed
            if computed:
                state.event_log.append({'event':'next_turn_resource_gain','resource':name,'identity_id':target_id,'amount':computed,'before':before,'after':nxt[name],'source_resource':source,'trigger_rule_id':command.rule_id})
            return nxt[name]
        if command.kind == "resource_gain_affiliation_count":
            affiliation = str(p.get("affiliation", ""))
            resolver = ctx.get("affiliation_resolver")
            if resolver is None or state is None:
                return {"applied": False, "reason": "missing_affiliation_resolver"}
            members = resolver.members(affiliation, include_dead=False, state=state)
            multiplier = int(p.get("multiplier", 1))
            cap_raw = p.get("cap", None)
            computed = len(members) * multiplier
            if cap_raw is not None:
                computed = min(computed, int(cap_raw))
            return self.resources.gain(actor, name, computed, state=state, reason=command.rule_id or "rule")
        if command.kind == "resource_consume":
            before = self.resources.get(actor, name)
            after = self.resources.consume(actor, name, amount, state=state, reason=command.rule_id or "rule")
            if p.get("overheat_at_zero") and before > 0 and after == 0:
                # Preserve the Foresight Eye legacy transition as part of the
                # generic resource-consume contract.
                flag = str(p.get("overheat_flag", "예지안 과열"))
                self.resources.gain(actor, flag, 1, state=state, reason=command.rule_id or "overheat")
            return after
        if command.kind == "resource_set":
            return self.resources.set(actor, name, amount, state=state, reason=command.rule_id or "rule")
        if command.kind == "resource_convert":
            source = str(p.get("source", name)); target = str(p.get("target", p.get("to", "")))
            ratio = int(p.get("ratio", 1)); available = self.resources.get(actor, source)
            consumed = min(available, amount)
            self.resources.consume(actor, source, consumed, state=state, reason=command.rule_id or "convert")
            gained = consumed * ratio
            if target:
                self.resources.gain(actor, target, gained, state=state, reason=command.rule_id or "convert")
            return {"source": source, "consumed": consumed, "target": target, "gained": gained}
        return {"applied": False, "reason": "unsupported_resource_effect"}

    def _status_legacy(self, command: EffectCommand, ctx: Dict[str, Any]) -> Any:
        p = command.params
        state = ctx.get("state")
        if command.kind == "support_poise_gain":
            if state is None: return {"deferred":True,"reason":"missing_state_context","command":command}
            fighters=getattr(state,"fighters",{}) or {}; available=[str(x) for x in (ctx.get("available_identity_ids") or fighters.keys())]; policy=str(p.get("target_policy","formation_first")); targets=[]
            if policy == "formation_first": targets=[available[0]] if available else []
            elif policy == "highest_sp":
                cand=[(float(getattr(fighters[i],"sp",0)),idx,i) for idx,i in enumerate(available) if i in fighters and float(getattr(fighters[i],"hp",0))>0]
                if cand: targets=[min(cand,key=lambda x:(-x[0],x[1]))[2]]
            events=[]
            for tid in targets:
                f=fighters.get(tid)
                if f is None: continue
                amount=int(p.get("amount",2)); before=(int(f.poise.potency),int(f.poise.count)); f.poise.potency+=amount
                if p.get("use_count",False): f.poise.count+=amount
                ev={"event":"support_poise_gain","identity_id":tid,"amount":amount,"count_amount":amount if p.get("use_count",False) else 0,"before":before,"after":(int(f.poise.potency),int(f.poise.count)),"trigger_rule_id":command.rule_id}; state.event_log.append(ev); events.append(ev)
            return {"applied":bool(events),"targets":targets,"events":events,"command":command}
        if command.kind == "support_poise_count_bonus":
            if state is None: return {"deferred":True,"reason":"missing_state_context","command":command}
            tid=str(ctx.get("identity_id") or ctx.get("actor_id") or ctx.get("rule_owner_id") or ""); f=getattr(state,"fighters",{}).get(tid)
            if f is None: return {"deferred":True,"reason":"support_actor_not_found","command":command}
            amount=int(p.get("amount",1)); before=int(f.poise.count); f.poise.count+=amount
            state.event_log.append({"event":"support_poise_count_bonus","identity_id":tid,"amount":amount,"before":before,"after":int(f.poise.count),"trigger_rule_id":command.rule_id})
            return {"applied":True,"target":tid,"amount":amount,"command":command}
        if command.kind == "status_transform":
            if state is None:
                return {"deferred": True, "reason": "missing_state_context", "command": command}
            tid=str(p.get("identity_id") or ctx.get("rule_owner_id") or ctx.get("identity_id") or "")
            fighter=(getattr(state,"fighters",{}) or {}).get(tid)
            if fighter is None:
                return {"deferred": True, "reason": "status_transform_target_missing", "command": command}
            gate=str(p.get("gate_status", "")); source=str(p.get("source_status", "")); reward=str(p.get("reward_status", ""))
            if gate and gate not in getattr(fighter,"statuses",{}):
                return {"applied":False,"reason":"gate_status_missing","command":command}
            src=getattr(fighter,"statuses",{}).get(source)
            if src is None:
                return {"applied":False,"reason":"source_status_missing","command":command}
            before=dict(getattr(src,"__dict__",{}))
            fighter.statuses.pop(source,None)
            if reward:
                dst=fighter.statuses.get(reward)
                if dst is None:
                    dst=Status(potency=0,count=0); fighter.statuses[reward]=dst
                dst.potency=max(1,int(getattr(dst,"potency",0))); dst.count=max(1,int(getattr(dst,"count",0)))
            ev={"event":"status_transform","identity_id":tid,"gate_status":gate,"source_status":source,"reward_status":reward,"source_before":before,"trigger_rule_id":command.rule_id}
            if hasattr(state,"event_log"): state.event_log.append(ev)
            return {"applied":True,"event":ev,"command":command}
        if command.kind == "status_gain_affiliation_ordered":
            resolver=ctx.get("affiliation_resolver")
            if state is None or resolver is None:
                return {"deferred":True,"reason":"missing_affiliation_resolver","command":command}
            fighters=getattr(state,"fighters",{}) or {}; owner_id=str(p.get("owner_id") or ctx.get("rule_owner_id") or "")
            members=resolver.members(str(p.get("affiliation","")), include_dead=False, state=state, exclude_ids=[owner_id] if p.get("exclude_owner") else [])
            order=str(p.get("order","formation"))
            if order == "slowest":
                members.sort(key=lambda m: (float(getattr(fighters.get(str(m.identity_id)), "speed", 0)), int(getattr(m, "formation_index", 10**9))))
            else:
                members.sort(key=lambda m: int(getattr(m, "formation_index", 10**9)))
            base_count=int(p.get("base_count",1)); max_count=int(p.get("max_count",base_count))
            member_count=resolver.count(str(p.get("affiliation","")), include_dead=False, state=state)
            count=min(max_count, base_count)
            if member_count >= int(p.get("boost_member_count",10**9)):
                count=min(max_count, int(p.get("boost_count",count)))
            planned_max=int(getattr(state, "runtime", {}).get("max_resonance_count", count) or count)
            count=min(count, max(0, planned_max))
            amount=int(p.get("amount",1))
            if member_count >= int(p.get("boost_member_count",10**9)):
                amount=int(p.get("boost_amount",amount))
            status=str(p.get("status","")); events=[]
            for member in members[:count]:
                fighter=fighters.get(str(member.identity_id))
                if fighter is None: continue
                st=fighter.statuses.get(status)
                if st is None: st=Status(); fighter.statuses[status]=st
                before=int(getattr(st,"count",0)); st.count += amount; st.potency += amount
                ev={"event":"affiliation_status_gain_ordered","status":status,"identity_id":str(member.identity_id),"amount":amount,"before":before,"after":int(st.count),"order":order,"trigger_rule_id":command.rule_id}
                state.event_log.append(ev); events.append(ev)
            return {"applied":bool(events),"events":events,"command":command}

        if command.kind == "status_gain_affiliation":
            resolver=ctx.get("affiliation_resolver")
            if state is None or resolver is None: return {"deferred":True,"reason":"missing_affiliation_resolver","command":command}
            fighters=getattr(state,"fighters",{}) or {}; owner_id=str(p.get("owner_id") or ctx.get("rule_owner_id") or ""); events=[]
            for member in resolver.members(str(p.get("affiliation","")),include_dead=bool(p.get("include_dead",False)),state=state,exclude_ids=[owner_id] if p.get("exclude_owner") else []):
                f=fighters.get(str(member.identity_id));
                if f is None: continue
                name=str(p.get("status","")); amount=int(p.get("amount",1)); st=f.statuses.get(name)
                if st is None:
                    st=Status(); f.statuses[name]=st
                st.count+=amount; st.potency+=amount
                if p.get("fatal_prevention_once"): st.data["fatal_prevention_once"]=True
                ev={"event":"affiliation_status_gain","status":name,"identity_id":str(member.identity_id),"amount":amount,"trigger_rule_id":command.rule_id}; state.event_log.append(ev); events.append(ev)
            return {"applied":True,"events":events,"command":command}
        target = ctx.get("effect_target") or ctx.get("target") or self._resolve_actor(ctx, p)
        if target is None:
            return {"applied": False, "reason": "no_status_target"}
        if isinstance(target, dict):
            statuses = target.setdefault("statuses", {})
        else:
            statuses = getattr(target, "statuses", None)
            if statuses is None:
                statuses = {}; setattr(target, "statuses", statuses)
        p = command.params
        name = str(p.get("status", p.get("name", "")))
        if name == "Tremor" and command.kind in {"status_gain", "status_set"}:
            from keyword_runtime_v1 import KeywordRuntime
            target = ctx.get("effect_target") or ctx.get("target") or self._resolve_actor(ctx, p)
            if target is None:
                return {"applied": False, "reason": "no_status_target"}
            potency = int(p.get("potency", p.get("amount", 0)) or 0)
            count = int(p.get("count", 0) or 0)
            if command.kind == "status_set":
                st = getattr(target, "statuses", {}).get("Tremor")
                if st is not None:
                    st.potency = 0; st.count = 0
            st = KeywordRuntime.add_tremor(target, potency, count, state=state, event=ctx.get("event"), source_id=ctx.get("identity_id") or ctx.get("rule_owner_id"))
            return {"applied": True, "status": "Tremor", "potency": int(st.potency), "count": int(st.count), "command": command}
        if not name:
            return {"applied": False, "reason": "missing_status_name"}
        amount = int(p.get("amount", p.get("count", p.get("value", 0))))
        before = statuses.get(name, 0)
        if isinstance(before, dict):
            if command.kind == "status_lose":
                before["count"] = max(0, int(before.get("count", 0)) - amount)
            else:
                before["count"] = int(before.get("count", 0)) + amount
            return before
        if command.kind == "status_lose":
            after = max(0, int(before) - amount)
        elif command.kind == "status_set":
            after = amount
        else:
            after = int(before) + amount
        statuses[name] = after
        return after

    def _status(self, command: EffectCommand, ctx: Dict[str, Any]) -> Any:
        kind = command.kind
        p = dict(command.params or {})
        state = ctx.get("state")
        # Ordinary status effects remain valid in lightweight RuleRuntime contexts
        # that do not carry a TurnState. Only stateful specialized effects need it.
        if kind not in {"enemy_status_count_gain", "hongmaehwa_crit", "poise_gain"}:
            return self._status_generic(command, ctx)
        if state is None:
            return {"deferred": True, "reason": "missing_state_context", "command": command}
        # These handlers preserve the semantics previously owned by the
        # identity-specific gimmick bridge, but mutate through the common
        # EffectExecutor boundary so Rule IR execution is authoritative.
        if kind == "poise_gain":
            actor = self._resolve_actor(ctx, p)
            if actor is None or not hasattr(actor, "poise"):
                return {"deferred": True, "reason": "poise_actor_not_found", "command": command}
            amount = int(p.get("amount", 0))
            before = (int(getattr(actor.poise, "potency", 0)), int(getattr(actor.poise, "count", 0)))
            actor.poise.potency += amount
            # Legacy poise_gain changes potency only unless explicitly requested.
            if p.get("use_count", False):
                actor.poise.count += amount
            event = {"event": "poise_gain", "identity_id": str(getattr(actor, "id", ctx.get("identity_id", ""))),
                     "amount": amount, "count_amount": amount if p.get("use_count", False) else 0,
                     "before": before, "after": (int(actor.poise.potency), int(actor.poise.count)),
                     "trigger_rule_id": command.rule_id}
            if hasattr(state, "event_log"):
                state.event_log.append(event)
            return event
        if kind == "enemy_status_count_gain":
            enemy = getattr(state, "enemy", None)
            if enemy is None:
                return {"deferred": True, "reason": "missing_enemy_state", "command": command}
            attacker_id = str(ctx.get("attacker_id", ""))
            enemy_id = str(getattr(enemy, "id", "enemy_1"))
            if attacker_id and attacker_id not in {enemy_id, "enemy_1"}:
                return {"deferred": True, "reason": "enemy_attacker_mismatch", "command": command}
            status = str(p.get("status", "복수 대상"))
            amount = int(p.get("amount", 0))
            st = enemy.statuses.get(status)
            if st is None:
                st = Status(potency=0, count=0)
                enemy.statuses[status] = st
            before = int(getattr(st, "count", 0))
            st.count = max(0, before + amount)
            event = {"event": "enemy_status_count_gain", "status": status, "amount": amount,
                     "before": before, "after": int(st.count), "trigger_rule_id": command.rule_id}
            state.event_log.append(event)
            return event
        if kind == "hongmaehwa_crit":
            if not bool(ctx.get("is_crit", False)):
                return {"executed": False, "reason": "not_critical", "command": command}
            enemy = getattr(state, "enemy", None)
            if enemy is None:
                return {"deferred": True, "reason": "missing_enemy_state", "command": command}
            hm = enemy.statuses.get("홍매화")
            if hm is None:
                hm = Status(); enemy.statuses["홍매화"] = hm
            current = int(getattr(hm, "count", 0))
            threshold = int(p.get("threshold", 10))
            if current >= threshold:
                down = enemy.statuses.get("Defense Level Down")
                if down is None:
                    down = Status(); enemy.statuses["Defense Level Down"] = down
                cap = int(p.get("defense_down_cap", 6))
                before = int(getattr(down, "potency", 0))
                down.potency = min(cap, before + int(p.get("defense_down_amount", 1)))
                event = {"event": "hongmaehwa_defense_down", "before": before,
                         "after": int(down.potency), "hongmaehwa": current,
                         "trigger_rule_id": command.rule_id}
            else:
                gained = int(state.runtime.get("hongmaehwa_gained", 0))
                cap_gain = int(p.get("hongmaehwa_cap", 3))
                add = min(int(p.get("hongmaehwa_amount", 1)), max(0, cap_gain - gained))
                if add <= 0:
                    return {"executed": False, "reason": "turn_gain_cap", "command": command}
                hm.count += add; hm.potency += add
                state.runtime["hongmaehwa_gained"] = gained + add
                event = {"event": "hongmaehwa_gain", "amount": add,
                         "before": current, "after": int(hm.count),
                         "trigger_rule_id": command.rule_id}
            state.event_log.append(event)
            return event
        return self._status_generic(command, ctx)

    def _status_generic(self, command: EffectCommand, ctx: Dict[str, Any]) -> Any:
        # Existing status/poise handlers are implemented below in the legacy
        # compatibility section.  Dispatch to the original implementation.
        return self._status_legacy(command, ctx)

    def _modifier(self, command: EffectCommand, ctx: Dict[str, Any]) -> Any:
        state = ctx.get("state")
        p = command.params
        target = ctx.get("effect_target") or ctx.get("target") or self._resolve_actor(ctx, p)
        # Prefer the declarative target id carried by the RuleIR command.
        # FighterState intentionally does not own an identity id, so deriving the
        # target only from ``fighter.id`` silently registered modifiers against
        # an empty bucket and the DamageEngine could never consume them.
        target_id = str(
            p.get("target_identity_id") or p.get("identity_id")
            or ((target or {}).get("id", (target or {}).get("identity_id", "")) if isinstance(target, dict)
                else getattr(target, "id", ""))
        )
        source = self._actor(ctx)
        source_id = str(
            p.get("source_identity_id")
            or ((source or {}).get("id", (source or {}).get("identity_id", "")) if isinstance(source, dict)
                else getattr(source, "id", ""))
            or ctx.get("identity_id")
            or ctx.get("rule_owner_id")
            or ""
        )

        # These two effects are historically executed immediately by the
        # gimmick layer.  Keeping their exact state mutation here makes their
        # Rule-IR migration semantics equivalent instead of turning them into
        # a generic damage modifier with different timing.
        if command.kind == "extra_damage_scale":
            if state is None or getattr(state, "enemy", None) is None:
                return {"applied": False, "reason": "no_enemy_state"}
            base = float(p.get("base_damage", ctx.get("actual_damage", 0)) or 0)
            scale = float(p.get("scale", 0) or 0)
            cap = int(p.get("cap", getattr(state.enemy, "hp", 0)) or 0)
            amount = min(int(base * scale + 0.5), max(0, cap), max(0, int(getattr(state.enemy, "hp", 0))))
            if amount <= 0:
                return 0
            before = float(state.enemy.hp)
            state.enemy.hp -= amount
            state.turn_damage += amount
            state.runtime["migration_extra_damage"] = int(state.runtime.get("migration_extra_damage", 0)) + amount
            if hasattr(state, "event_log"):
                state.event_log.append({
                    "event": "gimmick_extra_damage",
                    "identity_id": str(getattr(source, "id", ctx.get("identity_id", ""))),
                    "skill_id": str(ctx.get("skill_id", "")),
                    "coin": ctx.get("coin_index"),
                    "base_damage": base, "scale": scale, "extra_damage": amount,
                    "enemy_hp_before": before, "enemy_hp_after": float(state.enemy.hp),
                    "trigger_rule_id": command.rule_id, "migration": "rule_ir",
                })
            return amount

        if command.kind == "status_potency_damage":
            if state is None or getattr(state, "enemy", None) is None:
                return {"applied": False, "reason": "no_enemy_state"}
            aliases = list(p.get("status_aliases") or [])
            status_name = str(p.get("status", "Burn"))
            st = None; resolved_name = status_name
            for key in [status_name] + aliases:
                if key in getattr(state.enemy, "statuses", {}):
                    st = state.enemy.statuses.get(key); resolved_name = key; break
            potency = int(getattr(st, "potency", 0)) if st is not None else 0
            potency = min(potency, int(p.get("max_per_coin", 10)))
            if potency <= 0:
                return 0
            used = int(state.runtime.get("dawn_reused_wrath_damage", 0))
            turn_cap = int(p.get("turn_cap", 20))
            amount = min(potency, max(0, turn_cap-used), max(0, int(getattr(state.enemy, "hp", 0))))
            if amount <= 0:
                return 0
            before = float(state.enemy.hp)
            state.enemy.hp -= amount
            state.turn_damage += amount
            state.runtime["dawn_reused_wrath_damage"] = used + amount
            if hasattr(state, "event_log"):
                state.event_log.append({
                    "event": "reused_coin_status_damage",
                    "identity_id": str(getattr(source, "id", ctx.get("identity_id", ""))),
                    "skill_id": str(ctx.get("skill_id", "")),
                    "coin": ctx.get("coin_index"),
                    "reuse_index": int(ctx.get("reuse_index", 0)),
                    "status": resolved_name, "status_potency": potency, "damage": amount,
                    "damage_type": p.get("damage_type", "wrath"),
                    "enemy_hp_before": before, "enemy_hp_after": float(state.enemy.hp),
                    "trigger_rule_id": command.rule_id, "migration": "rule_ir",
                })
            return amount

        if state is None or not hasattr(state, "runtime"):
            return {"applied": False, "reason": "no_runtime_state"}
        kind = command.kind
        if kind == "damage_flat": kind = "flat_damage"
        amount = float(p.get("amount", p.get("value", 0)))
        return DamageModifierRuntime.register(
            state, target_identity_id=target_id, kind=kind, amount=amount,
            source_identity_id=source_id, attack_type=p.get("attack_type"),
            critical_only=bool(p.get("critical_only", False)),
            skill_name=p.get("skill_name"), reason=str(p.get("reason", "rule")),
            rule_id=command.rule_id or None,
        )
