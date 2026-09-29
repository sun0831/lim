"""Combat affiliation module: 거미집 (Spider House)."""
MODULE_NAME="spider_house"
DISPLAY_NAME="거미집"
RULE_KINDS=["foresight_start","foresight_clash_cost"]
RESOURCE_NAMES=["예지","예지안"]
def metadata(): return {"name":MODULE_NAME,"display_name":DISPLAY_NAME,"rule_kinds":list(RULE_KINDS),"resource_names":list(RESOURCE_NAMES)}
def owns_rule(kind): return kind in RULE_KINDS
def owns_resource(name): return str(name) in RESOURCE_NAMES
def build_trigger(registry,r):
    from trigger_rule_model_v1 import TriggerCondition, TriggerEffect
    if r.kind=="foresight_start": return "battle_start", [], [TriggerEffect("resource_gain",{"resource":"예지안","amount":int(r.extra_scale),"identity_id":r.owner_id})]
    if r.kind=="foresight_clash_cost": return "after_clash", [TriggerCondition("owner_id",r.owner_id),TriggerCondition("resource_gte","예지안","1")], [TriggerEffect("resource_consume",{"resource":"예지안","amount":1,"identity_id":r.owner_id,"overheat_at_zero":True})]
    return None
