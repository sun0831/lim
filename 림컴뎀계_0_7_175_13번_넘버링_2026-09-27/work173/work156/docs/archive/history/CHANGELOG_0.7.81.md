# 0.7.81 — 실제 원문 공격자 대상 오판 수정

## 감사 발견
실제 identity_catalog_v2.json 원문에서 `공격자에게`로 명시된 효과가 기존 passive compiler에서 `SelfTarget`로 컴파일되는 사례를 확인했다.

확인 사례:
- identity-10108 남부 디에치 협회 4과 가라앉는 지식
  - `피격 시 공격자에게 침잠 1 부여`
  - `보호막이 있는 동안 피격 시 침잠 1 추가 부여`
- identity-10215 거미집 약지 제자 아이언메이든 - 가시
  - `수비 스킬을 장착한 아군이 피격 시 공격자에게 출혈 4 부여`
  - `공격자의 출혈 횟수` 관련 후속 효과
- identity-10412 N사 E.G.O:: ... 그건 흐르고 울린다
  - `편성 순서가 가장 빠른 아군 1명이 적에게 피격시, 공격자에게 진동 1 부여`
  - `공격자에게 진동이 있으면, 추가로 진동 횟수 1 증가`

## 수정
- `공격자에게`를 명시한 효과의 대상은 `EventTarget('attacker')`로 보존.
- 기존 `EventTarget('target')` fallback은 명시적 attacker target이 없는 일반 event effect에만 유지.
- compile_one에서 event target에 `target_spec`이 존재하면 이를 실제 target으로 사용하도록 수정.

## 검증
- 공격자 대상 감사: 5개 확인 / 5개 PASS
- 관련 회귀: 111 PASS / 0 FAIL
- 전체 회귀: 887 PASS / 8 FAIL

전체 회귀의 8개 실패는 기존 실패로 분류:
- activation inventory / migration parity 기대값 차이 3건
- 기존 kill/death fixture 1건
- `/tmp/v736/identity_catalog_v2.json` 외부 fixture 의존 4건
