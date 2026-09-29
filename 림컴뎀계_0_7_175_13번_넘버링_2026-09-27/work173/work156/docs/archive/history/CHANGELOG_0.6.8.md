# 림컴뎀계 0.6.8

## Analyzer Trace 강화

- Action `state_diff`를 단순 HP/SP/충전/탄환 변화에서 확장.
- 적 Stagger 상태/단계/인덱스 변화 추적.
- 적 상태이상 Potency/Count 변경 추적.
- 인격 Poise 변화 추적.
- 인격 특수자원 추가/소모/변경을 before/after 형태로 추적.
- 인격 상태이상 추가/삭제/변경을 before/after 형태로 추적.
- 기존 결과 필드와 호환 유지.

## 검증

- 전체 pytest: 250 passed.
- 신규 Architecture state-diff 계약 테스트 추가.
