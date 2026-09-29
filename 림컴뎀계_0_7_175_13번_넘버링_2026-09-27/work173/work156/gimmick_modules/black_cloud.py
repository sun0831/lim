"""Combat affiliation module: 흑운회 (Black Cloud)."""
MODULE_NAME="black_cloud"
DISPLAY_NAME="흑운회"
RULE_KINDS=["blackcloud_received_s1","blackcloud_received_s4"]
RESOURCE_NAMES=[]
def metadata(): return {"name":MODULE_NAME,"display_name":DISPLAY_NAME,"rule_kinds":list(RULE_KINDS),"resource_names":[]}
def owns_rule(kind): return kind in RULE_KINDS
def owns_resource(name): return False
def build_trigger(registry,r):
    from trigger_rule_model_v1 import TriggerCondition, TriggerEffect
    if r.kind=="blackcloud_received_s1": return "after_received_attack", [TriggerCondition("received_target_died_or_hp_below_pct",25,negate=True),TriggerCondition("received_target_damaged",True)], [TriggerEffect("queue_action",{"identity_id":r.owner_id,"skill_name":r.skill_hint,"trigger_kind":"blackcloud_received_s1","target_mode":"attacker"})]
    if r.kind=="blackcloud_received_s4": return "after_received_attack", [TriggerCondition("received_target_died_or_hp_below_pct",25)], [TriggerEffect("queue_action",{"identity_id":r.owner_id,"skill_name":r.skill_hint,"trigger_kind":"blackcloud_received_s4","target_mode":"attacker"})]
    return None
