# 0.5.77 — Deferred / Next-Turn Effect Scheduler

## Added
- Added `deferred_turns` to compiled passive definitions.
- Passive effects containing `다음 턴` are scheduled instead of being applied during the causal event.
- Causal trigger parsing now ignores the temporal marker `다음 턴에`, so forms such as `적중시 다음 턴에 ...` retain their real trigger.
- Added `PassiveRuntime.apply_deferred_turn_start()` to consume effects whose delay expires.
- Added `PassiveAwareBattleStateMachineV23.start_next_turn()` for multi-turn callers: reset turn activations, apply deferred effects, then emit TurnStart.
- Deferred scheduling records an event-log entry for traceability.

## Scope / limitations
- This is infrastructure for future-turn state; the current one-turn solver records scheduled effects but does not pretend they affect the current turn.
- Clauses whose causal trigger/effect parser is otherwise unsupported remain unsupported.
- Skill transformation and slot replacement on next turn remain separate work.

## Verification
- 153 pytest tests passed.
