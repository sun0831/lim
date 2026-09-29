# 림컴뎀계 0.6.0

0.6.0은 0.5.x의 자원/대상/재사용 기반 위에 **교차 인격 반응 이벤트**를 확장한다.

## 이번 버전

- 아군 기본 공격 적중 후 소유 인격의 원호공격
- 소유자 자기 자신 제외 조건
- 턴당 발동 횟수 제한
- 적의 아군 공격 종료 후 사망/HP 임계값 기반 원호공격 브리지
- 공격자를 후속공격의 명시적 타겟으로 전달
- `after_received_attack` 정규 이벤트 API

### 이벤트 예시

```python
gimmicks.after_received_attack(state, {
    'action_index': 1,
    'attacker_id': 'enemy_1',
    'received_target_id': 'ally_1',
    'received_target_hp': 20,
    'received_target_max_hp': 100,
    'received_target_died': False,
})
```

이 API는 적 행동을 추정하지 않는다. 실제 적 공격 결과를 호출자가 넣었을 때만 패시브를 판정한다.

## 검증

- 전체 테스트: 232 passed
- 인격: 184
- 스킬: 621
- 정적 passive gap: 360
