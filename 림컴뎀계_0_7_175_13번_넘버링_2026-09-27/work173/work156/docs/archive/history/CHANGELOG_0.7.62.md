# 0.7.62 — 특정 편성 슬롯 Target Selector 정합화

## 목적
실제 identity_catalog_v2.json의 `편성 순서가 1번인 아군` 문구를 기존 `가장 빠른/가장 뒤` 및 상대적 편성 순서와 분리해 표현한다.

## 변경
- `target_selector_v1.py`
  - `formation_slot:N` 추가
  - `formation_1/2/3` alias 추가
  - 편성 슬롯은 1-based로 처리
- `passive_runtime_v29_base.py`
  - `AllySelectorTarget`에서 `formation_slot:N` 지원
  - 기존 `formation_min/max`, `formation_before_owner/after_owner`와 분리
- 특정 identity의 전체 패시브를 구현한 것이 아니라 재사용 가능한 Target Selector 경계만 추가.

## 실제 원문 근거
현재 catalog에서 확인된 대표 문구:
- `편성 순서가 1번인 아군이 스킬, 코인 효과로 얻는 진동 횟수의 값 +1`
- `편성 순서가 1번인 아군의 충전 횟수 최대치 +5`

## 검증
- 신규/관련 targeted regression: **107 PASS / 0 FAIL**
- 전체 pytest: **850 PASS / 8 FAIL**
  - 실패 8건은 이번 변경과 직접 관련 없는 기존 catalog inventory 불일치, 별도 compiler 기대치, `/tmp/v736` 외부 경로 의존 테스트 등으로 확인됨.
  - 본 변경의 targeted suite는 모두 통과.
