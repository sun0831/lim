"""Safely merged test file (AST-aware, whole-file rename incl. call sites, decorators preserved via line-removal import stripping).
Originals: test_buff_debuff_source_audit_0_7_96.py, test_buff_debuff_source_caps_0_7_95.py, test_status_scope_audit.py
"""
from __future__ import annotations

from types import SimpleNamespace
from status_effect_runtime_v1 import StatusEffectRuntime
from buff_debuff_runtime_v1 import BuffDebuffRuntime
import json


# ---- merged from test_buff_debuff_source_audit_0_7_96.py ----

def state():
    return SimpleNamespace(runtime={})

def test_crit_damage_up_is_ten_percent_per_stack():
    st=state()
    r=StatusEffectRuntime.apply_catalog_effect(st,target_id='A',name='Crit DMG Up',potency=2)
    assert r['applied']
    resolved=BuffDebuffRuntime.resolve(st,target_id='A')
    assert abs(resolved['critical_damage_percent'] - 0.2) < 1e-9

def test_weak_resist_damage_boost_is_not_unconditional_damage():
    st=state()
    r=StatusEffectRuntime.apply_catalog_effect(st,target_id='A',name='Weak-resist DMG Boost',count=20)
    assert r['deferred'] is True
    assert r['applied'] is False
    assert not st.runtime.get(BuffDebuffRuntime.KEY)


# ---- merged from test_buff_debuff_source_caps_0_7_95.py ----


def state__test_buff_debuff_source_caps_0_7_95():
    return SimpleNamespace(runtime={})


def test_source_defined_100_percent_caps_are_preserved():
    st=state__test_buff_debuff_source_caps_0_7_95()
    for name in ('Damage Up','Damage Down','Protection','Fragile'):
        StatusEffectRuntime.apply_catalog_effect(st,target_id='A',name=name,count=15)
        item=next(v for v in st.runtime[BuffDebuffRuntime.KEY].values() if v['name']==name)
        assert item['count']==10
        resolved=BuffDebuffRuntime.resolve(st,target_id='A')
        assert abs(resolved['damage_percent']) <= 1.0


# ---- merged from test_status_scope_audit.py ----


def state__test_status_scope_audit():
    return SimpleNamespace(runtime={})


def test_attack_power_up_only_affects_attack_skill_context():
    s=state__test_status_scope_audit(); StatusEffectRuntime.apply_catalog_effect(s,target_id='a',name='Attack Power Up',count=2)
    attack=BuffDebuffRuntime.resolve(s,target_id='a',context={'skill_is_defense':False})
    defense=BuffDebuffRuntime.resolve(s,target_id='a',context={'skill_is_defense':True})
    assert attack['skill_power']==2
    assert defense.get('skill_power',0)==0


def test_defense_power_up_only_affects_defense_skill_context():
    s=state__test_status_scope_audit(); StatusEffectRuntime.apply_catalog_effect(s,target_id='a',name='Defense Power Up',count=3)
    attack=BuffDebuffRuntime.resolve(s,target_id='a',context={'skill_is_defense':False})
    defense=BuffDebuffRuntime.resolve(s,target_id='a',context={'skill_is_defense':True})
    assert attack.get('skill_power',0)==0
    assert defense['skill_power']==3


def test_power_up_remains_unscoped():
    s=state__test_status_scope_audit(); StatusEffectRuntime.apply_catalog_effect(s,target_id='a',name='Power Up',count=2)
    assert BuffDebuffRuntime.resolve(s,target_id='a',context={'skill_is_defense':False})['skill_power']==2
    assert BuffDebuffRuntime.resolve(s,target_id='a',context={'skill_is_defense':True})['skill_power']==2
