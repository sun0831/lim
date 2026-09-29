# 0.7.90 — 실제 원문 공명/전투종료 조건 오판 수정

## 감사에서 확정된 오판

### 1. identity-11015 `정검[整劍]` — 전투 종료 조건의 trigger/condition 손실
실제 원문:
- `전투 종료시 자신의 호흡 위력이 20 이상이면, 자신의 호흡 횟수 1 증가`

기존 컴파일:
- `BeforeAttack`
- `Always`
- `AddPoise(count=1)`

즉 전투 종료 시점과 `호흡 위력 >= 20` 조건이 모두 손실되어 있었다.

수정:
- Trigger → `COMBAT_END`
- Condition → self Poise potency >= 20
- Effect → self Poise count +1

### 2. identity-11015 `정검[整劍]` — 공명 산식/소수점 버림 오판
실제 원문:
- `(오만 공명 수 / 2) +1만큼 호흡 얻음 (최대 4. 소수점 버림)`

정확한 의미:
- `floor(오만 공명 수 / 2) + 1`
- 최대 4

기존 generic resonance suffix 처리로는 괄호 내부 연산과 바깥 `+1`의 순서를 보존하지 못할 수 있었고, 명시적 `소수점 버림`/cap도 해당 문장에 대해 안전하게 보존되지 않았다.

수정:
- source-backed floor/cap expression 추가
- `Clamp(Floor(resonance / 2) + 1, 0, 4)` 구조로 보존

## 회귀
- 신규/관련 audit suite: **67 PASS / 0 FAIL**
- 전체 pytest는 별도 완료 전이며, 전체 회귀 수치는 이 버전에서 주장하지 않는다.

## 범위
이번 버전은 기능 추가보다 **실제 identity 원문 → compiler 해석의 오판**을 바로잡는 정합성 감사 수정이다.
