# E-18 — resource_transform clause decomposition

## 목적

E-17에서 정의한 Resource Primitive를 실제 `resource_transform` 원문에 적용하기 전에, 215개 gap record를 **clause 단위**로 분해해 공용 Primitive 후보의 반복 구조를 측정한다.

## 결과

- `resource_transform` record: 215
- unique source text: 214
- clause candidate: 2,043
- unresolved candidate: 86
- candidate 종류는 중복될 수 있음. 한 문장이 여러 Primitive를 동시에 포함할 수 있으므로 합계로 215를 나누어 분류하지 않는다.

주요 후보 수:

| 후보 | 검출 수 |
|---|---:|
| count_scaling | 595 |
| resource_gain | 495 |
| trigger | 345 |
| status_effect | 149 |
| resource_scaled_modifier | 106 |
| resource_consume | 92 |
| affiliation_count | 51 |
| resource_zero | 49 |
| lowest_resource_selector | 34 |
| random_target | 19 |
| skill_transform | 22 |
| unresolved | 86 |

## 해석상의 주의

이 수치는 의미론적 최종 분류가 아니라 **보수적 후보 추출 결과**다. 따라서 `count_scaling`처럼 일반 숫자가 포함된 문장이 넓게 잡히며, 한 문장에 여러 후보가 동시에 기록된다. `unresolved`는 자동 추측을 피한 항목이다.

이번 단계에서는 인격별 전용 Runtime을 만들지 않았다.
