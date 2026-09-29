# 림컴뎀계 0.5.23

## 이번 버전 핵심

### 합 과정의 적 코인 상태를 실제 Clash trace에 포함
기존 별도 `clash_exchange_runtime_v1` 입력뿐 아니라 기본 `DamageEngine.resolve_clash()`가 생성하는 일반 합 결과에도 아래 값이 기록된다.

- `defender_coins_before`
- `defender_coins_rolled`
- `defender_coins_after`
- `bleed_procs`
- `unopposed_after`
- `attacker_coins_before`
- `attacker_coins_after`
- `total_bleed_procs`

따라서 일반적인 코인 대 코인 합에서도 각 합 시점의 적 잔여 코인 수를 추적할 수 있다.

예: 3 vs 3에서 `L,L,W,W,W`라면 적 코인 기준은 `3,3,3,2,1`이고 출혈 발동 횟수 합은 `12`다.

## 중요한 설계
`exchange_count`와 스킬의 명목상 `coin_count`를 동일하다고 가정하지 않는다.

사용자 정의 반복 합에서는 `track_attacker_coins=false`를 사용하여 적 코인 변화만 추적할 수 있고, 일반적인 공격측 코인 소모를 모델링해야 하는 경우 `track_attacker_coins=true`를 사용할 수 있다.

## 검증
- 전체 테스트: 60 passed
- Python 문법 검사: PASS
