# 0.7.45

## 10409 제.지 — 신규 흐트러짐 트리거 공통화
- `identity-10409`의 `자신을 제외한 아군의 공격으로 흐트러짐 상태가 된 적`을 `ally_new_stagger_assist` 공통 TriggerRule로 정리.
- 트리거는 공격 시작/종료 상태를 비교한 `newly_staggered`를 사용한다.
- 이미 흐트러진 상태가 다음 턴까지 유지된 대상은 재발동 조건에 포함하지 않는다.
- 턴당 1회 활성화 제한 유지.
- 대상 선택은 원문대로 여러 대상이 새롭게 흐트러졌을 경우 체력이 가장 낮은 대상이며, 환상체는 본체 우선 이후 부위 규칙을 유지한다.
- 후속 S1의 제.지 전용 효과(진동 횟수 +1, 마지막 코인 진동 폭발)는 기존 identity-specific effect boundary를 유지한다.

## Activation/Golde​n inventory audit
- 현재 `identity_catalog_v2.json` 기준 TriggerRule inventory를 갱신: 67 rules.
- activation scope: global 61 / per_turn 2 / per_identity 1 / per_target 2 / per_skill 1.
- migration-safe catalog golden parity inventory: 67 rules.
- 과거 56-rule A1 기준값은 현재 catalog가 확장되면서 stale 상태였으므로 현재 catalog 기준으로 테스트 기대값을 갱신했다.
