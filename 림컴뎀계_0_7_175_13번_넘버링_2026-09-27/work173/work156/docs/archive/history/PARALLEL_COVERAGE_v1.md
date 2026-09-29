# 병렬 개선 커버리지 v1

|항목|수|
|---|---:|
|identities|184|
|skills|621|
|skills_with_resource_gain|5|
|skills_with_resource_cost|15|
|skills_with_conditional_resource|3|
|skills_with_conditional_max|4|
|skills_with_consumption_damage|4|
|skills_with_transform_text|27|
|skills_with_resource_coin_cost|14|

## 이번 버전의 의미

- 조건부 특수자원 최대 소모를 무조건 소모가 아니라 조건을 만족할 때만 실행하도록 분리했다.
- 실제 소모량 기반 피해량 증가를 현재 행동의 동적 피해 보정으로 연결했다.
- 트리거 소유자와 공격 실행자가 다른 경우 자원 획득 대상을 소유자 기준으로 처리한다.
- 결과에 인격별뿐 아니라 `identity_id:skill_id` 기준 스킬별 피해량과 행동 시작/종료 상태를 노출한다.
