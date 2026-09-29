"""Turn-level dynamic programming for probabilistic Bleed state propagation.

The runtime carries the exact integer Bleed Count distribution from one
requested action to the next. It does not enumerate raw paths; equivalent
Bleed states are merged. Damage/state evaluation is delegated to callbacks so
this layer remains independent of the game-specific solver.
"""
from __future__ import annotations
from collections import defaultdict
from dataclasses import dataclass
from typing import Any, Callable, Dict, Iterable


@dataclass(frozen=True)
class BleedTurnState:
    bleed_count: int


class TurnBleedStateRuntime:
    def __init__(self, trim_fraction: float = 0.05):
        if not 0 <= trim_fraction < 0.5:
            raise ValueError("trim_fraction must be in [0, 0.5)")
        self.trim_fraction = float(trim_fraction)

    @staticmethod
    def normalize(dist: Dict[int, float]) -> Dict[int, float]:
        s = sum(max(0.0, float(v)) for v in dist.values())
        if s <= 0:
            return {0: 1.0}
        return {int(k): max(0.0, float(v)) / s for k, v in dist.items() if float(v) > 0}

    def trim_distribution_with_retention(self, distribution: Dict[int, float]):
        """Trim both tails and return (distribution, per-atom retention).

        Retention is the fraction of each original probability atom that remains
        after trimming. It lets correlated quantities such as damage be trimmed
        consistently with the Bleed-proc distribution.
        """
        items = sorted((int(k), max(0.0, float(v))) for k, v in distribution.items() if float(v) > 0)
        if not items:
            return {0: 1.0}, {0: 1.0}
        total = sum(v for _, v in items)
        low = self.trim_fraction * total
        high = self.trim_fraction * total
        kept = []
        original = {value: mass for value, mass in items}
        for value, mass in items:
            cut = min(mass, low)
            low -= cut
            remain = mass - cut
            if remain > 0:
                kept.append((value, remain))
        kept2 = []
        for value, mass in reversed(kept):
            cut = min(mass, high)
            high -= cut
            remain = mass - cut
            if remain > 0:
                kept2.append((value, remain))
        kept2.reverse()
        kept_total = sum(m for _, m in kept2)
        if kept_total <= 0:
            return {}, {}
        trimmed = {value: mass / kept_total for value, mass in kept2}
        retention = {value: mass / original[value] for value, mass in kept2}
        return trimmed, retention

    def trim_distribution(self, distribution: Dict[int, float]) -> Dict[int, float]:
        """Trim 5% probability mass from each tail and renormalize."""
        return self.trim_distribution_with_retention(distribution)[0]

    def propagate_action(
        self,
        incoming: Dict[int, float],
        terminal_distribution_fn: Callable[[int], Dict[int, float]],
        damage_fn: Callable[[int, int, float], float] | None = None,
        *,
        infinite_count: bool = False,
    ) -> Dict[str, Any]:
        """Propagate one action and merge equal outgoing Bleed Count states.

        terminal_distribution_fn(incoming_count) returns a distribution of
        Bleed procs for that action.  The resulting count is max(0, incoming -
        procs), unless infinite_count is enabled.  damage_fn receives
        (incoming_count, bleed_procs, branch_probability) and returns the
        branch's expected direct damage contribution.
        """
        incoming = self.normalize(incoming)
        outgoing: Dict[int, float] = defaultdict(float)
        expected_damage = 0.0
        branch_rows = []
        for incoming_count, state_mass in incoming.items():
            terminals = self.normalize(terminal_distribution_fn(int(incoming_count)))
            for procs, p in terminals.items():
                mass = state_mass * p
                if mass <= 0:
                    continue
                next_count = int(incoming_count) if infinite_count else max(0, int(incoming_count) - int(procs))
                outgoing[next_count] += mass
                if damage_fn is not None:
                    expected_damage += float(damage_fn(int(incoming_count), int(procs), mass))
                branch_rows.append({
                    "incoming_bleed_count": int(incoming_count),
                    "bleed_procs": int(procs),
                    "probability": mass,
                    "outgoing_bleed_count": next_count,
                })
        outgoing = self.normalize(dict(outgoing))
        return {
            "outgoing_distribution": dict(sorted(outgoing.items())),
            "expected_damage": expected_damage,
            "branch_count": len(branch_rows),
            "branches": branch_rows,
        }

    def propagate_turn(
        self,
        initial_bleed_count: int,
        actions: Iterable[Dict[str, Any]],
        action_runner: Callable[[Dict[str, Any], Dict[int, float]], Dict[str, Any]],
        *,
        infinite_count: bool = False,
    ) -> Dict[str, Any]:
        distribution = {max(0, int(initial_bleed_count)): 1.0}
        total_damage = 0.0
        trace = []
        for index, action in enumerate(actions, 1):
            result = action_runner(action, distribution)
            distribution = self.normalize(result.get("outgoing_distribution", distribution))
            total_damage += float(result.get("expected_damage", 0.0))
            trace.append({
                "action_index": index,
                "incoming_distribution": result.get("incoming_distribution"),
                "outgoing_distribution": dict(sorted(distribution.items())),
                "expected_damage": float(result.get("expected_damage", 0.0)),
                "branch_count": int(result.get("branch_count", 0)),
            })
        return {
            "initial_bleed_count": max(0, int(initial_bleed_count)),
            "final_bleed_distribution": dict(sorted(distribution.items())),
            "expected_final_bleed_count": sum(k * p for k, p in distribution.items()),
            "expected_turn_damage": total_damage,
            "actions": trace,
        }
