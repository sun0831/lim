# 0.7.175 구현 정렬안 (TXT 기준 고정)

## 기준 문서(고정)
- `/home/runner/work/lim/lim/림컴뎀계 기본 규칙모음/림컴뎀계 기본 규칙.txt`
- `/home/runner/work/lim/lim/림컴뎀계 기본 규칙모음/림컴뎀계 목표_1차2차 병합본.txt`
- `/home/runner/work/lim/lim/림컴뎀계 기본 규칙모음/림컴뎀계 방법론 .txt`
- `/home/runner/work/lim/lim/림컴뎀계 기본 규칙모음/림컴뎀계 파일 분류법.txt`
- `/home/runner/work/lim/lim/림컴뎀계 기본 규칙모음/출혈 및 파불코 설명.txt`

## 1) 기준 문서 vs 현재 코드 충돌표

| 기준 규격 | 현재 상태(증거) | 충돌/갭 | 조치 |
|---|---|---|---|
| Filter→Priority→Rank→Count 대상 선택 | `target_selector_v1.py`는 문자열 selector 중심 | 복합 대상 지정 일반화 부족 | **구조화 policy(dict) + filters/priority/fallback** 추가 |
| RuleIR 구조 변환 확대 | `E35_RULEIR_COVERAGE_AUDIT.json` 31.37% | 복합 clause 변환률 낮음 | `E35_5/6` 미지원 축 우선 구현 |
| 복합 lowering | `E35_6_COMPOUND_LOWERING_AUDIT.json` implemented 2 / partial 80 / none 726 | compound 자동 처리 약함 | 복합 Target/Trigger/Transform 우선 |
| 원문→규칙→실행 1:1 추적 | `event_runtime_v1.py`는 `trigger_rule_id` 중심 로그 존재 | source_text/primitive까지 일관 추적은 부분적 | 규칙 메타 연결 강화(후속 단계) |
| 출혈/파불코 공통 모델 | `bleed_clash_probability_v1.py`에 normal/unbreakable 분리 존재 | solver/target 축과 연결 점검 필요 | 공통 이벤트 모델 유지 + 회귀 확대 |

## 2) 구현 단위 재분류(인격별 → Primitive별)

- Condition: 조건 판정 (`condition_runtime_v1.py`)
- Target: 대상 선택 (`target_selector_v1.py`, `target_runtime_v1.py`)
- Effect: 상태/자원/수치 효과 (`effect_runtime_v1.py`, `resource_runtime_v1.py`)
- Trigger: 이벤트 기반 발동 (`trigger_runtime_v1.py`, `event_runtime_v1.py`)
- Action: 실행/연쇄 행동 (`action_queue_v1.py`, `trigger_action_execution_v1.py`)

하드코딩 후보는 위 5축 중 하나로 흡수하는 것을 기본 정책으로 한다.

## 3) 1차 우선순위 축
1. 복합 Target
2. Priority/Fallback
3. Trigger→추가행동
4. Resource/Skill Transform

## 4) 원문→구조화→실행 1:1 연결 계약
- source_text: 원문
- structured_rule: 조건/대상/효과/시점
- runtime_path: 실제 실행 primitive 경로
- trace_key: rule_id + trigger_rule_id

## 5) 출혈/파불코 원칙
- 파불코는 일반 코인과 분리 추적
- 출혈 발동 횟수는 교환 시점 active 코인 기준
- 전용 하드코딩보다 공통 상태/코인 이벤트 흐름을 유지

## 6) 실행 루프
- 작은 수정
- 관련 테스트/회귀
- 다음 축 진행

## 7) 골든 비교(샘플)
- 샘플 인격 소수 선정
- 총 피해 + 인격/스킬/코인 단위 대조
- 로그로 최초 불일치 지점 역추적

---
이번 변경에서는 우선순위 1~2번(복합 Target, Priority/Fallback)을 공통 selector primitive에 반영했다.
