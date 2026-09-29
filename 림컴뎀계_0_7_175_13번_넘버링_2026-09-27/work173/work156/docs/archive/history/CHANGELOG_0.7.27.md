# 0.7.27 — Tremor canonical application runtime

## 변경
- Tremor 적용을 `KeywordRuntime.add_tremor()`로 공통화.
- Tremor는 Potency와 Count를 독립 축으로 한 번의 상태 변경에서 함께 처리 가능.
- `AddStatus('Tremor', potency, count)`가 공통 Tremor runtime을 사용하도록 변경.
- Rule/Effect 실행 경계의 `status_gain`에서 `status=Tremor`에 `potency`/`count` 파라미터를 지원.
- 이벤트 컨텍스트의 `tremor_potency_bonus` / `tremor_count_bonus`를 Tremor 적용 시점에 합산할 수 있도록 연결. 기존 규칙을 임의로 생성하지 않으며, 값이 없으면 0.
- 기존 Tremor Burst/Amplitude 경로 회귀 테스트 유지.

## 검증
- Tremor/Amplitude/Burst 관련 회귀: 40/40 PASS
- 전체 pytest: 기존 실패 2건이 중간에 재현되었고, 전체 실행은 120초 제한으로 완료되지 않음. 이번 변경으로 새 실패가 추가되었는지는 전체 실행 종료 전까지 단정하지 않음.
