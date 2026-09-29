# 림컴뎀계 0.5.80

사용자가 지정한 1턴 전투를 상태 변화와 함께 재현하는 분석기의 공통 피해 조건 지원을 확장한 버전.

주요 추가:
- 대상 상태이상 합/개별 상태 위력 기반 피해량 증가
- 자신의 명명 자원당 피해량 증가
- 적 현재 HP 비율 조건부 피해량 증가
- 최대치 자동 적용
- 코인 시점 동적 평가

검증:
- pytest: 162 passed
- 공격 스킬: 621개
- 현재 parser audit: supported 1,769 / unsupported 2,274 clauses (audit methodology counts parser clauses directly)
