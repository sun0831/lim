# 0.7.32 — Tremor Burst / Count 분리

## 핵심 수정
- `진동 폭발` 자체가 `진동 횟수 1 감소`를 의미하지 않도록 수정.
- 인격/스킬 원문에 `진동 폭발. 대상의 진동 횟수 1 감소`처럼 Count 감소가 명시된 경우에만 `count_cost=1`을 부여.
- 엔진에서도 `tremor_burst`에 `count_cost`가 없는 경우 Count를 보존.
- 기존 직접 effect 호출에서 `count_cost=1`을 명시하면 여전히 감소 가능하므로 하위 호환 유지.

## 10406 LCCB 대리 료슈 검증
실제 `identity_catalog_v2.json`의 1040603 마지막 코인은 다음 순서로 처리:
1. 크리티컬 시 진동/파열 위력·횟수 2배
2. 진동/파열 부여
3. 진동 폭발

해당 Burst에는 Count 감소 문구가 없으므로:
- 크리티컬: 진동 8/4, 파열 8/4
- 비크리티컬: 진동 4/2, 파열 4/2

## 테스트
- 신규 Count semantics 테스트 포함 targeted Tremor suite: 25 passed
- Wider Tremor/Amplitude/RuleIR suite: 53 passed, 1 failed
- 실패: 기존 E35 registry audit `336 == 337` mismatch (이번 수정과 무관)
