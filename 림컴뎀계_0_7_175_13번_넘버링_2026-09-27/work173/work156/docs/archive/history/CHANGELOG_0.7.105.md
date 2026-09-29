# 0.7.105 — Unrelenting Spirit 속도 조건 / 진동 적용 오판 수정

## 원문 기준
`Unrelenting Spirit -剛氣-`:
- 자신/공격자의 속도가 대상보다 3 이상 빠를 때 속도 차이 × 2.5% 피해량 증가, 최대 20%
- 자신의 Skills로 진동 위력 +1, 진동 횟수 +1

원문: `림버스컴퍼니 버프,디버프 원본.txt`

## 확인된 문제
기존 compiler는 `자신의 속도가 대상보다 3 이상 빠를 때` 형태의 조건을 명시적으로 인식하지 못해 해당 조건이 `Always`로 남을 수 있었다.
또한 `자신의 스킬에/로 진동 위력·횟수 추가`처럼 스킬 전체에 적용되는 문구는 기존의 `이 스킬에서 부여하는 ...` 전용 parser에 포함되지 않았다.

## 수정
- `자신의 속도가 대상보다 N 이상 빠를 때` → `SpeedRelation('faster') + SpeedDifferenceAtLeast(N)`
- 유닛의 스킬 전체에 적용되는 진동 위력/횟수 보너스 → 기존 event-scoped Tremor application context 재사용
- 단일 potency만 증가하는 변형과 potency+count 변형을 분리
- 기존 speed difference scaling과 일반 skill-scoped Tremor modifier 의미는 변경하지 않음

## 테스트
- Unrelenting Spirit targeted tests: 4 passed
- Tremor application modifier tests: 2 passed
- Damage modifier tests: 46 passed
- 합계: **52 passed**

## 판정
`MISMATCH` → 수정 완료

## 범위
이번 변경은 원문에 명시된 속도 관계 조건과 Skill 기반 Tremor 적용 보너스의 해석 정합성 수정이다. Overheat 등 별도 미구현 기믹은 이번 변경에 포함하지 않는다.
