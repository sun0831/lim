# Parallel Coverage v2

이번 버전의 실제 코드/테스트 기준 추가 범위. 퍼센트는 게임 전체 완성률이 아니라 구현된 런타임 영역의 구조적 커버리지 지표가 아니다.

- 특수자원: 획득/소모/조건/임계값/변형/트리거/연쇄 유지
- 자원 효과: resource/resource_gain/resource_consume 연결
- 상태 피해: Bleed 자가피해, Sinking SP 피해, Burn 턴종료 피해
- 흐트러짐: 기본 HP 임계값 + 고정피해/코인 효과/턴종료 피해 후 재검사
- 추적: 코인별 이벤트 + 행동 전후 자원/SP/Poise 스냅샷
- 방어 레벨: Fighter defense_level_bonus 상태 보존
- Clash/Critical: 0.5.20 기능 유지

검증: 51 passed, compile PASS
