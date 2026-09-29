"""Generic formation/affiliation resolver for one-turn combat rules.

This runtime owns only affiliation membership and deterministic selection.  It
never performs damage calculation.  Affiliation modules can therefore express
"same affiliation", "number of members", and "lowest/ordered member" rules
without embedding roster scans in each module.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Iterable, Optional

@dataclass(frozen=True)
class AffiliationMember:
    identity_id: str
    identity: Any
    formation_index: int

class AffiliationResolver:
    def __init__(self, identities: Iterable[Any], available_identity_ids: Iterable[str]):
        self.identities = list(identities or [])
        self.available_identity_ids = [str(x) for x in (available_identity_ids or [])]
        self._by_id = {str(getattr(x, 'id', '')): x for x in self.identities}

    @staticmethod
    def _affiliations(identity: Any) -> set[str]:
        vals = getattr(identity, 'affiliation', []) or []
        if isinstance(vals, str): vals = [vals]
        return {str(x).strip().upper() for x in vals if str(x).strip()}

    def has_affiliation(self, identity_or_id: Any, affiliation: str) -> bool:
        ident = identity_or_id if not isinstance(identity_or_id, str) else self._by_id.get(identity_or_id)
        if ident is None: return False
        wanted = str(affiliation).strip().upper()
        return wanted in self._affiliations(ident)

    def members(self, affiliation: str, *, include_dead: bool = True, state: Any = None,
                exclude_ids: Iterable[str] = ()) -> list[AffiliationMember]:
        excluded = {str(x) for x in (exclude_ids or [])}
        out=[]
        for idx, iid in enumerate(self.available_identity_ids):
            if iid in excluded: continue
            ident=self._by_id.get(iid)
            if ident is None or not self.has_affiliation(ident, affiliation): continue
            if not include_dead and state is not None:
                fighter=getattr(state, 'fighters', {}).get(iid)
                if fighter is not None and float(getattr(fighter, 'hp', 0)) <= 0: continue
            out.append(AffiliationMember(iid, ident, idx))
        return out

    def count(self, affiliation: str, *, include_dead: bool = True, state: Any = None) -> int:
        return len(self.members(affiliation, include_dead=include_dead, state=state))

    def ordered(self, affiliation: str, *, include_dead: bool = True, state: Any = None,
                exclude_ids: Iterable[str] = ()) -> list[AffiliationMember]:
        return self.members(affiliation, include_dead=include_dead, state=state, exclude_ids=exclude_ids)

    def select_lowest(self, affiliation: str, value_fn, *, include_dead: bool = True,
                      state: Any = None, exclude_ids: Iterable[str] = ()) -> Optional[AffiliationMember]:
        members=self.members(affiliation, include_dead=include_dead, state=state, exclude_ids=exclude_ids)
        if not members: return None
        return min(members, key=lambda m: (float(value_fn(m.identity, m.identity_id)), m.formation_index))

    def select_lowest_n(self, affiliation: str, n: int, value_fn, *, include_dead: bool = True,
                        state: Any = None, exclude_ids: Iterable[str] = ()) -> list[AffiliationMember]:
        if n <= 0: return []
        members=self.members(affiliation, include_dead=include_dead, state=state, exclude_ids=exclude_ids)
        members.sort(key=lambda m: (float(value_fn(m.identity, m.identity_id)), m.formation_index))
        return members[:n]
