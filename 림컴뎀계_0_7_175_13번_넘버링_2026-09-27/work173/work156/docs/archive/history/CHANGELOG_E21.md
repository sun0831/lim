# E21 — Resource selector symmetry / parameter audit

## Scope

E21 completes the planned highest/lowest resource-selector parameter audit without inventing a generic "highest" selector for unrelated metrics such as HP, status potency, or damage dealt.

## Verified source cases

The full `resource_transform` gap corpus contains 2 explicit highest/most-resource ally selection cases:

1. R사 제 4무리 코뿔소팀 — `충전 횟수가 가장 높은 아군`
2. 마침표 사무소 대표 — `탄환을 가장 많이 보유한 아군`

Both map to `HIGHEST_RESOURCE_TARGET` at the primitive level. They use different resource semantics (charge count vs ammo count), so the primitive remains resource-parameterized rather than creating identity-specific selectors.

## Implementation change

`primitive_from_effect()` now preserves an explicit `target_side` parameter for both `LOWEST_RESOURCE_TARGET` and `HIGHEST_RESOURCE_TARGET`. The previous default remains `ally` for backward compatibility.

## Deliberate non-matches

Phrases such as `최대 체력이 가장 높은 아군`, `잔향이 가장 높은 대상`, and `가장 많이 피해를 준 적` are not classified as resource selectors. They belong to other target-selection metrics and must be handled by the broader Target/Condition primitive work.

## Validation

Focused resource tests: 21 passed.

Full suite invocation reached 29% before the execution environment timeout; no test failure output was produced. Therefore E21 is **not** reported as a full-suite pass.
