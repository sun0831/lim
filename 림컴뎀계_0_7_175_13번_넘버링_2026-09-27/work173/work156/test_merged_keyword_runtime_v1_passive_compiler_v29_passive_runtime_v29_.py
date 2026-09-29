"""Safely merged test file (AST-aware, whole-file rename incl. call sites, decorators preserved via line-removal import stripping).
Originals: test_tremor_application_modifier.py, test_unrelenting_spirit_0_7_105.py
"""
from __future__ import annotations

from passive_compiler_v29 import compile_clause_template
from passive_runtime_v29_base import PassiveEvent, PassiveTrigger
from keyword_runtime_v1 import KeywordRuntime
from types import SimpleNamespace


# ---- merged from test_tremor_application_modifier.py ----

def test_compile():
    rule,_,unsupported=compile_clause_template('대상에게 시선이 있으면, 이 스킬에서 부여하는 출혈, 진동 위력 +2')
    assert any(type(c).__name__=='HasStatus' and c.name=='시선' and c.target=='enemy' for c in [rule.condition])
    assert any(type(e).__name__=='ModifyContext' and e.field=='tremor_potency_bonus' for e in rule.effects)
    assert not unsupported

def test_event_scoped_bonus():
    u=SimpleNamespace(statuses={})
    KeywordRuntime.add_tremor(u,3,1,event=PassiveEvent(PassiveTrigger.COIN_HIT,{'tremor_potency_bonus':2}))
    assert u.statuses['Tremor'].potency==5 and u.statuses['Tremor'].count==1
    u2=SimpleNamespace(statuses={})
    KeywordRuntime.add_tremor(u2,3,1,event=PassiveEvent(PassiveTrigger.COIN_HIT,{}))
    assert u2.statuses['Tremor'].potency==3


# ---- merged from test_unrelenting_spirit_0_7_105.py ----


def test_unrelenting_spirit_unit_skill_tremor_bonus_both():
    text = '자신의 스킬로 진동 위력 +1 및 진동 횟수 +1'
    rule, _, unsupported = compile_clause_template(text)
    assert any(type(e).__name__ == 'ModifyContext' and e.field == 'tremor_potency_bonus' and e.amount.value == 1 for e in rule.effects)
    assert any(type(e).__name__ == 'ModifyContext' and e.field == 'tremor_count_bonus' and e.amount.value == 1 for e in rule.effects)
    assert not unsupported

def test_unrelenting_spirit_unit_skill_tremor_bonus_potency_only():
    text = '자신의 스킬로 진동 위력 +2'
    rule, _, unsupported = compile_clause_template(text)
    assert any(type(e).__name__ == 'ModifyContext' and e.field == 'tremor_potency_bonus' and e.amount.value == 2 for e in rule.effects)
    assert not any(type(e).__name__ == 'ModifyContext' and e.field == 'tremor_count_bonus' for e in rule.effects)
    assert not unsupported

def test_unrelenting_spirit_speed_condition_is_actor_faster_by_three():
    text = '자신의 속도가 대상보다 3 이상 빠를 때, 피해량 +12.5% (최대 20%)'
    rule, _, unsupported = compile_clause_template(text)
    cond_repr = repr(rule.condition)
    assert 'SpeedRelation' in cond_repr
    assert 'SpeedDifferenceAtLeast' in cond_repr
    assert not unsupported

def test_unrelenting_spirit_tremor_context_mutation():
    u = SimpleNamespace(statuses={})
    event = PassiveEvent(PassiveTrigger.COIN_HIT, {'tremor_potency_bonus': 1, 'tremor_count_bonus': 1})
    KeywordRuntime.add_tremor(u, 3, 2, event=event)
    assert u.statuses['Tremor'].potency == 4
    assert u.statuses['Tremor'].count == 3


def test_0_7_136_negative_self_sp_damage_scaling():
    text = '절망 상태일 때, 기본 스킬로 가하는 피해량이 (-정신력 / 2)%만큼 증가 (최대 20%)'
    rule, effects, unsupported = compile_clause_template(text)
    assert any(type(e).__name__ == 'ModifyContext' and e.field == 'dynamic_damage_bonus' for e in rule.effects)
    assert 'negative_self_sp_scaling' in effects
    assert not unsupported
