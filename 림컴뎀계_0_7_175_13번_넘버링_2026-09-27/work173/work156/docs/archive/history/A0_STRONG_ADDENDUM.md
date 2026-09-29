# A0 강화 addendum (기존 A0_A1_ACTIVATION_AUDIT.md 보완)

기준 소스: 림컴뎀계_0_7_0_E36_A0_A1_merged.zip (production 파일 미변경)
바뀐 파일: `test_activation_scope_parity_a0.py` (11개 → 61개로 교체), `conftest.py` (slow 목록에 1개 추가), 이 문서.

## 이번에 추가로 확인한 사실 (기존 감사 문서에 없던 것)

1. `per_identity_target` 도 actor_id 폴백 차이가 있다 (기존 문서는 per_actor / per_actor_target 만 기록).
   - legacy `ID|T1`  vs  ledger `ACT|T1` (identity_id="ID", actor_id="ACT" 일 때)
2. global 스코프 + `turn_cap < max_activations` 는 legacy 만 turn_cap 을 무시한다.
   - max=2, turn_cap=1, 1회 소비 후: legacy eligible=True / ledger=False / ActivationRuntime=False
3. `limit < 0`: ledger/ActivationRuntime 은 "무제한", legacy TriggerRule 은 "항상 불가".
4. `ActivationRuntime._scope_key` / `.eligible` 가 ActivationLedger 와 코드가 중복돼 있다 (현재는 결과가 같음).
   A3 에서 ActivationRuntime 이 ledger 의 메서드를 호출하도록 바꿔서 중복을 없애야 한다.
5. `ledger.eligible()` 은 `rule.metadata["turn_cap"]` 을 스스로 읽지 않는다. 호출자가 `turn_cap=` 을 넘겨야 한다.
   현재 ProbabilisticTriggerRuntime 과 ActivationRuntime 은 넘기고 있다.

## A2 판단 근거 (정정 포함)

- production 경로(ActivationRuntime, ProbabilisticTriggerRuntime)는 이미 ledger 의미를 쓴다.
  legacy `TriggerRule.eligible/consume` 은 ledger 가 없을 때의 fallback 뿐이다.
- 따라서 "TriggerRule 동작에 맞추자"가 아니라 **production 계약(ledger == runtime)을 정본**으로 삼는 것이 맞다.
  legacy 에 맞추면 production 동작(actor_id 폴백, global turn_cap 적용, limit<0 무제한)이 바뀐다.
- 카탈로그 55개 규칙 기준 영향: per_actor 계열 0개, global+turn_cap 0개, limit<0 0개 → 어느 쪽이든 현재 데이터 영향 0.
- production 에서 actor_id 만 넘기는 호출은 없다. actor_id 폴백은 사용되지 않는 호환 경로다.
  (폴백을 제거할지 유지할지는 게임 규칙 결정 — 이 테스트는 결정하지 않고 현재 동작만 고정)

## 테스트 구성 (61개)

| 묶음 | 개수 | 내용 |
|---|---|---|
| parity (8 스코프 × 5) | 40 | 초기 상태 / 공유 행렬 / limit 2 예산 / production 순서 lockstep / reset |
| scope_key 중복 검증 (8) | 8 | ActivationRuntime._scope_key == ledger.scope_key (actor_id-only 컨텍스트 포함) |
| ledger 성질 | 3 | per_actor_target 격리(A/T1, A/T2, B/T1), clone 분기, snapshot 왕복 |
| turn_cap | 2 | gimmick:38(cap1) / gimmick:39(cap2) 형태의 타깃별 1회 + 턴 전체 cap |
| 알려진 차이 `test_known_diff_*` | 6 | actor_id 3종, per_identity 무차이, global+turn_cap, limit<0 |
| 계약 | 1 | ledger 는 turn_cap 인자를 호출자가 넘겨야 함 |
| 카탈로그 재고 (slow) | 1 | 55개 규칙, 스코프 분포, turn_cap 규칙 2개 |

`test_known_diff_*` 는 A3 에서 legacy 카운터를 지우면 의미가 사라진다. 그때 삭제하고
ledger == runtime 검증만 남긴다. (차이를 "고치는" 것이 아니라 비교 대상이 없어지는 것.)

## 변이 검증 (이 테스트가 실제로 결함을 잡는가)

production 코드를 일부러 망가뜨려서 새 테스트와 기존 A0 테스트(11개)를 비교했다.

| 변이 | 신규 61개 | 기존 11개 |
|---|---|---|
| ledger per_target 키 오류 | 잡음 (8 실패) | 잡음 (1) |
| ledger per_identity_target 이 target 무시 | 잡음 (11) | 잡음 (3) |
| ledger turn_cap 검사 제거 | 잡음 (4) | 잡음 (1) |
| ActivationRuntime._scope_key 오류 | 잡음 (4) | **못 잡음** |
| legacy per_skill 키 오류 | 잡음 (3) | 잡음 (1) |
| ledger consume 이 global 카운트 안 올림 | 잡음 (29) | 잡음 (1) |
| ledger reset 이 버킷을 안 지움 | 잡음 (7) | **못 잡음** |
| legacy 와 ledger 가 **동시에** 같은 방향으로 틀림 | 잡음 (8) | **못 잡음** |

마지막 행이 중요하다. A3 에서 legacy 를 지우고 ledger 를 고치는 동안 "둘 다 함께 틀리는" 회귀는
키 비교형 테스트로는 보이지 않는다. 신규 테스트는 스코프별 공유 행렬을 **의미 수준의 기대값**으로 고정해서 이를 잡는다.
