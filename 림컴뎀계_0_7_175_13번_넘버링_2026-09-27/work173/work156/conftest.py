"""pytest 공통 설정 (테스트 내용은 바꾸지 않음).

- 프로젝트 루트를 import 경로에 추가하고 작업 폴더를 루트로 맞춘다.
  (어느 폴더에서 실행해도 같은 결과가 나오게 함)
- 오래 걸리는 테스트(각 1초 이상)에 `slow` 표시를 붙인다.
    빠른 확인:  python run_tests.py --fast     (slow 제외, 약 3초)
    전체 확인:  python run_tests.py            (기본, 전부 실행)
"""
import os
import sys
import pytest

ROOT = os.path.dirname(os.path.abspath(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
os.chdir(ROOT)

# 실측 1초 이상 걸리는 테스트 (함수 이름 기준이라 파일을 옮겨도 유지됨).
# 새로 느린 테스트가 생기면 여기에 추가.
SLOW_TESTS = {
    "test_all_catalog_migration_safe_rules_have_golden_parity",              # 약 11초 (Legacy 비교, D단계 때 정리 대상)
    "test_infinite_bleed_keeps_terminal_count_fixed_even_after_trim",        # 약 7초 (출혈 확률 정밀 계산)
    "test_final_bleed_trim_reweights_correlated_turn_damage",                # 약 3초
    "test_probabilistic_after_clash_changes_next_exchange_probability_state",# 약 2.5초
    "test_catalog_generic_rules_do_not_fallback_to_legacy",                  # 약 1.5초
    "test_catalog_trigger_rules_are_fully_common_runtime_safe",              # 약 1.3초
    "test_support_right_effect_selects_adjacent_ally_and_default_skill",     # 약 1.2초
    "test_support_command_is_generic_and_keeps_captain_100_percent_rule",    # 약 1.2초
    "test_catalog_activation_inventory_matches_a1_audit",                    # 약 1.5초 (카탈로그 전체 빌드)
}


def pytest_configure(config):
    config.addinivalue_line("markers", "slow: 1초 이상 걸리는 테스트 (--fast 로 제외 가능)")


def pytest_collection_modifyitems(config, items):
    for item in items:
        if item.originalname in SLOW_TESTS or item.name in SLOW_TESTS:
            item.add_marker(pytest.mark.slow)
