"""병합 테스트: special_clause_audits

원본 파일 (내용은 AST 병합기로 합쳤고 테스트 본문은 바꾸지 않음):
  - test_v132_trigger_reclassifier.py
  - test_v134_skill_transform_audit.py
  - test_v135_non_resource_special_audit.py
  - test_v137_status_side_clause_audit.py
  - test_v138_cross_identity_audit.py
  - test_v139_target_selection_audit.py
  - test_v140_stack_threshold_audit.py
  - test_v142_multi_target_audit.py
  - test_v143_probability_random_audit.py
  - test_v144_special_state_audit.py
이름 충돌 helper 는 `이름__vNN` 으로 분리했다. 매핑은 tools/MERGE_MAP.json 참고.
"""
import json
import sys
from trigger_clause_reclassifier_v1 import TriggerOutput, classify_trigger, reclassify_records
from resource_primitive_v1 import ResourcePrimitive, ResourcePrimitiveSpec, validate, primitive_from_effect
from non_resource_special_audit_v1 import audit, AuditKind
from pathlib import Path
from cross_identity_clause_audit_v1 import classify_clause, split_clauses, CrossCluster, Match
from target_selection_clause_audit_v1 import (
    classify_clause as classify_clause__v139_target,
    TargetCluster,
    Match as Match__v139_target,
)
from stack_threshold_audit_v1 import route_clause
from multi_target_clause_audit_v1 import audit_records
from probability_random_audit_v1 import audit as audit__v143_probability, classify_text
from special_state_audit_v1 import audit as audit__v144_special



# ======================================================================
# 원본: test_v132_trigger_reclassifier.py
# ======================================================================

def test_resource_gain_branch():
    c = classify_trigger('적을 처치하면 충전 횟수 2 얻음')
    assert c.output is TriggerOutput.RESOURCE_GAIN

def test_status_branch():
    c = classify_trigger('공격 종료 시 모든 아군에게 공격 레벨 증가 1 부여')
    assert c.output is TriggerOutput.STATUS_EFFECT

def test_action_branch():
    c = classify_trigger('적중하면 대상에게 일방 공격함 (턴당 1회)')
    assert c.output is TriggerOutput.ACTION_TRIGGER

def test_condition_branch():
    c = classify_trigger('턴 시작 시 자신의 원한 문신이 15 이상이면 아래 효과 적용')
    assert c.output is TriggerOutput.CONDITION_ONLY

def test_trigger_catchall_audit_count_matches_e19():
    d = json.load(open('RESOURCE_PRIMITIVE_DECOMPOSITION_E18.json', encoding='utf-8'))
    rows = [x for x in d['clauses'] if x['kind'] == 'trigger']
    out = reclassify_records(rows)
    assert out['record_count'] == 345
    assert sum(out['counts'].values()) == 345
    assert out['unique_source_texts'] == 296


# ======================================================================
# 원본: test_v134_skill_transform_audit.py
# ======================================================================
sys.path.insert(0,'.')

def test_generic_skill_swap_is_distinct_from_resource_triggered_swap():
    a=ResourcePrimitiveSpec(ResourcePrimitive.SKILL_SWAP, source_skill='S1', target_skill='S3')
    b=ResourcePrimitiveSpec(ResourcePrimitive.RESOURCE_TRIGGERED_SKILL_SWAP, source_skill='S1', target_skill='S3', resource=None)
    validate(a); validate(b)
    assert a.primitive is not b.primitive

def test_skill_swap_effect_maps_to_generic_primitive():
    s=primitive_from_effect('skill_swap', {'source_skill':'S1','target_skill':'S3'})
    assert s is not None and s.primitive is ResourcePrimitive.SKILL_SWAP

def test_reclassify_remains_distinct():
    s=primitive_from_effect('skill_reclassify', {'skill_tag':'charge_gain'})
    assert s.primitive is ResourcePrimitive.SKILL_RECLASSIFY


# ======================================================================
# 원본: test_v135_non_resource_special_audit.py
# ======================================================================

def test_audit_finds_86_unresolved_clauses():
    xs=audit('RESOURCE_PRIMITIVE_DECOMPOSITION_E18.json')
    assert len(xs)==86

def test_skill_reclassify_is_absorbed():
    xs=audit('RESOURCE_PRIMITIVE_DECOMPOSITION_E18.json')
    assert sum(x.kind==AuditKind.SKILL_RECLASSIFY for x in xs)==2

def test_out_of_scope_bgm_is_not_promoted_to_runtime():
    xs=audit('RESOURCE_PRIMITIVE_DECOMPOSITION_E18.json')
    assert sum(x.kind==AuditKind.OUT_OF_SCOPE for x in xs)==4

def test_true_unresolved_is_preserved():
    xs=audit('RESOURCE_PRIMITIVE_DECOMPOSITION_E18.json')
    assert sum(x.kind==AuditKind.UNRESOLVED for x in xs)==26


# ======================================================================
# 원본: test_v137_status_side_clause_audit.py
# ======================================================================

def test_e26_status_side_clause_count_and_scope():
    p=Path(__file__).with_name('STATUS_SIDE_CLAUSE_AUDIT_E26.json')
    d=json.loads(p.read_text(encoding='utf-8'))
    assert d['status_effect_side_clause_candidates']==149
    assert d['unique_clause_texts']==129
    assert sum(d['routing_counts'].values())==149
    assert d['policy']

def test_e26_does_not_claim_execution_coverage():
    d=json.loads(Path(__file__).with_name('STATUS_SIDE_CLAUSE_AUDIT_E26.json').read_text(encoding='utf-8'))
    assert any('execution coverage' in x for x in d['policy'])


# ======================================================================
# 원본: test_v138_cross_identity_audit.py
# ======================================================================

def test_affiliation_count_and_resource():
    h=classify_clause('전투에 참여한 흑운회 소속 아군이 2명 이상이면 흑운도 1 얻음')
    cs={x.cluster for x in h}
    assert CrossCluster.AFFILIATION_MEMBERSHIP_COUNT in cs
    assert CrossCluster.AFFILIATION_MEMBERSHIP_COUNT in cs

def test_cross_identity_target_selector():
    h=classify_clause('속도가 가장 빠른 아군 1명이 출혈 부여 값 +1')
    assert any(x.cluster is CrossCluster.CROSS_IDENTITY_TARGET_SELECTION for x in h)

def test_cross_identity_action():
    h=classify_clause('적이 자신을 제외한 아군을 공격하여 피해를 입혔으면 공격자를 스킬 1로 일방 공격함')
    assert any(x.cluster is CrossCluster.CROSS_IDENTITY_SKILL_ACTION for x in h)

def test_unresolved_is_conservative():
    h=classify_clause('특수한 조건에 따라 추가 효과가 적용된다')
    assert any(x.cluster is CrossCluster.OUT_OF_AXIS for x in h)


# ======================================================================
# 원본: test_v139_target_selection_audit.py
# ======================================================================

def test_random_target_existing():
    assert any((x.cluster is TargetCluster.RANDOM and x.match is Match__v139_target.EXISTING_RANDOM for x in classify_clause__v139_target('무작위 적 1명에게 지령 대상 부여')))

def test_resource_lowest_highest():
    assert any((x.cluster is TargetCluster.LOWEST_RESOURCE for x in classify_clause__v139_target('탄환을 가장 적게 보유한 아군 1명')))
    assert any((x.cluster is TargetCluster.HIGHEST_RESOURCE for x in classify_clause__v139_target('충전 횟수가 가장 높은 아군 1명')))

def test_speed_hp_formation_existing():
    assert any((x.cluster is TargetCluster.SPEED and x.match is Match__v139_target.EXISTING_TARGET_SELECTOR for x in classify_clause__v139_target('속도가 가장 빠른 아군 1명')))
    assert any((x.cluster is TargetCluster.HP and x.match is Match__v139_target.EXISTING_TARGET_SELECTOR for x in classify_clause__v139_target('최대 체력이 가장 높은 아군 1명')))
    assert any((x.cluster is TargetCluster.FORMATION and x.match is Match__v139_target.EXISTING_TARGET_SELECTOR for x in classify_clause__v139_target('가장 왼쪽 슬롯의 기본 공격 스킬')))

def test_affiliation_is_existing_resolver():
    assert any((x.cluster is TargetCluster.AFFILIATION and x.match is Match__v139_target.EXISTING_AFFILIATION for x in classify_clause__v139_target('거미집 소속 아군 인격에게 보호막 부여')))


# ======================================================================
# 원본: test_v140_stack_threshold_audit.py
# ======================================================================

def test_resource_threshold_routes_without_new_runtime():
    r=route_clause('충전이 5 이상이면 다음 턴에 신속 2를 얻음')
    assert any(x.route=='resource_or_stack_threshold' for x in r)
    assert any(x.route=='numeric_or_resource_threshold' for x in r)

def test_status_threshold_routes_to_existing_status_condition():
    r=route_clause('대상의 화상 위력이 20 이상이면 추가 효과')
    assert any(x.route=='status_threshold' for x in r)

def test_hp_and_mental_thresholds_are_existing_condition_axes():
    r=route_clause('잃은 체력이 80% 이상이고 정신력이 20 이상이면 효과 적용')
    assert any(x.route=='hp_threshold' for x in r)
    assert any(x.route=='mental_threshold' for x in r)

def test_activation_cap_is_not_a_new_threshold_primitive():
    r=route_clause('턴당 1회 적용')
    assert any(x.route=='activation_limit' for x in r)


# ======================================================================
# 원본: test_v142_multi_target_audit.py
# ======================================================================

def _src():
    p=Path(__file__).with_name('GIMMICK_GAP_REPORT_v4.md.json')
    return json.loads(p.read_text(encoding='utf-8'))

def test_multi_target_corpus_count_and_no_new_primitive():
    d=_src(); records=[r for r in d['gaps'] if 'multi_target' in r.get('categories',[])]
    r=audit_records(records)
    assert r['record_count']==35
    assert r['unique_source_texts']==34
    assert r['new_primitive_candidate']==0

def test_explicit_count_and_all_target_route_to_existing_contracts():
    records=[{'identity_id':'x','source_text':'무작위 적 2명에게 화상 3 부여'}, {'identity_id':'y','source_text':'모든 적에게 화상 2 부여'}]
    r=audit_records(records)
    assert r['match_counts']['existing_target_count']>=1
    assert r['match_counts']['existing_random_selector']>=1
    assert r['match_counts']['existing_target_selector']>=1

def test_conditional_multi_target_is_compositional():
    records=[{'identity_id':'x','source_text':'적 처치 시 무작위 적 2명에게 화상 4 부여'}]
    r=audit_records(records)
    assert r['match_counts']['condition_plus_selector']>=1
    assert r['new_primitive_candidate']==0

def test_focused_battle_part_is_target_resolution_not_new_runtime():
    records=[{'identity_id':'x','source_text':'집중 전투에서는 부위에 부여'}]
    r=audit_records(records)
    assert r['match_counts']['existing_part_target']>=1
    assert r['new_primitive_candidate']==0


# ======================================================================
# 원본: test_v143_probability_random_audit.py
# ======================================================================

def test_random_target_routes_to_target_selector():
    r = audit__v143_probability([{'source_text': '무작위 적 2명에게 화상 3 부여'}])
    assert r['classification_counts']['random_target'] == 1
    assert r['new_dedicated_runtime_confirmed'] is False

def test_probability_trigger_routes_to_existing_runtime():
    r = audit__v143_probability([{'source_text': '25% 확률로 추가로 발동'}])
    assert r['classification_counts']['probabilistic_trigger_or_reuse'] == 1

def test_per_coin_probability_is_distinct_contract():
    r = audit__v143_probability([{'source_text': '각 탄환마다 30% 확률로 산나비를 얻음'}])
    assert r['classification_counts']['per_coin_random_outcome'] == 1
    assert r['important_contract_gap'] == 'per_coin_random_outcome'

def test_axis_audit_counts_unique_sources():
    rows = [{'source_text': '무작위 적 1명'}, {'source_text': '무작위 적 1명'}, {'source_text': '25% 확률로 추가로 발동'}]
    r = audit__v143_probability(rows)
    assert r['record_count'] == 3
    assert r['unique_source_text_count'] == 2


# ======================================================================
# 원본: test_v144_special_state_audit.py
# ======================================================================

def test_named_state_routes_to_existing_state_contract():
    r = audit__v144_special([{'source_text': '예지안이 0이 되면 예지안 과열 상태가 됨'}])
    assert r['classification_counts']['resource_or_counter_state'] == 1
    assert r['new_dedicated_runtime_confirmed'] is False

def test_turn_state_routes_to_lifecycle():
    r = audit__v144_special([{'source_text': '턴 종료 시 다음 턴에 상태를 얻음'}])
    assert r['classification_counts']['turn_lifecycle_state'] == 1

def test_skill_state_routes_to_skill_action_primitives():
    r = audit__v144_special([{'source_text': '다음 턴 시작 시 기본 스킬 하나를 특정 스킬로 변경'}])
    assert r['classification_counts']['skill_or_action_state'] == 1

def test_resource_state_routes_to_resource_runtime():
    r = audit__v144_special([{'source_text': '조망 21 얻음'}])
    assert r['classification_counts']['resource_or_counter_state'] == 1

def test_axis_counts_unique_sources():
    rows = [{'source_text': '예지안 0'}, {'source_text': '예지안 0'}, {'source_text': '턴 종료 시 상태 변경'}]
    r = audit__v144_special(rows)
    assert r['record_count'] == 3
    assert r['unique_source_text_count'] == 2
    assert r['contract_gap_count'] == 0
