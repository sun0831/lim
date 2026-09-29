# E35-2 RuleIR Coverage Audit

## Scope
`GIMMICK_GAP_REPORT_v4.json`의 현재 `gaps` 360건을 대상으로 기존 `passive_compiler_v29`의 clause 분해 결과를 E35 `Clause -> RuleIR` compiler에 통과시킨 구조적 변환률을 측정한다.

이 수치는 **게임 기믹 구현률이 아니다.** 기존 parser/runtime가 이미 표현할 수 있는 clause가 RuleIR로 내려오는 비율이며, 실제 전투 의미의 완전성은 E36 regression 및 real-game golden validation에서 별도로 확인한다.

## Result
- Gap records: **360**
- Clauses: **1,103**
- RuleIR-converted clauses: **231**
- Unsupported clauses: **872**
- Structural Clause -> RuleIR conversion rate: **20.94%**
- Unknown E34 primitive contract: **0**

## Axis breakdown
| Axis | Clauses | Converted | Rate |
|---|---:|---:|---:|
| action_trigger | 871 | 180 | 20.67% |
| cross_identity | 489 | 98 | 20.04% |
| multi_target | 149 | 43 | 28.86% |
| probability_random | 137 | 16 | 11.68% |
| resource_transform | 829 | 157 | 18.94% |
| skill_transform | 146 | 13 | 8.90% |
| special_state | 244 | 34 | 13.93% |
| stack_threshold | 149 | 37 | 24.83% |
| target_selection | 358 | 75 | 20.95% |

Axis totals overlap; they must not be summed as a denominator.

## Interpretation
The 20.94% figure is a **compiler-coverage metric only**. It does not mean the calculator is 20.94% implemented. A large portion of the 872 unsupported clauses is expected because E35 currently delegates semantic parsing to the canonical v29 compiler rather than introducing speculative parsers for every gap sentence.

The next work should therefore focus on the largest recurring unsupported clause families and route them through already-frozen E34 primitives, instead of creating new Runtime classes merely to increase the percentage.
