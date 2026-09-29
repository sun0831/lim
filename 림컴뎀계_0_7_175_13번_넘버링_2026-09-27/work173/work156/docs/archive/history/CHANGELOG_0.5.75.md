# v0.5.75 — enemy death event bridge

- Added a generic `after_kill` compilation path for deterministic `적 사망 시` / `적이 사망하면` effects that heal the lowest-HP living ally.
- The trigger is independent of the killer identity; any real enemy kill can fire the passive if its activation budget allows it.
- Reuses the existing activation-scope/turn-limit runtime.
- Keeps random-target, random-resource, and future-turn status clauses out of the parser until their required state semantics are available.
- Added regression coverage for cross-identity enemy-death healing and turn-limited activation.

Verification: `147 passed`.
