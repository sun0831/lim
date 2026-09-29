# 림컴뎀계 0.5.65

## 이번 버전
- Generated/Triggered Action에 target selection metadata를 전달하도록 연결.
- `main`/`primary` 대상 정책 정규화.
- 단일 aggregate enemy에서도 target selector가 사용할 수 있도록 main target record를 runtime에서 제공.
- `highest_status:<상태명>` target policy 추가.
- `자신의 공격 스킬 종료시 ... 꽃잎 30 이상 ... 잔향이 가장 높은 대상에게 '황홀한 종말'` 패턴을 보수적으로 컴파일.
- `아군이 적에게 기본 공격 스킬 종료 시 적(본체) 체력 20% 이하 ... 대상에게 '메르체'` 패턴을 보수적으로 컴파일.
- Enemy HP percentage trigger는 `after_skill` context에서 현재 HP/max HP를 사용.
- Self forced-skill resource trigger가 조사/주격 조사(`이/가/은/는`)를 포함한 리소스명도 정상 인식하도록 보정.

## 검증
- pytest: 130 passed
- 대상 선택 테스트: speed/HP/formation/highest-status
- forced follow-up target-policy 전달 회귀 테스트 포함
