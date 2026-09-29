"""병합 테스트: architecture_contracts

원본 파일 (내용은 AST 병합기로 합쳤고 테스트 본문은 바꾸지 않음):
  - test_v48_architecture_contract.py
  - test_v49_architecture_state_trace.py
  - test_v77_architecture_foundations.py
  - test_v90_runtime_registry_consistency.py
이름 충돌 helper 는 `이름__vNN` 으로 분리했다. 매핑은 tools/MERGE_MAP.json 참고.
"""
import architecture_audit_v1 as audit
import json
from one_turn_solver_v29 import IdentityCatalogV29, OneTurnSolverV29
from pathlib import Path
from data_validation_v1 import validate_catalog
from rule_ir_v1 import RuleIR, ConditionIR, EffectIR, RuleDependencyGraph
from golden_test_runtime_v1 import compare
from condition_runtime_v1 import ConditionRuntime
from effect_runtime_v1 import EffectRuntime
from rule_migration_runtime_v1 import RuleMigrationRuntime



# ======================================================================
# 원본: test_v48_architecture_contract.py
# ======================================================================

def test_first_divergence_finds_first_field():
    a = [{'event': 'coin', 'damage': 10}, {'event': 'coin', 'damage': 20}]
    b = [{'event': 'coin', 'damage': 10}, {'event': 'coin', 'damage': 25}]
    r = audit.first_divergence(a, b)
    assert r['found'] and r['index'] == 1 and r['field'] == 'damage'

def test_audit_requires_analyzer_contract():
    result = {
        'requested_plan': [{}], 'actions': [{
            'action_type': 'requested', 'requested_action': {}, 'resolved_action': {},
            'generated': False, 'identity_id': 'A', 'skill_id': 'S1', 'coins': [],
            'state_at_action_start': {}, 'state_at_action_end': {}, 'state_diff': {},
        }],
        'damage_by_identity': {}, 'damage_by_skill': {}, 'event_log': [],
        'state_diff': {}, 'next_turn_state': {},
    }
    r = audit.audit_result(result)
    assert r['ok']
    assert r['triggered_count'] == 0

def test_action_state_diff_exposes_status_resource_and_stagger_changes():
    before = {
        'enemy_hp': 100, 'enemy_staggered': False, 'enemy_stagger_level': 0,
        'enemy_stagger_index': 0, 'enemy_statuses': {'Burn': {'potency': 2, 'count': 1}},
        'fighter_sp': 10, 'fighter_charge': 2, 'fighter_ammo': 3,
        'fighter_poise': {'potency': 1, 'count': 2},
        'fighter_resources': {'예지안': 5},
        'fighter_statuses': {'가속': {'potency': 1, 'count': 1}},
    }
    after = {
        'enemy_hp': 88, 'enemy_staggered': True, 'enemy_stagger_level': 1,
        'enemy_stagger_index': 2, 'enemy_statuses': {'Burn': {'potency': 4, 'count': 0}},
        'fighter_sp': 7, 'fighter_charge': 4, 'fighter_ammo': 1,
        'fighter_poise': {'potency': 3, 'count': 2},
        'fighter_resources': {'예지안': 4, '새벽불': 2},
        'fighter_statuses': {},
    }
    d = __import__('one_turn_solver_v29').OneTurnSolverV29._action_state_diff(before, after)
    assert d['enemy_hp_delta'] == -12
    assert d['enemy_staggered_changed'] is True
    assert d['enemy_stagger_level_delta'] == 1
    assert d['enemy_stagger_index_delta'] == 2
    assert d['enemy_status_changes']['Burn']['after']['potency'] == 4
    assert d['fighter_resource_changes']['예지안']['after'] == 4
    assert d['fighter_resource_changes']['새벽불']['before'] is None
    assert d['fighter_status_changes']['가속']['after'] is None
    assert d['fighter_poise_potency_delta'] == 2


# ======================================================================
# 원본: test_v49_architecture_state_trace.py
# ======================================================================

def _solver_identity():
    data=json.load(open('identity_catalog_v2.json',encoding='utf8'))['identities']
    cat=IdentityCatalogV29(data)
    ident=cat.build_identity(next(iter(cat.records)))
    return OneTurnSolverV29(), ident

def test_action_start_snapshot_is_pre_action():
    solver, ident = _solver_identity()
    scenario={
        'identities':[ident.id],
        'enemy':{'hp':100,'max_hp':100},
        'actions':[{'identity_id':ident.id,'skill_id':next(iter(ident.skills)),'faces':['HEAD']}],
    }
    r=solver.solve(scenario,{ident.id:ident})
    a=r['actions'][0]
    assert 'fighter_statuses' in a['state_at_action_start']
    assert 'enemy_statuses' in a['state_at_action_start']
    assert 'fighter_charge' in a['state_at_action_start']
    assert a['state_diff']['fighter_ammo_delta'] == a['state_at_action_end']['fighter_ammo'] - a['state_at_action_start']['fighter_ammo']

def test_action_trace_has_explicit_coin_and_state_trace():
    solver, ident = _solver_identity()
    scenario={
        'identities':[ident.id],
        'enemy':{'hp':100,'max_hp':100},
        'actions':[{'identity_id':ident.id,'skill_id':next(iter(ident.skills)),'faces':['HEAD']}],
    }
    r=solver.solve(scenario,{ident.id:ident})
    a=r['actions'][0]
    assert isinstance(a['coins'], list)
    assert 'state_at_action_start' in a and 'state_at_action_end' in a
    assert 'state_diff' in a
    assert 'requested_action' in a and 'resolved_action' in a


# ======================================================================
# 원본: test_v77_architecture_foundations.py
# ======================================================================
ROOT=Path(__file__).resolve().parent

def test_catalog_validation():
    data=json.loads((ROOT/'identity_catalog_v2.json').read_text(encoding='utf8'))
    r=validate_catalog(data)
    assert r['ok'], r['errors'][:10]
    assert r['identity_count'] == 184

def test_rule_dependency_graph():
    a=RuleIR('a','i','skill_end')
    b=RuleIR('b','i','skill_end',dependencies=('a',))
    g=RuleDependencyGraph([a,b])
    assert g.dependencies_of('b') == ['a']
    assert g.dependents_of('a') == ['b']
    assert g.unresolved([]) == ['b']
    assert g.missing_dependencies() == {}
    assert g.cycles() == []

def test_rule_dependency_cycle_detection():
    a=RuleIR('a','i','x',dependencies=('b',))
    b=RuleIR('b','i','x',dependencies=('a',))
    cycles=RuleDependencyGraph([a,b]).cycles()
    assert cycles

def test_golden_compare():
    r={'total_damage':10,'damage_by_identity':{'a':10},'damage_by_skill':{},'next_turn_state':{'x':1}}
    assert compare(r,dict(r))['ok']
    r2=dict(r); r2['total_damage']=11
    assert compare(r,r2)['ok'] is False


# ======================================================================
# 원본: test_v90_runtime_registry_consistency.py
# ======================================================================

def test_condition_support_registry_is_shared_with_migration_safety():
    assert RuleMigrationRuntime.SUPPORTED_CONDITIONS is ConditionRuntime.SUPPORTED_OPS
    assert ConditionRuntime.is_supported('always') is True
    assert ConditionRuntime.is_supported('not_yet_supported') is False

def test_generic_effect_registry_is_shared_with_migration_classifier():
    assert EffectRuntime.is_generic_executable('resource_gain') is True
    assert EffectRuntime.is_generic_executable('queue_action') is True
    assert RuleMigrationRuntime._effect_state('resource_gain') == 'generic'
    assert RuleMigrationRuntime._effect_state('queue_action') == 'generic'

def test_specialized_category_does_not_become_generic_by_category_membership():
    assert EffectRuntime.category_for('support_action') == 'action'
    assert EffectRuntime.is_generic_executable('support_action') is True
    assert RuleMigrationRuntime._effect_state('support_action') == 'generic'
