# E32 — probability_random audit

## Scope
Audit the `probability_random` category in the current `GIMMICK_GAP_REPORT_v4.md.json` against existing probability/random primitives.

## Findings
- 30 records / 29 unique source texts.
- No standalone `ProbabilityRandomRuntime` was introduced.
- Random target clauses route to the existing target-selector/random-selection contract.
- Explicit probability clauses route to the existing probabilistic trigger/reuse contracts.
- One genuine semantic contract gap was isolated: **per-coin/per-ammo independent random outcomes**. This is not promoted to a new Runtime in E32; it is recorded as a RuleIR contract parameterization requirement.
- No arbitrary statistical correction, extreme-tail trimming, or forced 100% probability conversion was introduced by E32.

## Tests
- E32 audit tests: 4 passed.
- Related random-target/reuse regressions: 10 passed.
- Combined targeted tests: 14 passed.
- Full regression collection/run was not claimed here.
