"""Shared coin-by-coin execution lifecycle for the v29 one-turn solver.

This module deliberately owns only the common lifecycle: execute one coin,
measure damage, run the caller's post-coin hook, handle coin reuse, then run the
caller's after-skill hook.  Clash/outcome selection remains outside this core.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional
from copy import deepcopy
import inspect

@dataclass
class CoinExecutionContext:
    state: Any
    identity: Any
    skill: Any
    faces: List[str]
    start: int = 0
    is_crit: bool = False
    generated: bool = False
    source_identity_id: str = ""
    source_skill_id: str = ""
    depth: int = 1
    prior_heads: int = 0
    coin_index: int = 0
    coin_damage: float = 0.0
    hp_before: float = 0.0
    hp_after: float = 0.0
    reuse_counts: Dict[Any, int] = field(default_factory=dict)

class CoinExecutionCore:
    """Execute a skill's coin lifecycle without deciding Clash outcomes."""

    def __init__(self, simulate_coin: Callable[..., Any]):
        self.simulate_coin = simulate_coin

    def execute(
        self,
        ctx: CoinExecutionContext,
        *,
        before_coin: Optional[Callable[[CoinExecutionContext], Any]] = None,
        on_coin: Optional[Callable[[CoinExecutionContext], Any]] = None,
        on_skill: Optional[Callable[[CoinExecutionContext, float], Any]] = None,
        reuse_condition: Optional[Callable[[CoinExecutionContext, Any], bool]] = None,
    ):
        state = ctx.state
        skill = ctx.skill
        coins = list(getattr(skill, "coins", []) or [])
        added_coin_indices = set()
        if reuse_condition is not None:
            for ar in getattr(skill, 'added_coin_rules', []) or []:
                if reuse_condition(ctx, ar.get('condition')):
                    src = int(ar.get('source_coin_index', -1))
                    for _ in range(max(0, int(ar.get('count', 1)))):
                        if 0 <= src < len(coins):
                            c = deepcopy(coins[src])
                            c.unbreakable = bool(ar.get('unbreakable', c.unbreakable))
                            c.effects.extend(deepcopy(ar.get('effects', []) or []))
                            coins.append(c)
                            added_coin_indices.add(len(coins) - 1)
        exec_faces = list(ctx.faces)
        for ai in sorted(added_coin_indices):
            rule = next((r for r in (getattr(skill, 'added_coin_rules', []) or [])
                         if int(r.get('source_coin_index', -1)) < len(ctx.faces)), None)
            src = int(rule.get('source_coin_index', 0)) if rule else 0
            exec_faces.append(ctx.faces[src] if 0 <= src < len(ctx.faces) else 'H')
        ci = max(0, int(ctx.start))
        total_before = float(state.enemy.hp)
        prior_heads = int(ctx.prior_heads)
        trace: List[Any] = []

        while ci < len(coins):
            if float(state.enemy.hp) <= 0:
                break
            coin = coins[ci]
            hp_before = float(state.enemy.hp)
            face = exec_faces[ci] if ci < len(exec_faces) else "H"
            pre_ctx = CoinExecutionContext(
                state=state, identity=ctx.identity, skill=skill, faces=ctx.faces,
                start=ctx.start, is_crit=ctx.is_crit, generated=ctx.generated,
                source_identity_id=ctx.source_identity_id, source_skill_id=ctx.source_skill_id,
                depth=ctx.depth, prior_heads=prior_heads, coin_index=ci + 1,
                coin_damage=0.0, hp_before=hp_before, hp_after=hp_before,
                reuse_counts=ctx.reuse_counts,
            )
            if before_coin:
                before_coin(pre_ctx)
            # Keep the shared lifecycle backward-compatible with lightweight
            # test doubles / legacy engines that still expose the pre-0.7.38
            # simulate_coin signature. Production DamageEngine accepts the
            # added-coin marker; older doubles simply do not receive it.
            sim_params = inspect.signature(self.simulate_coin).parameters
            if 'is_added_coin' in sim_params:
                self.simulate_coin(
                    state, ctx.identity, skill, coin, face,
                    bool(ctx.is_crit), ci + 1, prior_heads,
                    is_added_coin=(ci in added_coin_indices),
                )
            else:
                self.simulate_coin(
                    state, ctx.identity, skill, coin, face,
                    bool(ctx.is_crit), ci + 1, prior_heads,
                )
            hp_after = float(state.enemy.hp)
            coin_damage = max(0.0, hp_before - hp_after)
            coin_ctx = CoinExecutionContext(
                state=state, identity=ctx.identity, skill=skill, faces=ctx.faces,
                start=ctx.start, is_crit=ctx.is_crit, generated=ctx.generated,
                source_identity_id=ctx.source_identity_id,
                source_skill_id=ctx.source_skill_id, depth=ctx.depth,
                prior_heads=prior_heads, coin_index=ci + 1,
                coin_damage=coin_damage, hp_before=hp_before,
                hp_after=hp_after, reuse_counts=ctx.reuse_counts,
            )
            hook_trace = on_coin(coin_ctx) if on_coin else None
            if hook_trace:
                if isinstance(hook_trace, list):
                    trace.extend(hook_trace)
                else:
                    trace.append(hook_trace)
            if str(face).upper() == "H":
                prior_heads += 1

            should_reuse = False
            for ri, rule in enumerate(getattr(coin, "reuse_rules", []) or []):
                key = (ci, ri)
                used = int(ctx.reuse_counts.get(key, 0))
                if used >= int(rule.get("max_reuses", 0)):
                    continue
                condition = rule.get("condition")
                if reuse_condition is not None and reuse_condition(ctx, condition):
                    ctx.reuse_counts[key] = used + 1
                    should_reuse = True
                    break
            if not should_reuse:
                ci += 1

        final_ctx = CoinExecutionContext(
            state=state, identity=ctx.identity, skill=skill, faces=ctx.faces,
            start=ctx.start, is_crit=ctx.is_crit, generated=ctx.generated,
            source_identity_id=ctx.source_identity_id,
            source_skill_id=ctx.source_skill_id, depth=ctx.depth,
            prior_heads=prior_heads, coin_index=ci,
            coin_damage=0.0, hp_before=total_before,
            hp_after=float(state.enemy.hp), reuse_counts=ctx.reuse_counts,
        )
        pre_skill_damage = max(0.0, total_before - float(state.enemy.hp))
        skill_trace = on_skill(final_ctx, pre_skill_damage) if on_skill else None
        # after-skill hooks may queue generated attacks or apply extra damage.
        # Recompute from the authoritative branch HP so those effects are part
        # of the returned action damage without requiring a second damage path.
        total_damage = max(0.0, total_before - float(state.enemy.hp))
        if skill_trace:
            if isinstance(skill_trace, list):
                trace.extend(skill_trace)
            else:
                trace.append(skill_trace)
        return state, total_damage, trace
