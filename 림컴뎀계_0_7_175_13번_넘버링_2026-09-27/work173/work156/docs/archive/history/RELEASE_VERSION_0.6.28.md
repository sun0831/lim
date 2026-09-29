# Release 0.6.28

검계 본국검술 서포트의 피해 증가 효과를 특정 기믹 코드가 아니라 공통 `DamageModifierRuntime`으로 처리하도록 확장했다.

- Generic Damage Modifier Runtime 추가
- `damage_percent` / `critical_damage_percent` / `flat_damage` 기반 마련
- 공격 유형 / 크리티컬 / 스킬 / 대상 조건 지원
- 본국검술 서포트 +15%를 공통 Runtime으로 연결
- 전체 회귀 테스트 301개 통과
