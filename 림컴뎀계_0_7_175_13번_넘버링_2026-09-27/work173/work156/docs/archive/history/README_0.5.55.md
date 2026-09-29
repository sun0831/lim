# 림컴뎀계 v0.5.55

## 이번 버전
- 처치 후 스킬 1회 재사용을 ActionQueue 기반으로 연결.
- 재사용 스킬은 원래 요청 순서를 변경하지 않고 처치 직후 생성 행동으로 실행.
- 재사용 행동은 `suppress_kill_reuse`로 표시하여 재귀적인 처치→재사용 루프를 차단.
- 현재 계산기의 대상 모델이 개별 적 객체가 아닌 사용자가 입력한 `target_count` 기반 집계 모델이므로, 처치 후 재사용은 `target_count > 1`일 때 다음 대상 슬롯을 대상으로 실행.
- 다음 대상은 현재 입력한 적의 초기 HP/기본 흐트러짐 상태를 기준으로 새 대상 슬롯으로 복원하여 계산.
- `target_count = 1`에서는 처치 후 재사용을 추가 실행하지 않음.
- `target_count`를 별도 입력하지 않은 행동도 전역 `target_count`를 기본값으로 사용.
- 기존 재사용/추가공격/Trigger 흐름과 호환.

## 검증
- `python run_tests.py`: 116 passed
- Python syntax check: PASS
- ZIP integrity: PASS
