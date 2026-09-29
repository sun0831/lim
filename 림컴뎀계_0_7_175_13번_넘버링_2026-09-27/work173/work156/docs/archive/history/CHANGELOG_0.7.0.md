# 림컴뎀계 0.7.0 — 7번 작업 시작

## 버전 승격
- 프로젝트 기준 버전을 0.6.60에서 0.7.0으로 승격.
- 0.6.x의 기존 changelog/architecture 문서는 역사 기록으로 보존.

## 0.6.60 → 0.7.0 기준에 포함된 변경
- 확률(출혈) 분기에서 `TriggerRuntime` 직접 실행 경로 제거.
- `probabilistic_trigger_runtime_v1.py` 기반 확률 Runtime 경계 도입.
- Legacy boundary 회귀 테스트 추가.
- 0.6.60 작업본의 392 PASS 기록은 역사적 기준으로만 보존하며, 현재 0.7.0 테스트 결과와 혼동하지 않는다.

## 다음 작업
- 남은 Production Legacy boundary 전수 조사
- 테스트베드 중복/구형 테스트 정리
- 공통 Runtime 통합
- Action / Trigger / Support 안정화
- 출혈 / 파불코 확률 Runtime 심화

### 7번 후속 — Legacy Trigger 데이터 모델 경계 분리
- `trigger_rule_model_v1.py`를 추가해 `TriggerCondition` / `TriggerEffect` / `TriggerRule` 선언 모델을 Legacy 실행기(`trigger_runtime_v1.py`)에서 분리.
- `one_turn_solver_v29.py`는 TriggerRuntime이 아니라 공통 선언 모델을 직접 참조.
- `special_gimmick_v2.py`의 Legacy TriggerRuntime 참조는 명시적인 compatibility 경로에서만 지연 로드.
- Production Rule IR 경계 자체는 유지하며 Legacy 실행기가 일반 전투 이벤트 경로로 다시 들어오지 않도록 회귀 테스트 추가.
- 경계/마이그레이션 관련 targeted tests: 30 PASS.

## Engine Conversion Follow-up

- Continued Production-to-Common-Runtime conversion.
- Kept `TriggerRuntime` behind `legacy_trigger_compat_v1` as an explicit compatibility boundary only.
- Removed dead code from `RuleRuntime.execute_trigger_rules()`.
- Corrected `RuleMigrationRuntime.execute_generic()` to use the canonical generic-effect predicate.
- Updated Legacy boundary regression coverage to assert lazy compatibility rather than direct Production construction.
- Verification: 24 targeted engine-boundary tests PASS; compileall PASS.

## Engine conversion continuation
- Moved migrated TriggerRule execution ownership into `RuleRuntime.execute_legacy_rules()`.
- Reduced duplicated Condition/Target/Effect execution logic in `RuleMigrationRuntime`.
- Kept Legacy `TriggerRuntime` compatibility-only.
- Related engine/migration regression: 51 PASS.

## Engine Conversion Audit — 2026-09-20
- Audited the current 184-identity catalog against the Common Rule IR/Runtime boundary.
- Compiled trigger-rule set: 55 rules; 55/55 are migration-safe and executable through the common runtime; 0 deferred, 0 unknown.
- Added `test_v111_engine_conversion_audit.py` to lock this boundary and prevent direct Production construction/import of the retired `TriggerRuntime`.
- Identity data was not expanded or rewritten; the audit treats it as input to validate the engine boundary.

## Engine Conversion Follow-up — v92 / v89 / v60-v61 audit correction (2026-09-20)
- Re-verified `one_turn_solver_v29._fire_probabilistic_trigger_event()` callers: the live probability path constructs and passes `ProbabilisticTriggerRuntime`; the `TriggerRuntime`-shaped compatibility branch is not used by the current production call sites.
- Updated v92 coverage to exercise `ProbabilisticTriggerRuntime` directly, including `per_skill` activation-bucket persistence across repeated events and skill changes.
- Kept the defensive legacy-shaped branch instead of deleting it blindly; it remains an isolated compatibility/unit boundary until the remaining callers are retired.
- Moved v60/v61 once-per-turn assertions onto production `GimmickRegistry.after_*` event handlers instead of `trigger_runtime.fire()` compatibility calls.
- Added production Rule IR turn-reset propagation through `RuleMigrationRuntime.reset_turn()` → `RuleRuntime.reset_turn()` so migrated activation budgets reset at turn boundaries.
- Corrected migrated `poise_gain` execution so the common `EffectExecutor` actually applies the Poise mutation instead of routing it through the generic status fallback.
- Target-resolution failure now emits `migration_target_unresolved=True` plus `migration_target_reason` and an event-log trace when state logging is available; activation is not consumed.
- Full regression after these corrections: **408 / 408 PASS**.

## 2026-09-20 — Activation Ledger conversion (A)

- Added `ActivationLedger` as the production single owner of turn-scoped activation counts and scope buckets.
- Attached the ledger to `BattleState` so deterministic and probabilistic branches deepcopy activation state together with TurnState.
- Bound common `ActivationRuntime`, `RuleRuntime`, and `ProbabilisticTriggerRuntime` to the TurnState ledger.
- Converted probabilistic branch state signatures/restoration to use the ledger as the authoritative activation state.
- Retained legacy activation fields only as compatibility mirrors at the migration boundary.
- Added three focused ledger ownership/branch-isolation tests in `test_v112_activation_ledger.py`.
- Regression: **411/411 PASS**.

## 2026-09-20 — Coin Execution Core conversion (B)
- Added `CoinExecutionCore` / `CoinExecutionContext` as the shared coin-by-coin lifecycle boundary.
- Converted the deterministic unopposed coin path and probabilistic generated-action path to use the same lifecycle core.
- Clash/outcome branching remains outside the core; only coin execution, post-coin trigger timing, coin reuse, and after-skill lifecycle are shared.
- Preserved branch-local state, trigger chains, generated-action attribution, and existing private-method compatibility while removing the duplicated coin-loop implementation.
- Added `test_v113_coin_execution_core.py` to verify shared-core ownership and lifecycle behavior.

## C Phase — solver module split
- Extracted `SkillTextParserV19`/`ParseReport` to `skill_text_parser_v19.py`.
- Extracted `IdentityCatalogV29` to `identity_catalog_v29.py`.
- Preserved imports from `one_turn_solver_v29.py` for compatibility.
- Added `test_v114_solver_module_split.py`.
- Validation: 416/416 tests passed.

## C-3 — TurnExecutionContext (2026-09-20)
- Extracted one-turn preparation/configuration into `OneTurnSolverV29._prepare_turn_context()`.
- Added `TurnExecutionContext` to carry state, resource runtime, resonance plan, passives, gimmicks, action queue, and damage accumulators across execution phases.
- Kept the action execution loop and finalization behavior unchanged.
- Added `test_v113_turn_execution_context.py` to lock the preparation boundary and public result contract.
- Full regression: 420/420 PASS.

### D-2 — Rule IR activation metadata preservation
- Preserve Rule metadata through `TriggerRule -> RuleIR` conversion.
- Enforce `turn_cap` in the common ActivationRuntime for scoped activations.
- Normalize received-target context for per-target activation buckets.
- Full regression: 430/430 PASS.

E-2 Buff/Debuff → Damage Runtime integration
- DamageModifierRuntime resolves actor/enemy BuffDebuffRuntime modifiers.
- skill_power / coin_power / attack_level_bonus / defense_level_bonus supported.
- vulnerability and damage_taken_up feed damage_percent.
- fast path avoids scanning B/D store when absent.
- New integration tests: test_v118_buff_debuff_damage_integration.py
- Full suite: 434 passed.

## E-9
- Rule IR -> ConditionRuntime -> EffectExecutor -> BuffDebuffRuntime -> DamageModifierRuntime end-to-end path locked by test_v124_rule_buff_damage_e2e.py.
- buff/debuff effect commands now preserve lifecycle, rule_expiry, and value_semantics metadata into BuffDebuffRuntime.
- Full suite: 449 passed.

E-13 note: introduced keyword_runtime_v1 as common seven-keyword lifecycle core; identity-specific variants remain deferred.

- E-15: Poise/Critical/Charge keyword lifecycle unified under `KeywordRuntime`; removed duplicate Poise Turn End consumption and preserved Charge-equivalent resources such as Bio Material from generic Charge decay.
