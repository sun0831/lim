# 림컴뎀계 0.5.43

## 일반 전투/Clash 상태 전파 보강

0.5.42의 출혈 계산을 유지하면서, 확률형 Clash가 일반 전투 실행과 더 가까워지도록 branch-local 상태 처리를 보강했다.

- 확률형 Clash의 `Clash Win` / `Clash Lose` 스킬 효과를 결과 branch에 즉시 적용.
- 해당 인격의 구조화된 `Clash Win` / `Clash Lose` 패시브 효과도 branch에 즉시 적용.
- 위 효과로 바뀐 SP/자원/상태/플래그가 다음 Clash 확률 계산에 반영된다.
- 생성(원호/추가) 공격도 일반 스킬과 동일하게 가능한 범위에서:
  - SP 비용/획득
  - 자원 비용/획득
  - 사용 전/사용 시 효과
  - 코인별 효과
  - 공격 종료 전후의 상태
  를 branch-local 상태에 반영한다.
- `final_ammo_coin` 계열 Trigger가 실제 `ammo_before / ammo_after / ammo_spent` 값을 보도록 수정.
- 생성 공격의 탄환 상태도 같은 방식으로 Trigger에 전달한다.
- 기존 Bleed 5%/5% 턴 최종 절삭, Draw 규칙, 99 Clash 규칙은 유지한다.

## 검증

- Python 문법 검사 통과
- 통합 테스트: **95 passed**

## 0.5.44
- Unified normal Clash draw handling: a draw keeps both active coins for the next exchange.
- Added the same 99-exchange hard cap to the deterministic Clash resolver; the 99th exchange is forced to defender win.
- Corrected probabilistic `after_clash` context so `clash_coin_removed` is true only for attacker loss.
- Added regression coverage for repeated draws and the 99th-exchange rule.
