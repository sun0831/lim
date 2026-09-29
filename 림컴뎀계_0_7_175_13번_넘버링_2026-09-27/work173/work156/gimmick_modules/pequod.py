"""Combat affiliation module: 피쿼드호 (Pequod)."""
MODULE_NAME="pequod"
DISPLAY_NAME="피쿼드호"
RULE_KINDS=["captain_right_assist"]
RESOURCE_NAMES=[]
def metadata(): return {"name":MODULE_NAME,"display_name":DISPLAY_NAME,"rule_kinds":list(RULE_KINDS),"resource_names":[]}
def owns_rule(kind): return kind in RULE_KINDS
def owns_resource(name): return False
def build_trigger(registry,r):
    from trigger_rule_model_v1 import TriggerCondition, TriggerEffect
    if r.kind=="captain_right_assist":
        conditions=[TriggerCondition("owner_id",r.owner_id),TriggerCondition("highest_resonance_gte",1)]
        if r.trigger_skill_names: conditions.insert(0,TriggerCondition("skill_name_any",list(r.trigger_skill_names)))
        effects=[TriggerEffect("support_action",{"identity_policy":"ally_right","source_identity_id":r.owner_id,"skill_policy":"requested_next","skill_name":"__support_default__","trigger_kind":"captain_right_assist","target_policy":"main"})]
        return "after_skill", conditions, effects
    return None
