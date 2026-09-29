# 림컴뎀계 0.6.4

## 0.6.4 추가 구현
- 중지 작은 형님 `앙갚음 장부`의 피격/아군 사망 자원 트리거를 실제 런타임에 연결.
- 공격자 `복수 대상` 상태와 `앙갚음 장부 [히스클리프]`를 이벤트 로그로 추적.
- 동일 피격 스킬당 1회 제한을 trigger runtime의 `per_skill` scope로 처리.



0.6.2 기반 패치.

## 잔영 직접 입력
1턴 계산 시 사용자가 초기 잔영을 직접 지정할 수 있다.

```json
{
  "enemy": {
    "hp": 1000,
    "max_hp": 1000,
    "afterimage_count": 2
  }
}
```

다중 적에서는 각 `enemy.targets[]` 항목에 `afterimage_count`를 지정할 수 있다.
기존 `enemy.statuses.잔영.count` 형식도 유지된다.
