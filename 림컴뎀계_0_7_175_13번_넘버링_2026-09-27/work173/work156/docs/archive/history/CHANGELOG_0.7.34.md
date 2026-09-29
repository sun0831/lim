# 0.7.34 — Tremor Burst / Count 명시 규칙 분리 강화

## 핵심
- `진동 폭발` 자체에는 Count 감소를 자동 부여하지 않음.
- 실제 인격 원문에 `진동 횟수 N 감소`가 명시된 경우에만 `count_cost=N`을 생성.
- `진동 폭발 N회`와 `진동 횟수 M 감소`를 별도 축으로 표현:
  - `burst_count=N`
  - `count_cost=M`
- `진동 폭발` 원문이 줄바꿈을 포함한 경우에도 후속 Count 감소 문구를 동일 clause에서 파싱하도록 coin parser를 multiline 대응.

## 실제 원문 검증 대상
identity_catalog_v2.json의 Tremor Burst 관련 실제 인격 문구에서 1/2/3/4 Count 감소 및 다중 Burst 사례를 확인.
특히:
- 1040603 LCCB 대리 료슈: `진동 폭발`만 존재 → Count 감소 없음
- 1020703 후회: 마지막 코인에 `진동 횟수 3 감소`
- 1050503 마무리 가속: `진동 횟수 3 감소`
- 1080503 부식성 점액 타격: `진동 횟수 4 감소`
- 1120503 갈아버리자고: `진동 횟수 2 감소`
- 107163/1071635 등: 다중 Burst와 Count 감소가 별도로 명시된 사례 존재

## 테스트
- 신규 명시 Count 파싱 테스트: 5/5
- 기존 Tremor Burst Count/runtime 테스트: 7/7
- Tremor/Amplitude/RuleIR 관련 묶음: 59/59
