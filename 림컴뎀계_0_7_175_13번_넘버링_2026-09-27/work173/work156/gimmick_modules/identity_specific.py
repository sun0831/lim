"""Identity-exclusive trigger rules.

The parser recognizes reusable rule shapes, but these effects are not tied to a
combat affiliation.  Keeping them here prevents special_gimmick_v2.py from
becoming an identity-mechanics monolith.
"""
import re
MODULE_NAME='identity_specific'
DISPLAY_NAME='인격 전용'
RULE_KINDS=['enemy_hp_followup','forced_skill','conditional_assist','reused_status_damage']
def metadata(): return {'name':MODULE_NAME,'display_name':DISPLAY_NAME,'rule_kinds':list(RULE_KINDS)}
def owns_rule(kind): return kind in RULE_KINDS

def build_trigger(registry,r):
    from trigger_rule_model_v1 import TriggerCondition, TriggerEffect
    k=r.kind; conditions=[]; effects=[]; event='after_skill'
    if k=='enemy_hp_followup':
        m=re.search(r'(\d+)%',r.source_text)
        conditions += [TriggerCondition('skill_basic',True),TriggerCondition('enemy_hp_percent_lte',int(m.group(1)) if m else 0),TriggerCondition('target_available',r.owner_id)]
        effects.append(TriggerEffect('queue_action',{'identity_id':r.actor_hint,'skill_name':r.skill_hint,'trigger_kind':k,'target_policy':'main'}))
    elif k=='forced_skill':
        if '기본 공격 스킬 종료 시' in r.source_text: conditions.append(TriggerCondition('skill_basic',True))
        conditions.append(TriggerCondition('owner_id',r.owner_id))
        rm=re.search(r'자신의\s*([^\s]+(?:\s*횟수)?)\s*(\d+)\s*이상',r.source_text)
        if rm:
            resource=rm.group(1).replace(' 횟수','').strip().rstrip('이가는은는'); conditions.append(TriggerCondition('resource_gte',resource,str(rm.group(2))))
        policy='highest_status:잔향' if '잔향이 가장 높은 대상' in r.source_text else 'main'
        effects.append(TriggerEffect('queue_action',{'identity_id':r.actor_hint,'skill_name':r.skill_hint,'trigger_kind':k,'target_policy':policy}))
    elif k=='conditional_assist':
        actor=registry._find_identity(r.actor_hint)
        conditions += [TriggerCondition('actor_id',str(actor.id) if actor else ''),TriggerCondition('actor_has_status','예지안'),TriggerCondition('skill_basic',True),TriggerCondition('actual_damage_gt_zero',True),TriggerCondition('target_available',r.owner_id)]
        effects.append(TriggerEffect('queue_action',{'identity_id':r.owner_id,'skill_name':r.skill_hint,'trigger_kind':k,'target_policy':'main'}))
    elif k=='reused_status_damage':
        event='after_coin'; conditions += [TriggerCondition('skill_basic'),TriggerCondition('actual_damage_gt_zero'),TriggerCondition('coin_reuse',True)]
        sinclair_ids=[str(x.id) for x in registry.identities if '새벽 사무소 해결사 싱클레어' in str(getattr(x,'full_name',''))]
        if sinclair_ids: conditions.append(TriggerCondition('target_available',sinclair_ids[0]))
        effects.append(TriggerEffect('status_potency_damage',{'status':'Burn','status_aliases':['화상'],'max_per_coin':10,'turn_cap':20,'damage_type':'wrath'}))
    else: return None
    return event,conditions,effects
