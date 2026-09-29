# 림컴뎀계 0.5.98

0.5.97의 재현 가능한 랜덤 타겟 기능에 **사용자 지정 랜덤 타겟 override**를 추가한 버전.

## 사용 예
```json
{
  "identity_id": "identity-id",
  "skill_id": "skill-id",
  "target_policy": "random",
  "target_override_ids": ["enemy_2"]
}
```

이 경우 스킬의 원래 타겟 정책은 `random`으로 남지만 실제 계산에서는 `enemy_2`를 대상으로 사용한다.

다중 대상이면:
```json
"target_policy": "random",
"target_override_ids": ["enemy_2", "enemy_4"]
```

즉, 게임 데이터상 랜덤 타겟 스킬도 계산기에서는 사용자가 실제 전투에서 발생시킨 타겟을 그대로 지정해 재현할 수 있다.
