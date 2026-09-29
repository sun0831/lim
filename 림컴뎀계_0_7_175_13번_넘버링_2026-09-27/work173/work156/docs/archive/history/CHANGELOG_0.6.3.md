# 림컴뎀계 0.6.3

## 변경
- 잔영 초기 보유량을 사용자 입력으로 지정할 수 있도록 추가.
- `enemy.afterimage_count` / `enemy.afterimages` 지원.
- 기존 `enemy.statuses.잔영.count` 직접 입력과 병행 가능.
- 다중 적 사용 시 `enemy.targets[].afterimage_count`로 대상별 잔영 입력 가능.
- 입력된 잔영은 자동 추론하지 않고 초기 상태로 그대로 반영하며 이후 런타임이 상태를 추적한다.
- 잔영 입력 회귀 테스트 추가.
