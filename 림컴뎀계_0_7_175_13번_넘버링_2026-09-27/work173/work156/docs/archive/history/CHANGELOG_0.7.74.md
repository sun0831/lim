# 0.7.74 — 실제 원문 오판 감사: Target Selector 동률 처리 정합화

## 감사에서 확인한 실제 오판
기존 `AllySelectorTarget`은 순위값이 같은 경우 일부 selector에서 `identity_id` 문자열을 2차 정렬키로 사용했다.

예:
- `speed_max/min`
- `hp_*`
- `charge_*`
- `ammo_*`
- `sp_*`
- Poise potency/count selector
- status-count / composite selector 일부

이 방식은 같은 순위값을 가진 아군이 있을 때 편성 순서와 무관하게 ID 문자열 순서로 대상이 바뀔 수 있다.

프로젝트의 기존 Target Selector 계약은 아군 후보의 기존 순서를 deterministic tie-break로 유지하도록 되어 있으며, 0.7.55에서도 이 의미를 명시했다.

## 수정
`passive_runtime_v29_base.py`의 랭크 selector 정렬을 다음 방식으로 통일했다.

1. 후보의 편성/기존 순서를 먼저 고정
2. 순위값으로 stable sort
3. 동률이면 기존 순서 유지

따라서 `max` selector에서도 동률 시 뒤쪽 편성이 선택되는 역전이 발생하지 않는다.

## 검증
- 신규 오판 회귀: `test_ow_0_7_74_semantic_mismatch.py` — 2 PASS
- Target/Identity/Trigger 관련: 113 PASS / 0 FAIL
- 전체 회귀: **871 PASS / 8 FAIL**
- 전체 회귀의 8개 실패는 기존 감사 환경의 activation inventory 기대값 차이 및 `/tmp/v736` 외부 fixture 의존 등 이번 변경과 무관한 기존 실패다.

## 범위
이번 작업은 새 기믹을 추가한 것이 아니라, **이미 구현되어 있던 대상 선택 기믹이 동률 상황에서 실제 계산 의도와 다르게 해석될 수 있는 부분을 수정**한 것이다.
