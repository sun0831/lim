"""Safely merged test file (AST-aware, whole-file rename incl. call sites, decorators preserved via line-removal import stripping).
Originals: test_ow_0_7_71_semantic_mismatch.py, test_ow_0_7_74_semantic_mismatch.py
"""
from __future__ import annotations

from passive_runtime_v29_base import AllySelectorTarget
from types import SimpleNamespace


# ---- merged from test_ow_0_7_71_semantic_mismatch.py ----


def fighter(fid,hp,max_hp,sp,formation=1,charge=0,ammo=0,statuses=None):
    return SimpleNamespace(id=fid,hp=hp,max_hp=max_hp,sp=sp,formation_index=formation,charge=charge,ammo=ammo,statuses=statuses or {},poise=None,speed=1)

def state(fs):
    return SimpleNamespace(fighters={f.id:f for f in fs})

def test_hp_min_is_current_hp_not_percent():
    a=fighter('a',40,100,0,1)
    b=fighter('b',30,50,0,2)
    # b has lower absolute HP and also higher HP percentage; absolute HP must win.
    got=AllySelectorTarget('hp_min',1).resolve(None,state([a,b]),'a')
    assert got[0].id=='b'

def test_hp_max_is_current_hp():
    a=fighter('a',40,100,0,1)
    b=fighter('b',60,200,0,2)
    got=AllySelectorTarget('hp_max',1).resolve(None,state([a,b]),'a')
    assert got[0].id=='b'

def test_status_present_sp_min_keeps_sp_rank_after_filter():
    a=fighter('a',100,100,10,1,statuses={'광신':SimpleNamespace(count=1)})
    b=fighter('b',100,100,-5,2,statuses={'광신':SimpleNamespace(count=1)})
    c=fighter('c',100,100,-20,3,statuses={})
    got=AllySelectorTarget('status_present_sp_min:광신',1).resolve(None,state([a,b,c]),'a')
    assert got[0].id=='b'


# ---- merged from test_ow_0_7_74_semantic_mismatch.py ----
"""11번 실제 원문 정합성 감사: Target Selector 동률 처리 검증."""


def fighter__test_ow_0_7_74_semantic_mismatch(slot, *, speed=5, hp=100, charge=0, ammo=0, sp=0, poise_potency=0, poise_count=0):
    return SimpleNamespace(
        hp=hp, max_hp=100, speed=speed, charge=charge, ammo=ammo, sp=sp,
        formation_index=slot,
        poise=SimpleNamespace(potency=poise_potency, count=poise_count),
        statuses={},
    )


class State:
    def __init__(self, fighters):
        self.fighters = fighters


def selected_id(state, policy):
    got = AllySelectorTarget(policy, 1).resolve(None, state, 'owner')
    return next(fid for fid, f in state.fighters.items() if got and f is got[0])


def test_ranked_ally_ties_follow_formation_not_identity_id():
    # Source-facing ranked selectors use deterministic roster/formation order on ties.
    st = State({
        'z_identity': fighter__test_ow_0_7_74_semantic_mismatch(1, speed=10),
        'a_identity': fighter__test_ow_0_7_74_semantic_mismatch(2, speed=10),
        'owner': fighter__test_ow_0_7_74_semantic_mismatch(3, speed=10),
    })
    assert selected_id(st, 'speed_max') == 'z_identity'
    assert selected_id(st, 'speed_min') == 'z_identity'


def test_special_poise_rank_ties_follow_formation_not_identity_id():
    st = State({
        'z_identity': fighter__test_ow_0_7_74_semantic_mismatch(1, poise_potency=7, poise_count=4),
        'a_identity': fighter__test_ow_0_7_74_semantic_mismatch(2, poise_potency=7, poise_count=4),
        'owner': fighter__test_ow_0_7_74_semantic_mismatch(3, poise_potency=1, poise_count=1),
    })
    assert selected_id(st, 'poise_potency_max') == 'z_identity'
    assert selected_id(st, 'poise_count_max') == 'z_identity'
