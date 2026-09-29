# 림컴뎀계 0.5.35

## 이번 버전
- 확률 분기 내부 `after_coin -> queue_action`을 즉시 실행하도록 연결
- 생성된 추가 공격의 피해를 원본 행동이 아닌 **실제 생성된 인격/스킬**에 귀속
- 추가 공격이 다시 생성한 하위 공격도 동일한 귀속 맵에서 누적
- `generated_damage`를 확률 branch trace에 기록
- 기존 코인 단위 상태 전파, Trigger 연쇄, HP/Stagger/SP/자원/출혈 전파 유지

## 검증
- 전체 테스트: 81 passed
- Python 문법 검사: 통과
