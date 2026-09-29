# 림컴뎀계 0.5.2

## 목적
사용자가 지정한 덱, 스킬, 행동 순서와 초기 예열/전투 조건을 그대로 1턴 순차 시뮬레이션하여 총 피해량과 인격별 피해량을 계산한다.

## 0.5.2 핵심 변경
- 스킬/패시브 실행에서 중복 패시브 변형을 동시에 발동하지 않도록 `passive_variant_mode=last`를 기본 적용.
- 원호 공격처럼 **새로운 공격을 생성하는 기믹**을 generic passive compiler와 분리한 `special_gimmick_v1.py`로 관리.
- 현재 카탈로그에서 고신뢰 패턴으로 인식되는 원호 공격을 실제 행동 큐에 삽입.
- 마지막 탄환 소모 후 피해량 비례 추가 피해처럼 secondary damage를 별도 이벤트로 처리하는 기반 추가.
- 코인별 탄환 소모, 피해량 증가, 크리티컬 피해량 증가, 파괴 불가 코인 텍스트를 스킬 데이터에 연결.
- 흐트러짐 손상은 HP 피해와 별도 이벤트로 기록.
- 결과에 `generated`, `reason`, `gimmicks`, `active_passives`를 추가하여 특수기믹과 일반 행동을 구분.

## 주의
현재 모든 특수 기믹을 완전 복제한 것은 아니다. 인식되지 않은 특수 기믹은 임의의 효과로 추정하지 않고 원문/미지원 상태로 남긴다. 정확도가 중요한 계산기이므로 이 원칙을 유지한다.

## 입력 핵심
- `actions`: 사용자가 원하는 순서 그대로 실행
- `allies`: SP/HP/호흡/충전/탄환/상태이상/커스텀 자원
- `enemy`: HP/방어/물리 내성/죄악 내성/Stagger
- `passive_mode`: `compiled_conservative`
- `passive_variant_mode`: `last` 기본, `all`은 데이터 진단용

## 출력 핵심
- `turn_damage`: 1턴 총 피해량
- `damage_by_identity`: 인격별 누적 피해량
- `actions`: 스킬별 피해량 및 코인 결과
- `enemy_*`: 적의 턴 종료 상태
- `event_log`: 코인/상태변화/Stagger/특수기믹 추적
