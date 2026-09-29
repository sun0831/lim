# 림컴뎀계 0.6.11 — 모듈 로딩 분류 보고서

## 목적

선택된 인격에 필요한 계산 모듈만 활성화할 수 있도록, **범용 키워드**와 **인격/소속 고유 기믹 모듈**을 분리하는 기반을 추가했다.

핵심 원칙:

- 7대 키워드: `충전 / 출혈 / 호흡 / 진동 / 화상 / 파열 / 침잠`
- 인격 고유/소속 기믹: `새벽 사무소 / 중지 / 피쿼드호 / 약지 / 거미집`
- 고유 자원이 기존 키워드와 같은 방식으로 작동하면 해당 키워드 모듈에 포함한다.
- **생체 재료는 `충전` 계열로 분류**한다. Ring 모듈은 생체 재료의 획득/소모 규칙만 제공한다.
- 실제 전투 계산은 기존 `ResourceRuntime / TriggerRuntime / ActionQueue / DamageEngine`을 계속 사용한다.

## 현재 카탈로그 분류 결과

카탈로그 184 인격 기준 모듈 보유 인격 수:

| 모듈 | 인격 수 |
|---|---:|
| charge | 25 |
| bleed | 53 |
| poise | 41 |
| tremor | 37 |
| burn | 28 |
| rupture | 50 |
| sinking | 32 |
| dawn_office | 3 |
| middle | 7 |
| pequod | 3 |
| ring | 7 |
| spider_house | 10 |

생체 재료를 가진 카탈로그 인격은 2명이며 모두 `charge` 모듈을 함께 갖도록 분류된다.

## 런타임 동작

`GimmickRegistry` 생성 시 현재 시나리오에서 선택된 인격만 `ModuleResolver`에 전달한다.

```text
선택 인격
  ↓
ModuleResolver
  ↓
필요한 Keyword + Gimmick Module 결정
  ↓
필요한 provider만 lazy import
  ↓
GimmickRegistry / TriggerRuntime
```

따라서 카탈로그 전체의 모든 기믹 provider를 전투마다 불러오는 구조가 아니다.

## 0.6.11에서 실제로 모듈 게이트를 적용한 규칙

- 피쿼드호 선장의 우측 원호 공격 → `pequod`
- 중지 작은 형님의 피격/앙갚음 장부 계열 → `middle`
- 약지 생체 재료 획득/소모 규칙 → `ring`
- 새벽불 관련 기본 공격 획득 규칙 → `dawn_office`
- 새벽 사무소 크로스-아이덴티티 흐트러짐 원호의 Dawn 대상 판정 → `dawn_office`

기존 계산 엔진 자체는 변경하지 않고 모듈 활성 여부만 추가했다.

## 테스트

- 기존 테스트: 253개
- 신규 모듈 로딩 테스트: 4개
- 최종: **257 passed**
- 실행 시간: 약 14초
- Python syntax check: PASS
