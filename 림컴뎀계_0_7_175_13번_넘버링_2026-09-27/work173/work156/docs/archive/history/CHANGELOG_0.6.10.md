# 0.6.10

## Fixed
- Fixed named resource per-stack damage scaling being parsed as a flat damage bonus.
- Added generic `ResourceField` value resolution for `FighterState.resources`, Charge, Ammo and Poise.
- Named resource damage modifiers without an explicit trigger now evaluate at `CoinStart`, so `ModifyContext` reaches the actual coin damage calculation.
- Added regression coverage for `오혈` and `흑수환염[黑獣丸染]` scaling and caps.

## Regression
- Full suite: 253 passed.
