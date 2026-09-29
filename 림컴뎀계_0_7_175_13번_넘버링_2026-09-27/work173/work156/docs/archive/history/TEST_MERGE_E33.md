# 테스트 병합 결과 (E33 기준)

## 결과 요약

| | 병합 전 (E33 + 검증 파일) | 병합 후 |
|---|---|---|
| 테스트 파일 | 190개 | **30개** (병합 22 + 단독 8) |
| 테스트 수 | 571개 | **571개** (동일) |
| 전체 실행 | 571 passed / 약 33초 | 571 passed / 약 33초 |
| 빠른 실행 (`--fast`) | - | 563 passed / **약 3초** |

- 실행 시간이 그대로인 이유: 전체 시간의 약 90%가 느린 테스트 8개(각 1초 이상)에서 나온다. 파일 수를 줄인다고 이 시간이 줄지 않는다. 대신 `--fast`로 8개를 뺀 3초짜리 확인 경로를 만들었다.
- 시간 병목 8개: `v94 golden parity`(약 11초, Legacy와 새 Rule 비교라 D단계에서 정리 대상), 출혈 확률 계산 3개(약 7·3·2.5초, 정밀 계산 자체가 오래 걸림), 카탈로그 전체를 도는 4개(각 1.2~1.5초).

## 왜 이전 병합 시도(549/571)와 다른가

이전 시도는 텍스트 이어붙이기라서 helper 이름 충돌(15), 클래스 이름 충돌(4), `@dataclass` 유실(3)로 22개가 실패했다. 이번 병합기(`tools/merge_tests.py`)는 코드를 AST로 분석해서 다음을 지킨다.

- 이름이 충돌하면 **정의와 모든 참조를 함께** `이름__파일태그`로 바꾼다. 함수 안의 같은 이름 지역변수는 건드리지 않는다.
- decorator, 클래스, 함수 본문은 AST 그대로 보존한다. rename이 필요 없는 문장은 원문(주석 포함) 그대로 옮긴다.
- 완전히 똑같은 helper는 1개로 합치고, 다른 helper는 분리한다. 서로 다른 모듈의 같은 이름(`GimmickRegistry`: `special_gimmick_v1` vs `v2` 등)은 import 별칭으로 구분한다.
- 다른 테스트 파일을 import하는 파일, `import *`를 쓰는 파일, `from __future__`를 쓰는 파일은 병합하지 않는다.

## 검증 (전부 통과)

1. 테스트 ID 일대일 대응: 원본 571개 = 병합본 571개, 이름이 바뀐 테스트 0개.
2. 전체 실행: 571 passed. 고정 순서 1회 + **무작위 순서 3회(seed 1·2·3)** 모두 통과. 병렬 실행(xdist)도 통과.
3. **AST 동일성 증명**: 병합본의 함수·클래스 658개를 rename 역변환한 뒤 원본과 비교 → 불일치 0. 테스트 본문이 바뀌지 않았다는 뜻이다.
4. 비-def 최상위 문(상수 등) 17개 전부 보존 확인, 참조 출처 정적 검증(각 코드가 자기 원본 파일의 helper를 참조하는지) 문제 0.
5. 원본 190개 파일 상태도 같은 무작위 순서 3회를 통과 → 병합 때문에 순서 의존이 생긴 것이 아니다.

## 병합 파일 목록

| 병합 파일 | 원본 파일 수 | 테스트 | rename된 이름 | 합쳐진 중복 helper |
|---|---|---|---|---|
| test_boundary_legacy_retirement.py | 9 | 25 | 1 | 0 |
| test_boundary_solver_structure.py | 12 | 27 | 2 | 0 |
| test_architecture_contracts.py | 4 | 12 | 0 | 0 |
| test_buff_debuff_runtime.py | 6 | 14 | 3 | 1 |
| test_status_effect_runtime.py | 5 | 18 | 0 | 2 |
| test_keyword_runtime.py | 3 | 8 | 0 | 0 |
| test_resource_primitives.py | 6 | 29 | 0 | 0 |
| test_resource_runtime.py | 9 | 27 | 3 | 2 |
| test_special_clause_audits.py | 10 | 39 | 4 | 0 |
| test_clash_bleed_probability.py | 7 | 28 | 1 | 0 |
| test_probabilistic_solver.py | 8 | 15 | 3 | 0 |
| test_coin_reuse_forced.py | 5 | 20 | 0 | 0 |
| test_target_selection.py | 13 | 31 | 2 | 0 |
| test_damage_modifiers.py | 13 | 43 | 1 | 0 |
| test_kill_death_stagger_gimmicks.py | 15 | 27 | 6 | 2 |
| test_identity_specific.py | 12 | 31 | 2 | 0 |
| test_affiliation_modules.py | 9 | 32 | 3 | 2 |
| test_support_runtime.py | 3 | 7 | 0 | 0 |
| test_rule_ir_foundation.py | 8 | 24 | 3 | 0 |
| test_rule_migration.py | 9 | 27 | 4 | 1 |
| test_effect_action_runtime.py | 5 | 13 | 2 | 0 |
| test_triggers_actions_queue.py | 11 | 28 | 2 | 0 |

원본 파일과 rename 내역은 `tools/MERGE_MAP.json`, 각 병합 파일의 맨 위 docstring에도 적혀 있다. 원본 파일은 프로젝트에서 제거했다(E33 zip에 그대로 있음).

## 병합하지 않은 단독 파일 8개

- `test_primitive_axis_regression.py` (31개): `from __future__` 사용, 이미 통합된 검증 파일(31개)
- `test_v141_skill_transform_contract.py` (3개): `import *` 사용
- `test_v29_bleed_finalization.py` (3개): test_v29_turn_bleed_state를 import (느린 테스트 포함)
- `test_v29_joint_bleed_damage_trim.py` (1개): test_v29_turn_bleed_state를 import (느린 테스트 포함)
- `test_v29_parallel_accuracy.py` (3개): `import *` 사용
- `test_v29_turn_bleed_state.py` (1개): 다른 파일이 이 파일의 helper를 import함
- `test_v76_damage_modifier_runtime.py` (3개): `import *` 사용
- `test_v94_catalog_rule_golden_parity.py` (1개): 느린 Legacy parity 테스트, D단계에서 제거 예정

## 앞으로 테스트를 추가할 때

- 새 테스트는 위 병합 파일 중 **주제가 맞는 곳에 함수로 추가**한다. helper 이름이 기존과 겹치면 다른 이름을 쓴다(충돌 자체를 피하는 게 가장 안전).
- 테스트 함수 이름은 프로젝트 전체에서 유일하게 짓는다. 1초 넘는 테스트가 생기면 `conftest.py`의 `SLOW_TESTS`에 함수 이름을 추가한다.
- 파일을 새로 만들면 `test_`로 시작해야 한다. 다른 테스트 파일을 import하지 않는다.
- 코드를 고치는 중에는 `python run_tests.py --fast`, 마무리에는 `python run_tests.py`, 구조를 크게 바꿨을 때는 `--shuffle`도 한 번 돌린다.

## 남은 한계

- 병합 파일의 rename된 helper(`이름__vNN`)는 기계적으로 붙인 이름이라 읽기에 덜 예쁘다. 같은 helper가 여러 개로 갈라진 곳(`_ident__v29_stagger` 등)은 나중에 하나로 정리하면 더 줄어든다.
- rename이 필요했던 함수는 원본의 함수 내부 주석이 사라졌을 수 있다(코드 동작은 동일). rename이 없던 함수는 주석까지 원문 그대로다.
- 병렬 실행은 정합성(571 통과)만 확인했다. 이 환경은 CPU가 1개라 속도 향상은 측정하지 못했다.