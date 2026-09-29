# 림컴뎀계 0.5.54

## 다중 대상 집계 방식

개별 적을 별도 전투 상태로 시뮬레이션하지 않고 사용자가 `target_count`(또는 `attack_target_count`)로 공격 대상 수를 직접 입력한다.

- `target_count=1`: 기존과 동일
- `target_count=2`: 메인 대상 1명 + 별도 대상 1명
- `target_count=N`: 메인 대상 1명 + 별도 대상 N-1명

기존 `turn_damage`/`damage_by_identity`/`damage_by_skill`은 하위 호환을 위해 **메인 대상 피해량**을 유지한다.

추가 출력:
- `main_target_damage`
- `additional_target_damage`
- `total_damage_all_targets`
- `main_target_damage_by_identity`
- `additional_target_damage_by_identity`
- `total_damage_all_targets_by_identity`
- 동일한 expected 계열 출력
- 액션별 `main_target_damage`, `additional_target_damage`, `total_damage_all_targets`

현재 추가 대상은 별도의 HP/Stagger 상태를 만들지 않는다. 따라서 대상별 처치/대상 선택/무작위 대상 분배는 아직 별도 기믹이며, 특수 콘텐츠(예: 죄종전) 규칙은 의도적으로 넣지 않았다.
