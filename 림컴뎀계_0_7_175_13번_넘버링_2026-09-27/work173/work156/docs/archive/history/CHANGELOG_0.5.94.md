# 림컴뎀계 0.5.94 — triggered target inheritance

## 변경
- 원호/강제공격/후속공격 등 생성 액션이 소스 액션의 명시적 `target_policy`, `target_index`, `target_ids`, `coin_target_ids`를 보존하도록 수정.
- 기존 기믹이 내부적으로 사용하는 `target_policy='main'`은 소스 액션에 명시적 대상 지정이 있을 때 기본값으로 취급.
- 기믹 자체가 다른 target policy/index/ids를 명시한 경우에는 그 지정이 우선.
- 따라서 다중 대상 공격에서 발생한 후속 공격이 마지막으로 처리된 적을 무조건 다시 때리는 문제를 방지.
- 공격자 측 효과의 다중 대상 중복 처리는 0.5.92 구조를 유지.

## 검증
- 전체 pytest: **200 passed**
- 신규 회귀 테스트: `test_v39_trigger_target_inheritance.py`
