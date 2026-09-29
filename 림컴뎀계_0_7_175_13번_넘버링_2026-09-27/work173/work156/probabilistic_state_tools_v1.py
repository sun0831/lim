"""Small, reusable helpers for probabilistic branch state snapshots.

These helpers contain no turn-selection logic. They only serialize/restore the
small part of BattleState needed when probabilistic branches are merged.
"""
from copy import deepcopy

from limbus_damage_engine_v29 import Status


def action_state_diff(before, after):
    """Return a compact action-state delta for debugging and trace output."""
    def mapping_delta(a, b):
        a = a or {}
        b = b or {}
        keys = sorted(set(a) | set(b), key=str)
        changed = {}
        for k in keys:
            av, bv = a.get(k), b.get(k)
            if av != bv:
                changed[str(k)] = {'before': deepcopy(av), 'after': deepcopy(bv)}
        return changed

    bp = before.get('fighter_poise') or {}
    ap = after.get('fighter_poise') or {}
    return {
        'enemy_hp_delta': float(after.get('enemy_hp', 0)) - float(before.get('enemy_hp', 0)),
        'enemy_staggered_changed': bool(before.get('enemy_staggered')) != bool(after.get('enemy_staggered')),
        'enemy_stagger_level_delta': int(after.get('enemy_stagger_level', 0)) - int(before.get('enemy_stagger_level', 0)),
        'enemy_stagger_index_delta': int(after.get('enemy_stagger_index', 0)) - int(before.get('enemy_stagger_index', 0)),
        'enemy_status_changes': mapping_delta(before.get('enemy_statuses'), after.get('enemy_statuses')),
        'fighter_sp_delta': float(after.get('fighter_sp', 0)) - float(before.get('fighter_sp', 0)),
        'fighter_charge_delta': int(after.get('fighter_charge', 0)) - int(before.get('fighter_charge', 0)),
        'fighter_charge_potency_delta': int(after.get('fighter_charge_potency', 0)) - int(before.get('fighter_charge_potency', 0)),
        'fighter_ammo_delta': int(after.get('fighter_ammo', 0)) - int(before.get('fighter_ammo', 0)),
        'fighter_poise_potency_delta': int(ap.get('potency', 0)) - int(bp.get('potency', 0)),
        'fighter_poise_count_delta': int(ap.get('count', 0)) - int(bp.get('count', 0)),
        'fighter_resource_changes': mapping_delta(before.get('fighter_resources'), after.get('fighter_resources')),
        'fighter_status_changes': mapping_delta(before.get('fighter_statuses'), after.get('fighter_statuses')),
    }


def status_signature(statuses):
    rows = []
    for name, st in (statuses or {}).items():
        rows.append((str(name), int(getattr(st, 'potency', 0)), int(getattr(st, 'count', 0))))
    return tuple(sorted(rows))


def restore_status_signature(statuses, signature):
    statuses.clear()
    for name, potency, count in signature:
        statuses[str(name)] = Status(potency=int(potency), count=int(count))


def probabilistic_state_signature(state):
    fighters = []
    for iid in sorted(state.fighters):
        f = state.fighters[iid]
        fighters.append((
            str(iid), int(f.sp), int(f.charge), int(getattr(f, 'charge_potency', 0)), int(f.ammo),
            int(f.poise.potency), int(f.poise.count), int(getattr(f, 'defense_level_bonus', 0)),
            tuple(sorted((str(k), int(v)) for k, v in f.resources.items())),
            tuple(sorted((str(k), int(v)) for k, v in f.sin_resources.items())),
            status_signature(f.statuses),
        ))
    e = state.enemy
    ledger = getattr(state, 'activation_ledger', None)
    return (
        tuple(fighters), int(e.sp), round(float(e.hp), 6),
        int(e.stagger_level), int(e.stagger_index), tuple(int(x) for x in e.stagger_thresholds),
        int(getattr(e, 'defense_level_bonus', 0)),
        tuple(sorted((str(k), float(v)) for k, v in e.physical_res.items())),
        tuple(sorted((str(k), float(v)) for k, v in e.sin_res.items())),
        status_signature(e.statuses),
        tuple(sorted((str(k), bool(v)) for k, v in state.runtime.get('condition_flags', {}).items())),
        tuple(sorted((str(k), int(v)) for k, v in ledger.counts.items())) if ledger is not None else (),
        tuple(
            sorted(
                (str(rid), tuple(sorted((str(bk), int(bv)) for (br, bk), bv in ledger.buckets.items() if br == str(rid))))
                for rid in sorted({str(br) for br, _ in ledger.buckets})
            )
        ) if ledger is not None else (),
    )


def restore_probabilistic_state_signature(state, signature):
    if len(signature) == 11:
        fighters, enemy_sp, enemy_hp, stagger_level, stagger_index, stagger_thresholds, enemy_def_bonus, physical_res, sin_res, enemy_statuses, condition_flags = signature
        trigger_activations = ()
        trigger_buckets = ()
    elif len(signature) == 12:
        fighters, enemy_sp, enemy_hp, stagger_level, stagger_index, stagger_thresholds, enemy_def_bonus, physical_res, sin_res, enemy_statuses, condition_flags, trigger_activations = signature
        trigger_buckets = ()
    else:
        fighters, enemy_sp, enemy_hp, stagger_level, stagger_index, stagger_thresholds, enemy_def_bonus, physical_res, sin_res, enemy_statuses, condition_flags, trigger_activations, trigger_buckets = signature

    for row in fighters:
        if len(row) == 10:
            iid, sp, charge, ammo, poise_potency, poise_count, def_bonus, resources, sin_resources, statuses = row
            charge_potency = 0
        else:
            iid, sp, charge, charge_potency, ammo, poise_potency, poise_count, def_bonus, resources, sin_resources, statuses = row
        if iid in state.fighters:
            f = state.fighters[iid]
            f.sp = int(sp)
            f.charge = int(charge)
            f.charge_potency = int(charge_potency)
            f.ammo = int(ammo)
            f.poise.potency = int(poise_potency)
            f.poise.count = int(poise_count)
            f.defense_level_bonus = int(def_bonus)
            f.resources = {str(k): int(v) for k, v in resources}
            f.sin_resources = {str(k): int(v) for k, v in sin_resources}
            restore_status_signature(f.statuses, statuses)

    state.enemy.sp = int(enemy_sp)
    state.enemy.hp = float(enemy_hp)
    state.enemy.stagger_level = int(stagger_level)
    state.enemy.stagger_index = int(stagger_index)
    state.enemy.stagger_thresholds = list(stagger_thresholds)
    state.enemy.defense_level_bonus = int(enemy_def_bonus)
    state.enemy.physical_res = {str(k): float(v) for k, v in physical_res}
    state.enemy.sin_res = {str(k): float(v) for k, v in sin_res}
    restore_status_signature(state.enemy.statuses, enemy_statuses)
    state.runtime['condition_flags'] = {str(k): bool(v) for k, v in condition_flags}

    ledger = getattr(state, 'activation_ledger', None)
    if ledger is not None:
        ledger.counts = {str(k): int(v) for k, v in trigger_activations}
        ledger.buckets = {}
        for rule_id, buckets in trigger_buckets:
            for bucket_key, value in buckets:
                ledger.buckets[(str(rule_id), str(bucket_key))] = int(value)
