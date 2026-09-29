# 0.7.63 — 충전 보유자 중 최저 충전 Target Selector 정합화

## 변경
- 실제 identity catalog의 문구:
  - `충전을 보유한 아군 중 충전 횟수가 가장 낮은 아군 1명`
- 기존 `charge_min`은 충전 0인 아군까지 후보에 포함하므로 위 문구와 의미가 다름.
- 새 Selector:
  - `charge_positive_min`
  - alias: `lowest_charge_holder`
- 후보 조건: `charge > 0`인 살아있는 아군만 대상.
- 그 후보 중 충전 횟수가 가장 낮은 아군을 선택.
- `AllySelectorTarget`에도 동일 정책 적용.
- passive compiler가 실제 문구를 `charge_positive_min`으로 매핑.

## 범위
- 특정 인격 전체 패시브 구현이 아니라 재사용 가능한 Target Selector 경계만 추가.
- 기존 `charge_min`은 유지.

## 검증
- `test_target_selection.py`
- `test_identity_specific.py`
- `test_triggers_actions_queue.py`
- 결과: **107 passed / 0 failed**
