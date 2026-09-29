"""v20 One-Turn Damage Solver.

Focus: one-turn damage from user-supplied initial conditions.  This layer adds
translation of the supplied Korean catalog skill text into a conservative,
explicit subset of executable skill effects.  Unsupported text remains in
`source_effects` and is never silently guessed.
"""
from __future__ import annotations
import re
import random
from copy import deepcopy
from dataclasses import dataclass
from typing import Any, List

from limbus_damage_engine_v29 import BattleState, EnemyState, FighterState, IdentityData, SkillData, CoinData, ClashData, Status, EventType
from one_turn_core_v29 import OneTurnCoreV17
from passive_compiler_v29 import compile_passive_v29
from special_gimmick_v2 import GimmickRegistry
from action_queue_v1 import ActionQueue
from resource_runtime_v1 import ResourceRuntime
from clash_exchange_runtime_v1 import ClashExchangeRuntime
from bleed_clash_probability_v1 import ProbabilisticBleedClashRuntime
from turn_bleed_state_runtime_v1 import TurnBleedStateRuntime
from trigger_rule_model_v1 import TriggerRule, TriggerCondition, TriggerEffect
from probabilistic_trigger_runtime_v1 import ProbabilisticTriggerRuntime
from rule_migration_runtime_v1 import RuleMigrationRuntime
from target_selector_v1 import select_targets, normalize as normalize_target_policy
from coin_execution_core_v1 import CoinExecutionCore, CoinExecutionContext
from buff_debuff_event_bridge_v1 import BuffDebuffEventBridge
from buff_debuff_runtime_v1 import BuffDebuffRuntime
from trigger_action_execution_v1 import TriggerActionExecutionBoundary
from skill_text_parser_v19 import SkillTextParserV19
from identity_catalog_v29 import IdentityCatalogV29
from legacy_condition_combinators_v1 import evaluate_composite_condition
from probabilistic_state_tools_v1 import (
    action_state_diff, status_signature, restore_status_signature,
    probabilistic_state_signature, restore_probabilistic_state_signature,
)

SIN = {"lust":"lust","envy":"envy","wrath":"wrath","sloth":"sloth","gluttony":"gluttony","gloom":"gloom","pride":"pride",
       "색욕":"lust","질투":"envy","분노":"wrath","나태":"sloth","폭식":"gluttony","우울":"gloom","오만":"pride"}
ATK={"참격":"slash","관통":"pierce","타격":"blunt","slash":"slash","pierce":"pierce","blunt":"blunt"}
STATUS={"출혈":"Bleed","화상":"Burn","파열":"Rupture","침잠":"Sinking","진동":"Tremor","호흡":"Poise","충전":"Charge","속박":"Bind","취약":"Damage Taken Up"}

@dataclass
class ParseReport:
    supported: List[str]
    unsupported: List[str]



@dataclass
class TurnExecutionContext:
    """Per-solve execution context shared by preparation, action execution and finalization."""
    state: Any
    mode: str
    resource_runtime: Any
    target_count: int
    expected_turn_base_state: Any
    resonance_plan: list
    selected_passives: dict
    passive_variant_mode: str
    gimmicks: Any
    action_queue: Any
    out: list
    damage_by_identity: dict
    damage_by_skill: dict
    expected_damage_by_identity: dict
    expected_damage_by_skill: dict
    expected_turn_damage: float


@dataclass
class ResolvedAction:
    """Action-boundary result: identity/skill/resources/faces/targets are resolved before execution."""
    request: Any
    raw_action: dict
    identity_id: str
    identity: Any
    original_skill_id: str
    skill: Any
    transform_info: Any
    fighter: Any
    consumed_resources: dict
    faces: list
    target_ctx: dict
    requested_target_count: int



class OneTurnSolverV29:
    # Compatibility shims: older tests/extensions call these helpers through
    # the solver class. The implementation now lives in a shared utility module.
    _action_state_diff = staticmethod(action_state_diff)
    _status_signature = staticmethod(status_signature)
    _restore_status_signature = staticmethod(restore_status_signature)
    _probabilistic_state_signature = staticmethod(probabilistic_state_signature)
    _restore_probabilistic_state_signature = staticmethod(restore_probabilistic_state_signature)
    def __init__(self,core=None):
        self.core=core or OneTurnCoreV17()
        self.clash_exchange_runtime=ClashExchangeRuntime()
        self.bleed_probability_runtime=ProbabilisticBleedClashRuntime(trim_extremes=True, trim_fraction=0.05)
        self.turn_bleed_state_runtime=TurnBleedStateRuntime(trim_fraction=0.05)
    @staticmethod
    def _status_map(raw):
        out={}
        for n,v in (raw or {}).items(): out[n]=Status(**{k:v.get(k,0) for k in ('potency','count')}) if isinstance(v,dict) else Status(potency=int(v))
        return out
    def build_state(self,scenario,identities):
        e=scenario.get('enemy',{})
        enemy_statuses=self._status_map(e.get('statuses'))
        explicit_afterimage=e.get('afterimage_count', e.get('afterimages'))
        if isinstance(explicit_afterimage, dict):
            explicit_afterimage=explicit_afterimage.get('count', explicit_afterimage.get('potency', 0))
        if explicit_afterimage is not None:
            try: n=max(0,int(explicit_afterimage))
            except (TypeError, ValueError): n=0
            if n > 0: enemy_statuses['잔영']=Status(potency=0,count=n)
            else: enemy_statuses.pop('잔영',None)
        enemy=EnemyState(float(e.get('hp',e.get('max_hp',1))),float(e.get('max_hp',e.get('hp',1))),level=int(e.get('level',60)),speed=int(e.get('speed',0)),defense_level=int(e.get('defense_level',0)),defense_level_bonus=int(e.get('defense_level_bonus',0)),physical_res={k:float(v) for k,v in e.get('physical_res',{'slash':1,'pierce':1,'blunt':1}).items()},sin_res={SIN.get(k,k):float(v) for k,v in e.get('sin_res',{}).items()},keyword_damage_modifiers={str(k):float(v) for k,v in e.get('keyword_damage_modifiers',{}).items()},sinking_sp_overflow_to_hp=bool(e.get('sinking_sp_overflow_to_hp',False)),statuses=enemy_statuses,stagger_level=int(e.get('stagger_level',0)),stagger_index=int(e.get('stagger_index',0)),stagger_thresholds=list(e.get('stagger_thresholds',[])),is_abnormality=bool(e.get('is_abnormality',e.get('abnormality',False))))
        fs={}
        for iid,ident in identities.items():
            a=scenario.get('allies',{}).get(iid,{})
            fs[iid]=FighterState(level=int(a.get('level',getattr(ident,'_catalog_level',60))),speed=int(a.get('speed',getattr(ident,'_scenario_speed',0) or 0)),sp=int(a.get('sp',0)),hp=float(a.get('hp',999999)),max_hp=float(a.get('max_hp',999999)),sin_resources={SIN.get(k,k):int(v) for k,v in a.get('sin_resources',{}).items()},poise=Status(**{k:v for k,v in a.get('poise',{}).items() if k in ('potency','count')}),charge=int(a.get('charge',0)),charge_potency=int(a.get('charge_potency',a.get('charge_power',0))),ammo=int(a.get('ammo',0)),defense_level_bonus=int(a.get('defense_level_bonus',0)),shield=float(a.get('shield',0)),charge_barrier_shield=float(a.get('charge_barrier_shield',0)),is_wcorp=('W CORP' in [str(x).upper() for x in getattr(ident,'affiliation',[])]) ,resources={str(k):int(v) for k,v in a.get('resources',{}).items()},statuses=self._status_map(a.get('statuses')))
        state = BattleState(enemy,fs)
        # Calculator UI semantics: target level and Defense Level are separate
        # inputs; Defense Level is already the effective value used by damage.
        state.runtime["defense_level_is_absolute"] = bool(scenario.get("defense_level_is_absolute", True))
        return state
    def _skill(self,ident,key): return ident.skills.get(str(key)) or next((s for s in ident.skills.values() if str(s.id)==str(key)),None)
    @staticmethod
    def _resonance_table_bonus(count: int) -> int:
        """Offense-level bonus for ordinary Sin Resonance position.

        This intentionally uses a compact table rather than simulating the
        game's dashboard internals.  Position 1 has no bonus; later matching
        skills use the published 0,1,3,3,5,5,7... progression.
        """
        if count <= 1:
            return 0
        return [0,1,3,3,5,5,7,7,9,9,11][min(count,11)-1]

    @staticmethod
    def _absolute_table_bonus(length: int) -> int:
        if length < 3:
            return 0
        table = [0,0,0,3,5,5,7,7,9,9,11,11]
        return table[min(length, 11)]

    def _build_resonance_plan(self, actions, identity_map):
        """Derive resonance entirely from the user-selected action order.

        Normal resonance counts all matching Sin skills in the selected turn;
        Absolute Resonance additionally requires 3+ consecutive matching
        actions.  This is a one-turn input interpretation: no prior-turn
        skill-board generation is simulated.
        """
        sin_counts = {}
        entries=[]
        for idx,a in enumerate(actions):
            ident=identity_map[str(a['identity_id'])]
            skill=self._skill(ident,a['skill_id'])
            sin=str(skill.sin)
            sin_counts[sin]=sin_counts.get(sin,0)+1
            entries.append({'index':idx+1,'sin':sin,'resonance_count':sin_counts[sin],
                            'resonance_offense_bonus':self._resonance_table_bonus(sin_counts[sin]),
                            'absolute_count':0,'absolute_offense_bonus':0,
                            'counts':dict(sin_counts)})
        # Find maximal consecutive chains and assign their A-Res bonus to all
        # members.  A-Res overrides ordinary resonance's offense bonus.
        start=0
        while start < len(entries):
            end=start+1
            while end < len(entries) and entries[end]['sin']==entries[start]['sin']:
                end+=1
            length=end-start
            if length>=3:
                bonus=self._absolute_table_bonus(length)
                for j in range(start,end):
                    entries[j]['absolute_count']=length
                    entries[j]['absolute_offense_bonus']=bonus
            start=end
        for e in entries:
            e['offense_bonus']=e['absolute_offense_bonus'] or e['resonance_offense_bonus']
        return entries

    @staticmethod
    def _normalize_condition_overrides(raw):
        """Turn-start simplification layer: flags/conditions the user declares as prepared."""
        if not raw:
            return {}
        if isinstance(raw, dict) and "flags" in raw:
            return {str(k): bool(v) for k, v in raw.get("flags", {}).items()}
        return {str(k): bool(v) for k, v in raw.items() if isinstance(v, (bool, int))}

    def _condition_met(self, state, identity, condition, skill=None):
        if not condition: return True
        kind=condition.get("type")
        if kind == "always": return True
        f=state.fighters[identity.id]; e=state.enemy
        if kind == "flag": return bool(state.runtime.get("condition_flags", {}).get(str(condition.get("name", "")), False))
        if kind == "hp_pct_lte": return e.max_hp > 0 and e.hp/e.max_hp*100 <= float(condition.get("value",0))
        if kind == "hp_pct_gte": return e.max_hp > 0 and e.hp/e.max_hp*100 >= float(condition.get("value",0))
        if kind == "self_hp_pct_lte": return f.max_hp > 0 and f.hp/f.max_hp*100 <= float(condition.get("value",0))
        if kind == "self_hp_pct_gte": return f.max_hp > 0 and f.hp/f.max_hp*100 >= float(condition.get("value",0))
        if kind == "speed_gte": return f.speed >= int(condition.get("value",0))
        if kind == "speed_lte": return f.speed <= int(condition.get("value",0))
        if kind == "speed_difference_gte": return (f.speed - e.speed) >= int(condition.get("value",0))
        if kind == "speed_difference_lte": return (f.speed - e.speed) <= int(condition.get("value",0))
        if kind == "charge_gte": return f.charge >= int(condition.get("value",0))
        if kind == "charge_lte": return f.charge <= int(condition.get("value",0))
        if kind == "ammo_gte": return f.ammo >= int(condition.get("value",0))
        if kind == "ammo_lte": return f.ammo <= int(condition.get("value",0))
        if kind == "poise_potency_gte": return f.poise.potency >= int(condition.get("value",0))
        if kind == "poise_count_gte": return f.poise.count >= int(condition.get("value",0))
        if kind == "enemy_staggered": return e.stagger_level > 0
        if kind == "enemy_stagger_level_gte": return e.stagger_level >= int(condition.get("value",0))
        if kind == "enemy_stagger_index_gte": return e.stagger_index >= int(condition.get("value",0))
        if kind in ("resonance_gte","sin_resonance_gte"):
            return int(state.runtime.get("current_resonance",{}).get(str(condition.get("sin")),0)) >= int(condition.get("value",0))
        if kind in ("absolute_resonance_gte","a_resonance_gte"):
            return int(state.runtime.get("current_absolute_resonance",{}).get(str(condition.get("sin")),0)) >= int(condition.get("value",0))
        if kind == "highest_resonance_gte": return max([int(x) for x in state.runtime.get("current_resonance",{}).values()] or [0]) >= int(condition.get("value",0))
        if kind in ("sin_resource_gte","sin_resource_lte"):
            cur=f.sin_resources.get(str(condition.get("sin")),0); val=int(condition.get("value",0)); return cur >= val if kind.endswith("gte") else cur <= val
        if kind in ("resource_gte","resource_lte"):
            cur=f.resources.get(str(condition.get("resource",condition.get("name",""))),0); val=int(condition.get("value",0)); return cur >= val if kind.endswith("gte") else cur <= val
        if kind == "status_threshold":
            target=e if condition.get("target","enemy")=="enemy" else f
            st=target.statuses.get(str(condition.get("name","")))
            if not st: return False
            field = condition.get("field","potency")
            current = state.runtime.get('virtual_bleed_count', st.count) if condition.get('name') == 'Bleed' and target is e and field == 'count' else getattr(st, field, 0)
            return float(current) >= int(condition.get("value",0))
        if kind == "negative_status_count_gte":
            target = e if condition.get("target", "enemy") == "enemy" else f
            count = len(target.statuses)
            return count >= int(condition.get("value", 0))
        if kind == "status":
            target=e if condition.get("target","enemy")=="enemy" else f; st=target.statuses.get(str(condition.get("name","")))
            if not st: return False
            effective_count = state.runtime.get('virtual_bleed_count', st.count) if condition.get('name') == 'Bleed' and target is e else st.count
            return ("potency_gte" not in condition or st.potency >= int(condition["potency_gte"])) and ("count_gte" not in condition or effective_count >= int(condition["count_gte"]))
        if kind == "not": return not self._condition_met(state,identity,condition.get("condition"),skill)
        composite = evaluate_composite_condition(
            condition, lambda child: self._condition_met(state, identity, child, skill)
        )
        if composite is not None: return composite
        if kind == "clash_result": return bool(skill and getattr(skill,"clash_result",None)==condition.get("value"))
        return False

    def _condition_effects(self, state, identity, skill, scenario):
        effects={"damage_bonus":0.0,"dynamic_damage_bonus":0.0,"static_damage_bonus":0.0,"coin_power_bonus":0,"attack_level_bonus":0}
        for rule in scenario.get("condition_effects",[]) or []:
            if self._condition_met(state,identity,rule.get("condition",{}),skill):
                for k in effects:
                    if k in rule.get("effects",{}): effects[k]+=rule["effects"][k]
        return effects

    @staticmethod
    def _apply_skill_modifiers(skill, mods):
        """Apply one-turn condition outcomes to a copied skill, never mutate catalog data."""
        if not any(mods.values()):
            return skill
        s = deepcopy(skill)
        s.damage_bonus += float(mods.get("damage_bonus", 0.0))
        s.dynamic_damage_bonus += float(mods.get("dynamic_damage_bonus", 0.0))
        s.static_damage_bonus += float(mods.get("static_damage_bonus", 0.0))
        s.coin_power_bonus += int(mods.get("coin_power_bonus", 0))
        s.offense_level_bonus += int(mods.get("attack_level_bonus", 0))
        return s

    @staticmethod
    def _active_passives(identity, mode="last"):
        """Select one catalog variant per passive name for execution.

        The catalog preserves upgraded/variant text as duplicate names. Running
        every duplicate simultaneously would double-apply passives. `last` is
        the default (latest/highest variant in the supplied catalog); `all` is
        available for raw-data diagnostics.
        """
        ps=list(getattr(identity,'passives',[]) or [])
        if mode == "all": return ps
        selected={}; order=[]
        for p in ps:
            name=str(p.get('name',''))
            if name not in selected: order.append(name)
            selected[name]=p
        return [selected[n] for n in order]

    @staticmethod
    def _build_passive_activation(scenario, identities):
        """Explicit user-controlled passive activation.

        Keys can be identity ids and values can be {passive_name: bool} or a
        list of enabled passive names.  This is deliberately an activation
        switch, not an attempt to infer preparation from prior turns.
        """
        raw = scenario.get("passive_activation", scenario.get("passive_overrides", {})) or {}
        gates = {}
        for iid, value in raw.items() if isinstance(raw, dict) else []:
            iid = str(iid)
            if isinstance(value, dict):
                for name, enabled in value.items():
                    gates[f"{iid}::{name}"] = {"enabled": bool(enabled)}
            elif isinstance(value, list):
                enabled_names = {str(x) for x in value}
                ident = identities.get(iid)
                for p in (getattr(ident, 'passives', []) if ident else []):
                    name = str(p.get('name',''))
                    if name: gates[f"{iid}::{name}"] = {"enabled": name in enabled_names}
        return gates

    @staticmethod
    def _apply_prepared_state(state, scenario):
        """Apply explicit pre-heated resources/statuses/flags without inference."""
        prep = (scenario.get("preparation", scenario) if isinstance(scenario, dict) else {}) or {}
        state.runtime["preparation"] = deepcopy(prep)
        flags = state.runtime.setdefault("condition_flags", {})
        for k,v in (prep.get("flags", {}) if isinstance(prep,dict) else {}).items():
            flags[str(k)] = bool(v)
        # Keep explicit preparation flags separate from derived runtime flags.
        for k,v in flags.items():
            state.runtime.setdefault('prepared_flags', {})[str(k)] = bool(v)
        # Optional named preparation levels are useful for UI display and
        # custom conditions, while actual resources remain the source of truth.
        state.runtime["preparation_levels"] = {
            str(k): v for k,v in (prep.get("levels", {}) if isinstance(prep,dict) else {}).items()
        }

    @staticmethod
    def _find_skill_by_name(ident, name):
        n=str(name).strip("'\"“”‘’ ")
        return next((x for x in ident.skills.values() if str(x.name)==n or n in str(x.name)), None)

    def _resolve_skill_transformation(self, state, ident, skill, action, resource_runtime=None):
        """Resolve explicit mid-turn [사용전] skill transformations.

        Common form: "[사용 전] 자원 X가 N 이상이면, '변형 스킬'로 발동".
        This is checked at action start, so resources accumulated by earlier
        actions in the same turn can complete the preparation and transform a
        later skill.  No preparation is inferred before the scenario begins.
        """
        # Turn-start revenge tattoo transformation. The passive is attached
        # to the turn-start state, so it must be checked before the generic
        # [사용 전] parser can return early for a skill without a resource
        # transformation clause.
        if any(ident.skills.get(slot) is skill or str(action.get('skill_id','')).upper() == slot for slot in ('S1','S2','S3')):
            tattoo_name = '원한 문신'
            owner_fighter = state.fighters.get(str(ident.id))
            tattoo = 0
            if owner_fighter is not None:
                tattoo = int(resource_runtime.get(owner_fighter, tattoo_name, 0)) if resource_runtime is not None else int(owner_fighter.resources.get(tattoo_name, 0))
                if tattoo == 0:
                    st = owner_fighter.statuses.get(tattoo_name)
                    if st is not None:
                        tattoo = int(getattr(st, 'count', 0) or getattr(st, 'potency', 0) or 0)
            if tattoo >= 15:
                target = self._find_skill_by_name(ident, '전원, 처형이다!!')
                if target is not None:
                    state.event_log.append({
                        'event':'skill_transformed', 'identity_id':str(ident.id),
                        'from_skill_id':skill.id, 'to_skill_id':target.id,
                        'resource':tattoo_name, 'value':tattoo, 'threshold':15,
                        'operator':'>=', 'reason':'turn_start_revenge_tattoo',
                    })
                    return target, {'resource':tattoo_name,'value':tattoo,'threshold':15,'operator':'>=','to_skill_id':target.id,'reason':'turn_start_revenge_tattoo'}
        text = " | ".join(getattr(skill, '_source_effects', []) or [])
        resource_runtime = resource_runtime or ResourceRuntime()
        resource_pattern='|'.join(re.escape(x) for x in sorted(SkillTextParserV19.SPECIAL_RESOURCE_NAMES, key=len, reverse=True))
        m = re.search(r"\[사용\s*전\].*?(" + resource_pattern + r")\s*(?:이|가|은|는)?\s*(\d+)\s*(?:이상(?:이면|일 때)?|이면|일 때).*?['‘’\"]([^'‘’\"]+)['‘’\"]\s*로\s*(?:발동|변경)", text)
        if not m:
            # Turn-start zero-resource variant, e.g. ammo absent -> alternate skill.
            zm = re.search(r"턴\s*시작\s*시\s*(" + resource_pattern + r")\s*(?:이|가|은|는)?\s*없(?:다면|으면|을 때).*?[\'‘’\"]([^\'‘’\"]+)[\'‘’\"]\s*로\s*(?:변경|발동)", text)
            if zm:
                resource = re.search(resource_pattern, zm.group(0)).group(0); target_name=zm.group(1); fighter=state.fighters[ident.id]
                current = resource_runtime.get(fighter, resource, 0) if resource not in ('충전','탄환','호흡') else (fighter.charge if resource=='충전' else fighter.ammo if resource=='탄환' else fighter.poise.potency)
                if current == 0:
                    target=self._find_skill_by_name(ident,target_name)
                    if target:
                        state.event_log.append({'event':'skill_transformed','identity_id':ident.id,'from_skill_id':skill.id,'to_skill_id':target.id,'resource':resource,'value':current,'threshold':0,'operator':'==','reason':'turn_start_zero_resource'})
                        return target, {'resource':resource,'value':current,'threshold':0,'operator':'==','to_skill_id':target.id}
            # Compact catalog form such as "[사용전] 새벽불이 30이면, '새벽녘'으로 발동됨".
            cm = re.search(r"\[사용\s*전\]\s*(" + resource_pattern + r").*?(\d+).*?['‘’\"]([^'‘’\"]+)['‘’\"]", text)
            if not cm:
                return skill, None
            resource, threshold, target_name = cm.group(1), int(cm.group(2)), cm.group(3)
        else:
            resource, threshold, target_name = m.group(1), int(m.group(2)), m.group(3)
        fighter=state.fighters[ident.id]
        if resource in ('충전','탄환'):
            current = fighter.charge if resource=='충전' else fighter.ammo
        elif resource=='호흡':
            current = fighter.poise.potency
        else:
            current = resource_runtime.get(fighter, resource, 0)
            st=fighter.statuses.get(resource)
            if st and current == 0:
                current=st.potency
        if current >= threshold:
            target=self._find_skill_by_name(ident,target_name)
            if target:
                state.event_log.append({'event':'skill_transformed','identity_id':ident.id,'from_skill_id':skill.id,'to_skill_id':target.id,'resource':resource,'value':current,'threshold':threshold})
                # Some catalog transformations explicitly consume the resource
                # used to unlock the alternate skill (e.g. "전부 소모하여").
                if re.search(r'전부\s*소모하여|전부\s*소모하고|모두\s*소모하여|모두\s*소모하고', text):
                    if resource not in ('충전','탄환','호흡'):
                        resource_runtime.consume(state.fighters[ident.id], resource, current, state=state, reason=f'transform:{skill.id}:consume_all')
                    elif resource=='충전':
                        before=state.fighters[ident.id].charge; state.fighters[ident.id].charge=0; state.event_log.append({'event':'resource_change','resource':'충전','delta':-before,'before':before,'after':0,'reason':f'transform:{skill.id}:consume_all'}); self._log_cumulative_consumption(state, ident.id, '충전', before, f'transform:{skill.id}:consume_all')
                    elif resource=='탄환':
                        before=state.fighters[ident.id].ammo; state.fighters[ident.id].ammo=0; state.event_log.append({'event':'resource_change','resource':'탄환','delta':-before,'before':before,'after':0,'reason':f'transform:{skill.id}:consume_all'})
                    elif resource=='호흡':
                        before=state.fighters[ident.id].poise.potency; state.fighters[ident.id].poise.potency=0; state.event_log.append({'event':'resource_change','resource':'호흡','delta':-before,'before':before,'after':0,'reason':f'transform:{skill.id}:consume_all'})
                return target, {'resource':resource,'value':current,'threshold':threshold,'to_skill_id':target.id}
        return skill, None

    @staticmethod
    def _bleed_head_probability(sp: float) -> float:
        # Clash coin face probability approximation used only by the
        # probabilistic Bleed mode. SP -45..45 maps to 5..95% heads.
        return max(0.0, min(1.0, 0.5 + float(sp) / 100.0))

    def _consume_probabilistic_clash_coin(self, state, identity, skill, coin_index, reason_prefix="probabilistic_clash"):
        """Consume attacker-side per-coin resources only when that clash coin is removed.

        A winning clash coin remains active and is therefore not consumed here; if it
        survives to the unopposed suffix, the normal coin executor consumes its
        resources exactly once. A loss/draw removes the coin from the clash, so its
        per-coin resource/ammo cost must be reflected in the branch state now.
        """
        if coin_index < 1 or coin_index > len(skill.coins):
            return {}
        fighter = state.fighters[identity.id]
        coin = skill.coins[coin_index - 1]
        rr = state.runtime.get('resource_runtime')
        changes = {}
        if rr is not None:
            for rname, amount in getattr(coin, 'resource_cost', {}).items():
                cur = rr.get(fighter, str(rname), 0)
                used = min(cur, int(amount))
                if used:
                    rr.consume(fighter, str(rname), used, state=state,
                               reason=f'{reason_prefix}:{skill.id}:{coin_index}:cost')
                    changes[str(rname)] = -used
            for rname, amount in getattr(coin, 'resource_cost_max', {}).items():
                cur = rr.get(fighter, str(rname), 0)
                used = min(cur, int(amount))
                if used:
                    rr.consume(fighter, str(rname), used, state=state,
                               reason=f'{reason_prefix}:{skill.id}:{coin_index}:cost_max')
                    changes[str(rname)] = changes.get(str(rname), 0) - used
            for rname in getattr(coin, 'resource_cost_all', []):
                cur = rr.get(fighter, str(rname), 0)
                if cur:
                    rr.consume(fighter, str(rname), cur, state=state,
                               reason=f'{reason_prefix}:{skill.id}:{coin_index}:cost_all')
                    changes[str(rname)] = changes.get(str(rname), 0) - cur
        ammo_spend = int(getattr(skill, 'coin_ammo_spend', {}).get(coin_index, 0))
        if ammo_spend:
            before = int(fighter.ammo)
            used = min(before, ammo_spend)
            fighter.ammo = before - used
            if used:
                state.event_log.append({'event':'probabilistic_clash_coin_ammo',
                    'identity_id':identity.id,'skill_id':skill.id,'coin_index':coin_index,
                    'ammo_before':before,'ammo_spent':used,'ammo_after':fighter.ammo})
                changes['탄환'] = changes.get('탄환', 0) - used
        return changes

    def _run_probabilistic_bleed_stateful(self, state, skill, clash_cfg, fighter, trigger_runtime_template, identity_map):
        """Stateful probabilistic Clash loop.

        Unlike the compact Bleed-only runtime, this version keeps a full branch-local
        BattleState after every Clash exchange.  ``after_clash`` triggers are fired
        immediately, so SP/resources/statuses/flags and generated actions can alter
        the probability of the next exchange.
        """
        defender_coins_raw = clash_cfg.get('coins', []) or []
        defender_coins = [CoinData(int(x.get('coin_power', 0)), ATK.get(x.get('damage_type','slash'), x.get('damage_type','slash')), SIN.get(x.get('sin',''), x.get('sin','')), unbreakable=bool(x.get('unbreakable', False))) for x in defender_coins_raw]
        normal0 = int(clash_cfg.get('initial_defender_coins', len(defender_coins)))
        ub0 = int(clash_cfg.get('defender_unbreakable_coins', sum(1 for c in defender_coins if c.unbreakable)))
        attacker0 = int(clash_cfg.get('initial_attacker_coins', len(skill.coins)))
        attacker_base = int(clash_cfg.get('attacker_base_power', skill.base_power))
        defender_base = int(clash_cfg.get('skill_power', 0))
        attacker_bonus = int(clash_cfg.get('attacker_clash_power_bonus', 0))
        defender_bonus = int(clash_cfg.get('defender_clash_power_bonus', 0))
        explicit = clash_cfg.get('outcome_probabilities')
        fighter_id = str(clash_cfg.get('_action_stub', {}).get('identity_id', ''))
        max_ex = min(int(clash_cfg.get('max_exchanges', 99)), 99)
        states = {(attacker0, normal0, ub0, 0, 0, 'START', probabilistic_state_signature(state)): 1.0}
        terminal_meta = {}
        terminal_states = {}
        exchange_dist = {}
        cap_mass = 0.0
        while states:
            nxt = {}
            for (a, nd, ub, ex, bleed, last, sig), mass in states.items():
                if mass <= 0: continue
                branch = deepcopy(state)
                restore_probabilistic_state_signature(branch, sig)
                active_d = nd + ub
                if a <= 0 or active_d <= 0 or ex >= max_ex:
                    key=(a,nd,ub,ex,bleed,last)
                    terminal_meta[key]=terminal_meta.get(key,0.0)+mass
                    terminal_states.setdefault(key, []).append((branch, mass))
                    exchange_dist[ex]=exchange_dist.get(ex,0.0)+mass
                    if ex>=max_ex: cap_mass += mass
                    continue
                idx = min(max(0, attacker0-a), max(0,len(skill.coins)-1))
                d_idx = min(max(0, normal0-nd), max(0,len(defender_coins)-1)) if defender_coins else 0
                ac = skill.coins[idx] if skill.coins else CoinData(0,'slash','')
                dc = defender_coins[d_idx] if defender_coins else CoinData(0,'slash','')
                ahp = self._bleed_head_probability(float(branch.fighters[fighter_id].sp))
                dhp = self._bleed_head_probability(float(branch.enemy.sp))
                if explicit is not None:
                    if isinstance(explicit,list) and explicit:
                        item=explicit[min(ex,len(explicit)-1)]
                    else: item=explicit
                    if isinstance(item,dict): probs=(float(item.get('win',0)),float(item.get('draw',0)),float(item.get('loss',0)))
                    else: probs=tuple(item)
                else:
                    probs={'win':0.0,'draw':0.0,'loss':0.0}
                    for ah,pa in ((True,ahp),(False,1-ahp)):
                        for dh,pd in ((True,dhp),(False,1-dhp)):
                            ap=attacker_base+(ac.coin_power if ah else 0)+attacker_bonus
                            dp=defender_base+(dc.coin_power if dh else 0)+defender_bonus
                            o='win' if ap>dp else 'loss' if ap<dp else 'draw'
                            probs[o]+=pa*pd
                    probs=(probs['win'],probs['draw'],probs['loss'])
                if max_ex==99 and ex+1==99: probs=(0.0,0.0,1.0)
                z=sum(max(0.0,float(x)) for x in probs) or 1.0
                probs=tuple(max(0.0,float(x))/z for x in probs)
                for outcome,prob in zip(('W','T','L'),probs):
                    if prob<=0: continue
                    bs=deepcopy(branch)
                    na,nn,nub=a,nd,ub
                    attacker_coin_index = min(max(1, attacker0 - a + 1), len(skill.coins)) if skill.coins else 1
                    if outcome=='W':
                        if nub>0: nub-=1
                        elif nn>0: nn-=1
                    elif outcome=='L':
                        na=max(0,na-1)
                        if skill.coins:
                            self._consume_probabilistic_clash_coin(bs, identity_map[fighter_id], skill, attacker_coin_index)
                    elif outcome=='T':
                        # Draw: neither side loses an active normal coin.
                        pass
                    nex=ex+1; nbleed=bleed+active_d
                    # Outcome-specific skill/passive effects and branch updates happen
                    # before the next probability calculation.  The deterministic engine
                    # already applies these in its Clash path; the probabilistic path must
                    # mirror them so a Clash Win/Lose effect can change the next exchange.
                    action_stub=dict(clash_cfg.get('_action_stub', {})); action_stub['identity_id']=fighter_id
                    clash_effects = skill.effects_on_clash_win if outcome == 'W' else (
                        skill.effects_on_clash_lose if outcome == 'L' else [])
                    for effect in clash_effects:
                        if self.core.machine.engine.condition_met(bs, identity_map[fighter_id], effect.get('condition'), skill):
                            self.core.machine.engine.apply_effect(bs, fighter_id, effect.get('target', 'self'), effect)
                    for p in getattr(identity_map[fighter_id], 'passives', []) or []:
                        trigger_name = 'Clash Win' if outcome == 'W' else ('Clash Lose' if outcome == 'L' else '')
                        if trigger_name and p.get('trigger') == trigger_name:
                            self.core.machine.engine.apply_trigger_effects(bs, identity_map[fighter_id], p.get('effects', []), skill)
                    self._apply_probabilistic_branch_updates(bs, skill, action_stub, outcome, apply_resources=False)
                    rt=deepcopy(trigger_runtime_template)
                    # Trigger max_activations is a turn/branch budget, not a
                    # per-Clash-exchange budget. Carry activation counters with
                    # the branch so a rule that already fired cannot silently
                    # fire again on the next Clash.
                    ctx={'identity_id':fighter_id,'skill_id':skill.id,'skill_name':str(skill.name),
                         'skill_slot':str(getattr(skill,'_slot','')),'event':'after_clash',
                         'outcome':outcome,'clash_outcome':outcome,'exchange_index':nex,
                         'attacker_coins':na,'defender_coins':nn+nub,'normal_defender_coins':nn,
                         'unbreakable_defender_coins':nub,'active_defender_coins':active_d,
                         'bleed_procs':active_d,'total_bleed':nbleed,'actual_damage':0.0,
                         'attacker_coin_index':attacker_coin_index, 'defender_coin_index':d_idx + 1,
                         # Only a loss removes the attacker's active coin.
                         # Draws leave both sides unchanged and must not consume
                         # an attacker coin before the next exchange.
                         'clash_coin_removed': outcome == 'L',
                         'action_start_staggered':bool(branch.enemy.staggered),
                         'action_end_staggered':bool(bs.enemy.staggered),
                         'condition_flags':bs.runtime.get('condition_flags',{}),
                         'available_identity_ids':list(identity_map.keys()),'generated':False}
                    fired=self._fire_probabilistic_trigger_event(rt, 'after_clash', ctx, bs)
                    queued=self._apply_probabilistic_trigger_effects(bs,fired,identity_map,fighter_id)
                    bs.runtime['probabilistic_trigger_max_depth']=int(clash_cfg.get('max_trigger_depth',16))
                    for gid,gskill in queued:
                        if gid in identity_map:
                            self._execute_probabilistic_generated_action(bs,rt,identity_map,gid,gskill,depth=1,
                                source_identity_id=fighter_id,source_skill_id=skill.id,trigger_chain=[])
                    nsig=probabilistic_state_signature(bs)
                    key=(na,nn,nub,nex,nbleed,outcome)
                    if na<=0 or nn+nub<=0 or nex>=max_ex:
                        terminal_meta[key]=terminal_meta.get(key,0.0)+mass*prob
                        # If the same compact key can be reached through different
                        # trigger-mutated states, retain each weighted state separately.
                        terminal_states.setdefault(key,[])
                        terminal_states[key].append((bs,mass*prob))
                        exchange_dist[nex]=exchange_dist.get(nex,0.0)+mass*prob
                        if nex>=max_ex: cap_mass += mass*prob
                    else:
                        skey=(na,nn,nub,nex,nbleed,outcome,nsig)
                        nxt[skey]=nxt.get(skey,0.0)+mass*prob
            states=nxt
        total=sum(terminal_meta.values()) or 1.0
        terminal_meta={k:v/total for k,v in terminal_meta.items()}
        for k,v in list(terminal_states.items()):
            if isinstance(v,list):
                sm=sum(m for _,m in v) or 1.0
                terminal_states[k]=[(st,m/sm) for st,m in v]
        return {'mode':'probabilistic_stateful','initial_attacker_coins':attacker0,
                'initial_defender_coins':normal0+ub0,'initial_defender_normal_coins':normal0,
                'initial_defender_unbreakable_coins':ub0,'max_exchanges':max_ex,
                'probability_reaching_99_exchanges':cap_mass/total if max_ex==99 else 0.0,
                '_terminal_meta':terminal_meta,'_terminal_states':terminal_states,
                'exchange_count_distribution':{k:v/total for k,v in exchange_dist.items()}}

    def _run_probabilistic_bleed(self, state, skill, clash_cfg, fighter):
        """Run expected Clash/ Bleed estimation for one requested action.

        The probability model uses the active coin pair at each exchange.
        Users may override it with explicit per-state W/T/L probabilities;
        otherwise the engine derives probabilities from SP and H/T coin powers.
        This layer estimates Bleed state for subsequent actions; it does not
        branch the whole one-turn damage simulation.
        """
        defender_coins_raw = clash_cfg.get('coins', []) or []
        defender_coins = [CoinData(int(x.get('coin_power', 0)), ATK.get(x.get('damage_type','slash'), x.get('damage_type','slash')), SIN.get(x.get('sin',''), x.get('sin','')), unbreakable=bool(x.get('unbreakable', False))) for x in defender_coins_raw]
        defender_count = int(clash_cfg.get('initial_defender_coins', len(defender_coins)))
        ub = int(clash_cfg.get('defender_unbreakable_coins', sum(1 for c in defender_coins if c.unbreakable)))
        attacker_count = int(clash_cfg.get('initial_attacker_coins', len(skill.coins)))
        attacker_base = int(clash_cfg.get('attacker_base_power', skill.base_power))
        defender_base = int(clash_cfg.get('skill_power', 0))
        attacker_bonus = int(clash_cfg.get('attacker_clash_power_bonus', 0))
        defender_bonus = int(clash_cfg.get('defender_clash_power_bonus', 0))
        explicit = clash_cfg.get('outcome_probabilities')
        attacker_sp = float(clash_cfg.get('attacker_sp', fighter.sp))
        defender_sp = float(clash_cfg.get('defender_sp', state.enemy.sp))
        p_ah = self._bleed_head_probability(attacker_sp)
        p_dh = self._bleed_head_probability(defender_sp)
        initial_a, initial_d = attacker_count, defender_count

        def probability_fn(ctx):
            if explicit is not None:
                if isinstance(explicit, list) and explicit:
                    item = explicit[min(int(ctx['exchange_index'])-1, len(explicit)-1)]
                    if isinstance(item, dict):
                        return (float(item.get('win', 0)), float(item.get('draw', 0)), float(item.get('loss', 0)))
                    return tuple(item)
            a_left=int(ctx['attacker_coins']); d_left=int(ctx['defender_coins'])
            ai=max(0, initial_a-a_left); di=max(0, initial_d-d_left)
            ac=skill.coins[min(ai, len(skill.coins)-1)]
            if defender_coins:
                dc=defender_coins[min(di, len(defender_coins)-1)]
            else:
                dc=CoinData(0, 'slash', '')
            probs={'win':0.0,'draw':0.0,'loss':0.0}
            for ah, pa in ((True,p_ah),(False,1-p_ah)):
                for dh, pd in ((True,p_dh),(False,1-p_dh)):
                    ap=attacker_base + (ac.coin_power if ah else 0) + attacker_bonus
                    dp=defender_base + (dc.coin_power if dh else 0) + defender_bonus
                    o='win' if ap>dp else 'loss' if ap<dp else 'draw'
                    probs[o]+=pa*pd
            return (probs['win'], probs['draw'], probs['loss'])

        result=self.bleed_probability_runtime.resolve(attacker_count, defender_count, probability_fn, defender_unbreakable_coins=ub, max_exchanges=int(clash_cfg.get('max_exchanges',99)))
        # This helper remains useful for per-action diagnostics, but the
        # authoritative 5%/5% trimming for a one-turn calculation is performed
        # only once by _probabilistic_turn_state at turn end.
        result['trim_scope'] = 'action_local_diagnostic_only'
        result['mode']='probabilistic'
        result['attacker_sp']=attacker_sp; result['defender_sp']=defender_sp
        return result

    def _expected_probabilistic_clash_damage(self, state, identity, skill, faces, probability_result, is_crit=False):
        """Estimate direct coin damage across the terminal Clash distribution.

        This is deliberately an action-local expectation: the existing solver
        still executes the user-selected Clash normally, while probabilistic
        mode additionally reports the damage expectation implied by its
        W/T/L terminal states.  A terminal state with defender coins at zero
        is a Clash win; only the attacker's coins remaining after losses become
        unopposed.  A lost Clash deals no ordinary attacker damage.
        """
        terminal_meta = probability_result.get('_terminal_meta', {})
        if not terminal_meta:
            return {'expected_damage': 0.0, 'raw_expected_damage': 0.0,
                    'trimmed_expected_damage': 0.0, 'terminal_damage_distribution': {}}
        # terminal_meta keys: (attacker_left, normal_defender_left,
        # unbreakable_left, exchanges, total_bleed), values are probabilities.
        raw_mass = sum(float(v) for v in terminal_meta.values())
        if raw_mass <= 0:
            return {'expected_damage': 0.0, 'raw_expected_damage': 0.0,
                    'trimmed_expected_damage': 0.0, 'terminal_damage_distribution': {}}
        dist = {}
        for key, mass in terminal_meta.items():
            attacker_left, normal_d, ub, _ex, _bleed, _outcome = key
            prob = float(mass) / raw_mass
            defender_left = int(normal_d) + int(ub)
            if defender_left > 0 or int(attacker_left) <= 0:
                dmg = 0.0
            else:
                # Every loss consumes the current attacker coin; ties/wins
                # keep it in play. Thus the surviving suffix starts at the
                # number of losses = initial attacker coins - attacker_left.
                initial_attacker = int(probability_result.get('initial_attacker_coins', len(skill.coins)))
                losses = max(0, initial_attacker - int(attacker_left))
                start = min(max(0, losses), len(skill.coins))
                clone = deepcopy(state)
                clone.runtime['special_after_coin'] = None
                resolved = deepcopy(skill)
                resolved.clash_result = 'win'
                before_hp = clone.enemy.hp
                clone, _dmg, _trace = self._execute_unopposed_coins_with_triggers(
                    clone, identity, resolved, faces, start, bool(is_crit),
                    source_identity_id=identity.id, source_skill_id=skill.id, depth=1)
                if clone.enemy.hp > 0:
                    for effect in getattr(resolved, 'effects_on_hit', []) or []:
                        if self.core.machine.engine.condition_met(clone, identity, effect.get('condition'), resolved):
                            self.core.machine.engine.apply_effect(clone, identity.id, effect.get('target', 'self'), effect)
                dmg = float(before_hp - clone.enemy.hp)
            dist[dmg] = dist.get(dmg, 0.0) + prob
        raw_expected = sum(float(d) * float(p) for d, p in dist.items())
        trimmed_expected = self.bleed_probability_runtime._trimmed_mean(dist)
        return {'expected_damage': trimmed_expected, 'raw_expected_damage': raw_expected,
                'trimmed_expected_damage': trimmed_expected,
                'terminal_damage_distribution': dict(sorted(dist.items()))}

    @staticmethod
    def _apply_bleed_proc_count(state, procs, infinite=False, expected=False):
        st=state.enemy.statuses.get('Bleed')
        if not st or infinite or procs <= 0:
            return {'before': int(st.count) if st else 0, 'consumed': 0.0, 'after': int(st.count) if st else 0}
        before=float(st.count)
        consumed=min(before, float(procs))
        if expected:
            # Keep fractional expectation in runtime while retaining the real
            # status object as an integer game-state value.
            remaining=max(0.0, before-consumed)
            state.runtime['virtual_bleed_count']=remaining
            st.count=int(remaining)
        else:
            consumed_i=int(consumed)
            st.count-=consumed_i
            if st.count<=0: state.enemy.statuses.pop('Bleed',None)
        return {'before':before,'consumed':consumed,'after':float(st.count) if st else 0.0}

    @staticmethod
    def _log_cumulative_consumption(state, identity_id, resource, amount, reason='consume'):
        amount=int(amount)
        if amount <= 0: return
        bucket=state.runtime.setdefault('cumulative_resource_consumed', {})
        key=(str(identity_id),str(resource)); before=int(bucket.get(key,0)); after=before+amount; bucket[key]=after
        state.event_log.append({'event':'resource_cumulative_consumed','identity_id':str(identity_id),'resource':str(resource),'amount':amount,
                                'cumulative_before':before,'cumulative_after':after,'reason':reason})

    @staticmethod
    def _apply_probabilistic_branch_updates(branch_state, skill, action, outcome, *, apply_resources=True):
        """Apply per-action resource changes and optional W/T/L SP deltas.

        Resource costs/gains are applied once for the action. SP deltas are
        applied after the Clash result so the next requested action observes
        the branch-specific SP. If no explicit SP delta map is supplied, SP is
        left unchanged in the probabilistic layer rather than inventing a
        hidden approximation.
        """
        rr = branch_state.runtime.get('resource_runtime')
        fighter = branch_state.fighters[str(action['identity_id'])]
        if apply_resources and rr is not None:
            for rname, amount in getattr(skill, 'resource_cost', {}).items():
                if str(rname).lower() == 'sp':
                    continue
                rr.change(fighter, str(rname), -int(amount), branch_state,
                          reason=f'probabilistic_skill:{skill.id}:cost')
            for rname, amount in getattr(skill, 'resource_gain', {}).items():
                if str(rname).lower() == 'sp':
                    continue
                rr.change(fighter, str(rname), int(amount), branch_state,
                          reason=f'probabilistic_skill:{skill.id}:gain')
            for rname, amount in getattr(skill, 'resource_cost_max', {}).items():
                if str(rname).lower() == 'sp':
                    continue
                cur = rr.get(fighter, str(rname), 0)
                rr.change(fighter, str(rname), -min(cur, int(amount)), branch_state,
                          reason=f'probabilistic_skill:{skill.id}:cost_max')
            for rname in getattr(skill, 'resource_cost_all', []):
                if str(rname).lower() == 'sp':
                    continue
                cur = rr.get(fighter, str(rname), 0)
                rr.change(fighter, str(rname), -cur, branch_state,
                          reason=f'probabilistic_skill:{skill.id}:cost_all')

        sp_cfg = action.get('sp_delta_by_outcome', {})
        if isinstance(sp_cfg, dict):
            raw = sp_cfg.get(outcome, sp_cfg.get(outcome.lower(), 0))
            if isinstance(raw, dict):
                ad = float(raw.get('attacker', 0))
                dd = float(raw.get('defender', 0))
            else:
                ad = float(raw or 0)
                dd = 0.0
            fighter.sp = max(-45, min(45, int(round(getattr(fighter, 'sp', 0) + ad))))
            branch_state.enemy.sp = max(-45, min(45, int(round(getattr(branch_state.enemy, 'sp', 0) + dd))))

    def _fire_probabilistic_trigger_event(self, runtime, event, ctx, state):
        """Execute migration-safe branch rules through the common Rule IR runtime."""
        if runtime is None:
            return []
        # The probability solver now owns its own trigger runtime. Keep this
        # direct path so generated-action tests and branch-local monkeypatches
        # observe exactly the same runtime object that the branch owns.
        if isinstance(runtime, ProbabilisticTriggerRuntime):
            exec_ctx = dict(ctx or {})
            exec_ctx['state'] = state
            exec_ctx.setdefault('owner_id', exec_ctx.get('identity_id', ''))
            exec_ctx.setdefault('actor', state.fighters.get(str(exec_ctx.get('identity_id', ''))))
            exec_ctx.setdefault('enemy', state.enemy)
            fired = runtime.fire(event, exec_ctx)
            return fired
        migration = RuleMigrationRuntime()
        safe, deferred = migration.partition(runtime.rules, event)
        # Production activation ownership lives on TurnState.activation_ledger.
        # No rule counters are restored into execution state here.
        exec_ctx = dict(ctx or {})
        exec_ctx['state'] = state
        exec_ctx.setdefault('owner_id', exec_ctx.get('identity_id', ''))
        exec_ctx.setdefault('actor', state.fighters.get(str(exec_ctx.get('identity_id', ''))))
        exec_ctx.setdefault('enemy', state.enemy)
        fired = []
        if safe:
            fired.extend(migration.fire_migrated(safe, event, exec_ctx))

        # Deferred/specialized probability rules are handled by a branch-local
        # probabilistic runtime. It preserves activation counters across deepcopy
        # without executing the retired TriggerRuntime.
        if deferred:
            branch_runtime = state.runtime.get('probabilistic_deferred_trigger_runtime')
            if branch_runtime is None:
                branch_runtime = ProbabilisticTriggerRuntime(deferred, getattr(state, "activation_ledger", None))
                state.runtime['probabilistic_deferred_trigger_runtime'] = branch_runtime
            fired.extend(branch_runtime.fire(event, exec_ctx))
        elif not safe:
            # Empty/compatibility runtime supplied by isolated tests. Convert its
            # rules into the new branch runtime rather than invoking Legacy.
            branch_runtime = state.runtime.get('probabilistic_deferred_trigger_runtime')
            if branch_runtime is None:
                branch_runtime = ProbabilisticTriggerRuntime(getattr(runtime, 'rules', []) or [], getattr(state, "activation_ledger", None))
                state.runtime['probabilistic_deferred_trigger_runtime'] = branch_runtime
            fired.extend(branch_runtime.fire(event, exec_ctx))

        return fired

    @staticmethod
    def _probabilistic_trigger_runtime(raw_rules):
        rules=[]
        for raw in raw_rules or []:
            if not isinstance(raw, dict) or not raw.get('id') or not raw.get('event'):
                continue
            conditions=[TriggerCondition(str(c.get('type')), c.get('value'), c.get('field'), bool(c.get('negate',False)))
                        for c in (raw.get('conditions') or []) if isinstance(c,dict) and c.get('type')]
            effects=[TriggerEffect(str(e.get('type')), {k:v for k,v in e.items() if k!='type'})
                     for e in (raw.get('effects') or []) if isinstance(e,dict) and e.get('type')]
            rules.append(TriggerRule(str(raw['id']), str(raw.get('owner_id','scenario')), str(raw['event']),
                                     conditions, effects, int(raw.get('max_activations',1)), 0,
                                     str(raw.get('source_text','scenario trigger')), dict(raw.get('metadata',{}))))
        return ProbabilisticTriggerRuntime(rules)

    def _fire_probabilistic_hit_triggers(self, branch_state, runtime, identity_map, identity, skill,
                                         coin_index, actual_damage, *, generated=False,
                                         source_identity_id='', source_skill_id=''):
        """Fire the explicit after_hit event immediately after a damaging coin.

        This is intentionally separate from after_coin: after_hit means the coin actually
        dealt damage, while after_coin is a post-coin lifecycle hook that may also run for
        zero-damage coins.  Keeping both events preserves the ordering needed by status
        conditions and subsequent coins/actions.
        """
        if runtime is None or float(actual_damage) <= 0:
            return []
        enemy_statuses = {k: v.__dict__.copy() for k,v in getattr(branch_state.enemy, 'statuses', {}).items()}
        self_statuses = {k: v.__dict__.copy() for k,v in branch_state.fighters[identity.id].statuses.items()}
        ctx = {
            'identity_id': identity.id, 'owner_id': identity.id, 'skill_id': skill.id,
            'skill_name': str(skill.name), 'skill_slot': str(getattr(skill, '_slot', '')),
            'coin_index': int(coin_index), 'actual_damage': float(actual_damage),
            'generated': bool(generated), 'statuses': self_statuses,
            'enemy_statuses': enemy_statuses, 'status_target': 'enemy',
            'enemy_hp': float(branch_state.enemy.hp),
            'enemy_max_hp': float(getattr(branch_state.enemy, 'max_hp', getattr(branch_state.enemy, 'hp', 0))),
            'self_hp': float(getattr(branch_state.fighters[identity.id], 'hp', 0)),
            'self_max_hp': float(getattr(branch_state.fighters[identity.id], 'max_hp', getattr(branch_state.fighters[identity.id], 'hp', 0))),
            'condition_flags': branch_state.runtime.get('condition_flags', {}),
            'available_identity_ids': list(identity_map.keys()),
            'source_identity_id': source_identity_id, 'source_skill_id': source_skill_id,
        }
        fired = self._fire_probabilistic_trigger_event(runtime, 'after_hit', ctx, branch_state)
        queued=[]
        for item in fired:
            eff=item.get('effect',{})
            if eff.get('type') == 'extra_damage_scale':
                eff=dict(eff); eff['base_damage']=float(actual_damage)
                item=dict(item); item['effect']=eff
            queued.extend(self._apply_probabilistic_trigger_effects(branch_state,[item],identity_map,identity.id))
        return queued

    def _apply_probabilistic_trigger_effects(self, branch_state, fired, identity_map, source_identity_id):
        queued=[]
        for item in fired:
            eff=item.get('effect',{}); et=eff.get('type')
            if et=='set_flag':
                branch_state.runtime.setdefault('condition_flags',{})[str(eff.get('flag',''))]=bool(eff.get('value',True))
            elif et in ('sp_set','set_sp','sp_delta'):
                target=str(eff.get('identity_id') or item.get('owner_id') or source_identity_id)
                if target in branch_state.fighters:
                    f=branch_state.fighters[target]
                    if et in ('sp_set','set_sp'):
                        f.sp=max(-45,min(45,int(eff.get('value',0))))
                    else:
                        f.sp=max(-45,min(45,int(round(f.sp+float(eff.get('amount',eff.get('delta',0)))))))
            elif et=='enemy_sp_set':
                branch_state.enemy.sp=max(-45,min(45,int(eff.get('value',0))))
            elif et=='enemy_sp_delta':
                branch_state.enemy.sp=max(-45,min(45,int(round(branch_state.enemy.sp+float(eff.get('amount',eff.get('delta',0)))))))
            elif et in ('resource_gain','resource_consume','resource_set'):
                target=str(eff.get('identity_id') or item.get('owner_id') or source_identity_id)
                if target not in branch_state.fighters: continue
                f=branch_state.fighters[target]; resource=str(eff.get('resource',''))
                rr=branch_state.runtime.get('resource_runtime')
                if et=='resource_gain':
                    amount=int(eff.get('amount',0))
                    if rr: rr.gain(f,resource,amount,state=branch_state,reason=f'prob_trigger:{item.get("rule_id")}')
                    else: f.resources[resource]=f.resources.get(resource,0)+amount
                elif et=='resource_consume':
                    amount=int(eff.get('amount',0))
                    if rr: rr.consume(f,resource,amount,state=branch_state,reason=f'prob_trigger:{item.get("rule_id")}')
                    else: f.resources[resource]=max(0,f.resources.get(resource,0)-amount)
                else:
                    f.resources[resource]=int(eff.get('value',0))
            elif et=='extra_damage_scale':
                scale=float(eff.get('scale',0.0))
                base=float(eff.get('base_damage',0.0))
                extra_now=min(int(base*scale+0.5), max(0.0, float(branch_state.enemy.hp)))
                if extra_now>0:
                    branch_state.enemy.hp-=extra_now
                    branch_state.turn_damage += extra_now
            elif et in ('add_status','status_add','remove_status','status_remove'):
                target=str(eff.get('target','enemy'))
                statuses=branch_state.enemy.statuses if target in ('enemy','target') else branch_state.fighters.get(target, branch_state.fighters[source_identity_id]).statuses
                name=str(eff.get('status',eff.get('name','')))
                if et in ('remove_status','status_remove'): statuses.pop(name,None)
                else: self.core.engine.apply_status(statuses,name,int(eff.get('potency',0)),int(eff.get('count',0)))
            elif et=='queue_action':
                target=str(eff.get('identity_id',''))
                if target in identity_map:
                    ident = identity_map[target]
                    skill_id = eff.get('skill_id')
                    sk = None
                    if skill_id is not None and hasattr(ident, 'skills'):
                        sk = ident.skills.get(str(skill_id))
                    if sk is None:
                        sk=self._find_skill_by_name(ident, eff.get('skill_name',''))
                    if sk: queued.append((target,sk))
        return queued

    def _execute_probabilistic_generated_action(self, branch_state, runtime, identity_map,
                                                   gid, gskill, *, depth=1,
                                                   source_identity_id='', source_skill_id='',
                                                   trigger_chain=None):
        """Execute a generated action using the shared coin lifecycle."""
        max_depth = int(branch_state.runtime.get('probabilistic_trigger_max_depth', 16))
        if depth > max_depth or gid not in identity_map or branch_state.enemy.hp <= 0:
            return 0.0, []
        gident = identity_map[gid]
        resolved = deepcopy(gskill)
        resolved.clash_result = 'win'
        if hasattr(self.core, 'apply_skill_sp'):
            self.core.apply_skill_sp(branch_state, gident, resolved, reason=f'generated:{resolved.id}')
        else:
            rg = getattr(resolved, 'resource_gain', {}) or {}
            rc = getattr(resolved, 'resource_cost', {}) or {}
            sp_gain = int(rg.get('SP', rg.get('sp', 0)))
            sp_cost = int(rc.get('SP', rc.get('sp', 0)))
            if hasattr(branch_state.fighters[gid], 'sp'):
                branch_state.fighters[gid].sp = max(-45, min(45, int(branch_state.fighters[gid].sp) - sp_cost + sp_gain))
        self._apply_probabilistic_branch_updates(
            branch_state, resolved, {'identity_id': gid}, 'W', apply_resources=True)
        for effect in (getattr(resolved, 'effects_before_use', []) or []) + (getattr(resolved, 'effects_on_use', []) or []):
            if self.core.machine.engine.condition_met(branch_state, gident, effect.get('condition'), resolved):
                self.core.machine.engine.apply_effect(branch_state, gid, effect.get('target', 'self'), effect)

        trace = []
        self_damage = 0.0
        before_snapshots = {}
        reuse_counts = {}

        def before_coin(c):
            before_snapshots[c.coin_index] = {
                'ammo': int(getattr(c.state.fighters[gid], 'ammo', 0)),
                'stagger_level': int(c.state.enemy.stagger_level),
                'stagger_index': int(c.state.enemy.stagger_index),
            }

        def on_coin(c):
            nonlocal self_damage
            snap = before_snapshots.get(c.coin_index, {})
            stagger_before = int(snap.get('stagger_level', 0))
            stagger_index_before = int(snap.get('stagger_index', 0))
            ammo_before = int(snap.get('ammo', 0))
            coin_damage = c.coin_damage

            hit_queued = self._fire_probabilistic_hit_triggers(
                c.state, runtime, identity_map, gident, resolved, c.coin_index, coin_damage,
                generated=True, source_identity_id=source_identity_id, source_skill_id=source_skill_id)
            for hgid, hgskill in hit_queued:
                if hgid in identity_map:
                    child_damage, child_trace = self._execute_probabilistic_generated_action(
                        c.state, runtime, identity_map, hgid, hgskill, depth=depth + 1,
                        source_identity_id=gid, source_skill_id=resolved.id, trigger_chain=[])
                    self_damage += float(child_damage)
                    trace.extend(child_trace)

            stagger_queued, _ = self._fire_probabilistic_stagger_triggers(
                c.state, runtime, identity_map, gid, resolved,
                before_level=stagger_before, before_index=stagger_index_before,
                actual_damage=coin_damage, generated=True,
                source_identity_id=source_identity_id, source_skill_id=source_skill_id, depth=depth)
            for sgid, sgskill in stagger_queued:
                if sgid in identity_map:
                    child_damage, child_trace = self._execute_probabilistic_generated_action(
                        c.state, runtime, identity_map, sgid, sgskill, depth=depth + 1,
                        source_identity_id=gid, source_skill_id=resolved.id, trigger_chain=[])
                    self_damage += float(child_damage)
                    trace.extend(child_trace)

            ammo_after = int(getattr(c.state.fighters[gid], 'ammo', 0))
            coin_ctx = {
                'identity_id': gid, 'skill_id': resolved.id,
                'skill_name': str(resolved.name), 'skill_slot': str(getattr(resolved, '_slot', '')),
                'coin_index': c.coin_index, 'actual_damage': coin_damage,
                'ammo_before': ammo_before, 'ammo_after': ammo_after,
                'ammo_spent': max(0, ammo_before-ammo_after),
                'is_lowest_ammo_identity': c.state.runtime.get('ammo_min_identity') == gid,
                'statuses': {k:v.__dict__.copy() for k,v in c.state.fighters[gid].statuses.items()},
                'condition_flags': c.state.runtime.get('condition_flags',{}),
                'available_identity_ids': list(identity_map.keys()), 'generated': True,
            }
            fired_coin = self._fire_probabilistic_trigger_event(runtime, 'after_coin', coin_ctx, c.state)
            BuffDebuffEventBridge.dispatch(c.state, event='after_coin', target_id=str(gid), context=coin_ctx)
            for item in fired_coin:
                eff = item.get('effect', {})
                if eff.get('type') == 'extra_damage_scale':
                    eff = dict(eff); eff['base_damage'] = coin_damage
                    item = dict(item); item['effect'] = eff
                self._apply_probabilistic_trigger_effects(c.state, [item], identity_map, gid)
            trace.append({'depth': depth, 'identity_id': gid, 'skill_id': resolved.id,
                          'coin_index': c.coin_index, 'damage': coin_damage,
                          'trigger_count': len(fired_coin)})

        def on_skill(c, skill_damage):
            # Skill-level on-hit effects happen after the complete coin sequence.
            if c.state.enemy.hp > 0:
                for effect in (getattr(resolved, 'effects_on_hit', []) or []):
                    if self.core.machine.engine.condition_met(c.state, gident, effect.get('condition'), resolved):
                        self.core.machine.engine.apply_effect(c.state, gid, effect.get('target', 'self'), effect)
            if c.state.enemy.hp <= 0:
                return 0.0
            skill_ctx = {
                'identity_id': gid, 'skill_id': resolved.id,
                'skill_name': str(resolved.name), 'skill_slot': str(getattr(resolved, '_slot', '')),
                'action_start_staggered': False,
                'action_end_staggered': bool(c.state.enemy.staggered),
                'action_start_hp': float(c.hp_before), 'action_end_hp': float(c.state.enemy.hp),
                'actual_damage': skill_damage, 'generated': True,
                'condition_flags': c.state.runtime.get('condition_flags',{}),
                'available_identity_ids': list(identity_map.keys()),
            }
            extra = 0.0
            fired_skill = self._fire_probabilistic_trigger_event(runtime, 'after_skill', skill_ctx, c.state)
            BuffDebuffEventBridge.dispatch(c.state, event='after_skill', target_id=str(gid), context=skill_ctx)
            for item in fired_skill:
                eff = item.get('effect', {})
                if eff.get('type') != 'queue_action':
                    before = float(c.state.enemy.hp)
                    self._apply_probabilistic_trigger_effects(c.state, [item], identity_map, gid)
                    extra += max(0.0, before - float(c.state.enemy.hp))
                    continue
                target = str(eff.get('identity_id',''))
                if target not in identity_map:
                    continue
                nxt = self._find_skill_by_name(identity_map[target], eff.get('skill_name', eff.get('skill_id','')))
                if not nxt:
                    continue
                child_damage, child_trace = self._execute_probabilistic_generated_action(
                    c.state, runtime, identity_map, target, nxt, depth=depth+1,
                    source_identity_id=gid, source_skill_id=resolved.id,
                    trigger_chain=list(trigger_chain or [])+[f'{gid}:{resolved.id}'])
                extra += float(child_damage)
                trace.extend(child_trace)
            return extra

        def reuse_condition(c, condition):
            return self.core.machine.engine.condition_met(c.state, gident, condition, resolved)

        core = CoinExecutionCore(self.core.machine.engine.simulate_coin)
        _, damage, _ = core.execute(
            CoinExecutionContext(branch_state, gident, resolved, ['H'] * len(resolved.coins), 0, False,
                                 True, source_identity_id, source_skill_id, depth, reuse_counts=reuse_counts),
            on_coin=on_coin, on_skill=on_skill, reuse_condition=reuse_condition,
            before_coin=before_coin)
        # Core damage already includes all child actions because they mutate the
        # same branch state.  Keep attribution separately for generated sources.
        id_map = branch_state.runtime.setdefault('probabilistic_generated_damage_by_identity', {})
        sk_map = branch_state.runtime.setdefault('probabilistic_generated_damage_by_skill', {})
        id_map[gid] = float(id_map.get(gid, 0.0)) + float(damage)
        sk_key = f'{gid}:{resolved.id}'
        sk_map[sk_key] = float(sk_map.get(sk_key, 0.0)) + float(damage)
        return damage, trace

    def _probabilistic_turn_state(self, state, scenario, identity_map, actions_out):
        """Carry Bleed + SP + special-resource state across the requested turn.

        Equivalent states are merged.  The authoritative deterministic solver
        remains unchanged; this parallel layer is used only for probabilistic
        Clash expectation.  Current state axes are Bleed Count, enemy HP/Stagger/statuses, and each ally's
        SP/resources/charge/ammo/poise/statuses.
        """
        initial = state.enemy.statuses.get('Bleed')
        initial_count = int(initial.count) if initial else 0
        has_prob = any(isinstance(a.get('bleed_clash_probability'), dict) for a in scenario.get('actions', []))
        if not has_prob:
            return None
        trigger_runtime_template = self._probabilistic_trigger_runtime(scenario.get('trigger_rules', []))
        state.runtime['probabilistic_trigger_runtime_template'] = trigger_runtime_template
        state.runtime['probabilistic_identity_map'] = identity_map
        state.runtime.setdefault('probabilistic_generated_damage_by_identity', {})
        state.runtime.setdefault('probabilistic_generated_damage_by_skill', {})
        initial_sig = probabilistic_state_signature(state)
        distribution = {(max(0, initial_count), initial_sig, 0): 1.0}
        total_damage = 0.0
        # Probability-weighted cumulative damage moments keyed by the exact
        # probabilistic state. This preserves correlation between total Bleed
        # procs and total turn damage without enumerating a separate damage axis.
        damage_moment = {(max(0, initial_count), initial_sig, 0): 0.0}
        identity_damage = {}
        skill_damage = {}
        trace = []
        for ai, action in enumerate(scenario.get('actions', []), 1):
            incoming = dict(distribution)
            pcfg = action.get('bleed_clash_probability')
            outgoing = {}
            expected_damage = 0.0
            branch_rows = []
            if not isinstance(pcfg, dict):
                # Deterministic explicit Clash actions consume Bleed but do not
                # introduce a new probabilistic branch. State axes are carried.
                proc_count = 0
                co = action.get('clash') or {}
                outcomes = co.get('exchange_outcomes') if isinstance(co, dict) else None
                if outcomes is not None:
                    d = int(co.get('initial_defender_coins', len(co.get('coins') or [])))
                    for raw in outcomes:
                        if d <= 0:
                            break
                        proc_count += d
                        if str(raw).upper() == 'W':
                            d = max(0, d - 1)
                for (bleed, sig, proc_total), mass in incoming.items():
                    ns = deepcopy(state)
                    restore_probabilistic_state_signature(ns, sig)
                    next_bleed = bleed if bool(scenario.get('bleed_count_infinite', False)) else max(0, bleed - proc_count)
                    out_sig = probabilistic_state_signature(ns)
                    out_key = (next_bleed, out_sig, int(proc_total + proc_count))
                    outgoing[out_key] = outgoing.get(out_key, 0.0) + mass
                    damage_moment[out_key] = damage_moment.get(out_key, 0.0) + damage_moment.get((bleed, sig, proc_total), 0.0) + mass * float(0.0)
                deterministic_damage = 0.0
                for row in actions_out:
                    if row.get('requested_index') == ai-1 and not row.get('generated', False):
                        deterministic_damage = float(row.get('expected_damage', row.get('damage', 0.0)))
                        break
                # Add the deterministic action's damage to every outgoing
                # branch in proportion to its branch mass.
                for out_key, out_mass in list(outgoing.items()):
                    if out_key[2] >= 0:
                        # This action has a single deterministic proc increment;
                        # each produced mass corresponds to one incoming branch.
                        damage_moment[out_key] = damage_moment.get(out_key, 0.0) + float(out_mass) * float(deterministic_damage)
                expected_damage = deterministic_damage
                iid0 = str(action.get('identity_id', ''))
                if iid0:
                    identity_damage[iid0] = identity_damage.get(iid0, 0.0) + expected_damage
                    sk0 = f'{iid0}:{action.get("skill_id", "")}'
                    skill_damage[sk0] = skill_damage.get(sk0, 0.0) + expected_damage
                distribution = self._normalize_probabilistic_state_distribution(outgoing)
                trace.append({'action_index': ai, 'incoming_distribution': self._collapse_bleed_distribution(incoming),
                              'outgoing_distribution': self._collapse_bleed_distribution(distribution),
                              'expected_damage': expected_damage, 'branch_count': 0, 'mode': 'deterministic'})
                total_damage += expected_damage
                continue

            iid = str(action['identity_id'])
            ident = identity_map[iid]
            base_skill = self._skill(ident, action['skill_id'])
            infinite = bool(scenario.get('bleed_count_infinite', False) or pcfg.get('bleed_count_infinite', False))
            faces = [str(x).upper() for x in (action.get('faces') if action.get('faces') is not None else ['H'] * len(base_skill.coins))]
            for (incoming_count, sig, proc_total_before), state_mass in incoming.items():
                branch_state = deepcopy(state)
                restore_probabilistic_state_signature(branch_state, sig)
                bst = branch_state.enemy.statuses.get('Bleed')
                if bst:
                    bst.count = int(incoming_count)
                elif incoming_count > 0:
                    branch_state.enemy.statuses['Bleed'] = Status(potency=1, count=int(incoming_count))
                branch_state.runtime['virtual_bleed_count'] = float(incoming_count)
                # Transform at action start using this branch's live resource state.
                skill, _transform = self._resolve_skill_transformation(
                    branch_state, ident, base_skill, action, branch_state.runtime.get('resource_runtime'))
                # Resource cost/gain happens once per requested action, before W/T/L.
                self._apply_probabilistic_branch_updates(branch_state, skill, action, 'T', apply_resources=True)
                pcfg_local = dict(pcfg)
                pcfg_local['attacker_sp'] = float(branch_state.fighters[iid].sp)
                pcfg_local['defender_sp'] = float(branch_state.enemy.sp)
                pcfg_local['_action_stub'] = action
                bp = self._run_probabilistic_bleed_stateful(
                    branch_state, skill, pcfg_local, branch_state.fighters[iid],
                    trigger_runtime_template, identity_map)
                terminal_meta = bp.get('_terminal_meta', {})
                mass_total = sum(float(v) for v in terminal_meta.values())
                if mass_total <= 0:
                    continue
                # Do NOT trim here.  Bleed extreme-value trimming is a turn-level
                # statistical post-processing step; trimming per action would
                # permanently remove probability mass before later Clash states
                # are propagated.
                for key, mass in terminal_meta.items():
                    proc = int(key[-2])
                    key_prob = float(mass) / mass_total
                    branch_prob = state_mass * key_prob
                    if branch_prob <= 0:
                        continue
                    next_count = int(incoming_count) if infinite else max(0, int(incoming_count) - int(proc))
                    mods = self._condition_effects(branch_state, ident, skill, scenario)
                    resolved_skill = self._apply_skill_modifiers(skill, mods)
                    terminal_candidates = bp.get('_terminal_states', {}).get(key)
                    if not terminal_candidates:
                        terminal_candidates = [(branch_state, 1.0)]
                    # A compact terminal key intentionally drops the full state
                    # signature.  Several trigger-mutated states can therefore
                    # share one key; process the complete local mixture instead
                    # of taking only the first candidate.
                    cand_total = sum(max(0.0, float(m)) for _st, m in terminal_candidates) or 1.0
                    prior_moment = float(damage_moment.get((incoming_count, sig, proc_total_before), 0.0))
                    prior_branch_moment = prior_moment * key_prob
                    for candidate_state, candidate_mass in terminal_candidates:
                        candidate_prob = branch_prob * (max(0.0, float(candidate_mass)) / cand_total)
                        if candidate_prob <= 0:
                            continue
                        terminal_state, damage = self._terminal_damage_state(
                            candidate_state, ident, resolved_skill, faces, bp, key, bool(action.get('crit', False)))
                        outcome = str(key[-1]).upper()
                        self._apply_probabilistic_branch_updates(
                            terminal_state, skill, action, outcome, apply_resources=False)
                        # Bleed Count is a real status axis for subsequent actions.
                        bst2 = terminal_state.enemy.statuses.get('Bleed')
                        if infinite:
                            if bst2:
                                bst2.count = int(incoming_count)
                        elif next_count > 0:
                            if bst2:
                                bst2.count = int(next_count)
                            else:
                                terminal_state.enemy.statuses.pop('Bleed', None)
                        else:
                            terminal_state.enemy.statuses.pop('Bleed', None)
                        terminal_state.runtime['virtual_bleed_count'] = float(next_count)
                        # Branch-local declarative triggers. Generated attacks are
                        # executed inside this exact terminal-state branch.
                        branch_trigger_rt = deepcopy(trigger_runtime_template)
                        trigger_ctx = {
                            'identity_id': iid, 'skill_id': skill.id,
                            'skill_name': str(skill.name), 'skill_slot': str(getattr(skill,'_slot','')),
                            'action_start_staggered': bool(branch_state.enemy.staggered),
                            'action_end_staggered': bool(terminal_state.enemy.staggered),
                            'action_start_hp': float(branch_state.enemy.hp),
                            'action_end_hp': float(terminal_state.enemy.hp),
                            'actual_damage': float(damage), 'generated': False,
                            'condition_flags': terminal_state.runtime.get('condition_flags',{}),
                            'available_identity_ids': list(identity_map.keys()),
                        }
                        fired = branch_trigger_rt.fire('after_skill', trigger_ctx)
                        queued = self._apply_probabilistic_trigger_effects(terminal_state, fired, identity_map, iid)
                        generated_damage = 0.0
                        generated_trace = []
                        terminal_state.runtime['probabilistic_trigger_max_depth'] = int(scenario.get('max_trigger_depth', 16))
                        for gid, gskill in queued:
                            child_damage, child_trace = self._execute_probabilistic_generated_action(
                                terminal_state, branch_trigger_rt, identity_map, gid, gskill, depth=1,
                                source_identity_id=iid, source_skill_id=skill.id,
                                trigger_chain=list(action.get('_trigger_chain', []))+[f'{iid}:{skill.id}'])
                            generated_damage += child_damage
                            generated_trace.extend(child_trace)
                        damage += generated_damage
                        final_sig = probabilistic_state_signature(terminal_state)
                        out_key = (next_count, final_sig, int(proc_total_before + proc))
                        outgoing[out_key] = outgoing.get(out_key, 0.0) + candidate_prob
                        # Carry the previous cumulative-damage moment into this
                        # branch and add this action's correlated damage.
                        prior_share = prior_branch_moment * (max(0.0, float(candidate_mass)) / cand_total)
                        damage_moment[out_key] = damage_moment.get(out_key, 0.0) + prior_share + candidate_prob * float(damage)
                        expected_damage += candidate_prob * float(damage)
                        gen_id_map = terminal_state.runtime.get('probabilistic_generated_damage_by_identity', {})
                        gen_sk_map = terminal_state.runtime.get('probabilistic_generated_damage_by_skill', {})
                        for gid2, gd in gen_id_map.items():
                            identity_damage[gid2] = identity_damage.get(gid2, 0.0) + candidate_prob * float(gd)
                        for gsk2, gd in gen_sk_map.items():
                            skill_damage[gsk2] = skill_damage.get(gsk2, 0.0) + candidate_prob * float(gd)
                        branch_rows.append({
                            'incoming_bleed_count': int(incoming_count), 'bleed_procs': int(proc),
                            'probability': candidate_prob, 'outgoing_bleed_count': next_count,
                            'outcome': outcome, 'enemy_hp_after': float(terminal_state.enemy.hp),
                            'enemy_staggered_after': bool(terminal_state.enemy.staggered),
                            'damage': float(damage),
                            'generated_damage': float(generated_damage),
                            'coin_trace': list(terminal_state.runtime.get('probabilistic_coin_trace', [])),
                            'generated_trace': generated_trace
                        })
            distribution = self._normalize_probabilistic_state_distribution(outgoing)
            total_damage += expected_damage
            # Generated damage was already attributed above; subtract it from
            # the source identity/skill buckets while keeping total turn damage.
            source_generated = sum(
                float(row.get('generated_damage', 0.0)) * float(row.get('probability', 0.0))
                for row in branch_rows
            )
            direct_expected = max(0.0, expected_damage - source_generated)
            identity_damage[iid] = identity_damage.get(iid, 0.0) + direct_expected
            sk=f'{iid}:{skill.id}'
            skill_damage[sk] = skill_damage.get(sk, 0.0) + direct_expected
            trace.append({'action_index': ai, 'identity_id': iid, 'skill_id': skill.id,
                          'incoming_distribution': self._collapse_bleed_distribution(incoming),
                          'outgoing_distribution': self._collapse_bleed_distribution(distribution),
                          'state_count': len(distribution), 'expected_damage': expected_damage,
                          'branch_count': len(branch_rows), 'branches': branch_rows})
        final_bleed = {}
        total_proc_dist = {}
        for (bleed, _sig, proc_total), mass in distribution.items():
            final_bleed[bleed] = final_bleed.get(bleed, 0.0) + mass
            total_proc_dist[proc_total] = total_proc_dist.get(proc_total, 0.0) + mass
        final_bleed = self._normalize_probabilistic_state_distribution(final_bleed)
        total_proc_dist = self._normalize_probabilistic_state_distribution(total_proc_dist)
        # The 5%/5% extreme-value trimming is deliberately applied ONCE, after
        # the entire requested turn has been propagated.  This keeps all
        # intermediate probability branches intact and only changes the reported
        # central-90% expectation.
        trimmed_proc_dist, retention_by_proc = self.turn_bleed_state_runtime.trim_distribution_with_retention(total_proc_dist)
        expected_trimmed_proc = sum(k*v for k,v in trimmed_proc_dist.items())
        expected_raw_proc = sum(k*v for k,v in total_proc_dist.items())
        # Build the joint projection P(total Bleed procs) x E[damage | total procs].
        # This is the key statistical bridge: trimming the proc distribution also
        # trims the corresponding damage mass, preserving their correlation.
        proc_damage_mass = {}
        proc_mass = {}
        for state_key, mass in distribution.items():
            proc = int(state_key[2])
            proc_mass[proc] = proc_mass.get(proc, 0.0) + float(mass)
            proc_damage_mass[proc] = proc_damage_mass.get(proc, 0.0) + float(damage_moment.get(state_key, 0.0))
        joint_proc_damage = {}
        for proc in sorted(proc_mass):
            m = proc_mass[proc]
            dm = proc_damage_mass.get(proc, 0.0)
            joint_proc_damage[proc] = {
                'probability': m,
                'damage_mass': dm,
                'expected_damage_given_proc': (dm / m if m > 0 else 0.0),
                'retained_fraction': float(retention_by_proc.get(proc, 0.0)),
            }
        trimmed_damage_mass = sum(
            proc_damage_mass.get(proc, 0.0) * float(retention_by_proc.get(proc, 0.0))
            for proc in proc_mass
        )
        retained_mass = sum(
            proc_mass.get(proc, 0.0) * float(retention_by_proc.get(proc, 0.0))
            for proc in proc_mass
        )
        expected_trimmed_damage = trimmed_damage_mass / retained_mass if retained_mass > 0 else total_damage
        expected_raw_damage = sum(proc_damage_mass.values())
        # Project the same final-tail trimming back onto the COMPLETE branch
        # state, rather than assuming final_count == initial_count - proc.
        # That assumption breaks when a Bleed gain occurs during the turn, and
        # it is also wrong for bleed_count_infinite.  `retention_by_proc` is the
        # exact fraction of each total-proc atom that survives the final 5%/5%
        # trim, so it can be applied uniformly to all branch states sharing that
        # proc total while preserving their internal correlations.
        trimmed_state_mass = {}
        for state_key, mass in distribution.items():
            proc = int(state_key[2])
            keep = float(retention_by_proc.get(proc, 0.0))
            if keep <= 0 or mass <= 0:
                continue
            trimmed_state_mass[state_key] = float(mass) * keep
        trimmed_state_mass = self._normalize_probabilistic_state_distribution(trimmed_state_mass)
        final_trimmed_bleed = {}
        for (bleed, _sig, _proc), prob in trimmed_state_mass.items():
            final_trimmed_bleed[int(bleed)] = final_trimmed_bleed.get(int(bleed), 0.0) + float(prob)
        final_trimmed_bleed = self._normalize_probabilistic_state_distribution(final_trimmed_bleed)
        expected_final_bleed_trimmed = sum(k*v for k,v in final_trimmed_bleed.items())
        # Keep one representative final signature for UI/debugging. The full
        # probability mass remains in `distribution`; this signature is only
        # a convenient projection for final flags.
        final_signature = next(iter(distribution.keys()))[1] if distribution else None
        return {'initial_bleed_count': initial_count, 'final_bleed_distribution': dict(sorted(final_bleed.items())),
                'expected_final_bleed_count': sum(k*v for k,v in final_bleed.items()),
                'total_bleed_proc_distribution': dict(sorted(total_proc_dist.items())),
                'trimmed_bleed_proc_distribution': dict(sorted(trimmed_proc_dist.items())),
                'expected_bleed_procs_raw': expected_raw_proc,
                'expected_bleed_procs_trimmed': expected_trimmed_proc,
                'trimmed_final_bleed_distribution': dict(sorted(final_trimmed_bleed.items())),
                'expected_final_bleed_count_trimmed': expected_final_bleed_trimmed,
                'trimmed_state_count': len(trimmed_state_mass),
                'expected_turn_damage': expected_trimmed_damage, 'expected_turn_damage_raw': expected_raw_damage,
                'expected_turn_damage_trimmed': expected_trimmed_damage,
                'expected_damage_by_identity': identity_damage,
                'joint_bleed_proc_damage': joint_proc_damage,
                'expected_damage_by_skill': skill_damage, 'actions': trace,
                'state_count': len(distribution), 'trim_fraction_each_tail': 0.05,
                'trim_scope': 'whole_turn_final_bleed_proc_distribution',
                'final_state_signature': final_signature}

    @staticmethod
    def _normalize_probabilistic_state_distribution(distribution):
        total = sum(max(0.0, float(v)) for v in distribution.values())
        if total <= 0:
            return {}
        return {k: max(0.0, float(v)) / total for k, v in distribution.items() if float(v) > 0}

    @staticmethod
    def _collapse_bleed_distribution(distribution):
        out = {}
        for key, mass in distribution.items():
            bleed = int(key[0]) if isinstance(key, tuple) else int(key)
            out[bleed] = out.get(bleed, 0.0) + float(mass)
        total = sum(out.values()) or 1.0
        return dict(sorted((k, v/total) for k,v in out.items()))

    def _fire_probabilistic_stagger_triggers(self, branch_state, runtime, identity_map, identity_id, skill,
                                            *, before_level=0, before_index=0, actual_damage=0.0, generated=False,
                                            source_identity_id='', source_skill_id='', depth=1):
        """Fire branch-local effects when a coin newly creates a Stagger state.

        Stagger is a state transition, not merely a damage modifier.  Keep it
        between the coin that caused the transition and the following coin so
        later coins/actions observe the new state.  Both declarative
        ``after_stagger`` rules and the legacy passive trigger name ``Stagger``
        are supported.
        """
        after_level = int(branch_state.enemy.stagger_level)
        after_index = int(branch_state.enemy.stagger_index)
        # `newly_staggered` means an actual transition into the Staggered state.
        # Increasing the stagger level while already staggered, or advancing a
        # threshold index while the level is capped, is not a new Stagger state.
        newly = int(before_level) <= 0 and after_level > 0
        if not newly:
            return [], False
        ctx = {
            'identity_id': identity_id, 'skill_id': skill.id, 'skill_name': str(skill.name),
            'skill_slot': str(getattr(skill, '_slot', '')), 'event': 'after_stagger',
            'actual_damage': float(actual_damage), 'generated': bool(generated),
            'action_start_staggered': int(before_level) > 0,
            'action_end_staggered': after_level > 0,
            'newly_staggered': True,
            'stagger_forced': False,
            'stagger_source': 'damage',
            'stagger_level_before': int(before_level), 'stagger_level_after': after_level,
            'stagger_index_before': int(before_index), 'stagger_index_after': after_index,
            'enemy_hp': float(branch_state.enemy.hp),
            'condition_flags': branch_state.runtime.get('condition_flags', {}),
            'available_identity_ids': list(identity_map.keys()),
        }
        queued=[]
        fired = self._fire_probabilistic_trigger_event(runtime, 'after_stagger', ctx, branch_state) if runtime is not None else []
        queued.extend(self._apply_probabilistic_trigger_effects(branch_state, fired, identity_map, identity_id))
        # Legacy/catalogue passive records may use the game-facing trigger name.
        ident = identity_map.get(identity_id)
        if ident is not None:
            for passive in getattr(ident, 'passives', []) or []:
                if passive.get('trigger') != 'Stagger':
                    continue
                cond = passive.get('condition')
                if cond and not self.core.machine.engine.condition_met(branch_state, ident, cond, skill):
                    continue
                # Legacy/catalogue Stagger passives historically went straight
                # through DamageEngine.apply_trigger_effects.  That applies state
                # effects correctly, but it silently drops queue_action effects.
                # Normalize them here so legacy Stagger passives have the same
                # generated-action semantics as declarative TriggerRuntime rules.
                legacy_effects = passive.get('effects', []) or []
                executable = []
                for effect in legacy_effects:
                    if str(effect.get('type', '')) == 'queue_action':
                        target_id = str(effect.get('identity_id', ''))
                        if target_id in identity_map:
                            target_ident = identity_map[target_id]
                            target_skill = None
                            sid = effect.get('skill_id')
                            if sid is not None and hasattr(target_ident, 'skills'):
                                target_skill = target_ident.skills.get(str(sid))
                            if target_skill is None:
                                target_skill = self._find_skill_by_name(target_ident, effect.get('skill_name', ''))
                            if target_skill is not None:
                                queued.append((target_id, deepcopy(target_skill)))
                        continue
                    executable.append(effect)
                if executable:
                    self.core.machine.engine.apply_trigger_effects(branch_state, ident, executable, skill)
        return queued, True

    def _execute_unopposed_coins_with_triggers(self, clone, identity, skill, faces, start, is_crit=False,
                                               *, source_identity_id='', source_skill_id='', depth=1):
        """Execute an unopposed coin suffix through the shared coin lifecycle."""
        runtime = clone.runtime.get('probabilistic_trigger_runtime_template')
        runtime = deepcopy(runtime) if runtime is not None else self._probabilistic_trigger_runtime([])
        imap = clone.runtime.get('probabilistic_identity_map', {})
        reuse_counts = {}
        generated_trace = []
        coin_trace = []
        before_snapshots = {}

        def before_coin(c):
            f = c.state.fighters[c.identity.id]
            before_snapshots[c.coin_index] = {
                "resources": dict(f.resources),
                "statuses": status_signature(f.statuses),
                "ammo": int(getattr(f, "ammo", 0)),
                "stagger_level": int(c.state.enemy.stagger_level),
                "stagger_index": int(c.state.enemy.stagger_index),
            }

        def on_coin(c):
            hp_before = c.hp_before
            coin_damage = c.coin_damage
            ci = c.coin_index
            snap = before_snapshots.get(ci, {})
            resources_before = dict(snap.get("resources", {}))
            statuses_before = snap.get("statuses", {})
            ammo_before = int(snap.get("ammo", 0))
            stagger_before = int(snap.get("stagger_level", 0))
            stagger_index_before = int(snap.get("stagger_index", 0))

            # The damage engine has already advanced the coin state.  Trigger
            # processing is the common post-coin lifecycle shared with the
            # probabilistic generated-action path.
            hit_queued = self._fire_probabilistic_hit_triggers(
                c.state, runtime, imap, c.identity, c.skill, ci, coin_damage,
                generated=False, source_identity_id=source_identity_id,
                source_skill_id=source_skill_id)
            for hgid, hgskill in hit_queued:
                if hgid in imap:
                    _, child_trace = self._execute_probabilistic_generated_action(
                        c.state, runtime, imap, hgid, hgskill, depth=depth + 1,
                        source_identity_id=c.identity.id, source_skill_id=c.skill.id,
                        trigger_chain=[])
                    generated_trace.extend(child_trace)

            stagger_queued, _ = self._fire_probabilistic_stagger_triggers(
                c.state, runtime, imap, c.identity.id, c.skill,
                before_level=stagger_before, before_index=stagger_index_before,
                actual_damage=coin_damage, generated=False,
                source_identity_id=source_identity_id, source_skill_id=source_skill_id,
                depth=depth)
            for sgid, sgskill in stagger_queued:
                if sgid in imap:
                    _, child_trace = self._execute_probabilistic_generated_action(
                        c.state, runtime, imap, sgid, sgskill, depth=depth + 1,
                        source_identity_id=c.identity.id, source_skill_id=c.skill.id,
                        trigger_chain=[])
                    generated_trace.extend(child_trace)

            ammo_after = int(getattr(c.state.fighters[c.identity.id], 'ammo', 0))
            coin_ctx = {
                'identity_id': c.identity.id, 'skill_id': c.skill.id,
                'skill_name': str(c.skill.name), 'skill_slot': str(getattr(c.skill, '_slot', '')),
                'coin_index': ci, 'actual_damage': coin_damage,
                'ammo_before': ammo_before, 'ammo_after': ammo_after,
                'ammo_spent': max(0, ammo_before-ammo_after),
                'is_lowest_ammo_identity': c.state.runtime.get('ammo_min_identity') == c.identity.id,
                'statuses': {k:v.__dict__.copy() for k,v in c.state.fighters[c.identity.id].statuses.items()},
                'condition_flags': c.state.runtime.get('condition_flags', {}),
                'available_identity_ids': list(c.state.fighters.keys()), 'generated': False,
                'enemy_hp_before': hp_before, 'enemy_hp_after': float(c.state.enemy.hp),
            }
            fired = runtime.fire('after_coin', coin_ctx)
            for item in fired:
                eff = item.get('effect', {})
                if eff.get('type') == 'extra_damage_scale':
                    eff = dict(eff); eff['base_damage'] = coin_damage
                    item = dict(item); item['effect'] = eff
                queued = self._apply_probabilistic_trigger_effects(c.state, [item], imap, c.identity.id)
                for gid, gskill in queued:
                    if gid in imap:
                        child_damage, child_trace = self._execute_probabilistic_generated_action(
                            c.state, runtime, imap, gid, gskill, depth=depth,
                            source_identity_id=c.identity.id, source_skill_id=c.skill.id,
                            trigger_chain=[f'{source_identity_id}:{source_skill_id}'] if source_identity_id else [])
                        generated_trace.extend(child_trace)

            coin_trace.append({
                'coin_index': ci, 'face': str(c.faces[ci-1] if ci-1 < len(c.faces) else 'H').upper(),
                'damage': coin_damage, 'enemy_hp_after': float(c.state.enemy.hp),
                'enemy_stagger_level_after': int(c.state.enemy.stagger_level),
                'resources_before': resources_before, 'resources_after': dict(c.state.fighters[c.identity.id].resources),
                'statuses_before': statuses_before,
                'statuses_after': status_signature(c.state.fighters[c.identity.id].statuses),
                'trigger_count': len(fired), 'generated_trace': list(generated_trace),
            })

        def on_skill(c, skill_damage):
            if c.state.enemy.hp <= 0 and not coin_trace:
                return None
            skill_ctx = {
                'identity_id': c.identity.id, 'skill_id': c.skill.id,
                'skill_name': str(c.skill.name), 'skill_slot': str(getattr(c.skill, '_slot', '')),
                'action_start_staggered': False, 'action_end_staggered': bool(c.state.enemy.staggered),
                'action_start_hp': float(c.hp_before), 'action_end_hp': float(c.state.enemy.hp),
                'actual_damage': skill_damage, 'generated': False,
                'condition_flags': c.state.runtime.get('condition_flags', {}),
                'available_identity_ids': list(c.state.fighters.keys()),
            }
            fired_skill = self._fire_probabilistic_trigger_event(runtime, 'after_skill', skill_ctx, c.state)
            imap2 = c.state.runtime.get('probabilistic_identity_map', {})
            for item in fired_skill:
                queued = self._apply_probabilistic_trigger_effects(c.state, [item], imap2, c.identity.id)
                for gid, gskill in queued:
                    if gid in imap2:
                        _, child_trace = self._execute_probabilistic_generated_action(
                            c.state, runtime, imap2, gid, gskill, depth=depth,
                            source_identity_id=c.identity.id, source_skill_id=c.skill.id,
                            trigger_chain=[])
                        generated_trace.extend(child_trace)
            return None

        def reuse_condition(c, condition):
            return self.core.machine.engine.condition_met(c.state, c.identity, condition, c.skill)

        core = CoinExecutionCore(self.core.machine.engine.simulate_coin)
        result_state, damage, _ = core.execute(
            CoinExecutionContext(clone, identity, skill, list(faces), int(start), bool(is_crit),
                                 False, source_identity_id, source_skill_id, depth, reuse_counts=reuse_counts),
            before_coin=before_coin, on_coin=on_coin, on_skill=on_skill, reuse_condition=reuse_condition)
        result_state.runtime['probabilistic_coin_trace'] = coin_trace
        return result_state, damage, generated_trace

    def _execute_terminal_unopposed_suffix(self, state, identity, skill, faces, probability_result, attacker_left, is_crit=False):
        """Execute the unopposed suffix shared by terminal probability branches."""
        initial_attacker = int(probability_result.get('initial_attacker_coins', len(skill.coins)))
        losses = max(0, initial_attacker - int(attacker_left))
        start = min(max(0, losses), len(skill.coins))
        clone = deepcopy(state)
        clone.runtime['special_after_coin'] = None
        resolved = deepcopy(skill)
        resolved.clash_result = 'win'
        clone, damage, trace = self._execute_unopposed_coins_with_triggers(
            clone, identity, resolved, faces, start, bool(is_crit),
            source_identity_id=identity.id, source_skill_id=skill.id, depth=1)
        return clone, damage, trace

    def _terminal_damage_state(self, state, identity, skill, faces, probability_result, terminal_key, is_crit=False):
        """Return post-terminal-Clash state and direct damage for one terminal branch."""
        attacker_left, normal_d, ub, _ex, _bleed, _outcome = terminal_key
        clone = deepcopy(state)
        if int(normal_d) + int(ub) > 0 or int(attacker_left) <= 0:
            return clone, 0.0
        resolved = deepcopy(skill)
        resolved.clash_result = 'win'
        clone2, damage, _trace = self._execute_terminal_unopposed_suffix(
            state, identity, resolved, faces, probability_result, attacker_left, bool(is_crit))
        return clone2, damage

    def _probabilistic_reuse_summary(self, state, identity, skill):
        """Summarize coin-reuse probability without mutating the authoritative state.

        This is intentionally a statistical side-channel: deterministic turn_damage
        remains authoritative, while expected reuse count is exposed separately.
        Rules whose conditions are state-dependent are evaluated at the current
        post-action state; unconditional/negative-status probability rules therefore
        get an exact bounded-Bernoulli distribution.
        """
        rows = []
        statuses = getattr(state.enemy, 'statuses', {})
        for ci, coin in enumerate(getattr(skill, 'coins', []) or []):
            for ri, rule in enumerate(getattr(coin, 'reuse_rules', []) or []):
                if not rule.get('high_point_assumption'):
                    continue
                try:
                    if not self.core.machine.engine.condition_met(state, identity, rule.get('condition'), skill):
                        continue
                except Exception:
                    continue
                p = 1.0
                dist = {int(rule.get('max_reuses', 0)): 1.0} if int(rule.get('max_reuses', 0)) > 0 else {0: 1.0}
                rows.append({'coin_index': ci + 1, 'rule_index': ri, 'probability': p,
                             'original_probability': rule.get('original_probability'),
                             'high_point_assumption': True,
                             'max_reuses': int(rule.get('max_reuses', 0)),
                             'expected_reuses': sum(k * v for k, v in dist.items()),
                             'distribution': dist})
        return rows

    def _prepare_turn_context(self, scenario, identity_map):
        """Build the immutable/configuration side of one-turn execution.

        C-3 extraction: state construction, target setup, prepared state,
        passive/gimmick registration, lifecycle initialization, and requested
        action queue construction happen here. Action execution remains in
        ``solve`` so behavior and ordering are unchanged.
        """
        state=self.build_state(scenario,identity_map); mode=scenario.get('coin_mode','max')
        # Multi-target is intentionally represented as a user-entered target count.
        # The engine keeps the existing single-target battle state as the main target;
        # additional targets receive the same resolved damage contribution for this
        # aggregate calculator view, without inventing separate enemy HP/stagger states.
        target_count = max(1, int(scenario.get('target_count', scenario.get('attack_target_count', 1)) or 1))
        state.runtime['target_count'] = target_count
        # Explicit random targeting is reproducible per solve when a seed is supplied.
        # The RNG lives in runtime so successive random-target actions consume
        # successive draws rather than resetting to the same target each action.
        seed = scenario.get('random_seed', scenario.get('target_random_seed'))
        state.runtime['random_seed'] = int(seed) if seed is not None else None
        state.runtime['target_random_counter'] = 0
        state.runtime['target_selection'] = {'policy': normalize_target_policy(scenario.get('target_policy')), 'resolved_ids': [], 'resolved_indexes': []}
        # User-entered Afterimage state.  Afterimage is a target-side status,
        # so the calculator accepts an explicit count without trying to infer
        # random target assignment from the passive.  Supported forms:
        #   enemy.afterimage_count: N
        #   enemy.afterimages: N
        #   enemy.statuses.잔영.count: N (legacy/direct form)
        # and the same fields on each enemy.targets[] slot.
        def _apply_afterimage_input(statuses, raw, target_label='enemy'):
            if not isinstance(raw, dict):
                return statuses
            explicit = raw.get('afterimage_count', raw.get('afterimages'))
            if isinstance(explicit, dict):
                explicit = explicit.get('count', explicit.get('potency', 0))
            if explicit is not None:
                try:
                    n=max(0, int(explicit))
                except (TypeError, ValueError):
                    n=0
                if n > 0:
                    statuses['잔영'] = Status(potency=0, count=n)
                else:
                    statuses.pop('잔영', None)
            return statuses
        enemy_statuses = _apply_afterimage_input(state.enemy.statuses, scenario.get('enemy', {}))
        state.enemy.statuses = enemy_statuses
        enemy_targets = scenario.get('enemy', {}).get('targets') if isinstance(scenario.get('enemy', {}), dict) else None
        if isinstance(enemy_targets, list):
            # Explicit target slots become independent EnemyState objects.  The
            # legacy single enemy remains the primary target when no slots are
            # supplied, preserving backwards compatibility.
            slots=[]
            base_enemy=state.enemy
            for ti, raw in enumerate(enemy_targets):
                if not isinstance(raw, dict):
                    continue
                emax=float(raw.get('max_hp', raw.get('hp', base_enemy.max_hp)))
                est=EnemyState(
                    float(raw.get('hp', emax)), emax,
                    level=int(raw.get('level', base_enemy.level)),
                    speed=int(raw.get('speed', base_enemy.speed)),
                    defense_level=int(raw.get('defense_level', base_enemy.defense_level)),
                    defense_level_bonus=int(raw.get('defense_level_bonus', base_enemy.defense_level_bonus)),
                    physical_res={k:float(v) for k,v in raw.get('physical_res', base_enemy.physical_res).items()},
                    sin_res={SIN.get(k,k):float(v) for k,v in raw.get('sin_res', base_enemy.sin_res).items()},
                    statuses=_apply_afterimage_input(self._status_map(raw.get('statuses', {})), raw, str(raw.get('id', ti))),
                    is_abnormality=bool(raw.get('is_abnormality', raw.get('abnormality', base_enemy.is_abnormality))),
                    keyword_damage_modifiers={str(k):float(v) for k,v in raw.get('keyword_damage_modifiers', getattr(base_enemy,'keyword_damage_modifiers',{})).items()},
                    sinking_sp_overflow_to_hp=bool(raw.get('sinking_sp_overflow_to_hp', getattr(base_enemy,'sinking_sp_overflow_to_hp',False))),
                    stagger_level=int(raw.get('stagger_level', 0)),
                    stagger_index=int(raw.get('stagger_index', 0)),
                    stagger_thresholds=list(raw.get('stagger_thresholds', [])),
                )
                slots.append({'id':str(raw.get('id', ti)), 'index':ti, 'state':est, **{k:v for k,v in raw.items() if k not in ('id','index')}})
            if slots:
                state.runtime['enemy_target_states'] = slots
                state.runtime['enemy_targets'] = [dict(x, state=x.get('state')) for x in slots]
                # Primary target is the first explicit slot.
                state.enemy = slots[0]['state']
        resource_runtime=ResourceRuntime.from_scenario(scenario)
        state.runtime['resource_runtime']=resource_runtime
        state.runtime["condition_flags"] = self._normalize_condition_overrides(scenario.get("condition_overrides", {}))
        self._apply_prepared_state(state, scenario)
        initial_bleed = state.enemy.statuses.get("Bleed")
        state.runtime["virtual_bleed_count"] = float(initial_bleed.count) if initial_bleed else 0.0
        expected_turn_base_state = deepcopy(state)
        state.runtime["passive_activation"] = self._build_passive_activation(scenario, identity_map)
        # Optional high-point branch switches are calculator options, not
        # passive activation state.  Omitted keeps legacy behavior enabled.
        calc_options = scenario.get('calculation_options', {}) or {}
        state.runtime['calculation_options'] = {
            'enable_extra_tremor_burst': bool(calc_options.get('enable_extra_tremor_burst', True)),
        }
        resonance_plan=self._build_resonance_plan(scenario.get('actions',[]), identity_map)
        state.runtime['resonance_plan']=resonance_plan
        if mode not in ('max','fixed'): raise ValueError('use enumerate_branches for enumerate')
        idents=list(identity_map.values()); self.core.machine.passive_runtime.passives=[]
        # Catalog passive text is natural-language source.  Do not execute it
        # implicitly: conservative one-turn accuracy is more important than
        # silently firing a misparsed passive.  Structured/compiled passives can
        # be explicitly enabled per scenario.
        passive_mode=scenario.get("passive_mode", "compiled_conservative")
        passive_variant_mode=scenario.get("passive_variant_mode", "last")
        state.runtime['selected_passives'] = {}
        selected_passives={}
        if passive_mode == "compiled_conservative":
            for ident in idents:
                selected_passives[ident.id]=self._active_passives(ident,passive_variant_mode)
                state.runtime['selected_passives'][str(ident.id)] = list(selected_passives[ident.id])
                for i,p in enumerate(selected_passives[ident.id]):
                    bundle = compile_passive_v29(p,ident.id,i)
                    for rule in bundle.rules:
                        rule.activation_key = f"{ident.id}::{p.get('name','')}"
                    self.core.machine.passive_runtime.register_many(bundle.rules)
        else:
            selected_passives={ident.id:list(getattr(ident,'passives',[]) or []) for ident in idents}
            state.runtime['selected_passives'] = {str(k): list(v) for k,v in selected_passives.items()}
        gimmicks=GimmickRegistry(idents, selected_passives, available_identity_ids=identity_map.keys(), extra_trigger_rules=scenario.get('trigger_rules', []))
        # Resource substitution rules are runtime-owned state, so Charge Barrier
        # acquisition can be redirected before shield materialization.
        state.runtime['charge_barrier_substitution'] = {
            str(r.owner_id): str(r.effect_resource or '고전압 외피')
            for r in gimmicks.rules if r.kind == 'charge_barrier_substitution'
        }
        gimmicks.reset_turn()
        state.runtime['special_after_coin'] = gimmicks.after_coin
        # Target-death callbacks are collected by the core at coin resolution and
        # drained after the whole logical action.  This prevents a multi-target
        # coin from executing a generated follow-up between target A and target B.
        state.runtime['after_target_kill'] = gimmicks.after_kill
        state.runtime['pending_target_kill_actions'] = []
        # Explicit resource turn-reset rules are applied before Turn Start
        # passives. This keeps resource lifecycle ordering deterministic.
        resource_runtime.reset_turn_all(state, identity_map)
        self.core.machine.start(state)
        out=[]
        damage_by_identity={iid:0.0 for iid in identity_map}
        damage_by_skill={}
        # Expected-damage aggregation is kept separate from the ordinary
        # deterministic/max-mode damage trace. This lets a one-turn result
        # expose both the concrete execution and the probability-weighted
        # estimate when probabilistic Bleed Clash actions are present.
        expected_damage_by_identity={iid:0.0 for iid in identity_map}
        expected_damage_by_skill={}
        expected_turn_damage=0.0
        # The user's action order is fixed at turn setup. Runtime-triggered
        # actions are separate queue entries and never rewrite requested order.
        queued_actions=[]
        for raw_action in scenario.get('actions', []):
            qa=deepcopy(raw_action)
            if 'target_count' not in qa:
                qa['target_count']=target_count
            queued_actions.append(qa)
        action_queue=ActionQueue.from_scenario(
            queued_actions,
            max_depth=int(scenario.get('max_trigger_depth', 16)),
        )
        # Expose the live action boundary through TurnState so all trigger
        # events (including callbacks invoked deep inside coin resolution) can
        # materialize generic queue_action effects consistently.
        state.runtime['action_queue'] = action_queue
        state.runtime['identity_map'] = identity_map
        # Battle-start lifecycle resource rules execute once before Turn Start.
        # Turn-start lifecycle rules then execute before requested actions.
        # Resource-only lifecycle effects are applied immediately; generated
        # skill actions are still queued at the front without rewriting the
        # user's requested order.
        for iid, ident in identity_map.items():
            gimmicks.after_lifecycle_event(
                state, {'event':'battle_start','identity_id':iid, 'action_queue':action_queue, 'identity_map':identity_map}, identity_map, action_index=0
            )
        lifecycle_actions=[]
        for iid, ident in identity_map.items():
            for ga in gimmicks.after_lifecycle_event(
                state, {'event':'turn_start','identity_id':iid, 'action_queue':action_queue, 'identity_map':identity_map}, identity_map, action_index=0
            ):
                from action_queue_v1 import ActionRequest
                generated=ActionRequest(
                    identity_id=str(ga.identity_id), skill_id=str(ga.skill_id),
                    requested_index=0, faces=ga.forced_faces, generated=True,
                    reason=ga.reason, source_action_index=0, source_event=ga.trigger_kind,
                    trigger_chain=['TURN_START'], depth=1
                )
                lifecycle_actions.append(generated)
        if lifecycle_actions:
            action_queue.items[0:0]=lifecycle_actions
            state.runtime['lifecycle_trigger_actions']=[x.to_dict() for x in lifecycle_actions]
        return TurnExecutionContext(
            state=state, mode=mode, resource_runtime=resource_runtime, target_count=target_count,
            expected_turn_base_state=expected_turn_base_state, resonance_plan=resonance_plan,
            selected_passives=selected_passives, passive_variant_mode=passive_variant_mode,
            gimmicks=gimmicks, action_queue=action_queue, out=out,
            damage_by_identity=damage_by_identity, damage_by_skill=damage_by_skill,
            expected_damage_by_identity=expected_damage_by_identity,
            expected_damage_by_skill=expected_damage_by_skill,
            expected_turn_damage=expected_turn_damage,
        )

    def _resolve_action(self, *, state, scenario, identity_map, request, raw_action, mode, resource_runtime, target_count):
        """Resolve one requested/triggered action without executing its attack.

        C-5 boundary: skill transformation, action-start resource lifecycle,
        faces, target-count resolution and target selection are completed here.
        The execution loop only consumes the resulting ResolvedAction.
        """
        iid=str(request.identity_id)
        ident=identity_map[iid]
        skill=self._skill(ident, request.skill_id)
        if skill is None:
            raise KeyError(raw_action['skill_id'])
        original_skill_id=skill.id
        skill, transform_info=self._resolve_skill_transformation(
            state, ident, skill, raw_action, resource_runtime)
        fighter=state.fighters[iid]
        consumed_this_action={}
        action_resource_event_start = len(state.event_log)
        state.runtime['current_action_resource_event_start'] = action_resource_event_start
        state.runtime['current_action_resource_consumption']=consumed_this_action
        state.runtime['current_action_resource_start']=dict(fighter.resources)
        state.runtime['current_action_dynamic_damage_bonus']=0.0
        for rname, amount in getattr(skill, 'resource_cost', {}).items():
            if str(rname).lower() in ('sp',): continue
            before_r=resource_runtime.get(fighter, str(rname), 0)
            resource_runtime.change(fighter, str(rname), -int(amount), state, reason=f'skill:{skill.id}:cost')
            consumed_this_action[str(rname)]=consumed_this_action.get(str(rname),0)+max(0,before_r-resource_runtime.get(fighter,str(rname),0))
        for rname, amount in getattr(skill, 'resource_gain', {}).items():
            if str(rname).lower() in ('sp',): continue
            resource_runtime.change(fighter, str(rname), int(amount), state, reason=f'skill:{skill.id}:gain')
        for rname, amount in getattr(skill, 'resource_cost_max', {}).items():
            if str(rname).lower() in ('sp',): continue
            current=resource_runtime.get(fighter,str(rname),0); spent=min(current,int(amount))
            resource_runtime.change(fighter,str(rname),-spent,state,reason=f'skill:{skill.id}:cost_max')
            consumed_this_action[str(rname)]=consumed_this_action.get(str(rname),0)+spent
        for rname in getattr(skill, 'resource_cost_all', []):
            if str(rname).lower() in ('sp',): continue
            current=resource_runtime.get(fighter,str(rname),0)
            resource_runtime.change(fighter,str(rname),-current,state,reason=f'skill:{skill.id}:cost_all')
            consumed_this_action[str(rname)]=consumed_this_action.get(str(rname),0)+current
        for ce in getattr(skill, 'resource_conditional_cost_max', []):
            rname=str(ce.get('resource','')); current=resource_runtime.get(fighter,rname,0)
            threshold=int(ce.get('threshold',0)); op=str(ce.get('operator','>='))
            ok=(current>=threshold if op=='>=' else current>threshold if op=='>' else current<=threshold if op=='<=' else current<threshold if op=='<' else current==threshold)
            if ok:
                spent=min(current,int(ce.get('amount',0))); resource_runtime.change(fighter,rname,-spent,state,reason=f'skill:{skill.id}:conditional_cost_max')
                consumed_this_action[rname]=consumed_this_action.get(rname,0)+spent
        for ce in getattr(skill, 'resource_conditional_costs', []):
            rname=str(ce.get('resource','')); current=resource_runtime.get(fighter,rname,0)
            op=str(ce.get('operator','>=')); threshold=int(ce.get('threshold',0))
            ok=(current>=threshold if op=='>=' else current>threshold if op=='>' else current<=threshold if op=='<=' else current<threshold if op=='<' else current==threshold)
            if ok:
                spent=min(current,int(ce.get('amount',0))); resource_runtime.change(fighter,rname,-spent,state,reason=f'skill:{skill.id}:conditional_cost')
                consumed_this_action[rname]=consumed_this_action.get(rname,0)+spent
        for effect in getattr(skill, 'effects_on_use', []) or []:
            if effect.get('type')=='resource_gain_from_consumed':
                source=str(effect.get('source','')); consumed=int(consumed_this_action.get(source,0)); per=max(1,int(effect.get('source_per',1))); units=consumed//per
                if units:
                    target=str(effect.get('target','')); amount=units*int(effect.get('target_amount',0)); resource_runtime.change(fighter,target,amount,state,reason=f'skill:{skill.id}:convert_from_consumed')
            elif effect.get('type')=='resource_convert':
                source=str(effect.get('source','')); need=max(1,int(effect.get('source_amount',1))); target=str(effect.get('target','')); gain=int(effect.get('target_amount',0)); current=resource_runtime.get(fighter,source,0); units=current//need
                if units:
                    spent=units*need; resource_runtime.change(fighter,source,-spent,state,reason=f'skill:{skill.id}:convert_consume'); consumed_this_action[source]=consumed_this_action.get(source,0)+spent; resource_runtime.change(fighter,target,units*gain,state,reason=f'skill:{skill.id}:convert_gain')
        # Declarative Charge-over-cap damage rule.
        overflow_bonus = 0
        active_ps = state.runtime.get('selected_passives', {}).get(str(ident.id), []) or []
        overflow_event_rows = state.event_log[action_resource_event_start:]
        for pp in active_ps:
            ptxt = str(pp.get('effect','')) if isinstance(pp, dict) else str(getattr(pp,'effect',''))
            if ('자신의 스킬로 충전 횟수 최대치를 초과하여 충전 횟수를 얻으면' in ptxt
                    and '해당 스킬 피해량 +3%' in ptxt):
                for ev in overflow_event_rows:
                    if (ev.get('event') == 'resource_overflow' and ev.get('resource') == '충전'
                            and str(ev.get('identity_id','')) == str(ident.id)
                            and str(ev.get('skill_id','')) == str(skill.id)):
                        overflow_bonus += int(ev.get('overflow', 0))
                break
        if overflow_bonus:
            applied = min(overflow_bonus, 5) * 0.03
            state.runtime['current_action_dynamic_damage_bonus'] += applied
            state.event_log.append({'event':'charge_overflow_skill_damage_bonus',
                'identity_id':str(ident.id),'skill_id':str(skill.id),
                'overflow':min(overflow_bonus,5),'damage_bonus':applied})

        for rname, per in getattr(skill, 'resource_consumption_damage_per', {}).items():
            state.runtime['current_action_dynamic_damage_bonus'] += consumed_this_action.get(rname,0)*float(per)
        state.runtime['current_action_base_power_bonus']=0
        for rule in getattr(skill, '_ammo_base_power_rules', []):
            spent=int(consumed_this_action.get('탄환',0)); state.runtime['current_action_base_power_bonus'] += (spent//max(1,int(rule.get('per',1))))*int(rule.get('amount',0))
        faces=[str(x).upper() for x in (raw_action.get('faces') if raw_action.get('faces') is not None else (['H']*len(skill.coins) if mode=='max' else []))]
        if len(faces)!=len(skill.coins): raise ValueError(f'faces mismatch: {ident.name}/{skill.name}')
        if 'target_count' in raw_action: requested_target_count=raw_action.get('target_count')
        elif request.target_count is not None: requested_target_count=request.target_count
        elif 'target_count' in scenario or 'attack_target_count' in scenario: requested_target_count=scenario.get('target_count',scenario.get('attack_target_count'))
        else: requested_target_count=getattr(skill,'attack_weight',1)
        state.runtime['current_target_count']=max(1,int(requested_target_count or 1))
        target_ctx=self._resolve_action_target_context(state=state,scenario=scenario,request=request,raw_action=raw_action)
        return ResolvedAction(request,raw_action,iid,ident,original_skill_id,skill,transform_info,fighter,consumed_this_action,faces,target_ctx,int(requested_target_count or 1))

    def _resolve_action_target_context(self, *, state, scenario, request, raw_action):
        """Resolve the action's target boundary without executing damage.

        C-4 extraction: target-policy precedence, deterministic random-target
        sequencing, explicit coin-target mapping, and the public target-selection
        snapshot now live at one action boundary.  No damage/state mutation beyond
        target-selection runtime metadata is performed here.
        """
        action_target_policy = (request.target_policy if request.target_policy is not None
                                else raw_action.get('target_policy', scenario.get('target_policy')))
        action_target_index = (request.target_index if request.target_index is not None
                               else raw_action.get('target_index', scenario.get('target_index')))
        action_target_ids = (request.target_ids if request.target_ids is not None
                             else raw_action.get('target_ids', scenario.get('target_ids')))
        action_target_override_ids = (request.target_override_ids if request.target_override_ids is not None
                                      else raw_action.get('target_override_ids', scenario.get('target_override_ids')))
        if action_target_override_ids is not None:
            action_target_ids = action_target_override_ids
        action_coin_target_ids = (request.coin_target_ids if request.coin_target_ids is not None
                                  else raw_action.get('coin_target_ids', raw_action.get('coin_target_indices', scenario.get('coin_target_ids', scenario.get('coin_target_indices')))))
        target_pool = state.runtime.get('enemy_targets')
        if not isinstance(target_pool, list):
            target_pool = [{
                'id': 'main', 'index': 0, 'hp': float(state.enemy.hp),
                'max_hp': float(state.enemy.max_hp),
                'statuses': {k: getattr(v, '__dict__', v) for k,v in state.enemy.statuses.items()},
            }]
        random_seed = state.runtime.get('random_seed')
        if random_seed is not None:
            random_counter = int(state.runtime.get('target_random_counter', 0))
            target_rng = random.Random(random_seed + random_counter)
            state.runtime['target_random_counter'] = random_counter + 1
        else:
            target_rng = random.Random()
        chosen = select_targets(target_pool, action_target_policy, state.runtime['current_target_count'], action_target_index, action_target_ids, rng=target_rng)
        if action_coin_target_ids is not None:
            mapped = []
            for spec in action_coin_target_ids:
                vals = spec if isinstance(spec, (list, tuple)) else [spec]
                for value in vals:
                    if isinstance(value, int) or (isinstance(value, str) and value.isdigit()):
                        hit = next((x for x in target_pool if int(x.get('index', -1)) == int(value)), None)
                    else:
                        hit = next((x for x in target_pool if str(x.get('id')) == str(value)), None)
                    if hit is not None and hit not in mapped:
                        mapped.append(hit)
            if mapped:
                chosen = mapped
            normalized_coin_targets = []
            for spec in action_coin_target_ids:
                vals = spec if isinstance(spec, (list, tuple)) else [spec]
                out_vals = []
                for value in vals:
                    if isinstance(value, int) or (isinstance(value, str) and value.isdigit()):
                        hit = next((x for x in target_pool if int(x.get('index', -1)) == int(value)), None)
                        out_vals.append(str(hit.get('id')) if hit is not None else str(value))
                    else:
                        out_vals.append(str(value))
                normalized_coin_targets.append(out_vals if isinstance(spec, (list, tuple)) else (out_vals[0] if out_vals else None))
            action_coin_target_ids = normalized_coin_targets
        state.runtime['coin_target_ids'] = list(action_coin_target_ids) if action_coin_target_ids is not None else None
        selection = {'policy': normalize_target_policy(action_target_policy),
                     'resolved_ids': [str(x.get('id', x.get('index', i))) for i,x in enumerate(chosen)],
                     'resolved_indexes': [int(x.get('index', i)) for i,x in enumerate(chosen)]}
        state.runtime['target_selection'] = selection
        return {
            'target_pool': target_pool,
            'chosen': chosen,
            'target_selection': selection,
            'target_policy': action_target_policy,
            'target_index': action_target_index,
            'target_ids': action_target_ids,
            'target_override_ids': action_target_override_ids,
            'coin_target_ids': action_coin_target_ids,
        }

    def _execute_action_execution(self, *, state, scenario, request, raw_action,
                                  identity, skill, clash_skill, fighter, faces,
                                  identity_id, action_index, action_coin_target_ids,
                                  before_damage):
        """Execute the resolved action's clash/unopposed phase.

        This is the C-6 Action Execution Boundary.  Resolution (skill/resource/
        target preparation) is deliberately outside this method; this method is
        only responsible for handing a fully resolved action to the common core
        and returning the execution outcome needed by downstream trigger logic.
        """
        # Work on an action-local copy so conditional coin properties (such as
        # Charge-Potency-driven Unbreakable Coins) never mutate catalog data.
        skill = deepcopy(skill)
        for cond in getattr(skill, 'conditions', []) or []:
            if cond.get('effect') == 'unbreakable' and self._condition_met(state, identity, cond.get('condition', {}), skill):
                for coin in getattr(skill, 'coins', []) or []:
                    coin.unbreakable = True
        clash_trace = None
        result = None
        outcome = 'unopposed'
        if raw_action.get('clash'):
            clash_skill = deepcopy(clash_skill)
            # Common Clash Power buffs/debuffs are Clash-only. They must not
            # leak into final Skill Power/damage. Resolve them at the clash
            # boundary and apply actor-side bonus to the attacker's base clash
            # power and target-side bonus to the defender's clash power.
            clash_values = BuffDebuffRuntime.resolve(
                state, target_id=str(identity_id), timing="clash",
                context={"skill_is_defense": False}
            ) if getattr(state, "runtime", {}).get(BuffDebuffRuntime.KEY) else {}
            enemy_clash_values = BuffDebuffRuntime.resolve(
                state, target_id="enemy", timing="clash",
                context={"skill_is_defense": False}
            ) if getattr(state, "runtime", {}).get(BuffDebuffRuntime.KEY) else {}
            actor_clash_bonus = int(clash_values.get("clash_power", 0))
            target_clash_bonus = int(enemy_clash_values.get("clash_power", 0))
            if actor_clash_bonus:
                clash_skill.base_power += actor_clash_bonus
                clash_skill.clash_power += actor_clash_bonus
                state.event_log.append({
                    'event':'buff_debuff_clash_power', 'action_index':action_index,
                    'identity':identity_id, 'target':'self',
                    'bonus':actor_clash_bonus
                })
            # Rodion Accelerating Future: Base Skill Clash Power +1 for every
            # 2 stacks.  The stack was gained at Clash start above, so the current
            # clash sees the newly gained stack.
            if str(identity_id) == 'identity-10916' and str(getattr(skill, '_slot', '')).upper() in ('S1','S2','S3'):
                af = fighter.statuses.get('가속하는 미래')
                if af:
                    af_bonus = int(getattr(af, 'count', 0)) // 2
                    clash_power_bonus = target_clash_bonus + af_bonus
                    if af_bonus:
                        state.event_log.append({'event':'accelerating_future_clash_power','action_index':action_index,'identity':identity_id,'stacks':int(af.count),'bonus':af_bonus})
                else:
                    clash_power_bonus = target_clash_bonus
            else:
                clash_power_bonus = target_clash_bonus
            for cond in getattr(clash_skill, 'conditions', []) or []:
                if cond.get('effect') == 'clash_power' and self._condition_met(state, identity, cond.get('condition', {}), clash_skill):
                    clash_power_bonus += min(int(cond.get('max', 999999)), int(cond.get('amount', 0)))
                elif cond.get('effect') == 'clash_power_dynamic' and self._condition_met(state, identity, cond.get('condition', {}), clash_skill):
                    c = cond.get('condition', {}) or {}
                    resource = str(c.get('resource', ''))
                    if resource == '충전 위력':
                        value = int(getattr(fighter, 'charge_potency', 0))
                    elif resource == '충전':
                        value = int(getattr(fighter, 'charge', 0))
                    else:
                        value = int(getattr(fighter, 'resources', {}).get(resource, 0))
                    clash_power_bonus += min(int(cond.get('max', 999999)), value)
            clash_skill.base_power += clash_power_bonus
            clash_skill.clash_power += clash_power_bonus
            if clash_power_bonus:
                state.event_log.append({'event':'conditional_clash_power','action_index':action_index,'identity':identity_id,'skill':skill.id,'bonus':clash_power_bonus,'base_power_after':clash_skill.base_power})
            c=raw_action['clash']
            coins=[CoinData(int(x.get('coin_power',0)), ATK.get(x.get('damage_type','slash'),x.get('damage_type','slash')), SIN.get(x.get('sin',''),x.get('sin',''))) for x in c.get('coins',[])]
            exchange_outcomes=c.get('exchange_outcomes')
            if exchange_outcomes is not None:
                defender_count=int(c.get('initial_defender_coins', len(coins)))
                attacker_count=int(c.get('initial_attacker_coins', len(skill.coins)))
                clash_trace=self.clash_exchange_runtime.resolve(
                    attacker_count, defender_count, exchange_outcomes,
                    c.get('attacker_coins_after'), bool(c.get('track_attacker_coins', False)))
                for ex in clash_trace['exchanges']:
                    state.event_log.append({'event':'clash_exchange','action_index':action_index+1,'identity':identity_id,'skill':skill.id,**ex})
                state.event_log.append({'event':'bleed_proc_batch','action_index':action_index+1,'identity':identity_id,'skill':skill.id,
                    'total_procs':clash_trace['total_bleed_procs'],'exchange_count':clash_trace['exchange_count']})
                consumed_attacker=set(); active_attacker=0
                for ex in clash_trace['exchanges']:
                    if ex['outcome'] in ('L','T'):
                        if active_attacker < len(skill.coins):
                            consumed_attacker.add(active_attacker); active_attacker += 1
                surviving=[i for i in range(len(skill.coins)) if i not in consumed_attacker]
                resolved_skill=deepcopy(skill)
                resolved_skill.clash_result=('win' if clash_trace['defender_coins_remaining']==0
                    else 'lose' if clash_trace['attacker_coins_remaining']==0 else 'lose')
                self.core.machine.events.emit(EventType.CLASH_START, state, {'identity':identity,'skill':skill})
                if resolved_skill.clash_result == 'win':
                    self.core.machine.events.emit(EventType.CLASH_WIN, state, {'identity':identity,'skill':skill})
                else:
                    self.core.machine.events.emit(EventType.CLASH_LOSE, state, {'identity':identity,'skill':skill})
                clash_effects=(resolved_skill.effects_on_clash_win if resolved_skill.clash_result == 'win' else resolved_skill.effects_on_clash_lose)
                for effect in clash_effects:
                    if self.core.machine.engine.condition_met(state, identity, effect.get('condition'), resolved_skill):
                        self.core.machine.engine.apply_effect(state, identity_id, effect.get('target','self'), effect)
                trigger_name='Clash Win' if resolved_skill.clash_result == 'win' else 'Clash Lose'
                for passive in getattr(identity, 'passives', []) or []:
                    if passive.get('trigger') == trigger_name:
                        self.core.machine.engine.apply_trigger_effects(state, identity, passive.get('effects', []), resolved_skill)
                before_explicit=state.turn_damage; prior_heads=0
                for coin_index in surviving:
                    if state.enemy.hp <= 0: break
                    face=faces[coin_index] if coin_index < len(faces) else 'H'
                    self.core.machine.engine.simulate_coin(state, identity, resolved_skill, skill.coins[coin_index], face,
                        bool(raw_action.get('crit',False)), coin_index+1, prior_heads)
                    if face.upper() == 'H': prior_heads += 1
                if state.enemy.hp > 0:
                    for effect in getattr(resolved_skill, 'effects_on_hit', []) or []:
                        if self.core.machine.engine.condition_met(state, identity, effect.get('condition'), resolved_skill):
                            self.core.machine.engine.apply_effect(state, identity_id, effect.get('target','self'), effect)
                outcome=resolved_skill.clash_result
                result={'outcome':outcome,'damage':state.turn_damage-before_explicit,
                    'surviving_coin_indices':[i+1 for i in surviving],
                    'consumed_attacker_coin_indices':[i+1 for i in sorted(consumed_attacker)]}
            else:
                defender_skill_power = int(c.get('skill_power',0)) + int(target_clash_bonus)
                result=self.core.execute_clash(state, identity, clash_skill,
                    ClashData(defender_skill_power,coins), faces,
                    raw_action.get('defender_faces'), bool(raw_action.get('crit',False)))
                outcome=result['outcome']
        else:
            target_slots=state.runtime.get('enemy_target_states', [])
            resolved_indexes=list(state.runtime.get('target_selection', {}).get('resolved_indexes', []))
            selected=[]
            if target_slots and resolved_indexes:
                by_index={int(x['index']):x for x in target_slots}
                for ti in resolved_indexes:
                    if ti in by_index: selected.append((by_index[ti]['id'],by_index[ti]['state']))
            if action_coin_target_ids is not None and selected:
                result=self.core.execute_unopposed_multi_target(state, identity, skill, faces, selected,
                    bool(raw_action.get('crit',False)), coin_target_ids=action_coin_target_ids,
                    coin_target_policies=getattr(skill,'coin_target_policies',None))
                state.runtime['current_action_damage_by_target']=dict(result.get('damage_by_target', {}))
            elif len(selected)>1:
                result=self.core.execute_unopposed_multi_target(state, identity, skill, faces, selected,
                    bool(raw_action.get('crit',False)), coin_target_policies=getattr(skill,'coin_target_policies',None))
                state.runtime['current_action_damage_by_target']=dict(result.get('damage_by_target', {}))
            else:
                self.core.execute_unopposed(state, identity, skill, faces, bool(raw_action.get('crit',False)))
                if selected:
                    state.runtime['current_action_damage_by_target']={str(selected[0][0]): float(state.turn_damage-before_damage)}
                else:
                    state.runtime['current_action_damage_by_target']={}
            outcome='unopposed'
        return {'result':result,'outcome':outcome,'clash_trace':clash_trace}

    def solve(self,scenario,identity_map):
        ctx = self._prepare_turn_context(scenario, identity_map)
        state=ctx.state; mode=ctx.mode; resource_runtime=ctx.resource_runtime
        target_count=ctx.target_count; expected_turn_base_state=ctx.expected_turn_base_state
        resonance_plan=ctx.resonance_plan; selected_passives=ctx.selected_passives
        passive_variant_mode=ctx.passive_variant_mode; gimmicks=ctx.gimmicks
        action_queue=ctx.action_queue; out=ctx.out
        trigger_boundary = TriggerActionExecutionBoundary(action_queue)
        damage_by_identity=ctx.damage_by_identity; damage_by_skill=ctx.damage_by_skill
        expected_damage_by_identity=ctx.expected_damage_by_identity
        expected_damage_by_skill=ctx.expected_damage_by_skill
        expected_turn_damage=ctx.expected_turn_damage
        idx=0
        while action_queue:
            request=action_queue.pop(); idx += 1
            state.runtime['current_action_request'] = request
            resource_event_cursor=len(state.event_log)
            a=request.to_dict()
            if state.enemy.hp<=0: break
            iid=str(request.identity_id); ident=identity_map[iid]; skill=self._skill(ident,request.skill_id);
            action_start_staggered = bool(state.enemy.staggered)
            action_start_enemy_stagger_level = int(state.enemy.stagger_level)
            action_start_enemy_stagger_index = int(state.enemy.stagger_index)
            action_start_hp = float(state.enemy.hp)
            action_start_statuses = {k: (int(getattr(v, 'potency', 0)), int(getattr(v, 'count', 0))) for k, v in getattr(state.enemy, 'statuses', {}).items()}
            action_start_ammo = int(getattr(state.fighters[iid], 'ammo', 0)) if iid in state.fighters else 0
            # Analyzer-contract snapshot: capture the actor and target state BEFORE
            # skill transformation/resource costs/coin resolution.  Keeping this
            # snapshot immutable makes First Divergence analysis meaningful.
            _start_fighter = state.fighters[iid]
            action_start_sp = float(_start_fighter.sp)
            action_start_charge = int(getattr(_start_fighter, 'charge', 0))
            action_start_poise = deepcopy(_start_fighter.poise.__dict__)
            action_start_resources_full = dict(getattr(_start_fighter, 'resources', {}) or {})
            action_start_statuses = {k: deepcopy(v.__dict__) for k, v in getattr(_start_fighter, 'statuses', {}).items()}
            action_start_enemy_statuses = {k: deepcopy(v.__dict__) for k, v in getattr(state.enemy, 'statuses', {}).items()}
            state.runtime['current_action_index'] = idx + 1
            state.runtime['current_action_start_hp'] = float(state.enemy.hp)
            resolved = self._resolve_action(
                state=state, scenario=scenario, identity_map=identity_map,
                request=request, raw_action=a, mode=mode,
                resource_runtime=resource_runtime, target_count=target_count,
            )
            iid=resolved.identity_id; ident=resolved.identity; skill=resolved.skill
            original_skill_id=resolved.original_skill_id; transform_info=resolved.transform_info
            fighter=resolved.fighter; consumed_this_action=resolved.consumed_resources
            faces=resolved.faces
            target_pool=resolved.target_ctx['target_pool']
            action_target_policy=resolved.target_ctx['target_policy']
            action_target_index=resolved.target_ctx['target_index']
            action_target_ids=resolved.target_ctx['target_ids']
            action_target_override_ids=resolved.target_ctx['target_override_ids']
            action_coin_target_ids=resolved.target_ctx['coin_target_ids']

            mods=self._condition_effects(state, ident, skill, scenario)
            skill=self._apply_skill_modifiers(skill, mods)
            requested_index = int(request.requested_index or 0)
            if not request.generated and 1 <= requested_index <= len(resonance_plan):
                res_info=resonance_plan[requested_index-1]
            else:
                # Triggered actions do not retroactively alter the user's planned
                # resonance chain. Their own Sin resource generation still occurs.
                res_info={'index':requested_index or idx,'sin':skill.sin,'resonance_count':0,'resonance_offense_bonus':0,'absolute_count':0,'absolute_offense_bonus':0,'counts':{},'offense_bonus':0}
            state.runtime['current_resonance']=dict(res_info.get('counts', {}))
            state.runtime['current_absolute_resonance']={res_info['sin']:res_info['absolute_count']}
            state.runtime['current_resonance_offense_bonus']=int(res_info.get('offense_bonus',0))
            state.event_log.append({'event':'resonance','action_index':idx,**res_info})
            # Source-backed identity-specific buff: The Thumb Nursefather Rodion
            # (identity-10916) gains 1 Accelerating Future at the start of each
            # real Clash while Foresight Eye is present.  The Rodion variant is
            # distinct from the generic Accelerating Future definition: max 5,
            # Base Skill damage +3%/stack (cap 15%), Base Skill Clash Power +1/2
            # stacks, and +1 Base Skill Coin Power at 5 stacks.
            if str(iid) == 'identity-10916' and a.get('clash') and int(fighter.resources.get('예지안', 0)) > 0:
                st = fighter.statuses.setdefault('가속하는 미래', Status())
                before_stack = int(getattr(st, 'count', 0))
                st.count = min(5, before_stack + 1)
                state.event_log.append({
                    'event': 'accelerating_future_gain', 'action_index': idx,
                    'identity_id': iid, 'before': before_stack, 'after': int(st.count),
                    'max_stack': 5, 'source': '예지안_합_진행'
                })
            before=state.turn_damage
            if state.fighters:
                state.runtime['ammo_min_identity'] = min(state.fighters, key=lambda x: state.fighters[x].ammo)
            if scenario.get('auto_generate_sin_resources', True) and skill.sin:
                fighter=state.fighters[iid]
                fighter.sin_resources[skill.sin]=fighter.sin_resources.get(skill.sin,0)+1
                state.event_log.append({'event':'sin_resource_gain','action_index':idx,'sin':skill.sin,'amount':1,'after':fighter.sin_resources[skill.sin]})
            execution = self._execute_action_execution(
                state=state, scenario=scenario, request=request, raw_action=a,
                identity=ident, skill=skill, clash_skill=skill,
                fighter=fighter, faces=faces, identity_id=iid, action_index=idx,
                action_coin_target_ids=action_coin_target_ids, before_damage=before,
            )
            r = execution["result"]
            outcome = execution["outcome"]
            clash_trace = execution["clash_trace"]
            # Rodion's Accelerating Future expires at Skill End.  Remove it
            # before any after-skill generated action can be resolved.
            if str(iid) == 'identity-10916':
                af = fighter.statuses.pop('가속하는 미래', None)
                if af is not None:
                    state.event_log.append({
                        'event': 'accelerating_future_expire', 'action_index': idx,
                        'identity_id': iid, 'stack': int(getattr(af, 'count', 0))
                    })

            # Clash-loss follow-ups (e.g. 예지/골단) are generated immediately
            # after the clash result is known. This is deliberately before the
            # next requested action, preserving ActionQueue causal ordering.
            if a.get('clash'):
                clash_trigger_ctx = {
                    'action_index': idx,
                    'outcome': outcome,
                    'clash_outcome': outcome,
                    'fighter': fighter,
                    'state': state,
                    'resources': dict(getattr(fighter, 'resources', {}) or {}),
                    'statuses': {k:v.__dict__.copy() for k,v in fighter.statuses.items()},
                    'generated': request.generated,
                }
                for ga in gimmicks.after_clash(ident, skill, clash_trigger_ctx):
                    inherit_target = (ga.target_policy in (None, '', 'main') and
                                       ga.target_index is None and ga.target_ids is None and
                                       request.target_policy is not None)
                    dispatch = trigger_boundary.enqueue_from_gimmick(
                        request, ga, source_event='after_clash', source_context=clash_trigger_ctx)
                    generated = dispatch.generated
                    queued = dispatch.queued
                    state.event_log.append({
                        'event':'gimmick_action_queued', 'action_index':idx,
                        'queued':queued, 'reason':ga.reason, 'source':ga.source,
                        'identity_id':ga.identity_id, 'skill_id':ga.skill_id,
                        'trigger_kind':ga.trigger_kind, 'trigger_context':clash_trigger_ctx,
                        'requested_index':request.requested_index,
                        'depth':generated.depth, 'trigger_chain':generated.trigger_chain,
                    })

            # Optional probabilistic Bleed mode. It is action-local and feeds
            # the expected remaining Bleed Count into subsequent actions.
            bleed_probability_result = None
            bleed_consumption = None
            pcfg = a.get('bleed_clash_probability')
            if pcfg and isinstance(pcfg, dict):
                bleed_probability_result = self._run_probabilistic_bleed(state, skill, pcfg, fighter)
                expected_damage_result = self._expected_probabilistic_clash_damage(
                    state, ident, skill, faces, bleed_probability_result, bool(a.get('crit',False))
                )
                bleed_probability_result.update(expected_damage_result)
                infinite = bool(scenario.get('bleed_count_infinite', False) or pcfg.get('bleed_count_infinite', False))
                bleed_consumption = self._apply_bleed_proc_count(state, bleed_probability_result['expected_bleed_procs'], infinite=infinite, expected=True)
                # Terminal-state bookkeeping is internal to the expected-damage
                # calculation; do not expose the potentially large state map in
                # normal calculator output.
                bleed_probability_result.pop('_terminal_meta', None)
                state.event_log.append({'event':'bleed_probability','action_index':idx+1,'identity_id':iid,'skill':skill.id,
                    'expected_bleed_procs':bleed_probability_result['expected_bleed_procs'],
                    'expected_bleed_procs_raw':bleed_probability_result['expected_bleed_procs_raw'],
                    'probability_reaching_99_exchanges':bleed_probability_result['probability_reaching_99_exchanges'],
                    'bleed_consumption':bleed_consumption})
            elif clash_trace is not None:
                infinite = bool(scenario.get('bleed_count_infinite', False))
                bleed_consumption = self._apply_bleed_proc_count(state, clash_trace['total_bleed_procs'], infinite=infinite, expected=False)
                state.event_log.append({'event':'bleed_consumption','action_index':idx+1,'identity_id':iid,'skill':skill.id, **bleed_consumption})
            action_damage=state.turn_damage-before
            damage_by_identity[iid]=damage_by_identity.get(iid,0.0)+action_damage
            skill_key=f'{iid}:{skill.id}'
            damage_by_skill[skill_key]=damage_by_skill.get(skill_key,0.0)+action_damage
            action_expected_damage = (float(bleed_probability_result.get('expected_damage', 0.0))
                                      if bleed_probability_result is not None else float(action_damage))
            reuse_summary = self._probabilistic_reuse_summary(state, ident, skill)
            expected_reuse_count = sum(float(x.get('expected_reuses', 0.0)) for x in reuse_summary)
            # Keep deterministic damage authoritative; the probabilistic reuse
            # expectation is exposed explicitly so callers do not confuse an
            # expected branch with an actually executed branch.
            expected_turn_damage += action_expected_damage
            expected_damage_by_identity[iid] = expected_damage_by_identity.get(iid, 0.0) + action_expected_damage
            expected_damage_by_skill[skill_key] = expected_damage_by_skill.get(skill_key, 0.0) + action_expected_damage
            action_coins=[e for e in state.event_log if e.get('event')=='coin' and e.get('action_index')==idx+1]
            action_target_damage = state.runtime.get('current_action_damage_by_target') or {}
            action_has_explicit_targets = bool(state.runtime.get('enemy_target_states'))
            fighter_now=state.fighters[iid]
            action_start_resources=dict(state.runtime.get('current_action_resource_start',{}))
            action_end_resources=dict(fighter_now.resources)
            action_type = 'triggered' if request.generated else 'requested'
            requested_action = request.to_dict()
            resolved_action = {
                'identity_id': iid,
                'skill_id': skill.id,
                'identity_name': ident.name,
                'skill_name': skill.name,
                'original_skill_id': original_skill_id,
                'transformation': deepcopy(transform_info),
            }
            out.append({'index':idx,'action_type':action_type,'requested_action':requested_action,'resolved_action':resolved_action,'identity_id':iid,'identity_name':ident.name,'skill_id':skill.id,'skill_name':skill.name,'original_skill_id':original_skill_id,'transformation':transform_info,'damage':action_damage,'expected_damage':action_expected_damage,'expected_reuse_count':expected_reuse_count,'reuse_probability':reuse_summary,'main_target_damage':float((state.runtime.get('current_action_damage_by_target') or {}).get(str(state.runtime.get('target_selection',{}).get('resolved_ids',["main"])[0]), action_damage)) if state.runtime.get('current_action_damage_by_target') else action_damage,
                    'additional_target_damage':float(action_damage - ((state.runtime.get('current_action_damage_by_target') or {}).get(str(state.runtime.get('target_selection',{}).get('resolved_ids',["main"])[0]), action_damage))) if state.runtime.get('current_action_damage_by_target') else action_damage*max(0,target_count-1),
                    'total_damage_all_targets':action_damage if action_has_explicit_targets else action_damage*target_count,
                    'damage_by_target':deepcopy(state.runtime.get('current_action_damage_by_target',{})),
                    'expected_main_target_damage':action_expected_damage if not state.runtime.get('current_action_damage_by_target') else float((state.runtime.get('current_action_damage_by_target') or {}).get(str(state.runtime.get('target_selection',{}).get('resolved_ids',["main"])[0]), action_expected_damage)),
                    'expected_additional_target_damage':action_expected_damage*max(0,target_count-1) if not state.runtime.get('current_action_damage_by_target') else max(0.0, action_expected_damage-float((state.runtime.get('current_action_damage_by_target') or {}).get(str(state.runtime.get('target_selection',{}).get('resolved_ids',["main"])[0]), action_expected_damage))),
                    'expected_total_damage_all_targets':action_expected_damage if action_has_explicit_targets else action_expected_damage*target_count,'faces':faces,'outcome':outcome,'coins':action_coins,'clash_trace':clash_trace,'bleed_probability':bleed_probability_result,'bleed_consumption':bleed_consumption,'resonance':res_info,'condition_modifiers':mods,'resource_consumption':dict(consumed_this_action),'resource_dynamic_damage_bonus':state.runtime.get('current_action_dynamic_damage_bonus',0.0),'generated':request.generated,'reason':request.reason,'target_policy':request.target_policy,'target_index':request.target_index,'target_ids':request.target_ids,'target_override_ids':request.target_override_ids,'coin_target_ids':request.coin_target_ids,'resolved_target_selection':deepcopy(state.runtime.get('target_selection',{})),
                    'requested_index':request.requested_index,'source_action_index':request.source_action_index,
                    'source_event':request.source_event,'trigger_chain':list(request.trigger_chain),'execution_index':idx,'depth':request.depth,
                    'state_at_action_start':{
                        'enemy_hp':action_start_hp,
                        'enemy_staggered':action_start_staggered,
                        'enemy_stagger_level':int(state.enemy.stagger_level),
                        'enemy_stagger_index':int(state.enemy.stagger_index),
                        'enemy_statuses':action_start_enemy_statuses,
                        'fighter_sp':action_start_sp,
                        'fighter_charge':action_start_charge,
                        'fighter_ammo':action_start_ammo,
                        'fighter_poise':action_start_poise,
                        'fighter_resources':action_start_resources_full,
                        'fighter_statuses':action_start_statuses,
                    },
                    'state_at_action_end':{
                        'enemy_hp':float(state.enemy.hp),
                        'enemy_staggered':bool(state.enemy.staggered),
                        'enemy_stagger_level':int(state.enemy.stagger_level),
                        'enemy_stagger_index':int(state.enemy.stagger_index),
                        'enemy_statuses':{k:deepcopy(v.__dict__) for k,v in getattr(state.enemy, 'statuses', {}).items()},
                        'fighter_sp':float(fighter_now.sp),
                        'fighter_charge':int(getattr(fighter_now, 'charge', 0)),
                        'fighter_ammo':int(getattr(fighter_now, 'ammo', 0)),
                        'fighter_poise':deepcopy(fighter_now.poise.__dict__),
                        'fighter_resources':action_end_resources,
                        'fighter_statuses':{k:deepcopy(v.__dict__) for k,v in getattr(fighter_now, 'statuses', {}).items()},
                    },
                    'state_diff': action_state_diff(
                        {
                            'enemy_hp': action_start_hp,
                            'enemy_staggered': action_start_staggered,
                            'enemy_stagger_level': action_start_enemy_stagger_level,
                            'enemy_stagger_index': action_start_enemy_stagger_index,
                            'enemy_statuses': action_start_enemy_statuses,
                            'fighter_sp': action_start_sp,
                            'fighter_charge': action_start_charge,
                            'fighter_ammo': action_start_ammo,
                            'fighter_poise': action_start_poise,
                            'fighter_resources': action_start_resources_full,
                            'fighter_statuses': action_start_statuses,
                        },
                        {
                            'enemy_hp': float(state.enemy.hp),
                            'enemy_staggered': bool(state.enemy.staggered),
                            'enemy_stagger_level': int(state.enemy.stagger_level),
                            'enemy_stagger_index': int(state.enemy.stagger_index),
                            'enemy_statuses': {k: deepcopy(v.__dict__) for k, v in getattr(state.enemy, 'statuses', {}).items()},
                            'fighter_sp': float(fighter_now.sp),
                            'fighter_charge': int(getattr(fighter_now, 'charge', 0)),
                            'fighter_ammo': int(getattr(fighter_now, 'ammo', 0)),
                            'fighter_poise': deepcopy(fighter_now.poise.__dict__),
                            'fighter_resources': action_end_resources,
                            'fighter_statuses': {k: deepcopy(v.__dict__) for k, v in getattr(fighter_now, 'statuses', {}).items()},
                        },
                    )
                })
            # Drain target-local death callbacks collected during coin resolution.
            # Resource/heal effects are already applied by the callback; any queued
            # generated actions are inserted only after the full source action.
            pending_kills = list(state.runtime.pop('pending_target_kill_actions', []))
            state.runtime['pending_target_kill_actions'] = []
            for ga, kill_ctx in pending_kills:
                generated = action_queue.triggered_from(
                    request, ga.identity_id, ga.skill_id, ga.reason,
                    source_event='after_target_kill', faces=ga.forced_faces,
                    target_policy=ga.target_policy, target_index=ga.target_index,
                    target_ids=ga.target_ids, target_override_ids=ga.target_override_ids, coin_target_ids=ga.coin_target_ids,
                    trigger_kind=ga.trigger_kind,
                )
                queued = action_queue.enqueue_triggered(generated)
                state.event_log.append({
                    'event':'target_kill_action_queued', 'action_index':idx,
                    'queued':queued, 'identity_id':ga.identity_id, 'skill_id':ga.skill_id,
                    'trigger_kind':ga.trigger_kind, 'target_id':kill_ctx.get('target_id'),
                    'reason':ga.reason, 'requested_index':request.requested_index,
                    'depth':generated.depth, 'trigger_chain':generated.trigger_chain,
                })

            # Kill-triggered skill reuse: when this action newly kills the main
            # target, queue the same skill once (or according to its declarative
            # rule).  The reused copy is marked so it cannot recursively trigger
            # another kill-reuse cycle.  Because this calculator uses an aggregate
            # target count rather than separate enemy objects, the reused skill is
            # meaningful only when another target slot exists.
            if (not request.suppress_kill_reuse
                    and action_start_hp > 0
                    and state.enemy.hp <= 0
                    and target_count > 1
                    and getattr(skill, 'kill_reuse_rules', None)):
                kill_key = f'{iid}:{skill.id}'
                used_kill = int(state.runtime.setdefault('kill_reuse_counts', {}).get(kill_key, 0))
                for kri, krule in enumerate(getattr(skill, 'kill_reuse_rules', []) or []):
                    limit = int(krule.get('max_reuses', 0))
                    if used_kill >= limit:
                        continue
                    if not self._condition_met(state, ident, krule.get('condition'), skill):
                        continue
                    state.runtime['kill_reuse_counts'][kill_key] = used_kill + 1
                    # Reset the aggregate main-target state to the configured
                    # enemy baseline to represent the next occupied target slot.
                    enemy_cfg = scenario.get('enemy', {}) or {}
                    state.enemy.hp = float(enemy_cfg.get('hp', enemy_cfg.get('max_hp', state.enemy.max_hp)))
                    state.enemy.stagger_level = int(enemy_cfg.get('stagger_level', 0))
                    state.enemy.stagger_index = int(enemy_cfg.get('stagger_index', 0))
                    generated = action_queue.triggered_from(
                        request, iid, skill.id,
                        f'kill_reuse:{skill.id}',
                        source_event='kill_reuse',
                        faces=list(faces),
                        suppress_kill_reuse=True,
                    )
                    queued = action_queue.enqueue_triggered(generated)
                    state.event_log.append({
                        'event': 'kill_reuse_queued',
                        'action_index': idx,
                        'identity_id': iid,
                        'skill_id': skill.id,
                        'reason': 'target_killed',
                        'target_slot_consumed': 1,
                        'queued': queued,
                        'requested_index': request.requested_index,
                        'depth': generated.depth,
                    })
                    break

            # Special mechanics can enqueue additional attacks. They execute
            # immediately after the triggering action. Trigger evaluation receives
            # both action-start and action-end stagger state, so effects such as
            # 'was not staggered before the attack, then became staggered' are
            # distinguishable from an already-staggered target.
            action_end_staggered = bool(state.enemy.staggered)
            negative_status_names = {"Bleed","Burn","Rupture","Sinking","Tremor","Bind","Vulnerable","Defense Level Down","Attack Power Down","Offense Level Down","Damage Taken Up","Paralyze","Nails","Talisman","Dark Flame","Butterfly","Tremor - Scorch","Tremor Burst"}
            status_applied = False
            for _name in negative_status_names:
                _before = action_start_enemy_statuses.get(_name, {}) if 'action_start_enemy_statuses' in locals() else {}
                if isinstance(_before, dict): _before = (int(_before.get('potency',0)), int(_before.get('count',0)))
                _st = state.enemy.statuses.get(_name)
                _after = (int(getattr(_st, 'potency', 0)), int(getattr(_st, 'count', 0))) if _st is not None else (0, 0)
                if _after[0] > _before[0] or _after[1] > _before[1]:
                    status_applied = True; break
            trigger_ctx = {
                'action_index': idx,
                'action_start_staggered': action_start_staggered,
                'action_end_staggered': action_end_staggered,
                'action_start_hp': action_start_hp,
                'action_end_hp': float(state.enemy.hp),
                'target_died': bool(action_start_hp > 0 and state.enemy.hp <= 0),
                'negative_status_applied': bool(status_applied),
                'state': state,
                'action_queue': action_queue,
                'source_action': request,
                'identity_map': identity_map,
                'event': 'after_clash',
                'generated': request.generated,
                'resources': dict(getattr(state.fighters.get(iid), 'resources', {}) or {}),
                'current_resonance': dict(state.runtime.get('current_resonance', {}) or {}),
                'enemy_hp': float(state.enemy.hp),
                'enemy_max_hp': float(state.enemy.max_hp),
                'actual_damage': float(state.turn_damage - before),
                'action_ammo_spent': max(0, action_start_ammo - int(getattr(state.fighters[iid], 'ammo', 0))),
                'is_lowest_ammo_identity': state.runtime.get('ammo_min_identity') == iid,
                'available_identity_ids': list(getattr(gimmicks, 'available_identity_ids', []) or []),
                'actor_statuses': {k: v.__dict__ for k, v in getattr(state.fighters.get(iid), 'statuses', {}).items()} if state.fighters.get(iid) is not None else {},
                'action_start_poise_potency': int(getattr(getattr(state.fighters.get(iid), 'poise', None), 'potency', 0)),
                'action_start_poise_count': int(getattr(getattr(state.fighters.get(iid), 'poise', None), 'count', 0)),
                'action_end_poise_potency': int(getattr(getattr(state.fighters.get(iid), 'poise', None), 'potency', 0)),
                'action_end_poise_count': int(getattr(getattr(state.fighters.get(iid), 'poise', None), 'count', 0)),
            }
            trigger_ctx['action_end_poise_potency'] = int(getattr(getattr(state.fighters.get(iid), 'poise', None), 'potency', 0))
            trigger_ctx['action_end_poise_count'] = int(getattr(getattr(state.fighters.get(iid), 'poise', None), 'count', 0))
            for ga in gimmicks.after_skill(ident,skill,trigger_ctx):
                generated_skill_id = ga.skill_id
                generated_faces = ga.forced_faces
                # Support-attack skill selection is deliberately deterministic:
                # for a formation-relative support command, use the selected
                # ally's next *requested* action.  Do not invent a skill, pick
                # the highest-damage skill, or consume the original request.
                # This also permits the same identity to act again later.
                if generated_skill_id == '__support_default__':
                    generated_skill_id = None
                    selected_pending = None
                    for pending in action_queue.items[action_queue.position:]:
                        if (not pending.generated and str(pending.identity_id) == str(ga.identity_id)):
                            selected_pending = pending
                            generated_skill_id = pending.skill_id
                            if generated_faces is None and pending.faces is not None:
                                generated_faces = list(pending.faces)
                            break
                    if generated_skill_id is None:
                        state.event_log.append({'event':'gimmick_action_skipped','action_index':idx,
                            'reason':'captain_right_assist_no_pending_requested_skill','identity_id':ga.identity_id,
                            'skill_selection_policy':'next_requested_action'})
                        continue
                # A trigger rule's ``main`` policy is its historical default, not an
                # instruction to discard the source action's explicit target.
                # Preserve the triggering action's target metadata unless the
                # gimmick explicitly selects another policy/index/id set.
                generated, queued = action_queue.enqueue_generated(
                    request, ga.identity_id, generated_skill_id, ga.reason,
                    source_event=ga.trigger_kind, faces=generated_faces,
                    target_policy=ga.target_policy, target_index=ga.target_index,
                    target_ids=ga.target_ids, coin_target_ids=ga.coin_target_ids,
                    trigger_kind=ga.trigger_kind, inherit_target=True,
                )
                state.event_log.append({'event':'gimmick_action_queued','action_index':idx,
                                        'queued':queued,'reason':ga.reason,'source':ga.source,
                                        'identity_id':ga.identity_id,'skill_id':ga.skill_id,
                                        'trigger_kind':ga.trigger_kind,'trigger_context':trigger_ctx,
                                        'requested_index':request.requested_index,
                                        'depth':generated.depth,'trigger_chain':generated.trigger_chain})
            # Resource threshold triggers are evaluated after the source action.
            # This preserves the user's requested order while allowing a threshold
            # reached during a skill/coin to affect subsequent actions immediately.
            # Drain newly-created threshold events as well, so a trigger that
            # gains/consumes another resource can form a finite resource chain.
            while resource_event_cursor < len(state.event_log):
                rev=state.event_log[resource_event_cursor]; resource_event_cursor += 1
                if rev.get('event') not in ('resource_threshold_reached','resource_cumulative_consumed','resource_overflow'):
                    continue
                if 'identity_id' not in rev: rev['identity_id']=iid
                for ga in gimmicks.after_resource_event(state, rev, identity_map, action_index=idx):
                    generated=action_queue.triggered_from(request, ga.identity_id, ga.skill_id, ga.reason,
                        source_event=ga.trigger_kind, faces=ga.forced_faces,
                        target_policy=ga.target_policy, target_index=ga.target_index, target_ids=ga.target_ids,
                        coin_target_ids=ga.coin_target_ids,
                        trigger_kind=ga.trigger_kind)
                    queued=action_queue.enqueue_triggered(generated)
                    state.event_log.append({'event':'resource_trigger_action_queued','action_index':idx,
                        'queued':queued,'identity_id':ga.identity_id,'skill_id':ga.skill_id,
                        'trigger_kind':ga.trigger_kind,'source_event':'resource_threshold_reached',
                        'depth':generated.depth,'trigger_chain':generated.trigger_chain})
        # Phase 3: turn finalization / result assembly.
        return self._finalize_turn(
            state=state, scenario=scenario, identity_map=identity_map, out=out,
            action_queue=action_queue, target_count=target_count,
            damage_by_identity=damage_by_identity, damage_by_skill=damage_by_skill,
            expected_damage_by_identity=expected_damage_by_identity,
            expected_damage_by_skill=expected_damage_by_skill,
            expected_turn_damage=expected_turn_damage,
            expected_turn_base_state=expected_turn_base_state,
            gimmicks=gimmicks, resonance_plan=resonance_plan,
            selected_passives=selected_passives,
            passive_variant_mode=passive_variant_mode, resource_runtime=resource_runtime,
        )

    def _finalize_turn(self, *, state, scenario, identity_map, out, action_queue, target_count, damage_by_identity, damage_by_skill, expected_damage_by_identity, expected_damage_by_skill, expected_turn_damage, expected_turn_base_state, gimmicks, resonance_plan, selected_passives, passive_variant_mode, resource_runtime):
        self.core.machine.end_turn(state)
        # Full-turn Bleed-state DP runs in parallel with the authoritative
        # deterministic solver. It carries branch-specific Bleed Count into
        # later requested actions instead of reusing one action-local mean.
        turn_bleed_state = self._probabilistic_turn_state(expected_turn_base_state, scenario, identity_map, out)
        if turn_bleed_state is not None and turn_bleed_state.get('final_state_signature'):
            turn_bleed_state['final_condition_flags'] = list(turn_bleed_state['final_state_signature'][-3])
        if turn_bleed_state is not None:
            expected_turn_damage = float(turn_bleed_state['expected_turn_damage'])
            expected_damage_by_identity = dict(turn_bleed_state['expected_damage_by_identity'])
            expected_damage_by_skill = dict(turn_bleed_state['expected_damage_by_skill'])
        requested_plan=[x.to_dict() for x in action_queue.items if not x.generated]
        # Keep legacy `turn_damage` as the main-target damage. Expose aggregate
        # multi-target totals separately so existing callers remain compatible.
        expected_main_target_damage = float(turn_bleed_state['expected_turn_damage'] if turn_bleed_state is not None else expected_turn_damage)
        explicit_targets = bool(state.runtime.get('enemy_target_states'))
        if explicit_targets:
            main_damage_by_identity = {iid:0.0 for iid in identity_map}
            additional_damage_by_identity = {iid:0.0 for iid in identity_map}
            main_damage_by_skill = {}
            additional_damage_by_skill = {}
            for row in out:
                iid=row['identity_id']; sk=f"{iid}:{row['skill_id']}"
                dm=row.get('damage_by_target',{}) or {}
                ids=list(dm.keys())
                primary_id=str(state.runtime.get('enemy_target_states',[{}])[0].get('id','0'))
                primary=float(dm.get(primary_id,0.0))
                extra=max(0.0,float(sum(dm.values()))-primary)
                main_damage_by_identity[iid]=main_damage_by_identity.get(iid,0.0)+primary
                additional_damage_by_identity[iid]=additional_damage_by_identity.get(iid,0.0)+extra
                main_damage_by_skill[sk]=main_damage_by_skill.get(sk,0.0)+primary
                additional_damage_by_skill[sk]=additional_damage_by_skill.get(sk,0.0)+extra
            total_damage_by_identity={iid:main_damage_by_identity.get(iid,0.0)+additional_damage_by_identity.get(iid,0.0) for iid in identity_map}
            total_damage_by_skill={k:main_damage_by_skill.get(k,0.0)+additional_damage_by_skill.get(k,0.0) for k in set(main_damage_by_skill)|set(additional_damage_by_skill)}
            expected_main_damage_by_identity=dict(main_damage_by_identity)
            expected_additional_damage_by_identity=dict(additional_damage_by_identity)
            expected_total_damage_by_identity=dict(total_damage_by_identity)
            expected_main_damage_by_skill=dict(main_damage_by_skill)
            expected_additional_damage_by_skill=dict(additional_damage_by_skill)
            expected_total_damage_by_skill=dict(total_damage_by_skill)
            expected_total_all_targets=float(state.turn_damage)
            final_main=float(sum(main_damage_by_identity.values()))
            final_additional=float(sum(additional_damage_by_identity.values()))
            final_total=float(state.turn_damage)
        else:
            main_damage_by_identity = dict(damage_by_identity)
            additional_damage_by_identity = {iid: dmg * max(0, target_count-1) for iid, dmg in main_damage_by_identity.items()}
            total_damage_by_identity = {iid: dmg * target_count for iid, dmg in main_damage_by_identity.items()}
            expected_main_damage_by_identity = dict(expected_damage_by_identity)
            expected_additional_damage_by_identity = {iid: dmg * max(0, target_count-1) for iid, dmg in expected_main_damage_by_identity.items()}
            expected_total_damage_by_identity = {iid: dmg * target_count for iid, dmg in expected_main_damage_by_identity.items()}
            main_damage_by_skill = dict(damage_by_skill)
            additional_damage_by_skill = {k: dmg * max(0, target_count-1) for k, dmg in main_damage_by_skill.items()}
            total_damage_by_skill = {k: dmg * target_count for k, dmg in main_damage_by_skill.items()}
            expected_main_damage_by_skill = dict(expected_damage_by_skill)
            expected_additional_damage_by_skill = {k: dmg * max(0, target_count-1) for k, dmg in expected_main_damage_by_skill.items()}
            expected_total_damage_by_skill = {k: dmg * target_count for k, dmg in expected_main_damage_by_skill.items()}
            expected_total_all_targets = expected_main_target_damage * target_count
            final_main=float(state.turn_damage); final_additional=float(state.turn_damage*max(0,target_count-1)); final_total=float(state.turn_damage*target_count)
        target_state_output={}
        for x in state.runtime.get('enemy_target_states',[]):
            e=x['state']; target_state_output[str(x['id'])]={'index':int(x['index']),'hp':float(e.hp),'max_hp':float(e.max_hp),'staggered':bool(e.staggered),'stagger_level':int(e.stagger_level),'stagger_index':int(e.stagger_index),'statuses':{k:v.__dict__.copy() for k,v in e.statuses.items()},'is_abnormality':bool(getattr(e,'is_abnormality',False))}
        return {'requested_plan':requested_plan,'execution_count':len(action_queue.executed),'target_count':target_count,'main_target_damage':final_main,'additional_target_damage':final_additional,'total_damage_all_targets':final_total,'turn_damage':state.turn_damage,'expected_turn_damage':expected_main_target_damage,'expected_main_target_damage':expected_main_target_damage,'expected_additional_target_damage':expected_main_target_damage*max(0,target_count-1) if not explicit_targets else final_additional,'expected_total_damage_all_targets':expected_total_all_targets,'action_local_expected_turn_damage':expected_turn_damage,'turn_bleed_state':turn_bleed_state,'enemy_hp_before':float(scenario.get('enemy',{}).get('hp',scenario.get('enemy',{}).get('max_hp',1))),'enemy_hp_after':state.enemy.hp,'target_states':target_state_output,'actions':out,'fighters':{i:{'sp':f.sp,'charge':f.charge,'charge_potency':getattr(f,'charge_potency',0),'ammo':f.ammo,'defense_level_bonus':getattr(f,'defense_level_bonus',0),'shield':getattr(f,'shield',0.0),'charge_barrier':resource_runtime.get(f,'충전 역장',0),'charge_barrier_shield':getattr(f,'charge_barrier_shield',0.0),'resources':dict(f.resources),'poise':f.poise.__dict__.copy(),'statuses':{k:v.__dict__.copy() for k,v in f.statuses.items()}} for i,f in state.fighters.items()},'resource_specs':{k:{'minimum':v.minimum,'maximum':v.maximum,'threshold_variants':dict(v.threshold_variants),'threshold_operators':dict(v.threshold_operators),'turn_reset':v.turn_reset} for k,v in resource_runtime.specs.items()},'enemy_sp':state.enemy.sp,'enemy_stagger_level':state.enemy.stagger_level,'enemy_stagger_index':state.enemy.stagger_index,'enemy_stagger_thresholds':list(state.enemy.stagger_thresholds),'enemy_staggered':state.enemy.staggered,'damage_by_identity':damage_by_identity,'damage_by_skill':damage_by_skill,'main_target_damage_by_identity':main_damage_by_identity,'additional_target_damage_by_identity':additional_damage_by_identity,'total_damage_all_targets_by_identity':total_damage_by_identity,'expected_damage_by_identity':expected_damage_by_identity,'expected_damage_by_skill':expected_damage_by_skill,'expected_main_target_damage_by_identity':expected_main_damage_by_identity,'expected_additional_target_damage_by_identity':expected_additional_damage_by_identity,'expected_total_damage_all_targets_by_identity':expected_total_damage_by_identity,'main_target_damage_by_skill':main_damage_by_skill,'additional_target_damage_by_skill':additional_damage_by_skill,'total_damage_all_targets_by_skill':total_damage_by_skill,'expected_main_target_damage_by_skill':expected_main_damage_by_skill,'expected_additional_target_damage_by_skill':expected_additional_damage_by_skill,'expected_total_damage_all_targets_by_skill':expected_total_damage_by_skill,'enemy_statuses':{k:v.__dict__.copy() for k,v in state.enemy.statuses.items()},'virtual_bleed_count':float(state.runtime.get('virtual_bleed_count',0.0)),'event_log':state.event_log,'passive_trace':getattr(self.core.machine.passive_runtime,'trace',[]),'resonance':resonance_plan,'gimmicks':gimmicks.summary(),'trigger_rules':gimmicks.trigger_rules_data(),'passive_variant_mode':passive_variant_mode,'active_passives':{iid:[p.get('name','') for p in ps] for iid,ps in selected_passives.items()},'action_trace':out,'state_diff':{'enemy_hp_delta':float(state.enemy.hp)-float(scenario.get('enemy',{}).get('hp',scenario.get('enemy',{}).get('max_hp',1))),'turn_damage':float(state.turn_damage)},'next_turn_state':deepcopy(state.runtime.get('next_turn_state',{}))}

    def enumerate_branches(self, scenario, identity_map):
        import itertools
        total=sum(len(self._skill(identity_map[str(a['identity_id'])],a['skill_id']).coins) for a in scenario.get('actions',[]))
        limit=int(scenario.get('max_enumerated_coins',16))
        if total>limit: raise ValueError(f'enumeration blocked: {total} coins > {limit}')
        results=[]
        for flat in itertools.product(('H','T'), repeat=total):
            sc=deepcopy(scenario); pos=0
            for a in sc.get('actions',[]):
                n=len(self._skill(identity_map[str(a['identity_id'])],a['skill_id']).coins); a['faces']=list(flat[pos:pos+n]); pos+=n
            sc['coin_mode']='fixed'; results.append(self.solve(sc,identity_map))
        return results


# Backward-compatible aliases for existing callers.
OneTurnSolverV21 = OneTurnSolverV29
IdentityCatalogV19 = IdentityCatalogV29
