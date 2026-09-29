"""Probabilistic clash-path runtime for one-turn Bleed estimation.

This module is intentionally separate from the damage engine. It calculates
an expected Bleed-proc distribution from sequential Clash win/draw/loss
branches without enumerating every raw path.

Design rules:
- Bleed procs at each exchange equal the defender's currently active coin
  count before the result is applied.
- W: defender loses one normal coin.
- L: attacker loses one coin.
- T: both sides stay unchanged.
- 99 exchanges is a hard cap; exchange 99 is forced to defender victory.
- Optional 5% two-sided trimming removes probability mass from the lowest and
  highest 5% of the terminal total-Bleed distribution before calculating the
  trimmed expectation. No arbitrary probability correction is applied.
"""
from __future__ import annotations
from collections import defaultdict
from dataclasses import dataclass
from typing import Any, Callable, Dict, Iterable, List, Tuple

OutcomeProb = Tuple[float, float, float]  # win, draw, loss


@dataclass(frozen=True)
class ClashPathState:
    attacker_coins: int
    defender_coins: int
    exchanges: int
    total_bleed: int


class ProbabilisticBleedClashRuntime:
    MAX_EXCHANGES = 99

    def __init__(self, trim_extremes: bool = True, trim_fraction: float = 0.05):
        if not 0 <= trim_fraction < 0.5:
            raise ValueError("trim_fraction must be in [0, 0.5)")
        self.trim_extremes = bool(trim_extremes)
        self.trim_fraction = float(trim_fraction)

    @staticmethod
    def _normalize(p: OutcomeProb) -> OutcomeProb:
        vals = tuple(max(0.0, float(x)) for x in p)
        s = sum(vals)
        if s <= 0:
            raise ValueError("outcome probabilities must have positive mass")
        return tuple(x / s for x in vals)  # type: ignore[return-value]

    def resolve(
        self,
        attacker_coin_count: int,
        defender_coin_count: int,
        probability_fn: Callable[[Dict[str, Any]], OutcomeProb],
        *,
        defender_unbreakable_coins: int = 0,
        max_exchanges: int = MAX_EXCHANGES,
    ) -> Dict[str, Any]:
        if attacker_coin_count < 0 or defender_coin_count < 0 or defender_unbreakable_coins < 0:
            raise ValueError("coin counts must be >= 0")
        max_exchanges = min(int(max_exchanges), self.MAX_EXCHANGES)
        if max_exchanges < 1:
            raise ValueError("max_exchanges must be >= 1")

        # State -> probability. Keeping total_bleed in the state gives the
        # terminal distribution needed for exact probability-weighted trimming.
        normal_defender = int(defender_coin_count)
        unbreakable = int(defender_unbreakable_coins)
        states: Dict[Tuple[int, int, int, int, int, str], float] = {
            (int(attacker_coin_count), normal_defender, unbreakable, 0, 0, 'START'): 1.0
        }
        terminal: Dict[int, float] = defaultdict(float)
        terminal_meta: Dict[Tuple[int, int, int, int, int, str], float] = defaultdict(float)
        exchange_count_dist: Dict[int, float] = defaultdict(float)
        final_defender_dist: Dict[int, float] = defaultdict(float)
        final_attacker_dist: Dict[int, float] = defaultdict(float)
        p_reach_cap = 0.0

        while states:
            next_states: Dict[Tuple[int, int, int, int, int], float] = defaultdict(float)
            for (a, normal_d, ub, ex, bleed, last_outcome), mass in states.items():
                d = normal_d + ub
                if mass <= 0:
                    continue
                if a <= 0 or d <= 0 or ex >= max_exchanges:
                    terminal[bleed] += mass
                    terminal_meta[(a, normal_d, ub, ex, bleed, last_outcome)] += mass
                    exchange_count_dist[ex] += mass
                    final_defender_dist[d] += mass
                    final_attacker_dist[a] += mass
                    if ex >= max_exchanges:
                        p_reach_cap += mass
                    continue

                rolled = d
                context = {
                    "attacker_coins": a,
                    "defender_coins": d,
                    "normal_defender_coins": normal_d,
                    "unbreakable_defender_coins": ub,
                    "active_defender_coins": d,
                    "exchange_index": ex + 1,
                    "total_bleed_before": bleed,
                }
                if max_exchanges == 99 and ex + 1 == 99:
                    # Hard rule: the 99th exchange is defender win.
                    probs = (0.0, 0.0, 1.0)
                else:
                    probs = self._normalize(probability_fn(context))

                for outcome, p in zip(("W", "T", "L"), probs):
                    branch = mass * p
                    if branch <= 0:
                        continue
                    na, nn, nub = a, normal_d, ub
                    if outcome == "W":
                        # The first winning clash against an active unbreakable
                        # coin deactivates that coin for subsequent exchanges.
                        if nub > 0:
                            nub -= 1
                        elif nn > 0:
                            nn -= 1
                    elif outcome == "L":
                        na = max(0, a - 1)
                    # T intentionally leaves both coin counts unchanged.
                    nex = ex + 1
                    nbleed = bleed + rolled
                    nd = nn + nub
                    key = (na, nn, nub, nex, nbleed, outcome)
                    if na <= 0 or nd <= 0 or nex >= max_exchanges:
                        terminal[nbleed] += branch
                        terminal_meta[key] += branch
                        exchange_count_dist[nex] += branch
                        final_defender_dist[nd] += branch
                        final_attacker_dist[na] += branch
                        if nex >= max_exchanges:
                            p_reach_cap += branch
                    else:
                        next_states[key] += branch
            states = dict(next_states)

        total_mass = sum(terminal.values())
        if total_mass <= 0:
            raise RuntimeError("no terminal probability mass produced")
        terminal = {k: v / total_mass for k, v in terminal.items()}
        exchange_count_dist = {k: v / total_mass for k, v in exchange_count_dist.items()}
        final_defender_dist = {k: v / total_mass for k, v in final_defender_dist.items()}
        final_attacker_dist = {k: v / total_mass for k, v in final_attacker_dist.items()}
        p_reach_cap = p_reach_cap / total_mass

        raw_expected = sum(value * prob for value, prob in terminal.items())
        trimmed_expected = self._trimmed_mean(terminal) if self.trim_extremes else raw_expected

        return {
            "initial_attacker_coins": int(attacker_coin_count),
            "initial_defender_coins": int(defender_coin_count) + int(defender_unbreakable_coins),
            "initial_defender_normal_coins": int(defender_coin_count),
            "initial_defender_unbreakable_coins": int(defender_unbreakable_coins),
            "max_exchanges": max_exchanges,
            "trim_extremes": self.trim_extremes,
            "trim_fraction_each_tail": self.trim_fraction if self.trim_extremes else 0.0,
            "trimmed_mass": (1.0 - 2.0 * self.trim_fraction) if self.trim_extremes else 1.0,
            "expected_bleed_procs_raw": raw_expected,
            "expected_bleed_procs": trimmed_expected,
            "probability_reaching_99_exchanges": p_reach_cap if max_exchanges == 99 else 0.0,
            "exchange_count_distribution": dict(sorted(exchange_count_dist.items())),
            "terminal_bleed_distribution": dict(sorted(terminal.items())),
            "final_defender_coin_distribution": dict(sorted(final_defender_dist.items())),
            "final_attacker_coin_distribution": dict(sorted(final_attacker_dist.items())),
            # Kept for the one-turn solver's action-local expected-damage layer.
            "_terminal_meta": dict(terminal_meta),
        }

    def _trimmed_mean(self, distribution: Dict[int, float]) -> float:
        """Remove exactly 5% mass from each tail, including partial atoms."""
        if not distribution:
            return 0.0
        alpha = self.trim_fraction
        if alpha == 0:
            return sum(x * p for x, p in distribution.items()) / sum(distribution.values())
        items = sorted((float(x), float(p)) for x, p in distribution.items() if p > 0)
        total = sum(p for _, p in items)
        low = alpha * total
        high = alpha * total
        kept: List[Tuple[float, float]] = []
        for value, mass in items:
            cut = min(mass, low)
            low -= cut
            remain = mass - cut
            if remain > 0:
                kept.append((value, remain))
        # Remove upper tail from the remaining mass.
        kept2: List[Tuple[float, float]] = []
        for value, mass in reversed(kept):
            cut = min(mass, high)
            high -= cut
            remain = mass - cut
            if remain > 0:
                kept2.append((value, remain))
        kept2.reverse()
        mass_kept = sum(p for _, p in kept2)
        if mass_kept <= 0:
            raise RuntimeError("tail trimming removed all probability mass")
        return sum(value * p for value, p in kept2) / mass_kept
