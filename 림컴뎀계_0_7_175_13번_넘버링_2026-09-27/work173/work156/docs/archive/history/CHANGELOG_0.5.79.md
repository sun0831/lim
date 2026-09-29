# 0.5.79 — Dynamic damage condition coverage

## Changes
- Added conservative parsing/execution for high-impact dynamic damage modifiers:
  - speed difference × target status potency damage bonus, with cap
  - self lost-HP percentage damage scaling, with optional cap
  - enemy lost-HP ratio damage scaling, with optional cap
- These modifiers are evaluated in the existing dynamic damage layer so current state can affect later coins.
- Fixed a latent negative-status-count condition path that referenced undefined local variables.
- Added regression tests for the three new parser patterns.
- Preserved unified analysis trace, identity/skill damage breakdown, Bleed Clash behavior, and NextTurnState output.

## Verification
- Full pytest suite: 156 passed.
- Catalog audit after this change: 621 attack skills; 1,924 supported clauses / 2,117 unsupported clauses.
- Unsupported skill clauses remain conservative: ambiguous prose is not auto-executed.
