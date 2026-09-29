# 0.5.68 — Support Attack Skill Selection

- Formalized deterministic support-attack skill selection.
- `__support_default__` now resolves to the selected ally's next requested action.
- The original requested action is not consumed or replaced; the support attack is inserted as a generated action.
- Same identity may therefore execute the support attack and its original requested action separately.
- Preserves requested coin faces when available.
- Does not invent a skill or optimize/select by damage.
- Added regression coverage.

Verification: 136 pytest tests passed.
