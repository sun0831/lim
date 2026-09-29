# 0.7.39 — 추가 코인 Action Trace 경계

## 변경
- 실제 인격 파일 기반 추가 코인 실행을 Action Trace에서도 별도 식별 가능하도록 coin event에 `is_added_coin` / `coin_origin`을 추가.
- `coin_target_resolution`에도 동일한 추가 코인 경계를 노출.
- 기존 상태/피해 계산 로직은 변경하지 않음.

## 검증
- 신규 추가 코인 trace regression: 1 passed
- 특수 진동 경계: 7 passed
- Tremor / Amplitude / RuleIR 관련: 67 passed
- 총 확인: 67개 묶음 모두 통과
