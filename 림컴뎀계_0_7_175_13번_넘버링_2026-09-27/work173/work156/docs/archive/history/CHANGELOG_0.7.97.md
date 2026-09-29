# 0.7.97 — Clash Power 원문 오판 수정

## 목적
341KB 버프/디버프 원문과 현재 공통 Runtime의 의미를 대조하여, 이미 구현된 효과가 원문과 다른 채널로 해석되는 문제를 수정.

## 확정 오판

### 1. Clash Power Up/Down이 Skill Power 채널로 매핑됨
원문:
- Clash Power Up → Clash Power +X for this turn.
- Clash Power Down → Clash Power -X for this turn.

기존:
- `clash_power` semantic → `skill_power` modifier

수정:
- `clash_power` → 독립 `clash_power` modifier
- 공격자 측은 Clash 실행 시 attacker base clash power에 적용
- 방어자 측은 Clash 실행 시 defender clash power에 적용
- Final Skill Power / 피해량 채널로 누수되지 않도록 분리

### 2. catalog의 potency/count 소스 선택이 semantic 값만 보고 결정됨
예:
- Power Up: `count -> final_power`
- Power Down: `potency -> final_power`
- Clash Power Up: `count -> clash_power`
- Clash Power Down: `potency -> clash_power`

기존 generic fallback은 `final_power`/`clash_power`라는 semantic만 보고 Count를 선택할 수 있어 Down 계열의 Potency 값을 0으로 읽을 수 있었음.

수정:
- catalog의 semantic key 자체(`count`, `potency`, `stack`, `value`)를 수치 소스로 사용.

## 검증

- buff/debuff 전체 관련 테스트 + status/damage scope + 0.7.97 신규 감사 테스트
- **88 PASS / 0 FAIL**

## 범위 외

`Multiply Coin Boost/Drop`, 공격 유형별 Power/Protection 등은 현재 공통 catalog에 없는 **미구현 gap**으로 분리했으며 이번 오판 수정 카운트에는 포함하지 않음.
