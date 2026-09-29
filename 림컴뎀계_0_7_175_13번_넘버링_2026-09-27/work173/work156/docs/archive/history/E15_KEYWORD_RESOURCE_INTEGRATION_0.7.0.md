# E-15 — Poise / Charge 공통 Runtime 통합

## 목적
E-13/E-14에서 만든 KeywordRuntime 골격을 기존 Poise/Charge 상태축과 실제 엔진 lifecycle에 연결한다.

## 변경
- `KeywordRuntime.on_critical()` 추가: 하나의 논리적 Critical당 Poise Count를 정확히 1회 소비.
- `KeywordRuntime.turn_end()`가 Poise Turn End 감소를 단독 소유.
- `KeywordRuntime.turn_end()`가 일반 `Charge`만 1 감소시킴.
- `생체 재료` 등 `FighterState.resources`의 Charge-equivalent 자원은 자동 감소시키지 않음.
- `DamageEngine.turn_end()`의 중복 Poise 감소 제거.
- `DamageEngine`의 Critical Poise 소비를 공통 Runtime으로 연결.
- `resource_runtime`가 State Runtime에 존재하면 Charge lifecycle에서 재사용.

## 중요한 정정
E-14 코드에는 `KeywordRuntime.turn_end()`와 `DamageEngine.turn_end()` 양쪽에 Poise Count 감소가 존재하여 실제로 Turn End에 2회 감소할 수 있는 구조가 있었다. E-15에서 공통 Runtime을 단일 소유자로 만들고 중복 감소를 제거했다.

## 검증
- 신규 E-15 테스트: 3개
- 전체 테스트: 469개 PASS
- 기존 테스트의 Poise multi-target / crit persistence / Resource lifecycle도 재실행하여 통과 확인
