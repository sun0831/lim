"""Common Amplitude state/debuff runtime.

Amplitude is represented as a target status rather than as an identity-specific
runtime or a second state mirror.  The status payload keeps the minimum data
needed by generic predicates/effects: amplitude name, mode, source and the
Tremor potency/count snapshot available when the state was created.

This module intentionally does not infer game-specific conversion ratios or
Tremor consumption.  Those belong to explicit effects/rules.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Any


def _statuses(target: Any) -> dict:
    statuses = getattr(target, "statuses", None)
    if statuses is None:
        statuses = {}
        setattr(target, "statuses", statuses)
    return statuses


class AmplitudeRuntime:
    STATUS_NAME = "Amplitude"
    VALID_MODES = {"conversion", "entanglement"}

    def _container(self, target: Any) -> dict:
        statuses = _statuses(target)
        status = statuses.get(self.STATUS_NAME)
        if status is None:
            # Import lazily to avoid an import cycle with passive_runtime_v29_base.
            from limbus_damage_engine_v29 import Status
            status = Status()
            statuses[self.STATUS_NAME] = status
        status.data.setdefault("states", [])
        return status.data

    def get_states(self, target: Any) -> list[dict]:
        data = self._container(target)
        return [deepcopy(x) for x in data.get("states", []) if isinstance(x, dict)]

    def _write_states(self, target: Any, states: list[dict]) -> None:
        data = self._container(target)
        data["states"] = states
        # A zero-state container is not useful as a visible debuff.
        if not states:
            _statuses(target).pop(self.STATUS_NAME, None)

    def has_state(self, target: Any, amplitude: str | None = None,
                  mode: str | None = None) -> bool:
        for entry in self.get_states(target):
            if mode is not None and entry.get("mode") != mode:
                continue
            if amplitude is not None:
                names = entry.get("amplitudes") if entry.get("mode") == "entanglement" else [entry.get("amplitude")]
                if amplitude not in {str(x) for x in (names or [])}:
                    continue
            return True
        return False

    def set_state(self, state: Any, target: Any, amplitude: str, mode: str = "conversion",
                  *, source: str = "Tremor", owner_id: str | None = None) -> dict:
        if mode not in self.VALID_MODES:
            raise ValueError(f"unsupported amplitude mode: {mode}")
        if not amplitude:
            raise ValueError("amplitude must not be empty")

        states = self.get_states(target)
        tremor = getattr(target, "statuses", {}).get("Tremor")
        potency = int(getattr(tremor, "potency", 0))
        count = int(getattr(tremor, "count", 0))

        if mode == "conversion":
            # Conversion is a single current amplitude state. Do not consume
            # Tremor here: the source text must explicitly request consumption.
            states = [s for s in states if s.get("mode") != "conversion"]
            entry = {
                "amplitude": str(amplitude),
                "mode": "conversion",
                "source": source,
                "owner_id": owner_id,
                "tremor_potency": potency,
                "tremor_count": count,
            }
            states.append(entry)
        else:
            # Entanglement is additive and can coexist with conversion/other
            # entanglements. Merge the same named entanglement instead of
            # duplicating it.
            found = False
            for entry in states:
                if entry.get("mode") == "entanglement" and entry.get("amplitude") == str(amplitude):
                    entry.update({"source": source, "owner_id": owner_id,
                                  "tremor_potency": potency, "tremor_count": count})
                    found = True
                    break
            if not found:
                states.append({
                    "amplitude": str(amplitude),
                    "mode": "entanglement",
                    "source": source,
                    "owner_id": owner_id,
                    "tremor_potency": potency,
                    "tremor_count": count,
                })

        self._write_states(target, states)
        return states[-1]

    def entangle_current_tremor(self, state: Any, target: Any, *, owner_id: str | None = None) -> dict:
        # "current_tremor" is a symbolic source state, not a named game
        # amplitude. It is useful for generic compiler output until the source
        # rule supplies the concrete named amplitude.
        return self.set_state(state, target, "current_tremor", "entanglement",
                              source="Tremor", owner_id=owner_id)

    def remove(self, target: Any, amplitude: str | None = None,
               mode: str | None = None) -> int:
        states = self.get_states(target)
        kept = []
        removed = 0
        for entry in states:
            matches = (amplitude is None or entry.get("amplitude") == amplitude) and \
                      (mode is None or entry.get("mode") == mode)
            if matches:
                removed += 1
            else:
                kept.append(entry)
        self._write_states(target, kept)
        return removed
