# Charge Count / Potency cumulative-spend implementation

## Scope

- Explicit Charge Count consumption is tracked in `cumulative_resource_consumed`.
- Turn-end Charge Count decay is not cumulative spend.
- Charge Potency is an independent resource and persists when Charge Count reaches 0.
- Declarative rules of the form `누적으로 자신의 충전 횟수 10 소모할 때마다 ...` are compiled to `cumulative_resource_gain`.
- The parser accepts both `10을 소모` and `10 소모` source forms.
- Multi-word destination resources such as `충전 위력` are supported.
- `ResourceRuntime` applies the reward through the common resource runtime, so `충전 위력` updates `FighterState.charge_potency` rather than the generic resource map.
- A single consumption event may cross multiple thresholds; each newly crossed threshold fires once.

## Catalog coverage verified

- `identity-10116` (LCE E.G.O::차원찢개): cumulative Charge 10 -> Charge Potency 1.
- `identity-10210` (멀티크랙 사무소 대표): cumulative Charge 10 -> Charge 1.

## Regression

- Charge/resource targeted suite: 32 passed.
- Combined resource/rule/effect/keyword suite: 90 passed.
- Full-suite execution was attempted; the runner reached the end of the progress stream but did not return a final pytest summary within the execution window, so no full-suite pass claim is made here.
