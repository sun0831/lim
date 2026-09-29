# 0.7.93 — Sinking Deluge 원문 정합성 오판 수정

## 확정 오판

원문 `Sinking Deluge`는:
- Sinking Count × Sinking Potency 만큼 SP 피해
- 대상 SP가 -45 이하가 되면 초과분을 Gloom 계열 HP 피해로 전환
- Non-SP 대상은 전량 Gloom HP 피해
- 이후 Sinking 제거

기존 구현은 일반 SP 대상의 -45 이하 초과분 HP 피해를
`sinking_sp_overflow_to_hp=True`일 때만 적용하도록 만들어져 있었다.
즉 기본 경로에서는 원문에 명시된 초과분 HP 피해가 누락됐다.

## 수정

- 일반 SP 대상도 -45를 초과하는 Deluge 피해를 항상 Gloom HP 피해로 전환
- `sinking_sp_overflow_to_hp` 플래그에 의존하지 않도록 변경
- EventLog의 `overflow_to_hp`는 실제 overflow 발생 여부를 기록
- 기존 abnormality/non-SP 전량 Gloom HP 피해 동작은 유지

## 검증

- `test_keyword_runtime.py`
- `test_status_effect_runtime.py`
- `test_damage_modifiers.py`
- 83 passed / 0 failed
