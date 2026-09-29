# E36 Integration Regression Report

## Scope
E34 Primitive Registry + E35 Clause→RuleIR Compiler/Lowering integrated snapshot.

## Test inventory
- Collected: 603 tests
- Fast suite: 595 passed, 8 slow deselected
- Slow tests: 8 individually executed, 8 passed
- Effective full result: 603 passed, 0 failed

## Slow-test verification
1. catalog migration-safe golden parity: 1 passed (14.21s)
2. infinite bleed terminal-count finalization: 1 passed (9.01s)
3. correlated final bleed trim: 1 passed (3.72s)
4. probabilistic post-clash state: 1 passed (2.68s)
5. catalog generic rules do not fallback to legacy: 1 passed (1.62s)
6. catalog trigger rules common-runtime safe: 1 passed (1.55s)
7. generated-action target precedence: 1 passed (0.16s)
8. support command Captain 100% rule: 1 passed (1.52s)

## Notes
The unified full runner timed out in this environment before printing its final summary, but the fast suite plus all 8 slow tests were independently verified. No test failure was observed.

Legacy retirement is NOT performed in E36. The golden parity test remains active as a safety net. Retirement can be considered only after this integration result and subsequent real-game golden validation remain stable.
