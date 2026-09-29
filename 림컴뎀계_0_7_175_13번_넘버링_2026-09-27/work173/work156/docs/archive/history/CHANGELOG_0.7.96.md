# 0.7.96 — 버프/디버프 원문 정합성 추가 감사

## 확정 오판

1. **Crit DMG Up**
   - 원문: 스택당 Critical Hit 피해 +10%.
   - 기존 공통 catalog/runtime 매핑은 `critical_damage_percent`에 스택 값을 그대로 넣어 1스택=+100%가 될 수 있었음.
   - 수정: 스택당 `0.10`으로 변환.

2. **Weak-resist DMG Boost**
   - 원문: Weak resistance 대상 공격 피해를 `X%` 증가.
   - 기존 catalog가 일반 `damage_scale`로 분류되어 대상이 Weak인지 확인하지 않고 전역 피해 증가로 적용될 수 있었음.
   - 수정: `weak_resist_damage_scale`로 분리하고 현재 공통 runtime에서는 조건을 증명할 수 없으므로 deferred 처리. 잘못된 unconditional damage 적용을 차단.

## 검증
- 68 PASS / 0 FAIL
