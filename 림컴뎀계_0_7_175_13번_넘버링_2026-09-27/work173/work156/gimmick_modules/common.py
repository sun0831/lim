"""Common combat-gimmick trigger rules.

These are rule *shapes* shared by many identities.  Identity data determines
who owns/activates them; this module only contains the reusable trigger wiring.
"""
import re
MODULE_NAME='common'
DISPLAY_NAME='공통'
RULE_KINDS=[
    'assist','stagger_assist','ally_new_stagger_assist','support_left_assist','support_right_assist',
    'ally_hit_followup','received_attack_followup','clash_loss_followup',
    'defense_clash_loss_followup','kill_resource_gain','kill_resource_distribute','kill_charge_barrier','battle_start_charge_barrier_power','battle_start_charge_barrier_power_plus','defense_charge_barrier','next_turn_fixed_charge_barrier','next_turn_charge_barrier_from_charge','resource_spend_charge_barrier_lowest_hp','resource_spend_charge_barrier_distribution','resource_spend_charge_barrier_lowest_hp_2','kill_charge_barrier_self_random_ally',
    'kill_lowest_ally_heal','enemy_death_lowest_ally_heal',
    'target_death_resource_gain','lowest_ammo_poise','extra_damage',
    'resource_start','cumulative_resource_gain','turn_end_status_transform','support_poise_gain','support_poise_count_bonus','attack_end_negative_status_sp_gain',
]
def metadata(): return {'name':MODULE_NAME,'display_name':DISPLAY_NAME,'rule_kinds':list(RULE_KINDS)}
def owns_rule(kind): return kind in RULE_KINDS

def build_trigger(registry,r):
    from trigger_rule_model_v1 import TriggerCondition, TriggerEffect
    k=r.kind; conditions=[]; effects=[]; event='after_skill'
    if k=='assist':
        if r.trigger_skill_names: conditions.append(TriggerCondition('skill_name_any',list(r.trigger_skill_names)))
        actor=registry._find_identity(r.actor_hint)
        if actor: conditions.append(TriggerCondition('target_available',str(actor.id)))
        effects.append(TriggerEffect('support_action',{'identity_policy':'fixed','identity_id':r.actor_hint,'skill_policy':'named','skill_name':r.skill_hint,'trigger_kind':'assist','target_policy':'main'}))
    elif k=='stagger_assist':
        conditions += [TriggerCondition('skill_slot','S1'),TriggerCondition('newly_staggered')]
        dawn_ids=[str(x.id) for x in registry.identities if registry._module_enabled('dawn_office',getattr(x,'id','')) and str(x.id)!=str(r.owner_id)]
        if dawn_ids: conditions.append(TriggerCondition('identity_id_in',dawn_ids))
        effects.append(TriggerEffect('support_action',{'identity_policy':'fixed','identity_id':r.actor_hint,'skill_policy':'named','skill_name':r.skill_hint,'trigger_kind':'stagger_assist','target_policy':'main'}))
    elif k=='ally_new_stagger_assist':
        # Generic source-backed shape: an attack by someone other than the owner
        # newly staggers an enemy, then the owner performs a named support attack.
        # The once-per-turn cap is owned by ActivationLedger/reset_turn.
        event='after_skill'
        conditions += [TriggerCondition('identity_id_not',r.owner_id), TriggerCondition('newly_staggered')]
        effects.append(TriggerEffect('support_action',{'identity_policy':'fixed','identity_id':r.owner_id,'skill_policy':'named','skill_name':r.skill_hint,'trigger_kind':'ryoshu_10409_stagger_assist','target_policy':'lowest_hp_staggered'}))
    elif k in ('support_left_assist','support_right_assist'):
        if r.trigger_skill_names: conditions.append(TriggerCondition('skill_name_any',list(r.trigger_skill_names)))
        conditions.append(TriggerCondition('owner_id',r.owner_id))
        relation='ally_left' if k=='support_left_assist' else 'ally_right'
        effects.append(TriggerEffect('support_action',{'identity_policy':relation,'source_identity_id':r.owner_id,'skill_policy':'requested_next','skill_name':'__support_default__','trigger_kind':k,'target_policy':'main'}))
    elif k=='ally_hit_followup':
        conditions += [TriggerCondition('identity_id_not',r.owner_id),TriggerCondition('skill_basic'),TriggerCondition('actual_damage_gt_zero'),TriggerCondition('target_available',r.owner_id)]
        effects.append(TriggerEffect('queue_action',{'identity_id':r.owner_id,'skill_name':r.skill_hint,'trigger_kind':k,'target_policy':'main'}))
    elif k=='received_attack_followup':
        event='after_received_attack'
        conditions += [TriggerCondition('owner_id',r.owner_id),TriggerCondition('received_target_died_or_hp_below_pct',int(getattr(r,'_received_hp_threshold',25)))]
        effects.append(TriggerEffect('queue_action',{'identity_id':r.actor_hint,'skill_name':r.skill_hint,'trigger_kind':k,'target_policy':'attacker'}))
    elif k=='clash_loss_followup':
        event='after_clash'; conditions += [TriggerCondition('owner_id',r.owner_id),TriggerCondition('clash_outcome','lose'),TriggerCondition('skill_basic')]
        if '예지안이 있을 때' in r.source_text: conditions.append(TriggerCondition('resource_gte','예지안','1'))
        effects.append(TriggerEffect('queue_action',{'identity_id':r.actor_hint,'skill_name':r.skill_hint,'trigger_kind':k,'target_policy':'main'}))
    elif k=='defense_clash_loss_followup':
        event='after_clash'; m=re.search(r'신속이\s*(\d+)\s*이상',r.source_text); threshold=int(m.group(1)) if m else 0
        conditions += [TriggerCondition('owner_id',r.owner_id),TriggerCondition('clash_outcome','lose'),TriggerCondition('skill_defense'),TriggerCondition('status_count_gte','신속',str(threshold))]
        effects.append(TriggerEffect('queue_action',{'identity_id':r.actor_hint,'skill_name':r.skill_hint,'trigger_kind':k,'target_policy':'main'}))
    elif k=='resource_spend_charge_barrier_lowest_hp':
        event='resource_cumulative_consumed'; conditions=[TriggerCondition('owner_id',r.owner_id),TriggerCondition('resource','충전')]; effects.append(TriggerEffect('resource_gain_lowest_hp_ally',{'resource':'충전 역장','amount':int(r.extra_scale),'exclude_owner':True}))
    elif k=='resource_spend_charge_barrier_lowest_hp_2':
        event='after_skill'; conditions=[TriggerCondition('owner_id',r.owner_id),TriggerCondition('skill_slot','S3'),TriggerCondition('action_resource_consumed_gte','충전',10)]; effects.append(TriggerEffect('resource_spend_charge_barrier_lowest_hp_2',{'count':2,'min_consumed':10}))
    elif k=='kill_charge_barrier_self_random_ally':
        event='after_kill'; conditions=[TriggerCondition('killer_id',r.owner_id),TriggerCondition('coin_index',4),TriggerCondition('action_resource_consumed_gte','충전',15)]; effects.append(TriggerEffect('kill_charge_barrier_self_random_ally',{'amount':int(r.extra_scale),'min_consumed':15,'coin_index':4}))
    elif k=='resource_spend_charge_barrier_distribution':
        event='resource_cumulative_consumed'; conditions=[TriggerCondition('owner_id',r.owner_id),TriggerCondition('resource','충전')]; effects.append(TriggerEffect('resource_gain_lowest_allies',{'resource':'충전 역장','amount_base':int(r.extra_scale),'amount_resource':'충전','count':int(getattr(r,'_distribution_count',2)),'cap':int(getattr(r,'_distribution_cap',8)),'include_owner':True}))
    elif k=='kill_charge_barrier':
        event='after_kill'; conditions.append(TriggerCondition('killer_id',r.owner_id)); effects.append(TriggerEffect('resource_gain',{'resource':'충전 역장','amount':int(r.extra_scale),'identity_id':r.owner_id}))
    elif k=='battle_start_charge_barrier_power':
        event='battle_start'; conditions.append(TriggerCondition('owner_id',r.owner_id)); effects.append(TriggerEffect('resource_gain_from_charge_potency',{'resource':'충전 역장','identity_id':r.owner_id,'cap':int(getattr(r,'_barrier_cap',5))}))
    elif k=='battle_start_charge_barrier_power_plus':
        event='battle_start'; conditions.append(TriggerCondition('owner_id',r.owner_id)); effects.append(TriggerEffect('resource_gain_from_charge_potency_plus',{'resource':'충전 역장','identity_id':r.owner_id,'base':int(r.extra_scale),'cap':int(getattr(r,'_barrier_cap',6))}))
    elif k=='defense_charge_barrier':
        event='after_skill'; conditions += [TriggerCondition('owner_id',r.owner_id), TriggerCondition('skill_defense',True), TriggerCondition('skill_name_contains',r.trigger_skill_names[0] if r.trigger_skill_names else '')]; effects.append(TriggerEffect('resource_gain',{'resource':'충전 역장','amount':int(r.extra_scale),'identity_id':r.owner_id}))
    elif k=='next_turn_fixed_charge_barrier':
        event='after_coin'; conditions += [TriggerCondition('owner_id',r.owner_id), TriggerCondition('skill_name_contains',r.trigger_skill_names[0] if r.trigger_skill_names else ''), TriggerCondition('coin_index',int(getattr(r,'_coin_index',3))), TriggerCondition('actual_damage_gt_zero',True)]; effects.append(TriggerEffect('next_turn_resource_gain',{'resource':'충전 역장','amount':int(r.extra_scale),'identity_id':r.owner_id}))
    elif k=='next_turn_charge_barrier_from_charge':
        event='after_coin'; conditions += [TriggerCondition('owner_id',r.owner_id), TriggerCondition('skill_name_contains',r.trigger_skill_names[0] if r.trigger_skill_names else ''), TriggerCondition('coin_index',int(getattr(r,'_coin_index',2))), TriggerCondition('actual_damage_gt_zero',True)]; effects.append(TriggerEffect('next_turn_charge_barrier_from_charge',{'resource':'충전 역장','source_resource':'충전','per':5,'amount':1,'cap':int(getattr(r,'_barrier_cap',4)),'identity_id':r.owner_id}))
    elif k=='kill_resource_gain':
        event='after_kill'; conditions.append(TriggerCondition('killer_id',r.owner_id)); effects.append(TriggerEffect('resource_gain',{'resource':'충전','amount':int(r.extra_scale),'identity_id':r.owner_id}))
    elif k=='kill_resource_distribute':
        event='after_kill'; conditions.append(TriggerCondition('killer_id',r.owner_id)); effects.append(TriggerEffect('resource_gain_lowest_allies',{'resource':'충전','amount_base':int(r.extra_scale),'amount_resource':str(getattr(r,'_distribution_expr_resource','충전')),'count':int(getattr(r,'_distribution_count',1)),'cap':getattr(r,'_distribution_cap',None),'include_owner':True}))
    elif k=='kill_lowest_ally_heal':
        event='after_kill'; conditions.append(TriggerCondition('killer_id',r.owner_id)); effects.append(TriggerEffect('heal_lowest_ally',{'amount':int(r.extra_scale)}))
    elif k=='enemy_death_lowest_ally_heal':
        event='after_kill'; effects.append(TriggerEffect('heal_lowest_ally',{'amount':int(r.extra_scale)}))
    elif k=='target_death_resource_gain':
        event='after_skill'; conditions += [TriggerCondition('owner_id',r.owner_id),TriggerCondition('target_died',True)]; effects.append(TriggerEffect('resource_gain',{'resource':r.skill_hint,'amount':int(r.extra_scale),'identity_id':r.owner_id}))
    elif k=='lowest_ammo_poise':
        event='after_skill'; conditions=[TriggerCondition('is_lowest_ammo_identity',True),TriggerCondition('action_ammo_spent_gt_zero',True)]; effects.append(TriggerEffect('poise_gain',{'amount':int(r.extra_scale)}))
    elif k=='extra_damage':
        event='after_coin'; conditions.append(TriggerCondition('final_ammo_coin')); effects.append(TriggerEffect('extra_damage_scale',{'scale':r.extra_scale}))
    elif k=='resource_start':
        event='battle_start' if '전투 시작시' in r.source_text else 'turn_start'; effects.append(TriggerEffect('resource_gain',{'resource':r.skill_hint,'amount':int(r.extra_scale)}))
    elif k=='support_poise_gain':
        conditions=[TriggerCondition('formation_first_actor',True),TriggerCondition('skill_basic',True),TriggerCondition('owner_not_available',r.owner_id)]
        effects.append(TriggerEffect('support_poise_gain',{'target_policy':getattr(r,'_support_target_policy','formation_first'),'amount':int(r.extra_scale or 2),'use_count':False}))
    elif k=='support_poise_count_bonus':
        conditions=[TriggerCondition('poise_gained',True),TriggerCondition('support_target_actor',getattr(r,'_support_target_policy','highest_sp')),TriggerCondition('owner_not_available',r.owner_id)]
        effects.append(TriggerEffect('support_poise_count_bonus',{'amount':int(r.extra_scale or 1)}))
    elif k=='attack_end_negative_status_sp_gain':
        event='after_skill'
        conditions=[TriggerCondition('owner_id',r.owner_id), TriggerCondition('actual_damage_gt_zero'), TriggerCondition('negative_status_applied',True)]
        effects=[TriggerEffect('sp_gain',{'identity_id':r.owner_id,'amount':int(r.extra_scale or 0),'max_sp_followup':bool(getattr(r,'_max_sp_followup',False))})]
    elif k=='turn_end_status_transform':
        event='turn_end'
        conditions=[TriggerCondition('owner_id',r.owner_id), TriggerCondition('actor_has_status',getattr(r,'_turn_end_gate_status',''))]
        effects=[TriggerEffect('status_transform', {
            'identity_id':r.owner_id,
            'source_status':getattr(r,'_turn_end_source_status',''),
            'gate_status':getattr(r,'_turn_end_gate_status',''),
            'reward_status':getattr(r,'_turn_end_reward_status',r.skill_hint or ''),
            'once_per_battle':True,
        })]
    elif k=='cumulative_resource_gain':
        event='resource_cumulative_consumed'
        m=re.search(r'자신의\s*([^\s]+(?:\s*횟수)?)\s*(\d+)\s*을\s*소모할',r.source_text)
        if m:
            src=m.group(1).replace(' 횟수','').strip(); threshold=int(m.group(2)); conditions=[TriggerCondition('owner_id',r.owner_id),TriggerCondition('resource',src),TriggerCondition('cumulative_resource_crossed',threshold)]
        effects.append(TriggerEffect('resource_gain',{'resource':r.skill_hint,'amount':int(r.extra_scale)}))
        if hasattr(r,'_post_gain_threshold') and getattr(r,'_post_gain_status',''):
            effects.append(TriggerEffect('resource_threshold_status_gain', {
                'identity_id':r.owner_id, 'resource':r.skill_hint,
                'threshold':int(r._post_gain_threshold),
                'gain_amount':int(r.extra_scale),
                'status':str(r._post_gain_status),
            }))
    else: return None
    return event,conditions,effects
