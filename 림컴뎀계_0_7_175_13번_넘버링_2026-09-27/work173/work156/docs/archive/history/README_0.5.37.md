# 림컴뎀계 0.5.37

## 이번 버전
### 확률형 Clash의 terminal branch 상태 혼합 처리 보정
- 동일한 compact terminal Clash 결과에 여러 branch-local 상태가 합쳐질 수 있는 구조를 보정
- 기존에는 해당 terminal key에서 첫 번째 full state만 사용했지만, 이제 **모든 terminal state 후보를 확률 가중으로 처리**
- `after_clash` Trigger가 서로 다른 상태를 만든 경우에도 각 상태가 이후 unopposed 공격 / `after_skill` / 추가 공격에 독립적으로 반영
- 상태 후보별 HP, Stagger, SP, 자원, 상태, 플래그 및 생성 공격 결과가 각각 다음 상태로 전달
- 기대 데미지와 인격/스킬별 기대 데미지에도 후보 상태별 확률을 반영
- 기존 5% 양 극단 제거, 99 Clash 하드캡, Bleed Count 전파 규칙 유지

핵심적으로
**Clash 확률 분기 → Trigger로 상태 변화 → terminal branch 혼합 → 각 상태에서 후속 공격 계산**
흐름의 누락된 확률 가중치를 보정했습니다.

## 검증
- `python run_tests.py`
- **83 passed**
- Python 문법 검사 통과

## 범위
실제 게임의 모든 인격 기믹이 자동 구조화된 것은 아니며, 현재는 구조화된 Trigger/자원/상태 규칙을 중심으로 확률 분기를 계산합니다.
