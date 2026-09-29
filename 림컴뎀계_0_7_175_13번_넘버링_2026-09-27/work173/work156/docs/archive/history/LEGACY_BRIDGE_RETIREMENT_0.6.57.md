# 0.6.57 — Production Legacy Bridge Hardening

## 목적

Production 전투 경로에서 Rule IR 실행이 실패했을 때 `special_gimmick_v2.py`의 수동/Legacy 호환 처리로 조용히 내려가는 경로를 차단한다.

## 변경

- `RuleMigrationRuntime.production_fire()`가 live `action_queue` 컨텍스트에서 `migration_execution_deferred`를 발견하면 즉시 `RuntimeError`를 발생시킨다.
- ActionQueue가 없는 compatibility/unit 호출은 기존 deferred payload를 유지한다.
- `GimmickRegistry._fire_migrated_event()`에 production/compatibility 경계를 명시한다.
- Legacy `TriggerRuntime` 자체는 삭제하지 않는다. 외부 호환 및 명시적 테스트 경로를 위해 유지한다.
- 따라서 Production에서는 Generic Rule → Rule IR → EffectExecutor 경로가 실패하면 결과를 조용히 Legacy 처리하지 않고 즉시 검출할 수 있다.

## 검증

- 신규 boundary tests: 2 passed
- 전체 회귀: 382 passed
- Python compile: PASS

## 의미

이번 변경은 Legacy 코드를 무조건 삭제하는 작업이 아니라, **Production 경로와 Compatibility 경로를 명확하게 분리**하는 작업이다. 이를 통해 이후 `special_gimmick_v2.py`의 수동 Effect 처리부를 실제 호출 경로 기준으로 안전하게 축소할 수 있다.
