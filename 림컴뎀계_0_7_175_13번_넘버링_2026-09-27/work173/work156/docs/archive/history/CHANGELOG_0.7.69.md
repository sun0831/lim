# 0.7.69 — 실제 원문 기믹 오판 수정: 호흡 Target 의미 정합화

## 목적
실제 identity_catalog_v2.json의 원문 표현과 Target Selector 의미가 어긋난 사례를 수정한다.

## 발견된 오판
원문에는 다음 두 표현이 구분되어 사용된다.

- `호흡 위력을 가장 많이/적게 보유한` → 호흡 위력(Poise potency)
- `호흡을 가장 많이/적게 보유한` → 호흡 횟수(Poise count)

기존 구현은 `호흡`이라는 표현을 `poise_potency_*`로 처리하여, `호흡 횟수`가 아닌 경우에도 위력을 비교했다.

실제 원문 사례:
- `호흡을 가장 많이 보유한 아군 1명이 ...`
- `호흡을 가장 적게 보유한 아군 1명이 ... (호흡이 없는 대상에게는 적용되지 않음)`

## 수정
- bare `호흡을 가장 많이` → `poise_count_max`
- bare `호흡을 가장 적게` → `poise_count_min`
- explicit `호흡 위력` → `poise_potency_max/min`
- explicit `호흡 횟수` → `poise_count_max/min`
- `poise_count_max` Selector/Runtime 추가

## 검증
- `test_target_selection.py`
- `test_identity_specific.py`
- `test_triggers_actions_queue.py`
- 결과: 111 passed / 0 failed
