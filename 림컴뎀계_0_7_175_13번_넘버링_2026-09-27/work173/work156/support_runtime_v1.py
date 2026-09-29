"""Generic support/assist-action resolver for the one-turn combat runtime.

This module resolves *who* performs a generated support action and *which skill*
it uses.  It deliberately does not calculate damage; ActionQueue/DamageEngine
remain the execution layer.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Iterable, Optional

@dataclass(frozen=True)
class SupportCommand:
    source_identity_id: str
    identity_policy: str = "fixed"
    identity_id: Optional[str] = None
    skill_policy: str = "named"
    skill_name: Optional[str] = None
    trigger_kind: str = "assist"
    target_policy: str = "main"

class SupportActionResolver:
    """Resolve reusable formation-relative support commands.

    Policies are intentionally small and data-driven:
      fixed / ally_left / ally_right / next_available_ally
      named / requested_next / first_attack
    """
    def __init__(self, identities: Iterable[Any], available_identity_ids: Iterable[str]):
        self.identities = list(identities or [])
        self.available_identity_ids = [str(x) for x in (available_identity_ids or [])]

    def _find_identity(self, hint: Any):
        if hint is None:
            return None
        h=str(hint).strip()
        for ident in self.identities:
            if str(getattr(ident, 'id', '')) == h:
                return ident
            names=(getattr(ident,'name',''), getattr(ident,'full_name',''))
            if any(h and h in str(n) for n in names):
                return ident
        return None

    def resolve_identity(self, command: SupportCommand, source_identity_id: Optional[str] = None):
        src=str(source_identity_id or command.source_identity_id)
        policy=str(command.identity_policy or 'fixed')
        if policy == 'fixed':
            return self._find_identity(command.identity_id)
        try:
            pos=self.available_identity_ids.index(src)
        except ValueError:
            return None
        if policy == 'ally_right':
            idx=pos+1
        elif policy == 'ally_left':
            idx=pos-1
        elif policy == 'next_available_ally':
            idx=pos+1
        else:
            return None
        if not (0 <= idx < len(self.available_identity_ids)):
            return None
        return self._find_identity(self.available_identity_ids[idx])

    @staticmethod
    def resolve_skill(target, command: SupportCommand):
        policy=str(command.skill_policy or 'named')
        if policy == 'named':
            hint=str(command.skill_name or '')
            for s in (getattr(target,'skills',{}) or {}).values():
                if hint and hint in str(getattr(s,'name','')):
                    return s
            return None
        skills=list((getattr(target,'skills',{}) or {}).values())
        if policy == 'first_attack':
            for s in skills:
                if str(getattr(s,'_slot','')) in ('S1','S2','S3'):
                    return s
            return None
        if policy == 'requested_next':
            # Placeholder is intentionally resolved by the solver's action-plan
            # bridge. Returning None here keeps this resolver side-effect free.
            return None
        return None

    def resolve(self, command: SupportCommand, source_identity_id: Optional[str] = None):
        target=self.resolve_identity(command, source_identity_id)
        if target is None or str(getattr(target,'id','')) not in self.available_identity_ids:
            return None
        skill=self.resolve_skill(target, command)
        return target, skill


def command_from_effect(effect: dict[str, Any], source_identity_id: str) -> SupportCommand:
    return SupportCommand(
        source_identity_id=str(effect.get('source_identity_id') or source_identity_id),
        identity_policy=str(effect.get('identity_policy','fixed')),
        identity_id=effect.get('identity_id'),
        skill_policy=str(effect.get('skill_policy','named')),
        skill_name=effect.get('skill_name'),
        trigger_kind=str(effect.get('trigger_kind','assist')),
        target_policy=str(effect.get('target_policy','main')),
    )
