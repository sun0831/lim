"""Safely merged test file (AST-aware, whole-file rename incl. call sites, decorators preserved via line-removal import stripping).
Originals: test_rule_ir_compiler_e35.py, test_rule_ir_compiler_e35_4.py, test_rule_ir_compiler_e35_6.py
"""
from __future__ import annotations

import pytest
from rule_ir_compiler_v1 import compile_clause, compile_text, compile_record
from rule_ir_compiler_v1 import compile_clause
from rule_ir_compiler_v1 import compile_compound_clause


# ---- merged from test_rule_ir_compiler_e35.py ----


def test_damage_clause_lowers_to_rule_ir_and_registry_contract():
    rules = compile_clause("적중 시 피해량 +10%", "I1", "r1")
    assert len(rules) == 1
    r = rules[0]
    assert r.owner_id == "I1"
    assert r.trigger == "hit"
    assert r.effects[0].kind == "ModifyContext"
    assert r.effects[0].params["primitive_id"] == "damage_modifier_effect"


def test_status_clause_lowers_to_status_contract():
    rules = compile_clause("적에게 출혈 3 부여", "I1", "r2")
    assert len(rules) == 1
    assert rules[0].effects[0].params["primitive_id"] == "status_effect"


def test_resource_clause_preserves_structural_value():
    rules = compile_clause("적중 시 충전 2 증가", "I1", "r3")
    assert len(rules) == 1
    effect = rules[0].effects[0]
    assert effect.params["primitive_id"] == "resource_effect"
    assert "amount" in effect.params["value"]


def test_next_turn_clause_preserves_deferred_metadata():
    rules = compile_clause("적중 시 다음 턴에 출혈 2 부여", "I1", "r4")
    assert len(rules) == 1
    assert rules[0].metadata["deferred_turns"] == 1


def test_multi_clause_text_compiles_each_clause_without_dropping_source():
    rules, reasons, unsupported = compile_text("적중 시 충전 1 증가\n적에게 출혈 2 부여", "I1")
    assert len(rules) == 2
    assert {r.source_text for r in rules} == {"적중 시 충전 1 증가", "적에게 출혈 2 부여"}


def test_unsupported_clause_is_not_fabricated_into_rule_ir():
    rules, reasons, unsupported = compile_record({"id":"p", "name":"x", "effect":"전투 BGM 변경"}, "I1")
    assert rules == []
    assert unsupported


def test_e35_coverage_audit_has_no_unknown_registry_contracts():
    from e35_ruleir_coverage_audit_v1 import run
    audit = run("GIMMICK_GAP_REPORT_v4.json")
    assert audit["record_count"] == 360
    assert audit["total_clauses"] == 1103
    assert audit["converted_clauses"] == 346
    assert audit["unknown_primitive_contracts"] == {}
    assert audit["clause_conversion_rate_percent"] == 31.37


# ---- merged from test_rule_ir_compiler_e35_4.py ----


def test_e35_4_skill_swap_lowering():
    rs = compile_clause("기본 스킬 하나를 ‘처분’으로 변경 (가장 왼쪽 슬롯의 위 스킬 우선)", "I", "r")
    assert rs and rs[0].effects[0].params["primitive_id"] == "skill_swap_timed"
    assert rs[0].effects[0].params["slot_policy"] == "leftmost_above"


def test_e35_4_forced_followup_lowering():
    rs = compile_clause("스킬 종료 시 '포장을 뜯어볼까'로 일방 공격함", "I", "r")
    assert rs and rs[0].effects[0].params["primitive_id"] == "forced_followup_action"


def test_e35_4_lowest_resource_target_lowering():
    rs = compile_clause("탄환을 가장 적게 보유한 아군 1명이 스킬을 사용하면 호흡 3 부여", "I", "r")
    assert rs and rs[0].target.selector == "lowest_resource"
    assert rs[0].target.filters["resource"] == "탄환"


def test_e35_4_affiliation_target_lowering():
    rs = compile_clause("거미집 소속 아군 인격에게 보호막 1 부여", "I", "r")
    assert rs and rs[0].target.selector == "affiliation"


def test_e35_4_death_trigger_lowering():
    rs = compile_clause("아군 인격 사망시, 자원 3 얻음", "I", "r")
    assert rs and rs[0].trigger == "unit_death"


def test_e35_4_independent_rng_lowering():
    rs = compile_clause("확률은 각 탄환마다 개별적으로 적용됨", "I", "r")
    assert rs and rs[0].effects[0].params["rng_scope"] == "per_coin"


# ---- merged from test_rule_ir_compiler_e35_6.py ----

def test_compound_condition_and_resource_effect_lowers():
    r = compile_compound_clause("턴 시작 시 정신력이 40 이상이면 / 정신력 20 소모", "I", "r")
    assert r is not None
    assert r.status == "implemented"
    assert r.conditions[0].op == "gte"
    assert r.effects[0].params["mode"] == "consume"

def test_compound_unknown_is_partial_not_fabricated():
    r = compile_compound_clause("턴 시작 시 정신력이 40 이상이면 / 손도끼로 갈비뼈를 찍어 내릴 때는", "I", "r")
    assert r is not None
    assert r.status == "partial"
    assert r.metadata["unknown_fragments"]
