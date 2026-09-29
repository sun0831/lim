# E37 — 공격 레벨/방어 레벨/치명타 실측 반영

기준: 2026-09-22 KST

## 반영 내용

### 1. 공격 레벨 기준
피해 계산의 공격 레벨은 대상/인격의 단순 unit level을 별도로 참조하지 않고, 현재 전투 actor의 유효 공격 레벨을 사용한다.

`fighter.level + identity.offense_level + skill.offense_level_bonus + 전투 중 공격 레벨 보정`

### 2. 공격/방어 레벨 보정 정밀도
실측 Golden에 맞춰 다음 값을 피해 Static Modifier에 넣기 전에 **소수점 둘째 자리에서 버림(0 방향 절삭)**한다.

`diff / (abs(diff) + 25)`

예:
- Attack 60 / Defense 47 → 13/38 = 0.342105... → **0.34**
- Attack 60 / Defense 37 → 23/48 = 0.479166... → **0.47**

### 3. 치명타 처리
기본 치명타 +20%는 Static Modifier에 유지한다.

추가 `Crit Damage`는 기본 치명타와 분리해 Dynamic Modifier로 적용한다.

즉 구조는:

`Coin × (1 + Static[내성 + 공방레벨 + 기본 치명타 + ...]) × (1 + Dynamic[추가 치명타 피해 + 기타 동적 피해])`

## 실측 Golden

소지제자 싱클레어 S2, 공격 레벨 60, 코인값 19, 치명타, 오만 내성 0.75.

| 방어 레벨 | 실측 부위 피해 | 합계 | 엔진 Golden |
|---:|---|---:|---:|
| 47 | 14 + 15 | 29 | 29 |
| 37 | 16 + 16 | 32 | 32 |

각각 내부 계산:

### Defense 47

`19 × (1 - 0.125 + 0.34 + 0.20) × (1 + 0.10)`

`= 19 × 1.415 × 1.10`

`= 29.5735 → 29`

### Defense 37

`19 × (1 - 0.125 + 0.47 + 0.20) × (1 + 0.10)`

`= 19 × 1.545 × 1.10`

`= 32.2905 → 32`

## 테스트

추가:
- `test_e37_sinclair_defense_level_golden.py` — 2 Golden
- `test_triggers_actions_queue.py` — 공방 레벨 보정 정밀도 회귀 1건

실행 결과:
- 관련 회귀 + Golden: **79 passed**
- 전체 pytest 수집: **676 tests**
- 전체 회귀는 기존 catalog Golden parity 계열의 장시간 실행으로 제한시간 내 완료되지 않음. 따라서 전체 676개 PASS라고 주장하지 않는다.
