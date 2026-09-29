# 림컴뎀계 0.6.40 — 테스트 구조 정리 1차 + 최적화 작업 기준선

## 기준선
- 기준 코드: 0.6.39 migration safety gate
- 전체 테스트: 342개
- 테스트 파일: 123개
- 전체 실행 결과: **342 passed**
- 전체 실행 시간: pytest 16.44초 (프로세스 포함 18.65초)

## 1차 테스트 감사 결과

테스트는 삭제하지 않고 먼저 역할별로 분류했다.

| 영역 | 테스트 수 |
|---|---:|
| combat/runtime | 91 |
| gimmick/integration | 112 |
| architecture/runtime | 76 |
| probability/bleed | 32 |
| other | 31 |
| **합계** | **342** |

### 중요한 결과
- 단순 AST body 기준으로 완전히 동일한 테스트 본문은 1개 그룹(2개 테스트)뿐이다.
- 따라서 현재 342개를 단순히 "중복 테스트가 많아서" 대량 삭제하는 것은 근거가 부족하다.
- 실제 병합 후보는 **같은 Runtime 계약을 서로 다른 레거시 계층에서 반복 검증하는 테스트**이며, 이는 Runtime 이관이 진행된 뒤에 병합해야 한다.

## 2차 작업 원칙

1. 기존 테스트를 먼저 보존한다.
2. Rule/Condition/Effect/Target/Action Runtime 이관으로 검증 계층이 확정되는 순서에 맞춰 중복 테스트를 병합한다.
3. Identity-specific 테스트는 공통 Runtime 테스트로 흡수된 부분만 제거한다.
4. 과거 버그를 재현하는 regression/golden 테스트는 유지한다.
5. 최종적으로 `Unit → Runtime → Gimmick Integration → Identity Golden → Full Regression` 계층을 만든다.

## 다음 최적화 대상
0.6.39 기준으로 Rule Migration Report에는 53개 TriggerRule이 있고, fully generic 20개 / deferred 33개로 분류된다. 다음 최적화는 테스트를 먼저 삭제하는 것이 아니라, migration-safe rule의 shadow/golden 비교를 추가하여 Legacy handler 제거의 근거를 만드는 것이다.

특히 action/target 계열 deferred effect는 ActionQueue 및 기존 support/assist runtime과의 의미 보존이 확인된 뒤 이관한다.
