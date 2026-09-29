# 림컴뎀계 0.6.38 — Rule IR 실행 이관 안전성 강화

## 이번 사이클
- Legacy TriggerRule의 activation counter는 기존 TriggerRule이 계속 소유한다.
- `RuleMigrationRuntime.fire_migrated()`가 generic-safe Rule을 Rule IR → EffectCommand → EffectExecutor 경로로 실제 실행한다.
- deferred effect는 기존 fired payload 형태로 반환되어 전문 Runtime이 계속 처리할 수 있다.
- core resource(`충전`, `탄환`, `호흡`)를 ResourceRuntime이 직접 관리하도록 확장했다.
- `예지안` 소모 후 0 도달 시 `예지안 과열` 전환을 generic resource effect에서 보존한다.
- `extra_damage_scale`, `status_potency_damage`는 기존의 즉시 피해 타이밍을 유지하는 실행기를 추가했다.
- Rule migration execution golden tests 4개를 추가했다.

## 현재 측정
- 카탈로그 인격: 184
- compiled TriggerRule: 53
- fully generic Rule: 20
- deferred Rule: 33
- unknown Rule: 0
- 전체 테스트: 339 passed

## 주의
이번 버전에서도 `GimmickRegistry`의 모든 이벤트 호출을 일괄적으로 Rule IR 경로로 전환하지 않았다. generic-safe effect의 실제 실행 경계와 golden test를 먼저 확보하고, 다음 단계에서 이벤트별로 Legacy 실행을 제거한다.
