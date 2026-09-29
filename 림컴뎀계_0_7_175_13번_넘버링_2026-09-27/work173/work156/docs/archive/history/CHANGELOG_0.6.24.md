# 림컴뎀계 0.6.24

## 검계 홍매화 Runtime 연결

- 검계 `identity-10208`의 `크리티컬 적중 시 홍매화` 규칙을 검계 소속 모듈로 연결.
- 홍매화가 10 미만이면 크리티컬 적중 시 홍매화 +1.
- 홍매화가 10이면 홍매화 증가 대신 `Defense Level Down` +1.
- `Defense Level Down`은 최대 6까지 적용.
- 크리티컬 여부를 `DamageEngine → GimmickRegistry.after_coin()`으로 전달하도록 연결.
- 기존 PassiveCompiler의 방어 레벨 효과와 충돌하지 않도록 해당 크로스-인격 상태 변화는 검계 모듈에서 처리.

## 구조 원칙

- 검계 규칙은 `gimmick_modules/blade_lineage.py`에서 선언.
- 실제 상태 변경은 기존 `TriggerRuntime`/`GimmickRegistry`에서 처리.
- 인격별 별도 Runtime을 추가하지 않음.

## 검증

- Python 문법 검사 PASS
- 전체 테스트: **294 passed**
