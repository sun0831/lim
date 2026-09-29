# v0.5.71

## Conditional cross-identity support attack

- Added generic `actor_id` and `actor_has_status` trigger conditions.
- Added conservative parser for the explicit cross-identity pattern where a named ally with `예지안` lands a basic skill and the passive owner performs a named one-sided support attack on the target.
- Added runtime event context for the triggering actor's statuses and available identity roster.
- Preserved the original requested action; the support attack is queued as a triggered action.
- The rule remains turn-limited according to the source text.
- Ambiguous ally/enemy support wording is not auto-compiled.

## Verification

- pytest: 142 passed
- Identity catalog: 184 identities
