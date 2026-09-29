# 림컴뎀계 0.5.91 — 코인별 명시 대상 지정

## 변경 사항
- `coin_target_ids` 추가
  - 코인 순서별로 공격 대상을 직접 지정할 수 있음.
  - 예: `['t1', 't2']` → 1코인 `t1`, 2코인 `t2`.
- `coin_target_indices` 별칭 지원
  - 명시적 적 슬롯의 0-based `index`를 사용해 지정 가능.
- 코인별 대상 지정은 기존 `target_count`/`target_policy`보다 우선하는 명시적 입력으로 처리.
- 명시된 코인 대상이 일반 `target_count` 범위를 벗어나도 해당 대상 슬롯을 자동으로 포함.
- `ActionRequest` 및 생성 액션에도 코인 대상 메타데이터 전달.
- 코인 대상별 실행 로그 `coin_target_resolution` 추가.
- 기존 일반 다중 대상 처리와 하위 호환 유지.

## 테스트
- 전체 pytest: **191 passed**

## 입력 예시
```json
{
  "actions": [
    {
      "identity_id": "identity-id",
      "skill_id": "skill-id",
      "faces": ["H", "H"],
      "coin_target_ids": ["t1", "t2"]
    }
  ],
  "enemy": {
    "targets": [
      {"id": "t1", "hp": 100, "max_hp": 100},
      {"id": "t2", "hp": 100, "max_hp": 100}
    ]
  }
}
```

`coin_target_ids`는 현재 **코인 1개당 대상 1개**를 명시하는 용도다. 한 코인을 여러 대상에게 동시에 적용하는 구조는 별도 규칙으로 분리해 구현한다.
