# 0.7.0 Engine Conversion — Legacy Trigger Boundary

## Purpose

7번 작업의 우선순위를 **인격 데이터 추가보다 엔진 변환 완료**로 고정한다.
이번 변경은 Production 코드에서 retired `TriggerRuntime` 직접 의존을 제거하고, 공통 Rule Runtime을 유일한 전투 이벤트 실행 경계로 유지하기 위한 것이다.

## Change

- `special_gimmick_v2.py`에서 `TriggerRuntime` 직접 import 제거.
- Legacy 실행기는 `legacy_trigger_compat_v1.py` 한 곳에서만 명시적으로 접근.
- `fire_event()`는 계속 `RuleMigrationRuntime.production_fire()`만 사용.
- `fire_event_compat()`만 호환 경계를 사용한다.
- 기존 Legacy 데이터/테스트 API는 삭제하지 않고 격리한다.

## Validation

- Engine/migration/action/support regression: 39 PASS.
- Legacy boundary regression 포함.
- `compileall` 및 패키지 무결성 검증은 릴리스 시 다시 수행한다.

## Next

엔진 변환의 다음 남은 작업은 직접 Legacy 실행이 아니라 **Legacy 의미를 공통 Runtime으로 표현할 수 없는 잔여 Rule/Effect/Condition을 식별하고 공통 Runtime으로 승격하는 것**이다. 이후 버프/디버프 Runtime을 구현한다.
