# E25 — Resource Conversion / Exchange Audit

## Scope
Audit the remaining `resource_conversion_or_exchange` semantics in the resource-transform pipeline and register only a genuinely reusable primitive.

## Findings
- The existing `SkillTextParserV19` already has executable effect kinds `resource_convert` and `resource_gain_from_consumed`.
- `resource_primitive_v1.py` previously lacked a common primitive mapping for those effect kinds.
- E25 adds `ResourcePrimitive.RESOURCE_CONVERSION` as a normalization primitive, not a standalone runtime.
- Supported explicit modes:
  - `fixed`: A amount → B amount
  - `proportional`: consumed A unit(s) → B amount per unit
  - `substitution`: acquiring A is replaced by B
  - `transfer`: A is consumed from one holder and B is supplied to another holder/target
- No identity-specific runtime was introduced.
- Existing `SKILL_RECLASSIFY`, `SKILL_SWAP`, `RESOURCE_CONSUME_TRIGGER`, and `CUMULATIVE_SPEND_GAIN` remain separate because their semantics differ.

## Verification
Focused regression suite: **23 passed**.

The complete suite was started but the environment execution limit was reached after the test run had progressed to approximately 28%; no assertion failure was observed in the visible portion. Therefore this is **not** reported as a full-suite pass.
