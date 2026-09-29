# 0.7.67 — 상태 보유자 + 정신력 복합 Target Selector 정합화

## 작업 범위
실제 `identity_catalog_v2.json`의 다음 문구를 기준으로 복합 Target Selector 경계를 추가했다.

- `identity-35` / Passive: `광신 이 있는 아군 중 정신력이 가장 낮은 아군의 피해량 +10%`

## 구현
- `target_selector_v1.py`
  - `status_present_sp_min:<status>` 추가
  - 상태 보유 여부를 먼저 필터링한 뒤 정신력(SP) 최솟값을 선택
  - `lowest_sp_among_fanatics` 별칭 추가
- `passive_runtime_v29_base.py`
  - `status_present_sp_min:<status>` 런타임 처리 추가
  - 상태명은 대소문자 무관 fallback 지원
  - 기존 Poise selector의 잘못된 `pool` 참조도 정합화하여 실제 `AllySelectorTarget` 경로에서 동작하도록 수정
- `passive_compiler_v29.py`
  - `광신 이 있는 아군 중 정신력이 가장 낮은 아군`을 `status_present_sp_min:광신`으로 승격
  - 명시적인 `N명`이 없는 실제 단수 대상 문구도 count=1로 처리

## 검증
- `test_composite_target_selector.py`: PASS
- `test_target_selector_status_filter.py`: PASS
- `test_target_selection.py`: PASS
- `test_identity_specific.py`: PASS
- `test_triggers_actions_queue.py`: PASS
- 총 112 PASS / 0 FAIL

## 주의
이번 작업은 재사용 가능한 Target Selector/Compiler 경계를 정합화한 것이다.
`identity-35` 패시브 전체가 production Solver/Engine에서 자동 실행되도록 연결됐다고 의미하지 않는다.
RuleIR/Compiler의 production execution 연결은 별도 단계다.
