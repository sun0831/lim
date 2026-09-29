# 0.7.40 — Tremor Burst Count 암묵 감소 제거

## 핵심
- 실제 인격 문구 기준으로 `진동 폭발`과 `진동 횟수 감소`를 완전히 분리.
- Passive compiler의 `TriggerTremorBurst` 기본 `count_cost`를 `None`으로 변경.
- 원문에 명시된 `진동 횟수 N 감소`가 있을 때만 해당 N을 `count_cost`로 전달.
- 일반 Burst는 Count를 소모하지 않음.
- 기존 직접 호출에서 `count_cost=1`을 명시한 경로는 그대로 지원.

## 검증
- 신규/관련 Tremor 테스트: 19/19 passed
- 이번 변경은 실제 인격 파일의 명시적 Count 감소 여부를 기준으로만 적용.
