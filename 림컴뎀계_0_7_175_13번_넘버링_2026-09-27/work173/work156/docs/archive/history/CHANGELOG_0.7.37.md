# 0.7.37 — 진동 폭발 특수 경계 4종 source-backed 연결

## Source-backed targets
- identity-10414 / 1041405: 고독 부여 대체 조건 → 진동 폭발, 진동 횟수 1 감소
- identity-10716 / 107162: 완성되어가는 교본 보유 또는 결투 고조 보유 → 진동 폭발, 진동 횟수 1 감소
- identity-10813 / 1081305: 광【光】 위력 5 → 마지막 재사용 코인 적중시 진동 폭발 2회, 진동 횟수 1 감소
- identity-11216 / 112162: 추가된 코인 적중 시 진동 폭발, 진동 횟수 1 감소

## Implementation
- Conditional Burst를 generic `진동 폭발`로 뭉개지 않고 source condition을 유지.
- Burst Count와 Count cost를 별도 필드로 유지.
- `resource_gte(광【光】)` + `reuse_hit` 경계를 last-coin reuse에 연결.
- `추가된 코인`은 별도 `added_coin_hit` execution boundary로 등록.
- 고독 대체는 `tremor_burst_replacement` boundary로 등록하며 일반 고독 부여와 구분.
- 교본/결투 고조 조건은 OR 조건으로 유지.

## Verification
- 신규 special-boundary tests: 4/4
- Tremor reuse/count/catalog regression subset: 19/19
- Tremor/Amplitude/RuleIR suite: 64/64

## Remaining execution note
- 10414의 고독 부여 대체와 11216의 실제 추가 코인 생성/적중은 별도의 상태/코인 생성 execution boundary가 필요하므로, 이번 버전에서는 parser contract까지만 연결하고 generic hit로 오인 처리하지 않음.
