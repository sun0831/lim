# 0.7.80 — 실제 원문 조건 범위/필드 오판 수정

## 목적
구현 추가가 아니라 실제 인격/스킬 원문과 기존 `parse_conditions()` 해석을 직접 대조해 조건이 누락되거나 다른 대상/필드로 해석되는 사례를 수정.

## 확인된 오판
- `메인 타겟의 침잠 횟수가 6 이상이면` → 기존 `Always()` → `StatusThreshold(Sinking, count, enemy)`
- `자신의 진동 횟수가 5 이상이면` → 기존 `Always()` → `StatusThreshold(Tremor, count, self)`
- `자신의 호흡이 N 이상` → 기존 `Always()` → `PoiseAtLeast(N, potency)`
- `자신의 호흡 횟수가 N 이상` → `PoiseAtLeast(N, count)`
- `자신의 충전 횟수가 N 이상` → `ChargeAtLeast(N)` 명시 보존
- `대상의 출혈이 N 이상`에서 기존 generic fallback이 중복 조건을 만들던 문제 제거. `출혈`은 potency, `출혈 횟수`는 count.

## 실제 원문 범위
- 메인 타겟 상태 횟수 조건: catalog 대조 중 4개 패턴 항목
- 자기 상태 횟수 조건: 14개
- 자기 호흡 임계값 조건: 39개

## 추가 확인
- `메인 타겟의 (진동 위력 + 진동 횟수)가 N 이상` 2건도 기존 `Always()` 잔존을 확인하여 `TremorSumThreshold`로 통합.

## 검증
- 신규 감사 테스트 + 기존 관련 테스트: 117 PASS / 0 FAIL
- affected-pattern 재스캔: 해당 패턴의 `Always()` 잔존 0건
