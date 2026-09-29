# 림컴뎀계 0.6.42 — 개발용 집중 테스트 계층 추가

## 이번 작업
0.6.41의 계층형 테스트 실행을 한 단계 더 좁혀, 현재 최적화 작업처럼 특정 Runtime만 수정하는 사이클에서 불필요한 테스트를 실행하지 않도록 집중 Suite를 추가했다.

### 집중 Suite
- `migration`: Rule IR / migration / parity / effect executor / architecture 관련 테스트
- `combat_core`: DamageModifier / Target / Condition / Activation 관련 테스트
- `affiliation`: affiliation / support / blade 관련 테스트
- `bleed`: bleed / probability 관련 테스트

기존 `smoke`, `runtime`, `integration`, `all`은 유지한다.

## 원칙
- 테스트 삭제/병합은 하지 않는다.
- 집중 Suite는 개발 중 빠른 피드백용이다.
- `all`은 릴리즈 전 반드시 실행한다.
- 실제 중복 테스트 병합은 공통 Runtime 이관과 Golden/Integration 검증 이후 수행한다.
