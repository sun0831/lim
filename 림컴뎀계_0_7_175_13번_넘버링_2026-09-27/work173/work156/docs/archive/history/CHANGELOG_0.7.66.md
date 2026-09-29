# 0.7.66 — 호흡 최다 Target Selector 정합화

## 작업
- 실제 `identity_catalog_v2.json`에서 `호흡을 가장 많이 보유한 아군` 3건 확인.
- 해당 문구를 호흡 **위력(potency)** 기준 최댓값 선택으로 분리.
- `poise_potency_max` Target Selector 추가.
- `AllySelectorTarget`에도 동일 정책 추가.
- 기존 `poise_potency_min` / `poise_count_min`과 의미를 분리 유지.

## 의미 경계
- `호흡을 가장 많이 보유한` → 호흡 위력 최댓값
- `호흡을 가장 적게 보유한` → 호흡 위력 최솟값
- `호흡 횟수를 가장 적게 보유한` → 호흡 횟수 최솟값
- 현재 실제 카탈로그에서 `호흡 횟수를 가장 많이 보유한` 사례는 이번 작업에서 확인되지 않아 구현하지 않음.

## 검증
- `test_target_selection.py`: PASS
- `test_identity_specific.py`: PASS
- `test_triggers_actions_queue.py`: PASS
- 추가 직접 검증: 호흡 위력 최댓값/최솟값 및 미보유자=0 처리 PASS

## 주의
- Passive compiler는 여전히 오프라인 RuleIR/선언적 변환 경계이며, 이 변경만으로 실제 Solver/Engine에서 모든 해당 패시브가 자동 실행된다고 해석하지 않는다.
