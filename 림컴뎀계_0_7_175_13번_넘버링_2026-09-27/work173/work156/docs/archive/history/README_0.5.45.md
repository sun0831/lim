# 림컴뎀계 v0.5.45

## Clash/coin lifecycle alignment

- Deterministic Clash execution now applies skill-level Clash Win/Lose effects before surviving coins resolve.
- Explicit exchange-outcome Clash execution uses the same Clash Win/Lose lifecycle.
- Skill-level `effects_on_hit` now resolves after surviving attack coins in both deterministic Clash paths.
- Probabilistic terminal Clash damage paths reuse the branch-local unopposed coin executor and apply the same post-coin `effects_on_hit` lifecycle.
- This reduces divergence between normal, explicit-exchange, and probabilistic terminal execution paths.

## Verification

- `python run_tests.py`: 98 passed
- Python syntax check: passed
