# E25 Resource Conversion Audit

- Source: `GIMMICK_GAP_REPORT_v4.md.json`
- Total gap records: 360
- Raw candidate records: 14
- Unique candidate texts: 14

## Decision

A real common primitive is required: `RESOURCE_CONVERSION`.

This is **not** a new standalone runtime. Existing parser execution already supports `resource_convert` and `resource_gain_from_consumed`; E25 normalizes those effects into the common primitive registry.

### Modes
- `fixed`: A amount -> B amount
- `proportional`: consumed A unit(s) -> B amount per unit
- `substitution`: acquisition of A is replaced by B
- `transfer`: A is consumed from one holder and B is supplied to another holder/target

The mode is explicit; no semantic guessing is performed.
