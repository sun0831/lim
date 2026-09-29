# 0.5.97 — Random Target Resolution

## 변경
- `target_selector_v1.py`
  - `random` 타겟 정책을 실제 대상 선택으로 구현.
  - `random_seed` 사용 시 재현 가능한 무작위 선택.
  - 다중 무작위 타겟은 중복 없이 샘플링.
  - 생존 대상이 있으면 사망 대상은 무작위 후보에서 제외.
  - 모든 대상이 사망한 경우에만 기존 슬롯을 fallback으로 사용.
- `one_turn_solver_v29.py`
  - `random_seed` / `target_random_seed` 지원.
  - RNG 객체를 BattleState에 저장하지 않고 seed + draw counter로 관리하여 deepcopy/probabilistic 경로와 충돌하지 않음.
  - 같은 실행 내 연속 무작위 타겟 행동은 서로 다른 draw를 사용.
- `test_v45_random_target_selection.py`
  - 재현성 / 다중 선택 / 사망 타겟 제외 검증 추가.

## 검증
- 전체 pytest: **212 passed**
- 인격: **184**
- 스킬: **621**
- 스킬 clause audit: **2,309 supported / 1,729 unsupported / 57.18%**
- 특수기믹 passive gap audit: **360**

## 범위
이번 버전은 `random` **타겟 선택 엔진**을 구현한다. 카탈로그의 모든 `무작위` 문장을 자동으로 실행 가능한 기믹으로 번역한 것은 아니다. 조건·대상·발동 시점이 모호한 원문은 기존 보수적 파서 정책에 따라 미지원으로 남긴다.
