# 7대 키워드 Runtime 연결부 감사 — 2026-09-22

## 이번 범위
현재 0.7.0 작업본의 7대 키워드 Runtime, DamageEngine 연결부, lifecycle catalog, 관련 regression tests를 점검했다.

## 결과

| 키워드 | 현재 공통 Runtime | 현재 연결 | 감사 결과 |
|---|---|---|---|
| Burn | KeywordRuntime.turn_end | DamageEngine.turn_end | 기본 Turn End 피해/Count 소비 연결됨 |
| Bleed | 별도 BleedClashProbabilityRuntime + TurnBleedStateRuntime | Attack/Coin 경로 | 공통 Runtime으로 억지 통합하지 않는 현재 경계 유지 |
| Tremor | KeywordRuntime.burst | Rule/Effect + turn_end | **수정: Burst 외에도 Turn End Count -1 필요** |
| Rupture | KeywordRuntime.on_target_hit | DamageEngine hit bridge | Hit 단위 소비/고정 피해 연결됨 |
| Sinking | KeywordRuntime.on_target_hit | DamageEngine hit bridge | SP 대상 기본 경로 연결됨; **Non-SP Gloom/Deluge는 별도 Gap** |
| Poise | KeywordRuntime.on_critical / turn_end | Crit resolution | 확률/치명타 Count 소비/Turn End 소비 연결됨 |
| Charge | ResourceRuntime + KeywordRuntime.turn_end | resource/effect bridge | Count lifecycle 연결됨; **Charge Potency/Unique Charge는 별도 Gap** |

## 수정 사항

### Tremor
기존 `turn_end()`가 Burn/Poise/Charge만 처리하고 Tremor Count를 감소시키지 않았다.
따라서 Burst가 없는 턴에도 Tremor Count가 1 감소하도록 `KeywordRuntime.turn_end()`에 추가했다.

- Burst: 기존처럼 Burst 시 Count를 즉시 소비
- Turn End: 남은 Tremor Count에서 1 감소
- 0이 되면 상태 제거
- Stagger Threshold 자체는 Turn End에서 변경하지 않음

## 의도적으로 미수정한 Gap

### Sinking Non-SP / Deluge
현재 `EnemyState`는 SP 필드를 기본적으로 갖지만, Non-SP 대상이라는 개념과 Sinking Deluge를 공통 Runtime에 임의로 추가할 근거가 충분하지 않아 이번 패치에서 추정 구현하지 않았다. 별도 Rule/Target capability가 필요하다.

### Charge Potency / Unique Charge
현재 FighterState의 기본 Charge는 Count 중심이다. 공개 규칙에는 일부 Charge 사용자가 Charge Potency를 별도로 축적하고 Count가 0이 되어도 특정 조건에서 Potency가 유지되는 구조가 있으므로, 이를 단일 `charge` 정수로 확장하면 안 된다. 별도의 resource field/Rule contract가 필요하다.

### Bleed
Bleed는 일반 KeywordRuntime의 단순 on_hit/turn_end로 옮기지 않았다. Attack Coin roll 및 Clash exchange라는 특수 소비 단위를 이미 별도 Runtime이 표현하고 있기 때문이다.

## 테스트

수정 범위 회귀:
- `test_keyword_runtime.py`
- `test_status_effect_runtime.py`
- `test_clash_bleed_probability.py`
- `test_v29_bleed_finalization.py`
- `test_v29_turn_bleed_state.py`

결과: **60 passed**

## 다음 우선순위

1. Sinking의 Non-SP / Deluge를 Target capability + RuleIR로 연결
2. Charge Count / Charge Potency / Unique Charge를 분리된 Resource contract로 정식화
3. 7개 keyword의 Skill/Passive 데이터 연결부를 전수 coverage audit

## 후속 반영 — Sinking Non-SP / Deluge

외부 공개 규칙 확인 결과, Sinking은 Non-SP 유닛에 대해 일반적인 SP 피해 대신 Gloom HP 피해로 처리되며, Sinking Deluge는 `Sinking Potency × Sinking Count`의 SP 피해를 가한다. SP 유닛은 -45 SP를 넘는 초과분이 Gloom HP 피해로 전환되고, Non-SP 유닛은 전량 Gloom HP 피해로 처리된다. Deluge 활성화 후 Sinking은 제거된다.

이번 반영:
- 유닛별 `is_abnormality` 분기에서 일반 Sinking Hit를 Gloom HP 피해로 실행
- 명시적인 `sinking_deluge` EffectIR kind 추가
- Deluge는 Hit마다 자동 실행하지 않고 Rule/Effect가 명시적으로 호출할 때만 실행
- Deluge는 Potency×Count를 사용하고 Sinking을 제거
- Rule target이 있으면 해당 target에 적용할 수 있도록 `target` 인자를 지원

근거: Limbus Company Wiki의 Sinking 설명 및 Deluge 사례.

## 2026-09-22 — Sinking damage routing / target-side mitigation

- SP-bearing targets: Sinking is SP-only by default. Damage that would exceed the SP floor does **not** reduce HP by default.
- Non-SP/Abnormality targets: Sinking becomes Gloom HP damage.
- Gloom HP damage applies the target's `sin_res.gloom` affinity multiplier.
- Seven-keyword target-side damage modifiers are supported through `EnemyState.keyword_damage_modifiers` (1.0 = normal, 0.5 = 50% damage, 0 = immune). This is intentionally separate from Sin/Gloom affinity resistance.
- `sinking_sp_overflow_to_hp` is an explicit opt-in compatibility option for scenarios that need the prior Deluge overflow behavior. Default is false.
- Solver input accepts `keyword_damage_modifiers` and `sinking_sp_overflow_to_hp` per enemy.
- Targeted regression after this change: 134 passed.
- Full regression was started but exceeded the 120s execution limit in this environment; therefore it is not marked as fully passed.
