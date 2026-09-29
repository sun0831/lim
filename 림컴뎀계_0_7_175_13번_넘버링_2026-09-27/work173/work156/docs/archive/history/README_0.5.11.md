# 림컴뎀계 0.5.11

## 이번 버전
- 범용 `ResourceRuntime` 추가.
- 특수자원을 `set / gain-loss / clamp / threshold` 공통 lifecycle로 처리.
- 시나리오에서 `resource_specs`로 자원 최소/최대값과 스킬 변형 임계값을 명시할 수 있음.
- 초기/preheat 값은 계속 사용자 입력이며 과거 턴의 준비 과정을 추론하지 않음.
- 중간 행동으로 자원이 증가한 뒤 다음 사용자 행동을 Resolve할 때 최신 자원값을 사용.
- 기존 SP/충전/탄환/호흡과 별개인 인격 고유 자원을 generic `resources`로 유지.
- 기존 `apply_effect`의 잘못된 resource-condition 반환 분기 제거.
- 특수자원 Runtime 테스트 2개 추가.

## 테스트
- Python compile 검사: PASS
- pytest: **20 passed**
- 통합 실행: `python run_tests.py`
