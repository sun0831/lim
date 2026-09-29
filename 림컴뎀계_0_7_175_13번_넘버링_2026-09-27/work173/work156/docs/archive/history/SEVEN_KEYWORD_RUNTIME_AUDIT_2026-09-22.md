# 7대 키워드 Runtime 감사 — 2026-09-22

## 감사 결과

| 키워드 | 상태 | 핵심 판단 |
|---|---|---|
| Burn | 부분 구현 | Turn End 고정 HP 피해는 공통 Runtime에 존재. Unique/즉시 Activate는 Rule/Identity 층에서 처리 필요. |
| Bleed | 부분 구현 | 확률적 Clash/coin runtime은 별도 존재하지만 공통 KeywordRuntime의 일반 공격 Coin 경로와 완전히 통합되지 않음. |
| Tremor | 수정 | 기존 `burst()`가 Potency를 HP 피해로 처리하던 오류를 수정. 기본 Tremor Burst는 Stagger Threshold 상승 + Count 소비. |
| Rupture | 부분 구현 | Hit마다 Potency 고정 피해 + Count 소비 구조 존재. 신규 적용 타이밍/특수 변형은 Rule 층 필요. |
| Sinking | 부분 구현 | Hit마다 SP 피해 + Count 소비 존재. Non-SP → Gloom HP 및 Deluge는 별도 확장이 필요. |
| Poise | 부분 구현 | Critical 성공 시 Count 소비와 Turn End Count 감소 존재. 기본 Crit 확률 helper(`Potency × 5%`, 100% cap)를 추가. 실제 확률 분기는 solver 정책에 맡김. |
| Charge | 부분 구현 | Count gain/spend 및 Turn End -1이 ResourceRuntime/KeywordRuntime에 존재. Unique Charge와 누적 소비량은 Rule/Resource 층에서 처리. |

## 중요한 설계 결론

1. 7개를 하나의 동일한 피해 Runtime으로 합치면 안 된다.
2. 공통화 대상은 `potency/count 저장`, `gain/change/consume`, `trace` 같은 상태 수명 관리다.
3. 발동 단위는 키워드별로 분리해야 한다.
   - Burn: Turn End
   - Bleed: Attack Coin / Clash Coin
   - Tremor: Tremor Burst
   - Rupture: Hit
   - Sinking: Hit
   - Poise: Critical / Turn End
   - Charge: Gain / Spend / Turn End
4. Tremor Burst는 기본적으로 HP 피해가 아니다. Stagger Threshold를 올리고 Tremor Count를 소비한다.
5. Bleed는 기존 `bleed_clash_probability_v1.py` 및 `TurnBleedStateRuntime`과 연결되는 별도 실행축을 유지한다.
6. Sinking은 SP 보유 여부에 따라 결과가 달라질 수 있으므로 `is_sp_unit` 같은 명시적 상태가 필요하다.

## 이번 코드 수정

- `KeywordRuntime.burst(Tremor)` → HP 피해 제거, Stagger Threshold 상승 + Count 소비로 수정.
- `DamageEngine.apply_effect(tremor_burst)` → 동일하게 수정.
- Poise 기본 치명타 확률 helper 추가: `min(100, potency * 5)`.
- 기존 테스트의 Tremor Burst 기대값을 실제 키워드 의미에 맞게 수정.

## 외부 검증 근거

공개 Limbus Company Wiki의 최신 페이지에서 Bleed는 Attack Coin/Clash 단위 고정 피해, Tremor Burst는 Stagger Threshold 상승, Charge는 Count를 Turn End에 1 감소시키는 구조로 설명된다. Sinking은 Hit 시 SP 피해이며 Non-SP 대상은 Gloom HP 피해 예외가 존재한다. 

- Bleed: https://limbuscompany.wiki.gg/wiki/Bleed
- Charge: https://limbuscompany.wiki.gg/wiki/Charge
- Status effect data: https://limbuscompany.wiki.gg/wiki/Module%3AStatusEffect/data

## 테스트

이번 변경 범위 targeted regression: **54 passed**.
