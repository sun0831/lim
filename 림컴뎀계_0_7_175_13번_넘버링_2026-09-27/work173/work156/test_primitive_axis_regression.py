"""Consolidated regression tests for the E17-E33 primitive/gap-axis audit modules.

This file replaces the many single- and double-assertion test files that were
created one-per-stage during the E16-E33 primitive audit passes (see
CHANGELOG_E16.md .. CHANGELOG_E33.md). Each Test* class below owns exactly one
audit module and keeps the same golden assertions the original per-stage test
files checked, so consolidating file count does not drop axis coverage.

Guidance for future work on this codebase:
- Do NOT add a new one-off test_vNNN_eXX_*.py file for a future axis pass.
- Instead add a case to the matching Test* class, or a new Test* class if the
  axis is genuinely new, so a failing test still points at exactly one audit
  module.
- Every input string below was traced against the actual regex/enum logic in
  the corresponding module at the time this file was written. If a module's
  classification rules change, update the matching assertion in the same
  commit rather than deleting the test.

Axes intentionally NOT yet folded into this file (left for a follow-up pass
because their source modules were not verified line-by-line when this file
was written): resource_clause_decomposer_v1 (E18), skill_transform_clause_audit_v1
(E23), status_effect_side clause helpers (E26). Fold them in using the same
one-class-per-module pattern rather than creating new standalone files.
"""
from __future__ import annotations

import pytest

import resource_primitive_v1 as resource_primitive
import resource_semantic_clusters_v1 as resource_semantic
import resource_consumption_audit_v1 as resource_consumption
import non_resource_special_audit_v1 as non_resource_special
import cross_identity_clause_audit_v1 as cross_identity
import target_selection_clause_audit_v1 as target_selection
import stack_threshold_audit_v1 as stack_threshold
import skill_transform_audit_v1 as skill_transform
import multi_target_clause_audit_v1 as multi_target
import probability_random_audit_v1 as probability_random
import special_state_audit_v1 as special_state


# ---------------------------------------------------------------------------
# E17 - resource primitive schema (resource_primitive_v1.py)
# ---------------------------------------------------------------------------
class TestResourcePrimitiveE17:
    def test_trigger_gain_from_existing_effect_kind(self):
        spec = resource_primitive.primitive_from_effect(
            "resource_gain", {"resource": "charge", "amount": 1, "trigger": "on_hit"}
        )
        assert spec.primitive is resource_primitive.ResourcePrimitive.TRIGGER_GAIN

    def test_cumulative_spend_gain_from_existing_effect_kind(self):
        spec = resource_primitive.primitive_from_effect(
            "cumulative_resource_gain",
            {
                "resource": "bio_material",
                "threshold": 10,
                "reward_resource": "bio_material",
                "reward_amount": 1,
            },
        )
        assert spec.primitive is resource_primitive.ResourcePrimitive.CUMULATIVE_SPEND_GAIN
        assert spec.threshold == 10

    def test_highest_resource_selector_is_declared(self):
        # E20 gap fix: symmetric "highest" counterpart to lowest_resource_selector.
        spec = resource_primitive.primitive_from_effect(
            "highest_resource_selector", {"resource": "ammo", "target_side": "ally"}
        )
        assert spec.primitive is resource_primitive.ResourcePrimitive.HIGHEST_RESOURCE_TARGET

    def test_resource_triggered_skill_swap_is_distinct_from_reclassify(self):
        # E23 gap fix: must not collapse into SKILL_RECLASSIFY.
        spec = resource_primitive.primitive_from_effect(
            "resource_triggered_skill_swap",
            {"resource": "foresight", "trigger": "resource_zero", "source_skill": "s1", "target_skill": "s1_overheat"},
        )
        assert spec.primitive is resource_primitive.ResourcePrimitive.RESOURCE_TRIGGERED_SKILL_SWAP
        assert spec.primitive is not resource_primitive.ResourcePrimitive.SKILL_RECLASSIFY

    def test_unknown_effect_kind_returns_none(self):
        assert resource_primitive.primitive_from_effect("totally_unknown_kind", {}) is None

    def test_validate_rejects_incomplete_trigger_gain(self):
        bad = resource_primitive.ResourcePrimitiveSpec(resource_primitive.ResourcePrimitive.TRIGGER_GAIN)
        with pytest.raises(ValueError):
            resource_primitive.validate(bad)

    def test_validate_rejects_resource_conversion_without_mode(self):
        bad = resource_primitive.ResourcePrimitiveSpec(
            resource_primitive.ResourcePrimitive.RESOURCE_CONVERSION,
            resource=resource_primitive.ResourceRef("a"),
            reward=resource_primitive.ResourceRef("b"),
        )
        with pytest.raises(ValueError):
            resource_primitive.validate(bad)


# ---------------------------------------------------------------------------
# E19 - resource semantic clustering (resource_semantic_clusters_v1.py)
# ---------------------------------------------------------------------------
class TestResourceSemanticClusterE19:
    def test_cumulative_spend_pattern(self):
        hits = resource_semantic.classify(
            "전투 중 누적으로 자신의 생체 재료 횟수 10을 소모할 때마다 생체 재료를 1 얻음"
        )
        clusters = {h.cluster for h in hits}
        assert resource_semantic.SemanticCluster.CUMULATIVE_SPEND in clusters

    def test_affiliation_scaled_pattern(self):
        hits = resource_semantic.classify(
            "편성된 거미집 소속 아군 인격(자신 포함) 3명당 얽힘 버프의 최솟값, 최댓값 1 증가"
        )
        clusters = {h.cluster for h in hits}
        assert resource_semantic.SemanticCluster.AFFILIATION_SCALED in clusters

    def test_unresolved_when_no_pattern_matches(self):
        hits = resource_semantic.classify("완전히 다른 종류의 문장")
        assert hits[0].cluster is resource_semantic.SemanticCluster.UNRESOLVED


# ---------------------------------------------------------------------------
# E22 - resource consumption audit (resource_consumption_audit_v1.py)
# ---------------------------------------------------------------------------
class TestResourceConsumptionE22:
    def test_cumulative_spend_reward(self):
        a = resource_consumption.classify_consumption_clause(
            "전투 중 누적으로 자신의 생체 재료 횟수 10을 소모할 때마다 생체 재료를 1 얻음"
        )
        assert a.classification is resource_consumption.ConsumptionClass.CUMULATIVE_SPEND_REWARD
        assert a.primitive == "cumulative_resource_gain"

    def test_consume_trigger_without_cumulative_wording(self):
        a = resource_consumption.classify_consumption_clause(
            "탄환을 가장 적게 보유한 아군 1명이 코인에서 마지막 탄환을 소모하면, "
            "코인의 공격 종료 시, 각 대상에게 해당 코인의 공격으로 입힌 피해량의 50%만큼 추가 피해를 줌."
        )
        assert a.classification is resource_consumption.ConsumptionClass.CONSUME_TRIGGER
        assert a.primitive == "resource_consume_trigger"


# ---------------------------------------------------------------------------
# E24 - non-resource / special clause audit (non_resource_special_audit_v1.py)
# ---------------------------------------------------------------------------
class TestNonResourceSpecialE24:
    def test_skill_reclassify_phrase(self):
        kind, confidence, evidence = non_resource_special.classify(
            {"text": "기본 공격 스킬과 합 가능 반격 스킬이 충전 횟수를 얻는 스킬로 취급됨"}
        )
        assert kind is non_resource_special.AuditKind.SKILL_RECLASSIFY

    def test_bgm_change_is_out_of_scope(self):
        kind, confidence, evidence = non_resource_special.classify(
            {"text": "이번 턴이 종료될 때까지 전투 BGM을 변경 (일부 전투 제외)"}
        )
        assert kind is non_resource_special.AuditKind.OUT_OF_SCOPE


# ---------------------------------------------------------------------------
# E27 - cross_identity clause audit (cross_identity_clause_audit_v1.py)
# ---------------------------------------------------------------------------
class TestCrossIdentityE27:
    def test_affiliation_membership_count(self):
        hits = cross_identity.classify_clause("같은 소속 아군이 3명 이상이면 버프를 얻는다")
        clusters = {h.cluster for h in hits}
        assert cross_identity.CrossCluster.AFFILIATION_MEMBERSHIP_COUNT in clusters

    def test_out_of_axis_when_no_cross_identity_marker(self):
        hits = cross_identity.classify_clause("이번 턴이 종료될 때까지 전투 BGM을 변경")
        assert hits[0].cluster is cross_identity.CrossCluster.OUT_OF_AXIS


# ---------------------------------------------------------------------------
# E28 - target_selection clause audit (target_selection_clause_audit_v1.py)
# ---------------------------------------------------------------------------
class TestTargetSelectionE28:
    def test_random_target(self):
        hits = target_selection.classify_clause("무작위 대상 1명에게 잔영 부여")
        clusters = {h.cluster for h in hits}
        assert target_selection.TargetCluster.RANDOM in clusters

    def test_lowest_resource_target(self):
        hits = target_selection.classify_clause("탄환을 가장 적게 보유한 아군 1명")
        clusters = {h.cluster for h in hits}
        assert target_selection.TargetCluster.LOWEST_RESOURCE in clusters


# ---------------------------------------------------------------------------
# E29 - stack_threshold audit (stack_threshold_audit_v1.py)
# ---------------------------------------------------------------------------
class TestStackThresholdE29:
    def test_cumulative_and_resource_routes(self):
        routes = {
            r.route
            for r in stack_threshold.route_clause(
                "누적으로 자신의 생체 재료 횟수 10을 소모할 때마다 생체 재료를 1 얻음"
            )
        }
        assert "numeric_or_resource_threshold" in routes
        assert "resource_or_stack_threshold" in routes

    def test_activation_limit_route(self):
        routes = {r.route for r in stack_threshold.route_clause("스킬당 1회, 최대 3회")}
        assert "activation_limit" in routes


# ---------------------------------------------------------------------------
# E30 - skill_transform audit (skill_transform_audit_v1.py)
# ---------------------------------------------------------------------------
class TestSkillTransformE30:
    def test_true_skill_swap(self):
        a = skill_transform.classify("기본 스킬 하나를 '전원, 처형이다!!'로 변경")
        assert a.classification is skill_transform.SkillTransformClass.TRUE_SWAP

    def test_skill_reclassify_not_confused_with_swap(self):
        a = skill_transform.classify(
            "기본 공격 스킬과 합 가능 반격 스킬이 충전 횟수를 얻는 스킬로 취급됨"
        )
        assert a.classification is skill_transform.SkillTransformClass.SKILL_RECLASSIFY


# ---------------------------------------------------------------------------
# E31 - multi_target clause audit (multi_target_clause_audit_v1.py)
# ---------------------------------------------------------------------------
class TestMultiTargetE31:
    def test_all_targets(self):
        hits = multi_target.classify("모든 아군에게 버프를 부여")
        clusters = {h.cluster for h in hits}
        assert multi_target.Cluster.ALL_TARGETS in clusters

    def test_random_multi_target_with_count_scaling(self):
        hits = multi_target.classify(
            "사망한 아군 거미집 소속 인격 3명당, 추가로 무작위 적 1명에게 잔영 부여"
        )
        clusters = {h.cluster for h in hits}
        assert multi_target.Cluster.RANDOM_MULTI in clusters
        assert multi_target.Cluster.TARGET_COUNT in clusters


# ---------------------------------------------------------------------------
# E32 - probability_random audit (probability_random_audit_v1.py)
# ---------------------------------------------------------------------------
class TestProbabilityRandomE32:
    def test_random_target_without_percent(self):
        assert probability_random.classify_text("무작위 대상 1명에게 상태 부여") == "random_target"

    def test_probabilistic_effect_without_reuse_marker(self):
        assert probability_random.classify_text("50% 확률로 침묵 부여") == "probabilistic_effect"


# ---------------------------------------------------------------------------
# E33 - special_state audit (special_state_audit_v1.py)
# ---------------------------------------------------------------------------
class TestSpecialStateE33:
    def test_resource_zero_state_routes_to_resource(self):
        r = special_state.audit([{"source_text": "예지안이 0이 되면 예지안 과열 상태가 됨"}])
        assert r["classification_counts"]["resource_or_counter_state"] == 1
        assert r["new_dedicated_runtime_confirmed"] is False

    def test_turn_lifecycle_routing(self):
        r = special_state.audit([{"source_text": "턴 종료 시 다음 턴에 상태를 얻음"}])
        assert r["classification_counts"]["turn_lifecycle_state"] == 1

    def test_skill_state_routes_to_skill_action_primitives(self):
        r = special_state.audit([{"source_text": "다음 턴 시작 시 기본 스킬 하나를 특정 스킬로 변경"}])
        assert r["classification_counts"]["skill_or_action_state"] == 1

    def test_resource_state_routes_to_resource_runtime(self):
        r = special_state.audit([{"source_text": "조망 21 얻음"}])
        assert r["classification_counts"]["resource_or_counter_state"] == 1

    def test_axis_counts_unique_sources(self):
        rows = [
            {"source_text": "예지안 0"},
            {"source_text": "예지안 0"},
            {"source_text": "턴 종료 시 상태 변경"},
        ]
        r = special_state.audit(rows)
        assert r["record_count"] == 3
        assert r["unique_source_text_count"] == 2
        assert r["contract_gap_count"] == 0
