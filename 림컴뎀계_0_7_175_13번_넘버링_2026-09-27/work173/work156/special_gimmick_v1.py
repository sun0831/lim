"""High-impact special-gimmick layer for the one-turn calculator.

This module intentionally sits beside the generic passive compiler.  Mechanics
such as assist/follow-up attacks, percentage-of-hit extra damage, and skill
transformation are not ordinary stat modifiers: they create/replace actions or
spawn secondary damage.  Keeping them here prevents the canonical Value/
Condition/Effect compiler from becoming a pile of identity-specific branches.
"""
from __future__ import annotations
from dataclasses import dataclass, field
import re
from typing import Any, Optional

@dataclass
class GimmickAction:
    identity_id: str
    skill_id: str
    source: str
    reason: str
    damage_scale: float = 1.0
    target_mode: str = "main"
    forced_faces: Optional[list[str]] = None

@dataclass
class GimmickRule:
    owner_id: str
    source_text: str
    kind: str
    trigger_skill_name: Optional[str] = None
    actor_hint: Optional[str] = None
    skill_hint: Optional[str] = None
    once_per_turn: bool = True
    max_activations: int = 1
    activations: int = 0
    extra_scale: float = 0.0
    target_status: Optional[str] = None

    def reset_turn(self):
        self.activations = 0

    def eligible(self):
        return self.activations < self.max_activations

class GimmickRegistry:
    def __init__(self, identities, active_passives=None, available_identity_ids=None):
        self.identities = list(identities)
        self.active_passives = active_passives or {}
        self.available_identity_ids = set(str(x) for x in (available_identity_ids or [getattr(i, 'id', '') for i in self.identities]))
        self.rules: list[GimmickRule] = []
        self._seen_sources=set()
        self._compile()

    def _find_identity(self, hint: str):
        h = hint.replace(' ', '')
        # Longest textual match first.  This handles phrases such as
        # '가주 후보 이스마엘' against the catalog fullName.
        cand=[]
        for x in self.identities:
            for n in (getattr(x,'name',''), getattr(x,'full_name','')):
                if n and n.replace(' ','') in h or h in str(n).replace(' ',''):
                    cand.append(x); break
        return sorted(cand,key=lambda x:len(getattr(x,'name','')),reverse=True)[0] if cand else None

    def _find_skill(self, ident, hint: str):
        if not ident: return None
        h=hint.strip("'\"“”‘’ ")
        for s in ident.skills.values():
            if h in str(s.name): return s
        return None

    def _compile(self):
        # Assist/follow-up attack.  Example: "A 사용 후 B가 C 스킬로 원호 공격함 (턴 당 1회)".
        pat=re.compile(r"['‘’\"]?([^'‘’\"]+)['‘’\"]?\s*사용\s*후\s+(.+?)(?:가|이)\s+([^\s]+)\s*스킬로\s*원호\s*공격함(?:\s*\(턴\s*당\s*(\d+)회\))?")
        # Percentage-of-the-last-coin extra damage is another recurring special
        # gimmick (e.g. "해당 코인의 공격으로 입힌 피해량의 50%").
        pct_pat=re.compile(r"마지막\s*탄환.*?추가\s*피해.*?(\d+(?:\.\d+)?)%|입힌\s*피해량의\s*(\d+(?:\.\d+)?)%\s*만큼\s*추가\s*피해")
        for owner in self.identities:
            for p in self.active_passives.get(owner.id, getattr(owner,'passives',[])) or []:
                text=str(p.get('effect',''))
                for clause in re.split(r'\n+|\|',text):
                    m=pat.search(clause)
                    if m:
                        source_key=(owner.id, clause.strip())
                        if source_key in self._seen_sources: continue
                        self._seen_sources.add(source_key)
                        trigger,actor,skill,limit=m.groups()
                        target=self._find_identity(actor)
                        if target and self._find_skill(target,skill):
                            self.rules.append(GimmickRule(owner.id,clause,'assist',trigger,actor,skill,True,int(limit or 1)))
                            continue
                    m=pct_pat.search(clause)
                    if m:
                        pct=float(m.group(1) or m.group(2) or 0)/100
                        source_key=(owner.id, clause.strip())
                        if pct and source_key not in self._seen_sources:
                            self._seen_sources.add(source_key)
                            self.rules.append(GimmickRule(owner.id,clause,'extra_damage',extra_scale=pct))

    def reset_turn(self):
        for r in self.rules: r.reset_turn()

    def after_skill(self, identity, skill):
        out=[]
        for r in self.rules:
            if not r.eligible() or r.kind!='assist': continue
            if r.trigger_skill_name and r.trigger_skill_name.strip("'\"“”‘’ ") not in str(skill.name): continue
            target=self._find_identity(r.actor_hint or '')
            if not target or str(target.id) not in self.available_identity_ids: continue
            s=self._find_skill(target,r.skill_hint or '')
            if not s: continue
            r.activations += 1
            out.append(GimmickAction(target.id,s.id,r.source_text,'assist'))
        return out

    def extra_damage_scale_after_hit(self, state, action_identity_id, skill, coin_index):
        # Deliberately only activates rules whose source explicitly contains
        # "추가 피해".  This avoids interpreting ordinary damage percentages as
        # secondary damage.
        return sum(r.extra_scale for r in self.rules if r.kind=='extra_damage' and r.eligible())

    def summary(self):
        return {'total_rules': len(self.rules), 'assist_rules': sum(r.kind == 'assist' for r in self.rules)}

    def after_coin(self, state, identity, skill, coin_index, actual_damage, ammo_before, ammo_after, ammo_spent):
        """Apply high-confidence secondary-damage gimmicks after a coin.

        Current catalog example: LCCB 료슈's 마지막 탄환 50% 추가 피해.  We
        implement the mechanical core only when the selected attacker is the
        lowest-ammo ally at action start and the coin actually spent the final
        ammo.  This avoids turning unrelated "추가 피해" prose into damage.
        """
        if ammo_spent <= 0 or ammo_before <= 0 or ammo_after != 0 or actual_damage <= 0:
            return 0
        if state.runtime.get('ammo_min_identity') != identity.id:
            return 0
        scale=sum(r.extra_scale for r in self.rules if r.kind=='extra_damage' and r.eligible())
        if not scale: return 0
        extra=int(actual_damage*scale + 0.5)
        extra=min(extra,state.enemy.hp)
        state.enemy.hp-=extra; state.turn_damage+=extra
        target_id = state.runtime.get('current_target_id', 'main')
        state.event_log.append({'event':'gimmick_extra_damage','source':'last_ammo_extra_damage',
                                'identity_id':identity.id,'skill_id':skill.id,'coin':coin_index,
                                'target_id':str(target_id), 'base_damage':actual_damage,
                                'scale':scale,'extra_damage':extra,
                                'enemy_hp_after':state.enemy.hp})
        return extra
