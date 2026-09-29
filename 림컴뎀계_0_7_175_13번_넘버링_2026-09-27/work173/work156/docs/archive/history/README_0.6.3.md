# 림컴뎀계 0.6.3

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
