"""Common evaluator for Rule IR conditions.

The evaluator deliberately reuses the semantics of TriggerRuntime without
making Rule IR depend on the legacy TriggerCondition class.  Unsupported
operations return False rather than guessing.
"""
from __future__ import annotations
from typing import Any, Dict, Iterable
from rule_ir_v1 import ConditionIR

class ConditionRuntime:
    # Explicit operator registry used by both legacy compatibility and Rule IR
    # migration. Unsupported operators must never be guessed.
    SUPPORTED_OPS = frozenset({
        "always", "equals", "not_equals", "gte", "lte", "gt", "lt", "in",
        "skill_name_contains", "skill_name_any", "skill_basic", "skill_defense",
        "clash_outcome", "actual_damage_gt_zero", "formation_first_actor",
        "support_target_actor", "generated", "is_crit", "final_ammo_coin", "identity_id_in",
        "actor_id_in", "identity_id_not", "owner_id", "actor_id", "skill_slot",
        "target_id_in", "received_target_id", "received_target_id_in", "target_died",
        "received_target_died", "target_available", "has_status", "actor_has_status", "has_buff", "has_debuff",
        "flag", "action_start_not_staggered", "action_end_staggered", "newly_staggered", "stagger_forced", "newly_staggered_nonforced",
        "poise_gained", "coin_reuse", "highest_resonance_gte", "resonance_count_gte",
        "resource", "resource_variant", "resource_gte", "resource_lte", "resource_value",
        "resource_delta_gte", "resource_delta_lte", "cumulative_resource_crossed",
        "resource_threshold_gte", "resource_threshold_lte", "resource_threshold_operator",
        "negative_status_applied",
        "coin_index", "owner_not_available", "received_target_hp_below_pct",
        "received_target_died_or_hp_below_pct", "received_target_damaged",
        "is_lowest_ammo_identity", "action_ammo_spent_gt_zero", "action_resource_consumed_gte", "killer_id",
        "status_count_gte", "status_count_lte", "status_potency_gte", "status_potency_lte",
        "enemy_hp_percent_lte", "enemy_hp_percent_gte", "self_hp_percent_lte",
        "self_hp_percent_gte",
    })

    @classmethod
    def is_supported(cls, op: str) -> bool:
        return str(op) in cls.SUPPORTED_OPS

    @staticmethod
    def _get(ctx: Dict[str, Any], path: Any, default=None):
        cur = ctx
        for part in str(path).split('.'):
            if isinstance(cur, dict) and part in cur:
                cur = cur[part]
            else:
                return default
        return cur

    @classmethod
    def evaluate(cls, condition: ConditionIR, ctx: Dict[str, Any]) -> bool:
        op = str(condition.op)
        a = dict(condition.args or {})
        v = a.get('value', a.get('expected'))
        field = a.get('field')
        get = lambda p, d=None: cls._get(ctx, p, d)
        try:
            if op == 'always': ok = True
            elif op == 'not':
                child = a.get('condition') or {}
                child_ir = type('ConditionProxy', (), {'op': child.get('op', 'always'), 'args': child.get('args', child)})()
                ok = not cls.evaluate(child_ir, ctx)
            elif op in ('and', 'or'):
                children = a.get('conditions', []) or []
                vals = []
                for child in children:
                    child_ir = type('ConditionProxy', (), {'op': child.get('op', 'always'), 'args': child.get('args', child)})()
                    vals.append(cls.evaluate(child_ir, ctx))
                ok = all(vals) if op == 'and' else any(vals)
            elif op == 'equals': ok = get(field) == v
            elif op == 'not_equals': ok = get(field) != v
            elif op == 'gte': ok = float(get(field, 0)) >= float(v)
            elif op == 'lte': ok = float(get(field, 0)) <= float(v)
            elif op == 'gt': ok = float(get(field, 0)) > float(v)
            elif op == 'lt': ok = float(get(field, 0)) < float(v)
            elif op == 'in': ok = get(field) in (v or [])
            elif op == 'skill_name_contains': ok = str(v) in str(get('skill_name', ''))
            elif op == 'skill_name_any': ok = any(str(x) in str(get('skill_name', '')) for x in (v or []))
            elif op == 'skill_basic': ok = str(get('skill_slot','')) in ('S1','S2','S3')
            elif op == 'skill_defense': ok = bool(get('skill_is_defense',False)) or str(get('skill_attack_type','')) in ('방어','defense','guard')
            elif op == 'clash_outcome': ok = str(get('outcome',get('clash_outcome',''))).lower() == str(v).lower()
            elif op == 'actual_damage_gt_zero': ok = float(get('actual_damage',0)) > 0
            elif op == 'negative_status_applied': ok = bool(get('negative_status_applied', False))
            elif op == 'formation_first_actor': ok = bool(get('is_formation_first_actor',False)) == bool(v)
            elif op == 'support_target_actor':
                policy = str(v or 'highest_sp')
                ok = bool((get('support_target_match', {}) or {}).get(policy, False))
            elif op == 'generated': ok = bool(get('generated',False)) == bool(v)
            elif op == 'is_crit': ok = bool(get('is_crit',False)) == bool(v)
            elif op == 'final_ammo_coin':
                ok = (int(get('ammo_spent',0)) > 0 and int(get('ammo_before',0)) > 0
                      and int(get('ammo_after',0)) == 0 and float(get('actual_damage',0)) > 0
                      and bool(get('is_lowest_ammo_identity',False)))
            elif op in ('identity_id_in','actor_id_in'): ok = str(get('identity_id',get('actor_id',''))) in {str(x) for x in (v or [])}
            elif op == 'identity_id_not': ok = str(get('identity_id',get('actor_id',''))) != str(v)
            elif op == 'owner_id': ok = str(get('identity_id',get('owner_id',''))) == str(v)
            elif op == 'actor_id': ok = str(get('identity_id','')) == str(v)
            elif op == 'skill_slot': ok = str(get('skill_slot','')) == str(v)
            elif op == 'coin_index': ok = int(get('coin_index',0)) == int(v)
            elif op == 'target_id_in': ok = str(get('target_id','')) in {str(x) for x in (v or [])}
            elif op == 'received_target_id': ok = str(get('received_target_id',get('target_id',''))) == str(v)
            elif op == 'received_target_id_in': ok = str(get('received_target_id',get('target_id',''))) in {str(x) for x in (v or [])}
            elif op in ('target_died','received_target_died'): ok = bool(get('target_died' if op=='target_died' else 'received_target_died',False)) == bool(v)
            elif op == 'target_available': ok = str(v) in set(get('available_identity_ids',[]))
            elif op == 'has_status': ok = bool((get('statuses',{}) or {}).get(str(v)))
            elif op == 'actor_has_status': ok = bool((get('actor_statuses',{}) or {}).get(str(v)))
            elif op in ('has_amplitude_state', 'amplitude_potency_gte'):
                state = get('state')
                target_name = str(a.get('target', 'enemy'))
                if target_name == 'enemy':
                    unit = getattr(state, 'enemy', None) if state is not None else None
                else:
                    fid = str(get('identity_id', get('actor_id', '')))
                    unit = (getattr(state, 'fighters', {}) or {}).get(fid) if state is not None else None
                from amplitude_runtime_v1 import AmplitudeRuntime
                rt = AmplitudeRuntime()
                amp = a.get('amplitude')
                mode = a.get('mode')
                if op == 'has_amplitude_state':
                    ok = bool(unit is not None and rt.has_state(unit, amp, mode))
                else:
                    threshold = float(a.get('threshold', field or 0))
                    entries = rt.get_states(unit) if unit is not None else []
                    ok = any(
                        (amp is None or str(e.get('amplitude')) == str(amp))
                        and (mode is None or str(e.get('mode')) == str(mode))
                        and float(e.get('tremor_potency', 0)) >= threshold
                        for e in entries
                    )
            elif op in ('has_buff','has_debuff'):
                target_id = str(get('identity_id', get('actor_id','')))
                bdr = get('buff_debuff_runtime')
                ok = bool(bdr and bdr.has(get('state'), target_id=target_id, name=str(v), kind='buff' if op=='has_buff' else 'debuff'))
            elif op == 'flag': ok = bool((get('condition_flags',{}) or {}).get(str(v)))
            elif op == 'action_start_not_staggered': ok = not bool(get('action_start_staggered',False))
            elif op == 'action_end_staggered': ok = bool(get('action_end_staggered',False))
            elif op == 'newly_staggered': ok = not bool(get('action_start_staggered',False)) and bool(get('action_end_staggered',False))
            elif op == 'stagger_forced': ok = bool(get('stagger_forced', get('forced_stagger', False))) == bool(v if v is not None else True)
            elif op == 'newly_staggered_nonforced':
                ok = (not bool(get('action_start_staggered',False))
                      and bool(get('action_end_staggered',False))
                      and not bool(get('stagger_forced', get('forced_stagger', False))))
            elif op == 'poise_gained': ok = float(get('action_end_poise_potency',0)) > float(get('action_start_poise_potency',0)) or float(get('action_end_poise_count',0)) > float(get('action_start_poise_count',0))
            elif op == 'coin_reuse': ok = (int(get('reuse_index',0)) > 0) == bool(v)
            elif op in ('highest_resonance_gte','resonance_count_gte'):
                counts=get('current_resonance',{}) or {}; ok=max([float(x) for x in counts.values()] or [0.0]) >= float(v or 0)
            elif op == 'resource': ok = str(get('resource','')) == str(v)
            elif op == 'resource_variant': ok = str(get('variant','')) == str(v)
            elif op == 'resource_gte': ok = float((get('resources',{}) or {}).get(str(v),0)) >= float(field or 0)
            elif op == 'resource_lte': ok = float((get('resources',{}) or {}).get(str(v),0)) <= float(field or 0)
            elif op == 'resource_value': ok = float(get('after',get('resource_value',0))) == float(v)
            elif op == 'resource_delta_gte': ok = float(get('delta',0)) >= float(v)
            elif op == 'resource_delta_lte': ok = float(get('delta',0)) <= float(v)
            elif op == 'cumulative_resource_crossed':
                before=int(get('cumulative_before',0)); after=int(get('cumulative_after',0)); step=int(v or 0)
                ok=step > 0 and (before // step) < (after // step)
            elif op == 'resource_threshold_gte': ok = float(get('after',0)) >= float(v)
            elif op == 'resource_threshold_lte': ok = float(get('after',0)) <= float(v)
            elif op == 'resource_threshold_operator':
                cmp_op=str(get('operator','>=')); x=float(get('after',0)); y=float(v)
                ok={'>' : x>y, '>=':x>=y, '<':x<y, '<=':x<=y, '==':x==y}.get(cmp_op,False)
            elif op == 'owner_not_available': ok = str(v) not in {str(x) for x in (get('available_identity_ids',[]) or [])}
            elif op == 'received_target_hp_below_pct':
                mx=float(get('received_target_max_hp',0) or 0); hp=float(get('received_target_hp',0) or 0)
                ok=mx > 0 and hp/mx*100 < float(v)
            elif op == 'received_target_died_or_hp_below_pct':
                mx=float(get('received_target_max_hp',0) or 0); hp=float(get('received_target_hp',0) or 0)
                ok=bool(get('received_target_died',False)) or (mx > 0 and hp/mx*100 < float(v))
            elif op == 'received_target_damaged': ok = bool(get('received_target_damaged',False)) == bool(v)
            elif op == 'is_lowest_ammo_identity': ok = bool(get('is_lowest_ammo_identity',False)) == bool(v)
            elif op == 'action_ammo_spent_gt_zero': ok = (int(get('action_ammo_spent',0)) > 0) == bool(v)
            elif op == 'action_resource_consumed_gte': ok = float((get('consumed_resources',{}) or {}).get(str(v),0)) >= float(field or 0)
            elif op == 'killer_id': ok = str(get('killer_id',get('identity_id',''))) == str(v)
            elif op == 'actor_has_status': ok = bool((get('actor_statuses',{}) or {}).get(str(v)))
            elif op in ('has_amplitude_state', 'amplitude_potency_gte'):
                state = get('state')
                target_name = str(a.get('target', 'enemy'))
                if target_name == 'enemy':
                    unit = getattr(state, 'enemy', None) if state is not None else None
                else:
                    fid = str(get('identity_id', get('actor_id', '')))
                    unit = (getattr(state, 'fighters', {}) or {}).get(fid) if state is not None else None
                from amplitude_runtime_v1 import AmplitudeRuntime
                rt = AmplitudeRuntime()
                amp = a.get('amplitude')
                mode = a.get('mode')
                if op == 'has_amplitude_state':
                    ok = bool(unit is not None and rt.has_state(unit, amp, mode))
                else:
                    threshold = float(a.get('threshold', field or 0))
                    entries = rt.get_states(unit) if unit is not None else []
                    ok = any(
                        (amp is None or str(e.get('amplitude')) == str(amp))
                        and (mode is None or str(e.get('mode')) == str(mode))
                        and float(e.get('tremor_potency', 0)) >= threshold
                        for e in entries
                    )
            elif op in ('has_buff','has_debuff'):
                target_id = str(get('identity_id', get('actor_id','')))
                bdr = get('buff_debuff_runtime')
                ok = bool(bdr and bdr.has(get('state'), target_id=target_id, name=str(v), kind='buff' if op=='has_buff' else 'debuff'))
            elif op in ('status_count_gte','status_count_lte','status_potency_gte','status_potency_lte'):
                target=str(get('status_target','self')); name=str(get('status_name',v)); statuses=get('enemy_statuses' if target=='enemy' else 'statuses',{}) or {}; st=statuses.get(name,{})
                key='count' if 'count' in op else 'potency'; val=float(st.get(key,0)) if isinstance(st,dict) else float(getattr(st,key,0)); threshold=float(a.get('threshold',field or 0)); ok=val >= threshold if op.endswith('_gte') else val <= threshold
            elif op in ('enemy_hp_percent_lte','enemy_hp_percent_gte','self_hp_percent_lte','self_hp_percent_gte'):
                side='enemy' if op.startswith('enemy_') else 'self'; hp=float(get(f'{side}_hp',0)); mx=float(get(f'{side}_max_hp',0)); pct=100*hp/mx if mx else 0; ok=pct <= float(v) if op.endswith('_lte') else pct >= float(v)
            else:
                return False
        except (TypeError, ValueError, ZeroDivisionError):
            ok=False
        return (not ok) if bool(a.get('negate',False)) else ok

    @classmethod
    def all(cls, conditions: Iterable[ConditionIR], ctx: Dict[str,Any]) -> bool:
        return all(cls.evaluate(c,ctx) for c in conditions)
