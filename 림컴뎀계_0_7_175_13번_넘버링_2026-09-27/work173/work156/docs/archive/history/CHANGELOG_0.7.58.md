# 0.7.58 — 상태 횟수 기반 아군 Target Selector 정합화

## 반영
- `highest_status_count:<status>` / `lowest_status_count:<status>` Target Selector를 추가.
- `highest_tremor_count` / `lowest_tremor_count` canonical alias를 추가.
- `AllySelectorTarget`도 동일한 상태 횟수 기준을 사용할 수 있도록 정합화.
- 실제 `identity_catalog_v2.json`의 `identity-11105` / 어금니 사무소 해결사 / `윽박과 응원`에서 확인된
  `진동 횟수가 가장 높은 아군 1명` 패턴을 기준으로 범용 상태 횟수 Selector 경계를 확장.
- `passive_compiler_v29.py`의 아군 대상 선택 분기에 진동 횟수 최고/최저 정책을 연결.
- 상태 이름은 대소문자 차이로 누락되지 않도록 Selector 조회 시 case-insensitive fallback을 사용.

## 범위
- 1턴 계산기에서 실제 대상 선택에 필요한 상태 횟수 비교만 다룸.
- 상태 횟수와 상태 위력(potency)을 별도 축으로 유지.
- 상태 횟수가 높다는 이유만으로 해당 상태를 생성/증가시키는 효과를 자동 실행하지 않음.
- `identity-11105`의 전체 Support Passive 실행 자체를 새로 추측 구현하지 않음. 이번 작업은 반복 가능한 Target Selector 경계만 공통화함.

## 검증
- `test_target_selection.py`: 34 passed
- `test_identity_specific.py` + `test_triggers_actions_queue.py` 포함 관련 회귀: 101 passed / 0 failed
