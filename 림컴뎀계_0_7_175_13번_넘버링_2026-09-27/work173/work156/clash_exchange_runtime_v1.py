"""User-defined clash-exchange state for the one-turn calculator.

This layer tracks the *actual defender coin count at the start of every
clash exchange*. It intentionally does not assume that exchange count equals
skill coin count. A verified game-specific resolver can later feed the same
state machine automatically.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Sequence

@dataclass
class ClashExchange:
    exchange_index: int
    outcome: str
    defender_coins_before: int
    defender_coins_rolled: int
    defender_coins_after: int
    bleed_procs: int
    attacker_coins_before: int | None = None
    attacker_coins_after: int | None = None
    unopposed_after: bool = False

@dataclass
class ClashExchangeState:
    attacker_coin_count: int
    defender_coin_count: int
    remaining_defender_coins: int = field(init=False)
    remaining_attacker_coins: int | None = field(init=False)
    exchanges: List[ClashExchange] = field(default_factory=list)

    def __post_init__(self):
        if self.attacker_coin_count < 0 or self.defender_coin_count < 0:
            raise ValueError("coin counts must be >= 0")
        self.remaining_defender_coins = self.defender_coin_count
        self.remaining_attacker_coins = self.attacker_coin_count

class ClashExchangeRuntime:
    """Resolve a user-supplied sequence of clash outcomes.

    W removes one defender coin. L leaves defender coin count unchanged.
    Bleed procs for an exchange equal the defender's coin count *before* the
    exchange result is applied. The attacker side can optionally be supplied
    per exchange because the number of exchanges is not assumed to equal the
    attacker's nominal coin count.
    """
    VALID = {"W", "L", "T"}

    def resolve(self, attacker_coin_count: int, defender_coin_count: int,
                outcomes: Sequence[str],
                attacker_coins_after: Sequence[int] | None = None,
                track_attacker_coins: bool = False) -> Dict[str, Any]:
        state = ClashExchangeState(attacker_coin_count, defender_coin_count)
        if attacker_coins_after is not None and len(attacker_coins_after) != len(outcomes):
            raise ValueError("attacker_coins_after must match outcomes length")

        for i, raw in enumerate(outcomes, 1):
            outcome = str(raw).upper()
            if outcome not in self.VALID:
                raise ValueError(f"invalid clash outcome: {raw!r}")
            # Defender depletion always ends the clash sequence. The attacker
            # side is intentionally optional here: the calculator must also
            # support user-defined/repeated exchange sequences where the same
            # attacker-side resource is refreshed or where only defender coin
            # evolution is being modeled (e.g. five L results from 3 defender
            # coins). When requested, attacker coins become a hard stop.
            if state.remaining_defender_coins <= 0:
                break
            if track_attacker_coins and int(state.remaining_attacker_coins or 0) <= 0:
                break

            defender_before = state.remaining_defender_coins
            attacker_before = state.remaining_attacker_coins
            rolled = defender_before
            bleed = rolled

            if outcome == "W":
                # The winning attacker coin remains in play and removes one
                # defender coin.
                state.remaining_defender_coins = max(0, defender_before - 1)
            elif outcome == "L":
                # In the default user-defined mode, only defender evolution is
                # authoritative. Optional attacker tracking reproduces the
                # ordinary coin-consumption interpretation.
                if track_attacker_coins:
                    state.remaining_attacker_coins = max(0, int(state.remaining_attacker_coins or 0) - 1)
            else:  # T
                # Draw: both sides keep their current active coin counts.
                # The next exchange therefore starts from the same state.
                pass

            explicit_attacker_after = None
            if attacker_coins_after is not None:
                explicit_attacker_after = int(attacker_coins_after[i - 1])
                if explicit_attacker_after < 0:
                    raise ValueError("attacker coin count cannot be negative")
                state.remaining_attacker_coins = explicit_attacker_after

            unopposed = state.remaining_defender_coins == 0
            state.exchanges.append(ClashExchange(
                exchange_index=i,
                outcome=outcome,
                defender_coins_before=defender_before,
                defender_coins_rolled=rolled,
                defender_coins_after=state.remaining_defender_coins,
                bleed_procs=bleed,
                attacker_coins_before=attacker_before,
                attacker_coins_after=(explicit_attacker_after if explicit_attacker_after is not None
                                      else state.remaining_attacker_coins),
                unopposed_after=unopposed,
            ))
            if unopposed:
                break

        return {
            "initial_attacker_coins": attacker_coin_count,
            "initial_defender_coins": defender_coin_count,
            "track_attacker_coins": bool(track_attacker_coins),
            "exchange_count": len(state.exchanges),
            "total_bleed_procs": sum(x.bleed_procs for x in state.exchanges),
            "defender_coins_remaining": state.remaining_defender_coins,
            "attacker_coins_remaining": state.remaining_attacker_coins,
            "exchanges": [x.__dict__.copy() for x in state.exchanges],
        }
