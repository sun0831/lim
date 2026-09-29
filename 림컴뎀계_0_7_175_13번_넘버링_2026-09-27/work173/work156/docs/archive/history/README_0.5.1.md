# 림컴뎀계 0.5.1

## 무엇을 계산하는가
이 프로젝트는 사용자가 직접 지정한 **덱 + 스킬 + 행동 순서 + 초기 예열/전투 조건**을 1턴 동안 순차적으로 실행하고, 총 피해량과 인격별 피해량을 확인하는 계산기 엔진이다.

자동으로 최적의 덱이나 순서를 찾는 기능은 핵심 목표가 아니다.

## 입력
- 아군: 레벨, 속도, SP, HP, 충전, 탄환, 호흡/Poise, Sin 자원, 기타 자원/상태
- 적: HP, 방어 레벨, 물리 내성, 죄악 내성, Stagger 초기 상태와 임계값, 상태이상
- 행동: `identity_id`, `skill_id`, 코인 앞/뒷면, 대상 수
- 공명: 선택한 행동 순서에서 자동 산출
- 패시브: `compiled_conservative`일 때 지원된 컴파일 규칙만 실행

## 순차 계산
각 행동/코인 뒤에 BattleState를 갱신한다. 따라서 앞 행동의 피해, Stagger 진입, 버프/디버프, SP/충전/탄환/Poise 변화 등이 뒤 행동에 반영된다.

## 결과
`solve()`는 최소한 다음을 반환한다.
- `turn_damage`: 1턴 총 피해량
- `damage_by_identity`: 인격별 피해량
- `actions`: 행동별 피해량과 코인 결과
- `enemy_hp_after`
- `enemy_stagger_level/index/thresholds/staggered`
- `event_log`: 상태 변화 및 코인 계산 기록
- `passive_trace`: 실행된 패시브 추적

## 패키지 검증
현재 카탈로그의 184개 인격과 621개 스킬/변형 항목을 모두 `build_identity()`로 로딩할 수 있도록 v2 camelCase/list 구조를 지원한다.

테스트: `6 passed`
