"""Safely merged test file (AST-aware, whole-file rename incl. call sites, decorators preserved via line-removal import stripping).
Originals: test_formation_slot_selector.py, test_target_selector_status_filter.py
"""
from __future__ import annotations

from target_selector_v1 import select_targets


# ---- merged from test_formation_slot_selector.py ----

def test_formation_slot_is_one_based():
    ts=[{"id":"a","formation_index":1,"hp":10},{"id":"b","formation_index":2,"hp":10}]
    assert [x["id"] for x in select_targets(ts,"formation_slot:1")] == ["a"]
    assert [x["id"] for x in select_targets(ts,"formation_2")] == ["b"]

def test_formation_slot_does_not_mean_earliest():
    ts=[{"id":"a","formation_index":2,"hp":10},{"id":"b","formation_index":1,"hp":10}]
    assert [x["id"] for x in select_targets(ts,"formation_slot:2")] == ["a"]


# ---- merged from test_target_selector_status_filter.py ----

def test_status_present_sp_min_filters_before_rank():
    targets=[
      {'id':'a','sp':-20,'statuses':{}},
      {'id':'b','sp':-5,'statuses':{'광신':{'potency':1,'count':1}}},
      {'id':'c','sp':-10,'statuses':{'광신':{'potency':2,'count':1}}},
    ]
    assert [x['id'] for x in select_targets(targets,'status_present_sp_min:광신',1)] == ['c']


def test_structured_policy_filter_then_rank_then_count():
    targets=[
      {'id':'a','sp':-20,'hp':100,'statuses':{}},
      {'id':'b','sp':-5,'hp':100,'statuses':{'광신':{'potency':1,'count':1}}},
      {'id':'c','sp':-10,'hp':100,'statuses':{'광신':{'potency':2,'count':1}}},
    ]
    policy={
      'selector':'sp_min',
      'filters':{'status_present':'광신'},
      'count':1,
    }
    assert [x['id'] for x in select_targets(targets,policy)] == ['c']


def test_structured_policy_priority_then_fallback():
    targets=[
      {'id':'a','speed':3,'hp':30,'max_hp':100,'statuses':{}},
      {'id':'b','speed':9,'hp':20,'max_hp':100,'statuses':{}},
      {'id':'c','speed':5,'hp':10,'max_hp':100,'statuses':{'광신':{'potency':1,'count':1}}},
    ]
    policy={
      'selector':'speed_max',
      'priority':[{'selector':'sp_min','filters':{'status_present':'광신'}}],
      'fallback':'hp_min',
    }
    # priority branch wins because one fanatic target exists
    assert [x['id'] for x in select_targets(targets,policy)] == ['c']


def test_structured_policy_fallback_to_unfiltered_when_filtered_empty():
    targets=[
      {'id':'a','hp':30,'max_hp':100,'statuses':{}},
      {'id':'b','hp':20,'max_hp':100,'statuses':{}},
    ]
    policy={
      'selector':'sp_min',
      'filters':{'status_present':'광신'},
      'fallback':'hp_min',
      'fallback_to_unfiltered':True,
    }
    assert [x['id'] for x in select_targets(targets,policy)] == ['b']
