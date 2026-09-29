# 림컴뎀계 0.5.20

## 이번 버전

이번 버전은 특수자원 작업과 병렬로 **전투 결과의 상태 오염과 Clash 정확도**를 보강했다.

### 1. Clash 승패 방향 수정
- 공격 측 코인이 방어 측 코인을 모두 제거하고 공격 측 코인이 남는 경우 `win`으로 판정.
- 공격 측 코인이 먼저 모두 제거되면 `lose`.
- 양측이 동시에 소진되는 경우 `tie`.
- 기존 반대 방향 판정을 수정.

### 2. Clash의 임시 결과가 스킬 원본을 오염시키지 않도록 수정
- Clash 실행 중 설정되는 `clash_result`는 복사본에만 적용.
- 같은 인격/스킬을 이후 행동이나 분기 계산에서 재사용해도 이전 Clash 결과가 남지 않음.

### 3. Critical / Poise 안전성
- 실제 Coin 실행 시 Poise Count가 0이면 요청된 `crit=true`를 무효화.
- 성공한 Critical은 Poise Count를 1 소비.
- 따라서 MAX 분기에서 첫 Critical 이후 Poise Count가 사라진 상태를 다음 Coin이 잘못 이어받지 않도록 보호.

### 4. 기존 특수자원 기능 유지
- 특수자원 획득/소모/조건부 소모/최대 소모/전부 소모
- 코인 단위 자원 소비
- 임계값 도달 이벤트
- 턴 리셋
- 스킬 변형
- Trigger / ActionQueue 연쇄

## 검증

- `python run_tests.py`
- **46 passed**
- Python compile PASS
