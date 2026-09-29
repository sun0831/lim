from __future__ import annotations
from dataclasses import dataclass, field
from amplitude_runtime_v1 import AmplitudeRuntime
from enum import Enum
from typing import Any, Optional
from copy import deepcopy

class PassiveTrigger(str, Enum):
    TREMOR_BURST='TremorBurst'; TREMOR_BURST_RESOLVED='TremorBurstResolved'; ENCOUNTER_START='EncounterStart'; COMBAT_START='CombatStart'; TURN_START='TurnStart'; BEFORE_USE='BeforeUse'; ON_USE='OnUse'; SKILL_START='SkillStart'; CLASH_START='ClashStart'; CLASH_WIN='ClashWin'; CLASH_LOSE='ClashLose'; COIN_START='CoinStart'; COIN_ROLL='CoinRoll'; COIN_HIT='CoinHit'; HEADS_HIT='HeadsHit'; TAILS_HIT='TailsHit'; HIT='Hit'; DAMAGE='Damage'; STAGGER_CHECK='StaggerCheck'; STAGGER='Stagger'; SKILL_END='SkillEnd'; ATTACK_END='AttackEnd'; ON_KILL='OnKill'; UNIT_DEATH='UnitDeath'; TURN_END='TurnEnd'; COMBAT_END='CombatEnd'; BEFORE_ATTACK='BeforeAttack'; UNOPPOSED='OnUnopposedAttack'; HIT_AFTER_CLASH_WIN='HitAfterClashWin'

@dataclass(frozen=True)
class PassiveEvent:
    trigger: PassiveTrigger
    ctx: dict[str, Any]

class Value:
    def resolve(self,event,state,owner_id): raise NotImplementedError

@dataclass(frozen=True)
class TremorBurstCount(Value):
    def resolve(self,event,state,owner_id):
        return int(state.runtime.get('tremor_burst_counts', {}).get(str(owner_id), 0))

@dataclass(frozen=True)
class ConsumedChargeValue(Value):
    """Amount actually consumed by the immediately preceding ConsumeCharge effect."""
    def resolve(self,event,state,owner_id):
        return int(event.ctx.get('consumed_charge', 0))
@dataclass(frozen=True)
class Const(Value):
    value: float
    def resolve(self,event,state,owner_id): return self.value
@dataclass(frozen=True)
class MaxOfResonanceValue(Value):
    """Maximum resonance count among a source-backed set of Sin attributes."""
    sins: tuple[str, ...]
    absolute: bool = False
    def resolve(self,event,state,owner_id):
        table=state.runtime.get('current_absolute_resonance' if self.absolute else 'current_resonance',{}) or {}
        return max((int(table.get(s,0)) for s in self.sins), default=0)

@dataclass(frozen=True)
class ResonanceValue(Value):
    """Resolve a resonance count from the current selected-action runtime."""
    scope: str = 'current'
    sin: str | None = None
    absolute: bool = False
    def resolve(self,event,state,owner_id):
        skill=event.ctx.get("skill")
        sin=self.sin or (str(getattr(skill,"sin","")) if skill is not None else "")
        if self.scope == 'current':
            table=state.runtime.get('current_absolute_resonance' if self.absolute else 'current_resonance',{}) or {}
            return int(table.get(sin,0))
        if self.scope == 'max':
            return int(state.runtime.get('current_max_absolute_resonance_count' if self.absolute else 'current_max_resonance_count',0))
        if self.scope == 'max_sin':
            key='turn_absolute_resonance_by_sin' if self.absolute else 'turn_max_resonance_by_sin'
            table=state.runtime.get(key,{}) or {}
            return int(table.get(sin,0))
        return 0

@dataclass(frozen=True)
class ContextValue(Value):
    key: str; default: float=0
    def resolve(self,event,state,owner_id): return event.ctx.get(self.key,self.default)
@dataclass(frozen=True)
class UnitValue(Value):
    field: str; target: str='self'
    def resolve(self,event,state,owner_id):
        u = resolve_unit(self.target,event,state,owner_id)
        return getattr(u,self.field,0) if u else 0
@dataclass(frozen=True)
class StatusValue(Value):
    name: str; field: str='potency'; target: str='enemy'
    def resolve(self,event,state,owner_id):
        u=resolve_unit(self.target,event,state,owner_id)
        st=getattr(u,'statuses',{}).get(self.name) if u else None
        return getattr(st,self.field,0) if st else 0
@dataclass(frozen=True)
class ResourceValue(Value):
    name: str
    def resolve(self,event,state,owner_id): return state.fighters[owner_id].sin_resources.get(self.name,0)
@dataclass(frozen=True)
class FloorValue(Value):
    inner: Value
    def resolve(self,event,state,owner_id):
        import math
        return math.floor(float(self.inner.resolve(event,state,owner_id)))

@dataclass(frozen=True)
class BinaryValue(Value):
    left: Value; op: str; right: Value
    def resolve(self,event,state,owner_id):
        a,b=self.left.resolve(event,state,owner_id),self.right.resolve(event,state,owner_id)
        return {'+':a+b,'-':a-b,'*':a*b,'/':a/b if b else 0}.get(self.op,0)

def resolve_unit(kind,event,state,owner_id):
    if kind=='self': return state.fighters.get(owner_id)
    if kind in ('enemy','target'):
        if kind=='target' and event.ctx.get('target') is not None: return event.ctx['target']
        return state.enemy
    if kind in ('attacker','source'):
        return event.ctx.get('attacker') or state.fighters.get(owner_id)
    if kind=='event_target': return event.ctx.get('target')
    return state.fighters.get(owner_id)

class Condition:
    def check(self,event,state,owner_id): raise NotImplementedError
@dataclass(frozen=True)
class Always(Condition):
    def check(self,event,state,owner_id): return True
@dataclass(frozen=True)
class EventFlag(Condition):
    key:str; expected:Any=True
    def check(self,event,state,owner_id): return event.ctx.get(self.key)==self.expected
@dataclass(frozen=True)
class ContextCompare(Condition):
    key:str; op:str; value:Any
    def check(self,event,state,owner_id):
        a=event.ctx.get(self.key)
        if self.op=='eq': return a==self.value
        if self.op=='neq': return a!=self.value
        try:
            return {'gte':a>=self.value,'gt':a>self.value,'lte':a<=self.value,'lt':a<self.value}[self.op]
        except TypeError:return False
@dataclass(frozen=True)
class SelfSPAtMost(Condition):
    value: int
    def check(self, event, state, owner_id):
        u = resolve_unit('self', event, state, owner_id)
        return u is not None and int(getattr(u, 'sp', 0)) <= self.value

@dataclass(frozen=True)
class CoinPolarityIs(Condition):
    polarity: str
    def check(self, event, state, owner_id):
        coin = event.ctx.get('coin') if event else None
        if coin is None:
            return str(event.ctx.get('coin_type', '')) == self.polarity if event else False
        return str(getattr(coin, 'coin_type', '')) == self.polarity

@dataclass(frozen=True)
class DefenseSkillUsedThisTurn(Condition):
    """True when the specified unit has used a defense skill this turn.

    The one-turn engine records this as turn-scoped runtime state.  Scenario
    imports may seed the same flag when an enemy action occurred outside the
    calculator's action queue.
    """
    target: str = 'enemy'
    def check(self, event, state, owner_id):
        if self.target == 'enemy':
            return bool(state.runtime.get('turn_defense_skill_used_enemy', False)) or bool(
                state.runtime.get('condition_flags', {}).get('enemy_used_defense_this_turn', False)
            )
        u = resolve_unit(self.target, event, state, owner_id)
        uid = str(getattr(u, 'id', self.target)) if u is not None else str(self.target)
        return uid in set(state.runtime.get('turn_defense_skill_used_ids', set()))


@dataclass(frozen=True)
class TargetMaxHPAtAttackStart(Condition):
    """True at BEFORE_ATTACK when the target is at full HP."""
    target: str = 'enemy'
    def check(self, event, state, owner_id):
        u = resolve_unit(self.target, event, state, owner_id)
        if u is None:
            return False
        hp = float(getattr(u, 'hp', 0))
        mx = float(getattr(u, 'max_hp', 0))
        return mx > 0 and hp >= mx


@dataclass(frozen=True)
class TargetHasSP(Condition):
    """Whether the current target has a sanity/mental-power field."""
    target: str = 'enemy'
    def check(self, event, state, owner_id):
        u = resolve_unit(self.target, event, state, owner_id)
        return u is not None and getattr(u, 'sp', None) is not None

@dataclass(frozen=True)
class TargetDeadCondition(Condition):
    """True when the attack-end context says the attack target died.

    This is deliberately event-context based: at ATTACK_END the active
    ``state.enemy`` may already have been restored after multi-target
    resolution, so reading the current enemy HP is not a reliable causal
    record of whether the attack target died.
    """
    def check(self,event,state,owner_id):
        return bool(event.ctx.get("attack_target_dead", False))

@dataclass(frozen=True)
class HpPercent(Condition):
    value:float; op:str='lte'; target:str='enemy'
    def check(self,event,state,owner_id):
        u=resolve_unit(self.target,event,state,owner_id); mx=getattr(u,'max_hp',0) if u else 0; hp=getattr(u,'hp',0) if u else 0
        if not mx:return False
        x=hp/mx*100
        return {'lte':x<=self.value,'lt':x<self.value,'gte':x>=self.value,'gt':x>self.value}.get(self.op,False)
@dataclass(frozen=True)
class StatusThreshold(Condition):
    name:str; value:int; field:str='potency'; target:str='enemy'; op:str='gte'
    def check(self,event,state,owner_id):
        u=resolve_unit(self.target,event,state,owner_id); st=getattr(u,'statuses',{}).get(self.name) if u else None; x=getattr(st,self.field,0) if st else 0
        return {'gte':x>=self.value,'gt':x>self.value,'lte':x<=self.value,'lt':x<self.value,'eq':x==self.value}.get(self.op,False)
@dataclass(frozen=True)
class StatusPairThreshold(Condition):
    """Require a status potency/count pair on the same target.

    Source form: `대상의 파열이 15, 파열 횟수가 3 이상이면`.
    Both thresholds are conjunctive; neither may be silently dropped.
    """
    name: str
    potency: int
    count: int
    target: str = 'enemy'
    def check(self,event,state,owner_id):
        u=resolve_unit(self.target,event,state,owner_id)
        st=getattr(u,'statuses',{}).get(self.name) if u else None
        p=int(getattr(st,'potency',0)) if st else 0
        c=int(getattr(st,'count',0)) if st else 0
        return p >= self.potency and c >= self.count

@dataclass(frozen=True)
class StatusSumThreshold(Condition):
    """Sum two status potencies on the same target and compare to a threshold."""
    name_a: str
    name_b: str
    value: int
    target: str = 'enemy'
    op: str = 'gte'
    def check(self,event,state,owner_id):
        u=resolve_unit(self.target,event,state,owner_id)
        sts=getattr(u,'statuses',{}) if u else {}
        a=sts.get(self.name_a); b=sts.get(self.name_b)
        x=(int(getattr(a,'potency',0)) if a else 0)+(int(getattr(b,'potency',0)) if b else 0)
        return {'gte':x>=self.value,'gt':x>self.value,'lte':x<=self.value,'lt':x<self.value,'eq':x==self.value}.get(self.op,False)

@dataclass(frozen=True)
class CrossResourceStatusSumThreshold(Condition):
    """Sum one named self resource and one enemy status potency.

    Source form: `자신의 완성되어가는 교본과 메인 타겟 적의 결투 고조
    수치 합 ...`.  This is intentionally a condition primitive rather than
    an identity-specific rule so thresholded child effects can share it.
    """
    resource_name: str
    status_name: str
    value: int
    target: str = 'enemy'
    op: str = 'gte'
    def check(self,event,state,owner_id):
        u = state.fighters.get(owner_id)
        v = resolve_unit(self.target,event,state,owner_id)
        rs = int(getattr(u,'resources',{}).get(self.resource_name,0)) if u else 0
        if self.resource_name == '충전': rs = int(getattr(u,'charge',0)) if u else 0
        elif self.resource_name == '충전 위력': rs = int(getattr(u,'charge_potency',0)) if u else 0
        elif self.resource_name == '탄환': rs = int(getattr(u,'ammo',0)) if u else 0
        elif self.resource_name == '호흡': rs = int(getattr(getattr(u,'poise',None),'potency',0)) if u else 0
        st = getattr(v,'statuses',{}).get(self.status_name) if v else None
        total = rs + (int(getattr(st,'potency',0)) if st else 0)
        return {'gte':total>=self.value,'gt':total>self.value,'lte':total<=self.value,'lt':total<self.value,'eq':total==self.value}.get(self.op,False)

@dataclass(frozen=True)
class CrossStatusSumThreshold(Condition):
    """Sum status potencies across two explicit unit scopes."""
    name_a: str
    target_a: str
    name_b: str
    target_b: str
    value: int
    op: str = 'gte'
    def check(self,event,state,owner_id):
        ua=resolve_unit(self.target_a,event,state,owner_id); ub=resolve_unit(self.target_b,event,state,owner_id)
        sa=getattr(ua,'statuses',{}).get(self.name_a) if ua else None
        sb=getattr(ub,'statuses',{}).get(self.name_b) if ub else None
        x=(int(getattr(sa,'potency',0)) if sa else 0)+(int(getattr(sb,'potency',0)) if sb else 0)
        return {'gte':x>=self.value,'gt':x>self.value,'lte':x<=self.value,'lt':x<self.value,'eq':x==self.value}.get(self.op,False)

@dataclass(frozen=True)
class SpeedSumThreshold(Condition):
    value: int
    target: str = 'enemy'
    op: str = 'gte'
    def check(self,event,state,owner_id):
        a=state.fighters.get(owner_id)
        b=resolve_unit(self.target,event,state,owner_id)
        if a is None or b is None: return False
        x=float(getattr(a,'speed',0))+float(getattr(b,'speed',0))
        return {'gte':x>=self.value,'gt':x>self.value,'lte':x<=self.value,'lt':x<self.value,'eq':x==self.value}.get(self.op,False)

@dataclass(frozen=True)
class TremorSumThreshold(Condition):
    value: int
    target: str = 'enemy'
    op: str = 'gte'
    def check(self,event,state,owner_id):
        u=resolve_unit(self.target,event,state,owner_id)
        st=getattr(u,'statuses',{}).get('Tremor') if u else None
        x=int(getattr(st,'potency',0))+int(getattr(st,'count',0)) if st else 0
        return {'gte':x>=self.value,'gt':x>self.value,'lte':x<=self.value,'lt':x<self.value,'eq':x==self.value}.get(self.op,False)

@dataclass(frozen=True)
class ResourceThreshold(Condition):
    name:str; value:int; op:str='gte'
    def check(self,event,state,owner_id):
        x=state.fighters[owner_id].sin_resources.get(self.name,0); return {'gte':x>=self.value,'gt':x>self.value,'lte':x<=self.value,'lt':x<self.value,'eq':x==self.value}.get(self.op,False)
def _rank_condition_value(f, policy: str):
    """Return the comparable value used by actor/ally rank conditions."""
    p = str(policy)
    if p.startswith('speed_'): return float(getattr(f,'speed',0))
    if p.startswith('hp_percent_'): return float(getattr(f,'hp',0))/max(float(getattr(f,'max_hp',1)),1.0)
    if p.startswith('hp_'): return float(getattr(f,'hp',0))
    if p.startswith('max_hp_'): return float(getattr(f,'max_hp',0))
    if p.startswith('charge_'): return float(getattr(f,'charge',0))
    if p.startswith('ammo_'): return float(getattr(f,'ammo',0))
    if p.startswith('poise_count_'): return float(getattr(getattr(f,'poise',None),'count',0))
    if p.startswith('status_count_'):
        name=p.split('_',2)[2]
        st=getattr(f,'statuses',{}).get(name)
        return float(getattr(st,'count',0)) if st is not None else 0.0
    if p.startswith('highest_status_count:') or p.startswith('lowest_status_count:'):
        name=p.split(':',1)[1]
        sts=getattr(f,'statuses',{}) or {}
        st=sts.get(name)
        if st is None:
            st=next((v for k,v in sts.items() if str(k).lower()==name.lower()),None)
        return float(getattr(st,'count',0)) if st is not None else 0.0
    if p.startswith('sp_'): return float(getattr(f,'sp',0))
    return 0.0

@dataclass(frozen=True)
class ActorRankCondition(Condition):
    """True when the actor that caused the current event is at the requested roster rank.

    Unlike AllyRankCondition, this deliberately resolves against event.ctx['identity']
    (or source_id) so event-driven rules such as "the slowest ally's Tremor Burst"
    constrain the Burst source rather than the passive owner.
    """
    policy: str
    def check(self,event,state,owner_id):
        actor_id = event.ctx.get('identity', event.ctx.get('source_id', owner_id)) if event else owner_id
        fighters=[]
        for fid,f in state.fighters.items():
            if float(getattr(f,'hp',0))<=0: continue
            fighters.append((str(fid),f))
        actor=state.fighters.get(actor_id) if actor_id is not None else None
        if actor is None or not fighters: return False
        value=lambda f: _rank_condition_value(f, self.policy)
        vals=[value(f) for _,f in fighters]; av=value(actor)
        if self.policy.endswith('_max') or self.policy.startswith('highest_status_count:'): return av >= max(vals)
        return av <= min(vals)

@dataclass(frozen=True)
class LowestAllySPDecreasedThisTurnCondition(Condition):
    """True when the currently lowest-SP living ally lost SP this turn.

    Source-backed support condition: the selected lowest-SP ally must have
    actually lost SP during the current turn; merely being the lowest-SP ally
    is not sufficient.
    """
    def check(self,event,state,owner_id):
        fighters=[(str(fid),f) for fid,f in state.fighters.items() if float(getattr(f,'hp',0))>0]
        if not fighters:
            return False
        lowest_id, lowest=min(fighters, key=lambda x: (float(getattr(x[1],'sp',0)),
                                                        int(getattr(x[1],'formation_index',0)),
                                                        x[0]))
        for ev in getattr(state,'event_log',[]) or []:
            if ev.get('event') != 'sp_change':
                continue
            if str(ev.get('identity_id', ev.get('source_id', ''))) != lowest_id:
                continue
            try:
                if float(ev.get('delta',0)) < 0:
                    return True
            except (TypeError,ValueError):
                continue
        return False

@dataclass(frozen=True)
class RosterPositionCondition(Condition):
    """True when the passive owner occupies the requested 1-based lineup slot."""
    position: int = 1
    def check(self,event,state,owner_id):
        order = state.runtime.get('roster_order') if getattr(state, 'runtime', None) is not None else None
        if not order:
            order = list(getattr(state, 'fighters', {}).keys())
        try:
            return str(order[int(self.position) - 1]) == str(owner_id)
        except (IndexError, TypeError, ValueError):
            return False

@dataclass(frozen=True)
class AllyRankCondition(Condition):
    """True when the owner is tied for the requested rank among living allies."""
    policy: str
    exclude_owner: bool = False
    def check(self,event,state,owner_id):
        if self.exclude_owner: return False
        fighters=[]
        for fid,f in state.fighters.items():
            if float(getattr(f,'hp',0))<=0: continue
            fighters.append((str(fid),f))
        own=state.fighters.get(owner_id)
        if own is None or not fighters: return False
        value=lambda f: _rank_condition_value(f, self.policy)
        vals=[value(f) for _,f in fighters]; ov=value(own)
        if self.policy.endswith('_max') or self.policy.startswith('highest_status_count:'): return ov >= max(vals)
        return ov <= min(vals)

@dataclass(frozen=True)
class SpeedAtLeast(Condition):
    value:int
    def check(self,event,state,owner_id): return state.fighters[owner_id].speed>=self.value
@dataclass(frozen=True)
class ChargeAtLeast(Condition):
    value:int
    def check(self,event,state,owner_id): return state.fighters[owner_id].charge>=self.value
@dataclass(frozen=True)
class AmmoAtLeast(Condition):
    value:int
    def check(self,event,state,owner_id): return state.fighters[owner_id].ammo>=self.value
@dataclass(frozen=True)
class ResourceAtLeast(Condition):
    """Generic named-resource threshold from source text (e.g. `눈물 벼리기 3개 보유`)."""
    name: str
    value: int
    target: str = 'self'
    def check(self,event,state,owner_id):
        u = resolve_unit(self.target,event,state,owner_id)
        if u is None: return False
        if self.name == '충전': current = int(getattr(u,'charge',0))
        elif self.name == '충전 위력': current = int(getattr(u,'charge_potency',0))
        elif self.name == '탄환': current = int(getattr(u,'ammo',0))
        elif self.name == '호흡': current = int(getattr(getattr(u,'poise',None),'potency',0))
        else: current = int(getattr(u,'resources',{}).get(self.name,0))
        return current >= self.value
@dataclass(frozen=True)
class PoiseAtLeast(Condition):
    value:int; field:str='count'
    def check(self,event,state,owner_id): return getattr(state.fighters[owner_id].poise,self.field,0)>=self.value
@dataclass(frozen=True)
class StatusAtLeast(Condition):
    name: str; value: int; target: str='enemy'
    def check(self,event,state,owner_id):
        u=resolve_unit(self.target,event,state,owner_id)
        st=getattr(u,'statuses',{}).get(self.name) if u else None
        return int(getattr(st,'potency',0)) >= self.value if st else False

@dataclass(frozen=True)
class TargetCountAtLeast(Condition):
    value: int
    def check(self,event,state,owner_id):
        return int(event.ctx.get("target_count", state.runtime.get("current_target_count", 1))) >= self.value

@dataclass(frozen=True)
class BasicAttackSkillCondition(Condition):
    """True for the three basic attack skill slots (S1/S2/S3)."""
    def check(self,event,state,owner_id):
        skill = event.ctx.get('skill') if event else None
        sid = str(getattr(skill, 'id', '')) if skill is not None else ''
        slot = str(event.ctx.get('skill_slot', '')) if event else ''
        return slot in {'S1','S2','S3'} or bool(sid and sid[-1:] in {'1','2','3'} and sid[-1:] != '5')

@dataclass(frozen=True)
class IdentityDeadCondition(Condition):
    identity_id: str
    def check(self,event,state,owner_id):
        wanted = str(self.identity_id)
        for fid, fighter in getattr(state, 'fighters', {}).items():
            if str(getattr(fighter, 'identity_id', fid)) != wanted:
                continue
            return float(getattr(fighter, 'hp', 0)) <= 0
        return False

@dataclass(frozen=True)
class SkillCondition(Condition):
    """Match the currently executing skill by number/name/id fragment."""
    number: Optional[int] = None
    name: Optional[str] = None
    id_fragment: Optional[str] = None
    def check(self,event,state,owner_id):
        skill=event.ctx.get("skill")
        if skill is None: return False
        if self.number is not None:
            sid=str(getattr(skill,"id",""))
            # Catalog skill ids conventionally end in 1/2/3 (defense is 5).
            if not sid or not sid[-1].isdigit() or int(sid[-1]) != self.number: return False
        if self.name is not None and self.name not in str(getattr(skill,"name","")): return False
        if self.id_fragment is not None and self.id_fragment not in str(getattr(skill,"id","")): return False
        return True

@dataclass(frozen=True)
class SpeedDifferenceAtLeast(Condition):
    value: int
    direction: str = 'higher'
    def check(self,event,state,owner_id):
        f=state.fighters.get(owner_id); e=state.enemy
        if f is None: return False
        diff=int(getattr(f,'speed',0))-int(getattr(e,'speed',0))
        return diff >= self.value if self.direction=='higher' else diff <= self.value

@dataclass(frozen=True)
class SpeedRelation(Condition):
    relation: str  # faster / slower / equal
    def check(self,event,state,owner_id):
        self_u=state.fighters.get(owner_id); enemy=state.enemy
        if self_u is None: return False
        a=int(getattr(self_u,"speed",0)); b=int(getattr(enemy,"speed",0))
        return {"faster":a>b,"slower":a<b,"equal":a==b}.get(self.relation,False)

@dataclass(frozen=True)
class AttackTypeIs(Condition):
    value: str
    def check(self,event,state,owner_id):
        skill=event.ctx.get("skill")
        return skill is not None and str(getattr(skill,"attack_type","")) == self.value

@dataclass(frozen=True)
class CoinIndexIs(Condition):
    value: int
    def check(self,event,state,owner_id):
        return int(event.ctx.get("coin_index",0)) == self.value

@dataclass(frozen=True)
class TargetWeakToAttackType(Condition):
    """True when the current attack hits a target with physical resistance > 1.5."""
    threshold: float = 1.5
    def check(self,event,state,owner_id):
        skill=event.ctx.get("skill")
        if skill is None: return False
        atk=str(getattr(skill,"attack_type",""))
        return float(getattr(state.enemy,"physical_res",{}).get(atk,1.0)) > self.threshold

@dataclass(frozen=True)
class IsCrit(Condition):
    def check(self,event,state,owner_id): return bool(event.ctx.get('is_crit', False))

@dataclass(frozen=True)
class AllAlliesFasterThanEnemy(Condition):
    def check(self,event,state,owner_id):
        if not state.fighters: return False
        e=int(getattr(state.enemy,'speed',0))
        return all(int(getattr(f,'speed',0)) > e for f in state.fighters.values())

@dataclass(frozen=True)
class SinIs(Condition):
    value: str
    def check(self,event,state,owner_id):
        skill=event.ctx.get("skill")
        return skill is not None and str(getattr(skill,"sin","")) == self.value

@dataclass(frozen=True)
class CurrentResonanceAtLeast(Condition):
    value: int
    sin: str | None = None
    def check(self,event,state,owner_id):
        skill=event.ctx.get("skill")
        sin=self.sin or (str(getattr(skill,"sin","")) if skill is not None else "")
        return int(state.runtime.get("current_resonance",{}).get(sin,0)) >= int(self.value)

@dataclass(frozen=True)
class CurrentAbsoluteResonanceAtLeast(Condition):
    value: int
    sin: str | None = None
    def check(self,event,state,owner_id):
        skill=event.ctx.get("skill")
        sin=self.sin or (str(getattr(skill,"sin","")) if skill is not None else "")
        return int(state.runtime.get("current_absolute_resonance",{}).get(sin,0)) >= int(self.value)

@dataclass(frozen=True)
class MaxResonanceIs(Condition):
    sin: str
    absolute: bool = False
    value: int = 1
    def check(self,event,state,owner_id):
        key='current_max_absolute_resonance_count' if self.absolute else 'current_max_resonance_count'
        max_count=int(state.runtime.get(key,0))
        if max_count < int(self.value):
            return False
        max_sin=state.runtime.get('current_max_absolute_resonance_sin' if self.absolute else 'current_max_resonance_sin')
        return str(max_sin or '') == self.sin

@dataclass(frozen=True)
class MaxAbsoluteResonanceAtLeast(Condition):
    value: int
    sin: str | None = None
    def check(self,event,state,owner_id):
        if self.sin:
            return int(state.runtime.get("turn_absolute_resonance_by_sin",{}).get(self.sin,0)) >= int(self.value)
        return int(state.runtime.get("turn_max_absolute_resonance_count",0)) >= int(self.value)

@dataclass(frozen=True)
class AbsoluteResonanceSumAtLeast(Condition):
    value: int
    sin: str | None = None
    def check(self,event,state,owner_id):
        if self.sin:
            return int(state.runtime.get("turn_absolute_resonance_by_sin",{}).get(self.sin,0)) >= int(self.value)
        return int(state.runtime.get("turn_absolute_resonance_sum",0)) >= int(self.value)

@dataclass(frozen=True)
class HasAbsoluteResonance(Condition):
    sin: str | None = None
    def check(self,event,state,owner_id):
        if self.sin:
            return int(state.runtime.get("turn_absolute_resonance_by_sin",{}).get(self.sin,0)) >= 3
        return bool(state.runtime.get("turn_absolute_resonance_sum",0))

@dataclass(frozen=True)
class HasStatus(Condition):
    name:str; target:str='self'
    def check(self,event,state,owner_id): return self.name in getattr(resolve_unit(self.target,event,state,owner_id),'statuses',{})

@dataclass(frozen=True)
class HasShield(Condition):
    """Canonical shield-presence predicate; Shield is a numeric FighterState field, not a status entry."""
    target:str='self'
    def check(self,event,state,owner_id):
        u=resolve_unit(self.target,event,state,owner_id)
        return u is not None and float(getattr(u,'shield',0.0)) > 0

@dataclass(frozen=True)
class AmplitudePotencyThreshold(Condition):
    """Check the Tremor potency snapshot carried by a named Amplitude state."""
    amplitude: str
    value: int
    target: str = 'enemy'
    op: str = 'gte'
    def check(self,event,state,owner_id):
        u=resolve_unit(self.target,event,state,owner_id)
        if u is None:
            return False
        from amplitude_runtime_v1 import AmplitudeRuntime
        entries = AmplitudeRuntime().get_states(u)
        for entry in entries:
            if not isinstance(entry,dict):
                continue
            names=entry.get('amplitudes',[entry.get('amplitude')]) if entry.get('mode') == 'entanglement' else [entry.get('amplitude')]
            if self.amplitude not in {str(x) for x in names}:
                continue
            x=int(entry.get('tremor_potency',0))
            return {'gte':x>=self.value,'gt':x>self.value,'lte':x<=self.value,'lt':x<self.value,'eq':x==self.value}.get(self.op,False)
        return False

@dataclass(frozen=True)
class HasAmplitudeState(Condition):
    """Query common amplitude state without assuming conversion/entanglement are mutually exclusive."""
    target: str = 'enemy'
    amplitude: Optional[str] = None
    mode: Optional[str] = None
    def check(self,event,state,owner_id):
        u=resolve_unit(self.target,event,state,owner_id)
        if u is None: return False
        from amplitude_runtime_v1 import AmplitudeRuntime
        entries = AmplitudeRuntime().get_states(u)
        if not entries: return False
        for entry in entries:
            if not isinstance(entry, dict):
                continue
            if str(entry.get('mode','')) not in ('conversion','entanglement'):
                continue
            if self.amplitude is not None and str(entry.get('amplitude','')) != self.amplitude:
                continue
            if self.mode is not None and str(entry.get('mode','')) != self.mode:
                continue
            return True
        return False
@dataclass(frozen=True)
class And(Condition):
    conditions:tuple[Condition,...]
    def check(self,event,state,owner_id): return all(c.check(event,state,owner_id) for c in self.conditions)
@dataclass(frozen=True)
class Or(Condition):
    conditions:tuple[Condition,...]
    def check(self,event,state,owner_id): return any(c.check(event,state,owner_id) for c in self.conditions)
@dataclass(frozen=True)
class Not(Condition):
    condition:Condition
    def check(self,event,state,owner_id): return not self.condition.check(event,state,owner_id)

class Target:
    def resolve(self,event,state,owner_id): raise NotImplementedError

class AllySelectorTarget(Target):
    def __init__(self, policy: str, count: int = 1, exclude_owner: bool = False):
        self.policy=str(policy); self.count=max(1,int(count)); self.exclude_owner=bool(exclude_owner)
    def resolve(self,event,state,owner_id):
        candidates=[]; order=list(state.fighters.keys())
        for fid,f in state.fighters.items():
            if self.exclude_owner and str(fid)==str(owner_id): continue
            if float(getattr(f,'hp',0))<=0: continue
            candidates.append((str(fid),f))
        if not candidates: return []
        def val(item):
            _,f=item; p=self.policy
            if p.startswith('speed_'): return float(getattr(f,'speed',0))
            if p.startswith('hp_percent_'): return float(getattr(f,'hp',0))/max(float(getattr(f,'max_hp',1)),1.0)
            if p.startswith('hp_'): return float(getattr(f,'hp',0))
            if p.startswith('max_hp_'): return float(getattr(f,'max_hp',0))
            if p.startswith('charge_'): return float(getattr(f,'charge',0))
            if p.startswith('ammo_'): return float(getattr(f,'ammo',0))
            if p.startswith('poise_count_'): return float(getattr(getattr(f,'poise',None),'count',0))
            if p.startswith('status_count_'):
                name=p.split('_',2)[2]
                st=getattr(f,'statuses',{}).get(name)
                return float(getattr(st,'count',0)) if st is not None else 0.0
            if p.startswith('highest_status_count:') or p.startswith('lowest_status_count:'):
                name=p.split(':',1)[1]
                sts=getattr(f,'statuses',{}) or {}
                st=sts.get(name)
                if st is None:
                    st=next((v for k,v in sts.items() if str(k).lower()==name.lower()),None)
                return float(getattr(st,'count',0)) if st is not None else 0.0
            if p.startswith('sp_'): return float(getattr(f,'sp',0))
            return 0.0
        pos={str(fid):int(getattr(f,'formation_index',i)) for i,(fid,f) in enumerate(state.fighters.items())}
        owner=state.fighters.get(owner_id)
        owner_pos=pos.get(str(owner_id), 10**9)
        if self.policy.startswith('status_present_sp_min:') or self.policy.startswith('status_present_sp_max:'):
            name=self.policy.split(':',1)[1]
            def has_status(f):
                sts=getattr(f,'statuses',{}) or {}
                if name in sts: return True
                return any(str(k).lower()==name.lower() for k in sts)
            candidates=[x for x in candidates if has_status(x[1])]
            reverse_rank=self.policy.startswith('status_present_sp_max:')
            candidates.sort(key=lambda x:(pos.get(x[0],10**9),x[0]))
            candidates.sort(key=lambda x:float(getattr(x[1],'sp',0)), reverse=reverse_rank)
            return [f for _,f in candidates[:min(self.count,len(candidates))]]
        if self.policy.startswith('formation_slot:'):
            try: slot=int(self.policy.split(':',1)[1])
            except (TypeError,ValueError): return []
            if slot < 1: return []
            candidates=[x for x in candidates if pos.get(x[0],10**9) == slot]
        elif self.policy == 'charge_positive_min':
            candidates=[x for x in candidates if float(getattr(x[1],'charge',0)) > 0]
            candidates.sort(key=lambda x:(pos.get(x[0],10**9),x[0]))
            candidates.sort(key=lambda x:float(getattr(x[1],'charge',0)))
        elif self.policy in ('poise_potency_max','poise_potency_min','poise_count_max','poise_count_min'):
            key_name = 'potency' if self.policy in ('poise_potency_max','poise_potency_min') else 'count'
            def poise_value(f):
                st=getattr(f,'statuses',{}).get('Poise')
                if st is None: st=getattr(f,'poise',None)
                return float(getattr(st,key_name,0)) if st is not None else 0.0
            reverse_rank=self.policy in ('poise_potency_max','poise_count_max')
            candidates.sort(key=lambda x:(pos.get(x[0],10**9),x[0]))
            candidates.sort(key=lambda x:poise_value(x[1]), reverse=reverse_rank)
        elif self.policy in ('formation_before_owner','formation_after_owner','formation_before_owner_charge_min'):
            if self.policy == 'formation_before_owner':
                candidates=[x for x in candidates if pos.get(x[0],10**9) < owner_pos]
                candidates.sort(key=lambda x:(pos.get(x[0],10**9),x[0]))
            elif self.policy == 'formation_after_owner':
                candidates=[x for x in candidates if pos.get(x[0],10**9) > owner_pos]
                candidates.sort(key=lambda x:(pos.get(x[0],10**9),x[0]))
            else:
                candidates=[x for x in candidates if pos.get(x[0],10**9) < owner_pos]
                candidates.sort(key=lambda x:(pos.get(x[0],10**9),x[0]))
                candidates.sort(key=lambda x:float(getattr(x[1],'charge',0)))
        elif self.policy in ('leftmost','rightmost','formation_min','formation_max'):
            candidates.sort(key=lambda x:pos.get(x[0],10**9), reverse=self.policy in ('rightmost','formation_max'))
        else:
            reverse_rank=self.policy.endswith('_max') or self.policy.startswith('highest_status_count:')
            candidates.sort(key=lambda x:(pos.get(x[0],10**9),x[0]))
            candidates.sort(key=lambda x:val(x), reverse=reverse_rank)
        return [f for _,f in candidates[:min(self.count,len(candidates))]]

class SelfPlusAllyTarget(Target):
    def __init__(self, ally_target): self.ally_target=ally_target
    def resolve(self,event,state,owner_id):
        own=state.fighters.get(owner_id); out=[]
        if own is not None and float(getattr(own,'hp',0))>0: out.append(own)
        for f in self.ally_target.resolve(event,state,owner_id):
            if f is not own: out.append(f)
        return out

class AllAlliesTarget(Target):
    def __init__(self, exclude_owner=False): self.exclude_owner=bool(exclude_owner)
    def resolve(self,event,state,owner_id):
        return [f for fid,f in state.fighters.items() if (not self.exclude_owner or str(fid)!=str(owner_id)) and float(getattr(f,'hp',0))>0]

class SelfTarget(Target):
    def resolve(self,event,state,owner_id): return [state.fighters[owner_id]]
class EnemyTarget(Target):
    def resolve(self,event,state,owner_id): return [state.enemy]
class EventTarget(Target):
    def __init__(self,key='target'): self.key=key
    def resolve(self,event,state,owner_id):
        u=event.ctx.get(self.key); return [u] if u is not None else []

class Effect:
    def apply(self,event,state,owner_id,targets): raise NotImplementedError

@dataclass(frozen=True)
class EnsureAmmoAtLeast(Effect):
    """Initialize catalog-declared always-on ammo without overwriting scenario input."""
    amount: Value
    def apply(self,event,state,owner_id,targets):
        f=state.fighters[owner_id]
        f.ammo=max(int(f.ammo), int(self.amount.resolve(event,state,owner_id)))

@dataclass(frozen=True)
class AddCharge(Effect):
    amount:Value
    def apply(self,event,state,owner_id,targets): state.fighters[owner_id].charge += int(self.amount.resolve(event,state,owner_id))
@dataclass(frozen=True)
class AddAmmo(Effect):
    amount:Value
    def apply(self,event,state,owner_id,targets): state.fighters[owner_id].ammo += int(self.amount.resolve(event,state,owner_id))
@dataclass(frozen=True)
class AddPoise(Effect):
    potency:Value=Const(0); count:Value=Const(0)
    def apply(self,event,state,owner_id,targets):
        p=state.fighters[owner_id].poise; p.potency+=int(self.potency.resolve(event,state,owner_id)); p.count+=int(self.count.resolve(event,state,owner_id))
@dataclass(frozen=True)
class AddShield(Effect):
    amount:Value
    cap:Value=Const(999999)
    cap_total: bool = True
    def apply(self,event,state,owner_id,targets):
        for t in targets:
            if not hasattr(t,'shield'): continue
            add=max(0.0, float(self.amount.resolve(event,state,owner_id)))
            cap=max(0.0, float(self.cap.resolve(event,state,owner_id)))
            if self.cap_total:
                t.shield=min(float(getattr(t,'shield',0.0))+add, cap)
            else:
                t.shield=float(getattr(t,'shield',0.0))+min(add, cap)

@dataclass(frozen=True)
class AddStatus(Effect):
    name:str; potency:Value=Const(0); count:Value=Const(0)
    def apply(self,event,state,owner_id,targets):
        if self.name == 'Tremor':
            from keyword_runtime_v1 import KeywordRuntime
            p = int(self.potency.resolve(event,state,owner_id))
            c = int(self.count.resolve(event,state,owner_id))
            return [KeywordRuntime.add_tremor(t, p, c, state=state, event=event, source_id=owner_id) for t in targets]
        from limbus_damage_engine_v29 import Status
        for t in targets:
            st=t.statuses.setdefault(self.name,Status()); st.potency+=int(self.potency.resolve(event,state,owner_id)); st.count+=int(self.count.resolve(event,state,owner_id))

@dataclass(frozen=True)
class AddNextTurnStatus(Effect):
    """Queue a status for the owner's next-turn state instead of mutating current state."""
    name:str; potency:Value=Const(0); count:Value=Const(0)
    def apply(self,event,state,owner_id,targets):
        nxt=state.runtime.setdefault('next_turn_state',{}).setdefault('fighters',{}).setdefault(str(owner_id),{})
        statuses=nxt.setdefault('statuses',{})
        cur=dict(statuses.get(self.name,{}) or {})
        cur['potency']=int(cur.get('potency',0))+int(self.potency.resolve(event,state,owner_id))
        cur['count']=int(cur.get('count',0))+int(self.count.resolve(event,state,owner_id))
        statuses[self.name]=cur
        state.event_log.append({'event':'next_turn_status_gain','identity_id':str(owner_id),'status':self.name,'potency':cur['potency'],'count':cur['count']})
@dataclass(frozen=True)
class AddNextTurnTargetStatus(Effect):
    """Queue a status on the current event target for the next turn."""
    name:str; potency:Value=Const(0); count:Value=Const(0)
    def apply(self,event,state,owner_id,targets):
        target = event.ctx.get('target') or (targets[0] if targets else None)
        if target is None: return
        key = str(getattr(target, 'id', 'enemy'))
        nxt=state.runtime.setdefault('next_turn_state',{}).setdefault('targets',{}).setdefault(key,{})
        statuses=nxt.setdefault('statuses',{})
        cur=dict(statuses.get(self.name,{}) or {})
        cur['potency']=int(cur.get('potency',0))+int(self.potency.resolve(event,state,owner_id))
        cur['count']=int(cur.get('count',0))+int(self.count.resolve(event,state,owner_id))
        statuses[self.name]=cur
        state.event_log.append({'event':'next_turn_target_status_gain','identity_id':str(owner_id),'target':key,'status':self.name,'potency':cur['potency'],'count':cur['count']})

@dataclass(frozen=True)
class AddSinResource(Effect):
    sin:str; amount:Value
    def apply(self,event,state,owner_id,targets): state.fighters[owner_id].sin_resources[self.sin]=state.fighters[owner_id].sin_resources.get(self.sin,0)+int(self.amount.resolve(event,state,owner_id))

@dataclass(frozen=True)
class AddResource(Effect):
    """Add a generic identity resource (distinct from Sin/E.G.O resources)."""
    name: str; amount: Value
    def apply(self,event,state,owner_id,targets):
        f=state.fighters[owner_id]
        f.resources[self.name]=f.resources.get(self.name,0)+int(self.amount.resolve(event,state,owner_id))
        state.event_log.append({'event':'resource_gain','identity_id':str(owner_id),'resource':self.name,'amount':int(self.amount.resolve(event,state,owner_id)),'after':int(f.resources[self.name])})
@dataclass(frozen=True)
class TriggerTremorBurst(Effect):
    """Execute one or more common Tremor Bursts against the resolved target.

    The engine owns the canonical Burst semantics, including one Tremor-count
    consumption per Burst.  This effect therefore must not separately consume
    Tremor count, which would double-consume catalog clauses that explicitly
    mention the post-Burst count decrease.
    """
    target: str = 'enemy'
    count: int = 1
    count_cost: int | None = None
    option_key: str | None = None
    def apply(self,event,state,owner_id,targets):
        engine = state.runtime.get('damage_engine')
        if engine is None:
            return
        for t in targets:
            target_name = 'enemy' if t is getattr(state, 'enemy', None) else str(getattr(t, 'id', self.target))
            for _ in range(max(1, int(self.count))):
                engine.apply_effect(state, owner_id, target_name, {'type':'tremor_burst','name':'Tremor','count_cost':int(self.count_cost)})

@dataclass(frozen=True)
class ModifyBurstContext(Effect):
    """Modify the current Tremor Burst's stagger-damage multiplier."""
    amount: Value
    def apply(self,event,state,owner_id,targets):
        state.runtime['tremor_burst_stagger_bonus'] = float(state.runtime.get('tremor_burst_stagger_bonus', 0.0)) + float(self.amount.resolve(event,state,owner_id))

@dataclass(frozen=True)
class AddBurstSecondaryDamage(Effect):
    """Attach a typed damage component derived from this Burst's final stagger damage."""
    sin: str
    scale: Value
    cap: Value = Const(10**9)
    def apply(self,event,state,owner_id,targets):
        state.runtime.setdefault('tremor_burst_secondary_damage', []).append({
            'sin': self.sin,
            'scale': float(self.scale.resolve(event,state,owner_id)),
            'cap': float(self.cap.resolve(event,state,owner_id)),
        })

@dataclass(frozen=True)
class AmplitudeStateEffect(Effect):
    """Apply a common Amplitude state through AmplitudeRuntime."""
    amplitude: str
    mode: str = 'conversion'
    source: str = 'Tremor'
    def apply(self,event,state,owner_id,targets):
        runtime = AmplitudeRuntime()
        for t in targets:
            if self.amplitude == 'current_tremor' and self.mode == 'entanglement':
                runtime.entangle_current_tremor(state, t, owner_id=owner_id)
            else:
                runtime.set_state(state, t, self.amplitude, self.mode, source=self.source, owner_id=owner_id)

@dataclass(frozen=True)
class ModifyContext(Effect):
    field:str; amount:Value
    def apply(self,event,state,owner_id,targets): event.ctx[self.field]=event.ctx.get(self.field,0)+self.amount.resolve(event,state,owner_id)
@dataclass(frozen=True)
class AddPersistentModifier(Effect):
    name:str; amount:Value; target:str='self'
    def apply(self,event,state,owner_id,targets):
        from limbus_damage_engine_v29 import Status
        u=resolve_unit(self.target,event,state,owner_id); u.statuses.setdefault(self.name,Status()).potency += int(self.amount.resolve(event,state,owner_id))
@dataclass(frozen=True)
class ConsumeCharge(Effect):
    amount:Value
    cap_to_available: bool = False
    def apply(self,event,state,owner_id,targets):
        requested=max(0,int(self.amount.resolve(event,state,owner_id)))
        available=max(0,int(getattr(state.fighters[owner_id],'charge',0)))
        actual=min(requested,available) if self.cap_to_available else min(requested,available)
        state.fighters[owner_id].charge=available-actual
        event.ctx['consumed_charge']=actual

@dataclass(frozen=True)
class ConsumeChargeUpTo(Effect):
    cap: Value
    def apply(self,event,state,owner_id,targets):
        available=max(0,int(getattr(state.fighters[owner_id],'charge',0)))
        requested=max(0,int(self.cap.resolve(event,state,owner_id)))
        actual=min(available,requested)
        state.fighters[owner_id].charge=available-actual
        event.ctx['consumed_charge']=actual
@dataclass(frozen=True)
class ConsumeAmmo(Effect):
    amount:Value
    def apply(self,event,state,owner_id,targets): state.fighters[owner_id].ammo=max(0,state.fighters[owner_id].ammo-int(self.amount.resolve(event,state,owner_id)))
@dataclass(frozen=True)
class ConsumeStatus(Effect):
    name:str; amount:Value=Const(1); target:str='enemy'
    def apply(self,event,state,owner_id,targets):
        u=resolve_unit(self.target,event,state,owner_id); st=getattr(u,'statuses',{}).get(self.name) if u else None
        if st: st.count-=int(self.amount.resolve(event,state,owner_id)); st.count=max(0,st.count); 
        if st and st.count==0: u.statuses.pop(self.name,None)

@dataclass
class PassiveDefinition:
    id:str; name:str; owner_id:str; trigger:PassiveTrigger
    conditions:list[Condition]=field(default_factory=lambda:[Always()]); target:Target=field(default_factory=SelfTarget); effects:list[Effect]=field(default_factory=list)
    priority:int=0; max_activations:Optional[int]=None; source_text:str=''; supported:bool=True; activations:int=0; deferred_turns:int=0
    def can_run(self,event,state):
        # Scenario-level passive activation gate.  The calculator does not infer
        # whether a user has pre-heated a passive: the scenario explicitly
        # supplies enabled/disabled state.  Omitted passives remain enabled for
        # backward compatibility.
        gates = state.runtime.get('passive_activation', {})
        key = getattr(self, 'activation_key', None)
        if key and key in gates and not bool(gates[key].get('enabled', True)):
            return False
        # Fine-grained calculator options can gate individual effects without
        # disabling the whole passive.  This is used for optional high-point
        # branches such as the 25% additional Tremor Burst.
        for effect in self.effects:
            option_key = getattr(effect, 'option_key', None)
            if option_key:
                options = state.runtime.get('calculation_options', {}) or {}
                if not bool(options.get(option_key, True)):
                    return False
        return (self.max_activations is None or self.activations<self.max_activations) and all(c.check(event,state,self.owner_id) for c in self.conditions)

class PassiveRuntime:
    def __init__(self): self.passives=[]; self.trace=[]
    def register(self,p): self.passives.append(p); self.passives.sort(key=lambda x:(-x.priority,x.id))
    def register_many(self,ps):
        for p in ps:self.register(p)
    def preview_context(self, trigger, ctx, state, owner_id):
        """Preview declarative context modifiers without consuming activation.

        Used at action-selection boundaries where a BEFORE_USE modifier must be
        known before target selection. Only ModifyContext effects are previewed;
        no passive activation counters or persistent state are mutated.
        """
        event=PassiveEvent(trigger,ctx)
        out={}
        for p in self.passives:
            if p.trigger!=trigger or not p.supported or p.owner_id != owner_id:
                continue
            if not p.can_run(event,state):
                continue
            for effect in p.effects:
                if isinstance(effect, ModifyContext):
                    value=effect.amount.resolve(event,state,p.owner_id)
                    out[effect.field]=out.get(effect.field,0)+value
        return out

    def emit(self,trigger,ctx,state):
        event=PassiveEvent(trigger,ctx)
        active = state.runtime.setdefault('_active_passive_ids', set())
        for p in self.passives:
            if p.trigger!=trigger or not p.supported or not p.can_run(event,state): continue
            # Prevent a passive from recursively retriggering itself when its
            # effect emits the same event. Other passives still observe the
            # nested event normally.
            if p.id in active:
                continue
            active.add(p.id)
            try:
                if getattr(p, 'deferred_turns', 0) > 0:
                    queue = state.runtime.setdefault('deferred_effects', [])
                    queue.append({
                        'turns_remaining': int(p.deferred_turns),
                        'passive_id': p.id,
                        'owner_id': p.owner_id,
                        'trigger': trigger.value,
                        'source_text': p.source_text,
                        'ctx': {k: deepcopy(v) for k,v in event.ctx.items() if k not in ('state', 'identity')},
                        'effects': deepcopy(p.effects),
                        'target_kind': p.target,
                    })
                    state.event_log.append({'event':'deferred_effect_scheduled','passive_id':p.id,
                                            'owner_id':p.owner_id,'turns_remaining':int(p.deferred_turns),
                                            'trigger':trigger.value,'source_text':p.source_text})
                else:
                    targets=p.target.resolve(event,state,p.owner_id)
                    for e in p.effects:e.apply(event,state,p.owner_id,targets)
                p.activations+=1
                self.trace.append({'trigger':trigger.value,'passive':p.id,'owner':p.owner_id,
                                   'deferred':bool(getattr(p,'deferred_turns',0))})
            finally:
                active.discard(p.id)

    def apply_deferred_turn_start(self, state):
        queue = state.runtime.setdefault('deferred_effects', [])
        remaining=[]
        applied=[]
        for item in queue:
            item['turns_remaining'] = int(item.get('turns_remaining', 0)) - 1
            if item['turns_remaining'] > 0:
                remaining.append(item); continue
            event=PassiveEvent(PassiveTrigger.TURN_START, deepcopy(item.get('ctx', {})))
            owner_id=item.get('owner_id')
            target=item.get('target_kind')
            try:
                targets=target.resolve(event,state,owner_id) if hasattr(target,'resolve') else []
                for effect in item.get('effects',[]):
                    effect.apply(event,state,owner_id,targets)
                applied.append(item)
                state.event_log.append({'event':'deferred_effect_applied','passive_id':item.get('passive_id'),
                                        'owner_id':owner_id,'source_text':item.get('source_text','')})
            except Exception as exc:
                state.event_log.append({'event':'deferred_effect_error','passive_id':item.get('passive_id'),
                                        'owner_id':owner_id,'error':str(exc)})
                remaining.append(item)
        state.runtime['deferred_effects']=remaining
        return applied
    def reset_activations(self):
        for p in self.passives:p.activations=0
    def clone(self):
        x=deepcopy(self); return x
