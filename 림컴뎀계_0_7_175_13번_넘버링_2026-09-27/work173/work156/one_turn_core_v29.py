"""v17 one-turn focused combat layer.

Goal: calculate one-turn damage, not clone the entire game.  This layer adds
three things that matter directly to that goal:
  1) explicit SP state/progression;
  2) deterministic/maximum/fixed/enumerated coin-face resolution;
  3) clash-result events that passives can observe before surviving coins deal damage.

The SP->head probability function is configurable.  The default is the common
calculator convention: 50% at 0 SP, +1 percentage point per SP, clamped to 5-95%.
For maximum-damage mode, probability is intentionally irrelevant: Heads are
selected directly.  This avoids pretending that a maximum-damage optimizer is
a probabilistic simulator.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from itertools import product
from copy import deepcopy
from typing import Any, Dict, List, Optional, Sequence, Tuple

from limbus_damage_engine_v29 import BattleState, EventType, IdentityData, SkillData, ClashData, EnemyState
from battle_core_v29 import ClashAwareBattleStateMachineV23


@dataclass
class SPConfig:
    min_sp: int = -45
    max_sp: int = 45
    base_head_probability: float = 0.50
    probability_per_sp: float = 0.01

    def clamp(self, sp: int) -> int:
        return max(self.min_sp, min(self.max_sp, int(sp)))

    def head_probability(self, sp: int) -> float:
        sp = self.clamp(sp)
        return max(0.05, min(0.95, self.base_head_probability + self.probability_per_sp * sp))


@dataclass
class CoinFacePlan:
    faces: Tuple[str, ...]
    probability: float
    sp_before: int
    sp_after: int


@dataclass
class SPEvent:
    reason: str
    delta: int
    before: int
    after: int


class OneTurnCoreV23:
    def __init__(self, machine: Optional[ClashAwareBattleStateMachineV23] = None,
                 sp_config: Optional[SPConfig] = None):
        self.machine = machine or ClashAwareBattleStateMachineV23()
        self.sp_config = sp_config or SPConfig()
        self.sp_events: List[SPEvent] = []

    def set_sp(self, state: BattleState, identity: IdentityData, value: int,
               reason: str = "set") -> int:
        fighter = state.fighters[identity.id]
        before = fighter.sp
        fighter.sp = self.sp_config.clamp(value)
        self.sp_events.append(SPEvent(reason, fighter.sp - before, before, fighter.sp))
        return fighter.sp

    def change_sp(self, state: BattleState, identity: IdentityData, delta: int,
                  reason: str = "effect") -> int:
        fighter = state.fighters[identity.id]
        before = fighter.sp
        fighter.sp = self.sp_config.clamp(fighter.sp + int(delta))
        actual = fighter.sp - before
        self.sp_events.append(SPEvent(reason, actual, before, fighter.sp))
        state.event_log.append({"event": "sp_change", "identity_id": identity.id, "reason": reason,
                                "delta": actual, "sp_before": before, "sp_after": fighter.sp})
        return fighter.sp

    def apply_skill_sp(self, state: BattleState, identity: IdentityData,
                       skill: SkillData, reason: str = "skill") -> None:
        """Apply explicit skill resource fields when SP is present.

        `resource_gain/cost` is intentionally the source of truth here.  No
        hidden identity-specific SP behavior is invented.
        """
        gain = int(skill.resource_gain.get("SP", skill.resource_gain.get("sp", 0)))
        cost = int(skill.resource_cost.get("SP", skill.resource_cost.get("sp", 0)))
        if cost:
            self.change_sp(state, identity, -cost, reason=f"{reason}:cost")
        if gain:
            self.change_sp(state, identity, gain, reason=f"{reason}:gain")

    def resolve_faces(self, state: BattleState, identity: IdentityData,
                      skill: SkillData, mode: str = "max",
                      fixed_faces: Optional[Sequence[str]] = None,
                      sp_delta_per_head: int = 0,
                      sp_delta_per_tail: int = 0) -> List[CoinFacePlan]:
        n = len(skill.coins)
        sp0 = state.fighters[identity.id].sp
        if mode == "fixed":
            if fixed_faces is None or len(fixed_faces) != n:
                raise ValueError("fixed mode requires one face per coin")
            candidates = [tuple(x.upper() for x in fixed_faces)]
        elif mode == "max":
            candidates = [tuple("H" for _ in range(n))]
        elif mode == "enumerate":
            candidates = list(product(("H", "T"), repeat=n))
        else:
            raise ValueError("mode must be max, fixed, or enumerate")

        plans=[]
        for faces in candidates:
            sp=sp0
            prob=1.0
            for face in faces:
                p=self.sp_config.head_probability(sp)
                if face == "H":
                    prob *= p
                    sp=self.sp_config.clamp(sp + sp_delta_per_head)
                else:
                    prob *= (1.0-p)
                    sp=self.sp_config.clamp(sp + sp_delta_per_tail)
            plans.append(CoinFacePlan(faces, prob, sp0, sp))
        return plans

    def _queue_target_death_callbacks(self, state: BattleState, identity: IdentityData, skill: SkillData,
                                      target_id: str, target: EnemyState, coin_index: int) -> None:
        """Collect target-local death callbacks for post-action processing."""
        cb = state.runtime.get('after_target_kill')
        if not cb:
            return
        ctx = {
            'action_index': state.runtime.get('current_action_index'),
            'coin_index': int(coin_index),
            'target_id': str(target_id),
            'target': target,
            'action_start_hp': state.runtime.get('current_action_start_hp'),
            'action_end_hp': float(target.hp),
        }
        generated = cb(state, identity, skill, ctx) or []
        if generated:
            state.runtime.setdefault('pending_target_kill_actions', []).extend((ga, dict(ctx)) for ga in generated)

    def execute_unopposed_multi_target(self, state: BattleState, identity: IdentityData,
                                       skill: SkillData, faces: Sequence[str],
                                       target_states: Sequence[tuple[str, EnemyState]],
                                       is_crit: bool = False, coin_target_ids=None, coin_target_policies=None) -> Dict[str, Any]:
        """Resolve one attack against explicit enemy targets.

        Skill/use lifecycle and attacker resources are shared; each selected enemy
        receives the same coin sequence independently.  The state.enemy reference
        is swapped only while a target is being resolved so the existing damage,
        status, stagger and event machinery remains authoritative.
        """
        self.apply_skill_sp(state, identity, skill, reason="skill")
        self.machine.engine.bus.emit(EventType.BEFORE_USE,
            {"state": state, "identity": identity, "skill": skill})
        for effect in skill.effects_before_use + skill.effects_on_use:
            if self.machine.engine.condition_met(state, identity, effect.get("condition"), skill):
                self.machine.engine.apply_effect(state, identity.id, effect.get("target", "self"), effect)
        self.machine.engine.bus.emit(EventType.ON_USE,
            {"state": state, "identity": identity, "skill": skill})
        original_enemy = state.enemy
        per_target = {}
        target_by_id = {str(tid): target for tid, target in target_states}
        # coin_target_ids is an explicit per-coin assignment. Each entry may be
        # a target id/index or a list of them. A mapped coin is resolved once per
        # mapped target, while the skill/use lifecycle remains shared.
        if coin_target_ids is not None:
            for tid, target in target_states:
                per_target[str(tid)] = 0.0

            def resolve_coin_targets(spec):
                vals = spec if isinstance(spec, (list, tuple)) else [spec]
                resolved = []
                seen = set()
                for value in vals:
                    key = str(value)
                    target = target_by_id.get(key)
                    if target is not None and key not in seen:
                        resolved.append((key, target)); seen.add(key)
                return resolved

            def resolve_one_logical_coin(coin_index, coin, face, resolved, prior_heads, reuse_index=0):
                logical_ammo_context = None
                any_alive = False
                any_kill = False
                for target_pos, (tid, target) in enumerate(resolved):
                    if target.hp <= 0:
                        state.event_log.append({'event':'coin_target_skipped','target_id':str(tid),
                                                'identity_id':identity.id,'skill_id':skill.id,
                                                'coin':coin_index + 1,'reuse_index':reuse_index,
                                                'reason':'target_dead'})
                        continue
                    any_alive = True
                    state.enemy = target
                    state.runtime["current_target_id"] = str(tid)
                    before = state.turn_damage
                    secondary = target_pos > 0
                    self.machine.engine.simulate_coin(
                        state, identity, skill, coin,
                        face, is_crit, coin_index + 1, prior_heads,
                        consume_attacker_state=not secondary,
                        run_special_after_coin=True,
                        consume_poise=not secondary,
                        allow_crit_without_poise=secondary,
                        attacker_ammo_context=logical_ammo_context, reuse_index=reuse_index,
                        is_added_coin=(coin_index in added_coin_indices))
                    if target.hp <= 0:
                        self._queue_target_death_callbacks(state, identity, skill, str(tid), target, coin_index + 1)
                    if not secondary:
                        for ev in reversed(state.event_log):
                            if ev.get('event') == 'coin' and ev.get('coin') == coin_index + 1 and ev.get('identity') == identity.id:
                                logical_ammo_context = (ev.get('ammo_before', state.fighters[identity.id].ammo),
                                                         ev.get('ammo_after', state.fighters[identity.id].ammo),
                                                         ev.get('ammo_spent', 0))
                                break
                    damage = float(state.turn_damage - before)
                    per_target[str(tid)] = per_target.get(str(tid), 0.0) + damage
                    if target.hp <= 0:
                        any_kill = True
                    state.event_log.append({'event':'coin_target_resolution','target_id':str(tid),
                                            'identity_id':identity.id,'skill_id':skill.id,
                                            'coin':coin_index + 1,'reuse_index':reuse_index,
                                            'is_added_coin': bool(coin_index in added_coin_indices),
                                            'coin_origin': ('added' if coin_index in added_coin_indices else 'base'),
                                            'secondary_target':secondary,'damage':damage,
                                            'hp_after':float(target.hp)})
                return any_alive, any_kill

            logical_reuse_counts = {}
            logical_kill_reuse_used = 0
            # Source-backed added-coin rules are evaluated after skill on-use
            # effects. The added coin is a copy of the referenced source coin,
            # marked through execution context so "added coin hit" effects
            # only see the generated copy.
            execution_coins = list(skill.coins)
            added_coin_indices = set()
            for ar in getattr(skill, 'added_coin_rules', []) or []:
                if self.machine.engine.condition_met(state, identity, ar.get('condition'), skill):
                    src = int(ar.get('source_coin_index', -1))
                    for _ in range(max(0, int(ar.get('count', 1)))):
                        if 0 <= src < len(skill.coins):
                            c = deepcopy(skill.coins[src])
                            c.unbreakable = bool(ar.get('unbreakable', c.unbreakable))
                            c.effects.extend(deepcopy(ar.get('effects', []) or []))
                            execution_coins.append(c)
                            added_coin_indices.add(len(execution_coins)-1)
            exec_faces = list(faces)
            for ai in sorted(added_coin_indices):
                src = int(next((r.get('source_coin_index') for r in (getattr(skill, 'added_coin_rules', []) or []) if True), 0))
                exec_faces.append(faces[src] if 0 <= src < len(faces) else 'H')
            for coin_index, coin in enumerate(execution_coins):
                spec = coin_target_ids[coin_index] if coin_index < len(coin_target_ids) else None
                resolved = resolve_coin_targets(spec)
                face = exec_faces[coin_index] if coin_index < len(exec_faces) else "H"
                resolved_any, any_kill = resolve_one_logical_coin(coin_index, coin, face, resolved,
                                                                  sum(1 for f in faces[:coin_index] if str(f).upper() == "H"))
                state.runtime["last_coin_face"] = face
                state.runtime["last_coin_critical"] = bool(is_crit)

                # Kill-reuse is a skill-level trigger. The existing single-target
                # executor records this trigger but intentionally does not invent
                # a new target after the killing target disappears. Keep the same
                # rule here while making the trigger target-aware.
                if any_kill and logical_kill_reuse_used == 0:
                    for kr in getattr(skill, 'kill_reuse_rules', []) or []:
                        if logical_kill_reuse_used >= int(kr.get('max_reuses', 0)):
                            continue
                        alive_after = [(tid,t) for tid,t in target_states if t.hp > 0]
                        condition_target = alive_after[0][1] if alive_after else (resolved[0][1] if resolved else None)
                        if condition_target is not None:
                            state.enemy = condition_target
                            if self.machine.engine.condition_met(state, identity, kr.get('condition'), skill):
                                logical_kill_reuse_used += 1
                                state.event_log.append({'event':'kill_skill_reuse_triggered',
                                                        'identity_id':identity.id,'skill_id':skill.id,
                                                        'reuse_index':logical_kill_reuse_used,
                                                        'target_aware':True})
                                break

                # Coin-local reuse is evaluated against the targets actually hit
                # by this logical coin. A target-local condition may therefore
                # trigger from any mapped target, while attacker-global state is
                # still consumed only once on the reused logical coin.
                should_reuse = False
                trigger_target = None
                for tid, target in resolved:
                    if target.hp <= 0:
                        continue
                    state.enemy = target
                    for ri, rule in enumerate(getattr(coin, 'reuse_rules', []) or []):
                        key=(coin_index,ri)
                        used=int(logical_reuse_counts.get(key,0))
                        if used >= int(rule.get('max_reuses',0)):
                            continue
                        if self.machine.engine.condition_met(state, identity, rule.get('condition'), skill):
                            logical_reuse_counts[key]=used+1
                            should_reuse=True
                            trigger_target=str(tid)
                            break
                    if should_reuse:
                        break
                reuse_index = 0
                while should_reuse and resolved:
                    reuse_index += 1
                    _, reused_kill = resolve_one_logical_coin(coin_index, coin, face, resolved,
                                                               sum(1 for f in faces[:coin_index] if str(f).upper() == "H"),
                                                               reuse_index=reuse_index)
                    state.event_log.append({'event':'coin_reuse_triggered',
                                            'identity_id':identity.id,'skill_id':skill.id,
                                            'coin':coin_index + 1,'reuse_index':reuse_index,
                                            'target_id':trigger_target})
                    should_reuse = False
                    for tid, target in resolved:
                        if target.hp <= 0:
                            continue
                        state.enemy = target
                        for ri, rule in enumerate(getattr(coin, 'reuse_rules', []) or []):
                            key=(coin_index,ri)
                            used=int(logical_reuse_counts.get(key,0))
                            if used >= int(rule.get('max_reuses',0)):
                                continue
                            if self.machine.engine.condition_met(state, identity, rule.get('condition'), skill):
                                logical_reuse_counts[key]=used+1
                                should_reuse=True; trigger_target=str(tid); break
                        if should_reuse:
                            break

            # Last-coin reuse is a skill-level effect. It is a new logical coin
            # execution and therefore consumes attacker state once, while all
            # explicitly mapped targets receive the reused final coin.
            if skill.coins:
                last_idx = len(skill.coins) - 1
                last_coin = skill.coins[last_idx]
                last_face = faces[last_idx] if last_idx < len(faces) else 'H'
                alive_targets = [(tid,t) for tid,t in target_states if t.hp > 0]
                if alive_targets:
                    state.enemy = alive_targets[0][1]
                    for rule in getattr(skill, 'last_coin_reuse_rules', []) or []:
                        if self.machine.engine.condition_met(state, identity, rule.get('condition'), skill):
                            for ri in range(max(0, int(rule.get('max_reuses', 0)))):
                                mapped_spec = coin_target_ids[last_idx] if last_idx < len(coin_target_ids) else None
                                mapped_alive = [(tid,t) for tid,t in resolve_coin_targets(mapped_spec) if t.hp > 0]
                                if not mapped_alive:
                                    mapped_alive = alive_targets
                                resolve_coin_targets_result = resolve_one_logical_coin(
                                    last_idx, last_coin, last_face, mapped_alive,
                                    sum(1 for f in faces[:last_idx] if str(f).upper() == 'H'),
                                    reuse_index=ri + 1)
                                # Source-explicit [재사용 적중시] effects belong to the
                                # reused logical coin, not the original final coin.
                                for reff in (rule.get('reuse_hit_effects') or []):
                                    limit = int(reff.get('reuse_hit_limit', 0) or 0)
                                    if limit and (ri + 1) > limit:
                                        continue
                                    self.machine.engine.apply_effect(state, identity.id, reff.get('target', 'enemy'), reff)
                                state.event_log.append({'event':'last_coin_reuse_triggered',
                                                        'identity_id':identity.id,'skill_id':skill.id,
                                                        'reuse_index':ri + 1,
                                                        'target_ids':[str(tid) for tid,_ in mapped_alive]})

        else:
            logical_reuse_counts = {}
            logical_coin_index = 0
            logical_prior_heads = 0
            logical_ammo_contexts = {}
            execution_coins = list(skill.coins)
            added_coin_indices = set()
            for ar in getattr(skill, 'added_coin_rules', []) or []:
                if self.machine.engine.condition_met(state, identity, ar.get('condition'), skill):
                    src = int(ar.get('source_coin_index', -1))
                    for _ in range(max(0, int(ar.get('count', 1)))):
                        if 0 <= src < len(skill.coins):
                            c = deepcopy(skill.coins[src])
                            c.unbreakable = bool(ar.get('unbreakable', c.unbreakable))
                            c.effects.extend(deepcopy(ar.get('effects', []) or []))
                            execution_coins.append(c)
                            added_coin_indices.add(len(execution_coins)-1)
            exec_faces = list(faces)
            for ai in sorted(added_coin_indices):
                src = int(next((r.get('source_coin_index') for r in (getattr(skill, 'added_coin_rules', []) or []) if True), 0))
                exec_faces.append(faces[src] if 0 <= src < len(faces) else 'H')
            for target_id, target in target_states:
                per_target[str(target_id)] = 0.0
            while logical_coin_index < len(execution_coins):
                coin = execution_coins[logical_coin_index]
                face = exec_faces[logical_coin_index] if logical_coin_index < len(exec_faces) else "H"
                reuse_counts = logical_reuse_counts.setdefault(logical_coin_index, {})
                resolved_any = False
                role = (coin_target_policies[logical_coin_index]
                        if coin_target_policies is not None and logical_coin_index < len(coin_target_policies)
                        else None)
                alive_for_role = [(tid,t) for tid,t in target_states if t.hp > 0]
                if role in ('main','single_main'):
                    resolved_targets = alive_for_role[:1]
                elif role == 'sub':
                    resolved_targets = alive_for_role[1:]
                else:
                    resolved_targets = list(target_states)
                for target_pos, (target_id, target) in enumerate(resolved_targets):
                    if target.hp <= 0:
                        continue
                    state.enemy = target
                    state.runtime["current_target_id"] = str(target_id)
                    before = state.turn_damage
                    secondary = target_pos > 0
                    self.machine.engine.simulate_coin(
                        state, identity, skill, coin, face, is_crit,
                        logical_coin_index + 1, logical_prior_heads,
                        consume_attacker_state=not secondary,
                        run_special_after_coin=True,
                        consume_poise=not secondary,
                        allow_crit_without_poise=secondary,
                        attacker_ammo_context=logical_ammo_contexts.get(logical_coin_index),
                        is_added_coin=(logical_coin_index in added_coin_indices))
                    if target.hp <= 0:
                        self._queue_target_death_callbacks(state, identity, skill, str(target_id), target, logical_coin_index + 1)
                    if not secondary:
                        # Capture the single attacker-global ammo transition for
                        # this logical coin so every additional target receives
                        # the same last-ammo/conditional context.
                        for ev in reversed(state.event_log):
                            if ev.get('event') == 'coin' and ev.get('coin') == logical_coin_index + 1 and ev.get('identity') == identity.id:
                                logical_ammo_contexts[logical_coin_index] = (ev.get('ammo_before', state.fighters[identity.id].ammo),
                                                                             ev.get('ammo_after', state.fighters[identity.id].ammo),
                                                                             ev.get('ammo_spent', 0))
                                break
                    per_target[str(target_id)] += float(state.turn_damage - before)
                    resolved_any = True
                    state.event_log.append({'event':'target_resolution','target_id':str(target_id),
                                            'identity_id':identity.id,'skill_id':skill.id,
                                            'coin':logical_coin_index + 1,
                                            'secondary_target':secondary,
                                            'damage':float(state.turn_damage-before),
                                            'hp_after':float(state.enemy.hp)})
                if face == "H":
                    logical_prior_heads += 1
                # Reuse conditions are evaluated once per logical coin against
                # the first resolved target; target-specific reuse remains an
                # explicit future extension rather than duplicating attacker state.
                first_alive = next(((tid,t) for tid,t in resolved_targets if t.hp > 0), None)
                should_reuse = False
                if first_alive is not None:
                    state.enemy = first_alive[1]
                    for ri, rule in enumerate(getattr(coin, "reuse_rules", []) or []):
                        used=int(reuse_counts.get(ri,0))
                        if used >= int(rule.get("max_reuses",0)): continue
                        if self.machine.engine.condition_met(state, identity, rule.get("condition"), skill):
                            reuse_counts[ri]=used+1; should_reuse=True; break
                if not should_reuse:
                    logical_coin_index += 1
            for target_id, target in target_states:
                state.event_log.append({'event':'target_resolution','target_id':str(target_id),
                                        'identity_id':identity.id,'skill_id':skill.id,
                                        'damage':per_target[str(target_id)],
                                        'hp_after':float(target.hp)})
        # Preserve the causal target-death result before restoring the
        # main enemy pointer.  ATTACK_END passives must evaluate the target
        # that was actually resolved, not whichever enemy object happens to
        # be current after multi-target processing.
        attack_target_dead = any(float(getattr(target, "hp", 0)) <= 0 for _, target in target_states)
        state.runtime["attack_target_dead"] = attack_target_dead
        state.enemy = original_enemy
        state.runtime.pop("current_target_id", None)
        self.machine.engine.bus.emit(EventType.ATTACK_END,
            {"state": state, "identity": identity, "skill": skill,
             "attack_target_dead": attack_target_dead})
        state.runtime.pop("attack_target_dead", None)
        return {"damage": sum(per_target.values()),
                "damage_by_target": per_target,
                "sp": state.fighters[identity.id].sp,
                "faces": tuple(faces)}

    def execute_unopposed(self, state: BattleState, identity: IdentityData,
                          skill: SkillData, faces: Sequence[str],
                          is_crit: bool = False) -> Dict[str, Any]:
        self.apply_skill_sp(state, identity, skill, reason="skill")
        before = state.turn_damage
        # Emit skill lifecycle events explicitly so passive triggers can modify
        # the per-coin damage context.
        self.machine.engine.bus.emit(EventType.BEFORE_USE,
            {"state": state, "identity": identity, "skill": skill})
        # Execute structured skill-level effects before the first coin.
        for effect in skill.effects_before_use + skill.effects_on_use:
            if self.machine.engine.condition_met(state, identity, effect.get("condition"), skill):
                self.machine.engine.apply_effect(state, identity.id, effect.get("target", "self"), effect)
        self.machine.engine.bus.emit(EventType.ON_USE,
            {"state": state, "identity": identity, "skill": skill})
        prior_heads=0
        reuse_counts={}
        # Reuse counters are skill-local.  Reset the last-coin counter so a
        # reused coin in a later action is still recognized as reuse #1.
        state.runtime['last_coin_reuse_index']=0
        kill_reuse_used=0
        reused_skill=False
        coin_index=0
        logical_reuse_index={}
        while coin_index < len(skill.coins):
            if state.enemy.hp <= 0: break
            coin=skill.coins[coin_index]
            face=faces[coin_index] if coin_index < len(faces) else "H"
            reuse_index=int(logical_reuse_index.get(coin_index,0))
            self.machine.engine.simulate_coin(state, identity, skill, coin, face, is_crit, coin_index+1, prior_heads, reuse_index=reuse_index)
            if state.enemy.hp <= 0:
                self._queue_target_death_callbacks(state, identity, skill, str(state.runtime.get("current_target_id", "main")), state.enemy, coin_index + 1)
            state.runtime["last_coin_face"] = face
            state.runtime["last_coin_critical"] = bool(is_crit)
            if face == "H": prior_heads += 1
            # A skill-level kill reuse is evaluated immediately after the killing
            # coin. The reused copy is marked so its own kill-reuse clause does not
            # recursively fire.
            if state.enemy.hp <= 0 and not reused_skill and kill_reuse_used == 0:
                for kr in getattr(skill, 'kill_reuse_rules', []) or []:
                    if kill_reuse_used >= int(kr.get('max_reuses', 0)):
                        continue
                    if self.machine.engine.condition_met(state, identity, kr.get('condition'), skill):
                        kill_reuse_used += 1
                        reused_skill = True
                        # The current target is dead, so a true random-target reuse
                        # requires target selection. Keep the deterministic same-target
                        # path disabled rather than resurrecting a dead target.
                        state.event_log.append({'event':'kill_skill_reuse_triggered','identity_id':identity.id,'skill_id':skill.id,'reuse_index':kill_reuse_used})
                        break
            should_reuse=False
            for ri, rule in enumerate(getattr(coin, "reuse_rules", []) or []):
                key=(coin_index,ri)
                used=int(reuse_counts.get(key,0))
                if used >= int(rule.get("max_reuses",0)): continue
                if self.machine.engine.condition_met(state, identity, rule.get("condition"), skill):
                    reuse_counts[key]=used+1
                    logical_reuse_index[coin_index]=int(logical_reuse_index.get(coin_index,0))+1
                    should_reuse=True
                    break
            if not should_reuse:
                coin_index += 1
        # Skill-level last-coin reuse (e.g. a use-time resource threshold).
        if state.enemy.hp > 0 and skill.coins:
            for rule in getattr(skill, 'last_coin_reuse_rules', []) or []:
                if self.machine.engine.condition_met(state, identity, rule.get('condition'), skill):
                    for _ in range(max(0, int(rule.get('max_reuses', 0)))):
                        if state.enemy.hp <= 0: break
                        last_idx=len(skill.coins)-1
                        last_coin=skill.coins[last_idx]
                        face=faces[last_idx] if last_idx < len(faces) else 'H'
                        last_reuse_index=int(state.runtime.get('last_coin_reuse_index',0))+1
                        state.runtime['last_coin_reuse_index']=last_reuse_index
                        self.machine.engine.simulate_coin(state, identity, skill, last_coin, face, is_crit, last_idx+1, prior_heads, reuse_index=last_reuse_index)
                        state.runtime["last_coin_face"] = face
                        state.runtime["last_coin_critical"] = bool(is_crit)
                        if face == 'H': prior_heads += 1
                        # Reused final coins may themselves have a bounded local reuse.
                        for rr in getattr(last_coin, 'reuse_rules', []) or []:
                            if state.enemy.hp <= 0: break
                            if self.machine.engine.condition_met(state, identity, rr.get('condition'), skill):
                                for _j in range(max(0, int(rr.get('max_reuses', 0)))):
                                    if state.enemy.hp <= 0: break
                                    last_reuse_index=int(state.runtime.get('last_coin_reuse_index',0))+1
                                    state.runtime['last_coin_reuse_index']=last_reuse_index
                                    self.machine.engine.simulate_coin(state, identity, skill, last_coin, face, is_crit, last_idx+1, prior_heads, reuse_index=last_reuse_index)
                                    state.runtime["last_coin_face"] = face
                                    state.runtime["last_coin_critical"] = bool(is_crit)
                                    if face == 'H': prior_heads += 1
        self.machine.engine.bus.emit(EventType.ATTACK_END,
            {"state": state, "identity": identity, "skill": skill})
        return {"damage": state.turn_damage-before,
                "sp": state.fighters[identity.id].sp,
                "faces": tuple(faces)}

    def execute_clash(self, state: BattleState, identity: IdentityData,
                      skill: SkillData, defender: ClashData,
                      faces: Optional[Sequence[str]] = None,
                      defender_faces: Optional[Sequence[str]] = None,
                      is_crit: bool = False) -> Dict[str, Any]:
        self.apply_skill_sp(state, identity, skill, reason="skill")
        return self.machine.execute_clash(state, identity, skill, defender,
                                          attacker_faces=faces,
                                          defender_faces=defender_faces,
                                          is_crit=is_crit)


OneTurnCoreV17 = OneTurnCoreV23
