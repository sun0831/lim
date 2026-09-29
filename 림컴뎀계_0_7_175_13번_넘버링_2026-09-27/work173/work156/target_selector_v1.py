"""Deterministic target-selection primitives for one-turn simulation.

The current engine still uses an aggregate enemy state by default. This module
normalizes explicit target-selection requests and can select from a list of
enemy slot dictionaries when a scenario provides per-target data. It never
guesses a target when the requested selector cannot be evaluated.
"""
from __future__ import annotations
from typing import Any, Dict, List, Optional
import random

ALIASES = {
    "fastest": "speed_max", "slowest": "speed_min",
    "fastest_ally": "speed_max", "slowest_ally": "speed_min",
    "highest_hp": "hp_max", "lowest_hp": "hp_min",
    "highest_hp_percent": "hp_percent_max", "lowest_hp_percent": "hp_percent_min",
    "leftmost": "formation_min", "rightmost": "formation_max",
    "fastest_formation_ally": "formation_min", "slowest_formation_ally": "formation_max",
    "earliest_ally": "formation_min", "latest_ally": "formation_max",
    "random": "random", "event_target": "explicit",
    "main": "explicit", "lowest_hp_staggered": "lowest_hp_staggered", "primary": "explicit",
    "highest_tremor_count": "highest_status_count:Tremor", "lowest_tremor_count": "lowest_status_count:Tremor",
    "highest_taunt": "taunt_max", "highest_provoke": "taunt_max",
    "faster_roster_allies": "formation_before_owner",
    "slower_roster_allies": "formation_after_owner",
    "lowest_charge_among_faster_allies": "formation_before_owner_charge_min",
    "lowest_charge_holder": "charge_positive_min",
    "formation_1": "formation_slot:1",
    "formation_2": "formation_slot:2",
    "formation_3": "formation_slot:3",
    "lowest_sp_among_fanatics": "status_present_sp_min:광신",
}

def normalize(policy: Any) -> Optional[str]:
    if policy is None: return None
    p=str(policy).strip().lower()
    return ALIASES.get(p, p)

def select_targets(targets: List[Dict[str,Any]], policy: Any, count: int = 1, target_index: Optional[int] = None, target_ids: Optional[List[str]] = None, rng: Optional[random.Random] = None) -> List[Dict[str,Any]]:
    if not targets: return []
    # target_ids is the generic explicit selector; callers can map a
    # target_override_ids field to it before calling this primitive.
    if target_ids:
        wanted={str(x) for x in target_ids}
        return [t for t in targets if str(t.get("id",t.get("index",""))) in wanted][:max(1,int(count))]
    if target_index is not None:
        i=int(target_index)
        return [targets[i]] if 0 <= i < len(targets) else []
    p=normalize(policy)
    if not p or p in ("explicit","selected"): return targets[:max(1,int(count))]
    def num(t,k,default=0):
        try: return float(t.get(k,default))
        except (TypeError,ValueError): return float(default)
    def status_obj(t,name):
        sts=t.get("statuses",{}) or {}
        st=sts.get(name,{})
        if st != {}: return st
        lname=str(name).lower()
        for k,v in sts.items():
            if str(k).lower()==lname: return v
        return {}
    if p.startswith("formation_slot:"):
        try: slot=int(p.split(":",1)[1])
        except (TypeError,ValueError): return []
        if slot < 1: return []
        # Game-facing formation positions are 1-based.
        out=[t for t in targets if int(num(t,"formation_index",t.get("index",0))) == slot]
        return out[:max(1,int(count))]
    if p == "lowest_hp_staggered":
        # Prefer newly staggered targets.  For abnormality multi-part targets,
        # the body (non-part) is preferred before parts, then lowest HP.
        candidates=[]
        for t in targets:
            st=t.get('state')
            staggered=bool(getattr(st,'staggered',False)) if st is not None else bool(t.get('staggered',False))
            if not staggered:
                continue
            abnormality=bool(t.get('is_abnormality', getattr(st,'is_abnormality',False) if st is not None else False))
            is_part=bool(t.get('is_part', t.get('part', False)))
            candidates.append((0 if (abnormality and not is_part) else 1, num(t,'hp',t.get('max_hp',0)), num(t,'formation_index',t.get('index',0)), t))
        if not candidates:
            return []
        candidates.sort(key=lambda x:(x[0],x[1],x[2]))
        return [candidates[0][3]]
    if p == "random":
        # Random targeting is now reproducible when the caller supplies a seeded
        # RNG.  Without one we still use Python's RNG, but never silently turn
        # the request into "no target".
        chooser = rng if rng is not None else random
        # In combat, dead targets are not valid random recipients.  Preserve
        # the explicit target list only as a fallback when every slot is dead.
        alive = [t for t in targets if num(t, "hp", t.get("max_hp", 0)) > 0]
        pool = alive or list(targets)
        n = min(max(1, int(count)), len(pool))
        return chooser.sample(pool, n)
    if p == "taunt_max":
        def key(t):
            # Accept the common normalized field plus legacy/source aliases.
            return num(t, "taunt", t.get("taunt_value", t.get("provoke", 0)))
    elif p == "speed_max": key=lambda t:num(t,"speed")
    elif p == "speed_min": key=lambda t:num(t,"speed")
    elif p == "hp_max": key=lambda t:num(t,"hp",t.get("max_hp",0))
    elif p == "hp_min": key=lambda t:num(t,"hp",t.get("max_hp",0))
    elif p == "hp_percent_max": key=lambda t:num(t,"hp",0)/max(num(t,"max_hp",1),1)
    elif p == "hp_percent_min": key=lambda t:num(t,"hp",0)/max(num(t,"max_hp",1),1)
    elif p == "charge_positive_min":
        eligible=[t for t in targets if num(t,"charge",0) > 0]
        if not eligible: return []
        targets=eligible
        key=lambda t:num(t,"charge",0)
    elif p == "formation_min": key=lambda t:num(t,"formation_index",t.get("index",0))
    elif p == "formation_max": key=lambda t:num(t,"formation_index",t.get("index",0))
    elif p == "poise_potency_max":
        name="Poise"
        def key(t):
            st=status_obj(t,name)
            return num(st,"potency",0) if isinstance(st,dict) else num(st,"potency",getattr(st,"potency",0))
    elif p == "poise_potency_min":
        name="Poise"
        def key(t):
            st=status_obj(t,name)
            return num(st,"potency",0) if isinstance(st,dict) else num(st,"potency",getattr(st,"potency",0))
    elif p == "poise_count_max":
        name="Poise"
        def key(t):
            st=status_obj(t,name)
            return num(st,"count",0) if isinstance(st,dict) else num(st,"count",getattr(st,"count",0))
    elif p == "poise_count_min":
        name="Poise"
        def key(t):
            st=status_obj(t,name)
            return num(st,"count",0) if isinstance(st,dict) else num(st,"count",getattr(st,"count",0))
    elif p.startswith("highest_status:"):
        name=p.split(":",1)[1]
        def key(t):
            st=status_obj(t,name)
            if isinstance(st,dict): return num(st,"potency",0)
            return num(st,"potency",getattr(st,"potency",0))
    elif p.startswith("lowest_status:"):
        name=p.split(":",1)[1]
        def key(t):
            st=status_obj(t,name)
            if isinstance(st,dict): return num(st,"potency",0)
            return num(st,"potency",getattr(st,"potency",0))
    elif p.startswith("highest_status_count:"):
        name=p.split(":",1)[1]
        def key(t):
            st=status_obj(t,name)
            if isinstance(st,dict): return num(st,"count",0)
            return num(st,"count",getattr(st,"count",0))
    elif p.startswith("lowest_status_count:"):
        name=p.split(":",1)[1]
        def key(t):
            st=status_obj(t,name)
            if isinstance(st,dict): return num(st,"count",0)
            return num(st,"count",getattr(st,"count",0))
    elif p.startswith("highest_status_total:"):
        name=p.split(":",1)[1]
        def key(t):
            st=status_obj(t,name)
            if isinstance(st,dict):
                return num(st,"potency",0) + num(st,"count",0)
            return num(st,"potency",getattr(st,"potency",0)) + num(st,"count",getattr(st,"count",0))
    elif p.startswith("status_present_sp_min:"):
        name=p.split(":",1)[1]
        targets=[t for t in targets if status_obj(t,name)]
        if not targets: return []
        key=lambda t:num(t,"sp",0)
    elif p.startswith("status_present_sp_max:"):
        name=p.split(":",1)[1]
        targets=[t for t in targets if status_obj(t,name)]
        if not targets: return []
        key=lambda t:num(t,"sp",0)
    elif p.startswith("lowest_status_total:"):
        name=p.split(":",1)[1]
        def key(t):
            st=status_obj(t,name)
            if isinstance(st,dict):
                return num(st,"potency",0) + num(st,"count",0)
            return num(st,"potency",getattr(st,"potency",0)) + num(st,"count",getattr(st,"count",0))
    else: return []
    reverse=p.endswith("_max") or p in ("speed_max","hp_max","hp_percent_max","formation_max","taunt_max") or p.startswith("highest_status:") or p.startswith("highest_status_count:") or p.startswith("highest_status_total:")
    return sorted(targets,key=key,reverse=reverse)[:max(1,int(count))]
