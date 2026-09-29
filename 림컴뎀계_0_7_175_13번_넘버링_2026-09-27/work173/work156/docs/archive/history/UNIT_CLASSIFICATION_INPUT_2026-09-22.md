# 유닛별 환상체 여부 입력 규칙

## 목적
환상체 여부를 전역 `enemy` 설정 하나로 두지 않고, `enemy.targets[]`의 각 유닛이 독립적으로 선택할 수 있도록 한다.

## 입력
각 대상 유닛에 다음 필드를 사용할 수 있다.

```json
{
  "id": "t1",
  "is_abnormality": true
}
```

- `true`: 해당 유닛을 환상체로 취급
- `false`: 일반 대상(기본값)
- 레거시 별칭 `abnormality`도 입력으로 허용
- `enemy.is_abnormality`를 지정하면 명시적인 `targets[]` 유닛이 값을 생략했을 때 기본값으로 상속

## 의도
이 값은 Target/Unit capability 축이며, 특정 키워드에 하드코딩하지 않는다.
현재 연결된 구현에서는 Sinking이 일반 대상의 SP 경로와 환상체 대상의 별도 경로를 구분할 수 있게 된다. 환상체 대상의 Gloom HP 피해 및 Sinking Deluge의 구체적 Rule은 별도 구현 대상으로 남긴다.

## 예시
```json
{
  "enemy": {
    "is_abnormality": false,
    "targets": [
      {"id": "human_1", "is_abnormality": false},
      {"id": "abnormality_1", "is_abnormality": true}
    ]
  }
}
```

두 유닛은 같은 전투에서 서로 다른 환상체 여부를 가질 수 있다.
