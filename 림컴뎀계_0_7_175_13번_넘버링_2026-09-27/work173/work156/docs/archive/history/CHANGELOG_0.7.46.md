# 0.7.46

## 공통 코인 실행 호환성 보정
- `coin_execution_core_v1.py`의 `is_added_coin` 전달을 레거시/테스트용 `simulate_coin` 시그니처와 호환되도록 보정.
- Production `DamageEngine.simulate_coin()`에는 기존대로 `is_added_coin`을 전달.
- 구형 mock/legacy engine에는 해당 인자를 전달하지 않아 기존 coin-trigger 테스트가 깨지지 않도록 처리.
- 0.7.45에서 `ally_new_stagger_assist`를 공통 Runtime으로 승격한 현재 카탈로그 기준 trigger rule 수 67개를 구조 테스트에 반영.
