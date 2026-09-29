"""Explicit runtime model for Limbus '특수 충전' bookkeeping.

This module deliberately does NOT invent a single '고유 충전' resource.
Catalog text uses '특수 충전' as a category and separately names concrete
resources.  The runtime therefore keeps concrete special-charge entries by
name and records whether an entry is fixed-power.

Semantics from the catalog:
- special charge with count+power participates in Charge-count aggregates;
- fixed-power special charge participates in Charge-count aggregates where the
  clause explicitly says '(위력 고정)' / '특수 충전 포함', but is excluded by
  clauses that explicitly say '위력 고정 특수 충전 제외';
- fixed-power special charge is never treated as Charge Potency.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict


@dataclass
class SpecialCharge:
    name: str
    count: int = 0
    potency: int = 0
    fixed_power: bool = False

    def clamp(self) -> None:
        self.count = max(0, int(self.count))
        self.potency = max(0, int(self.potency))


@dataclass
class SpecialChargeBook:
    entries: Dict[str, SpecialCharge] = field(default_factory=dict)

    def ensure(self, name: str, *, fixed_power: bool = False) -> SpecialCharge:
        key = str(name)
        item = self.entries.get(key)
        if item is None:
            item = SpecialCharge(key, fixed_power=fixed_power)
            self.entries[key] = item
        elif fixed_power:
            item.fixed_power = True
        return item

    def count_total(self, *, include_fixed_power: bool = True) -> int:
        return sum(
            max(0, int(x.count))
            for x in self.entries.values()
            if include_fixed_power or not x.fixed_power
        )

    def count_non_fixed(self) -> int:
        return self.count_total(include_fixed_power=False)

    def potency_total(self) -> int:
        # Fixed-power special charges are not Charge Potency.
        return sum(max(0, int(x.potency)) for x in self.entries.values() if not x.fixed_power)

    def snapshot(self) -> Dict[str, Dict[str, int | bool]]:
        return {
            k: {
                "count": int(v.count),
                "potency": int(v.potency),
                "fixed_power": bool(v.fixed_power),
            }
            for k, v in self.entries.items()
        }
