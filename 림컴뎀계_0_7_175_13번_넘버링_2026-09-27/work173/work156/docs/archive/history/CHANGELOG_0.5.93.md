# 림컴뎀계 0.5.93 — target-aware reuse execution

## 변경
- 명시적 `coin_target_ids` 다중 대상 공격에서 코인 재사용을 지원.
- 코인 재사용 시 원래 코인의 대상 매핑을 그대로 반복.
- 한 번의 재사용 코인에 대한 공격자 측 상태 소모는 논리 코인 기준 1회, 추가 대상은 중복 소모하지 않음.
- 재사용 코인의 대상별 피해/HP 변화/스킵을 `coin_target_resolution`으로 기록하고 `reuse_index`를 추가.
- `kill_skill_reuse_triggered`가 명시적 대상 슬롯의 처치 여부를 인식하도록 확장.
- 기존 단일 대상 실행기의 동작과 일관되게, 처치 후 새 대상을 임의로 발명하여 재사용 공격을 실행하지 않음.
- 스킬의 `last_coin_reuse_rules`를 명시적 다중 대상 경로에서도 처리.
- 마지막 코인 재사용 역시 하나의 논리 코인으로 취급하여 공격자 측 상태를 대상 수만큼 중복 적용하지 않음.
- 마지막 코인의 명시적 대상 매핑이 비어 있거나 사망 대상만 남은 경우에는 살아 있는 선택 대상 슬롯을 사용.

## 테스트
- 전체 pytest: **198 passed**
- 신규 회귀 테스트: `test_v41_multitarget_reuse.py` 3개
  - coin reuse + 다중 대상 + 공격자 자원 1회/재사용
  - last coin reuse + 명시적 대상 매핑
  - kill skill reuse + 사망 대상 부활/재사용 방지
