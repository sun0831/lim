"""Combat affiliation module: 새벽 사무소 (Dawn Office)."""
MODULE_NAME="dawn_office"
DISPLAY_NAME="새벽 사무소"
RULE_KINDS=["resource_gain"]
RESOURCE_NAMES=["새벽불","불꽃나비의 관","새벽녘"]
def metadata(): return {"name":MODULE_NAME,"display_name":DISPLAY_NAME,"rule_kinds":list(RULE_KINDS),"resource_names":list(RESOURCE_NAMES)}
def owns_rule(kind): return kind in RULE_KINDS
def owns_resource(name): return str(name) in RESOURCE_NAMES
def owns_resource_gain_rule(r): return r.kind=="resource_gain" and "새벽불" in r.source_text
def build_trigger(registry,r):
    from trigger_rule_model_v1 import TriggerCondition, TriggerEffect
    if owns_resource_gain_rule(r): return "after_coin", [TriggerCondition("skill_basic"),TriggerCondition("actual_damage_gt_zero"),TriggerCondition("has_status","새벽맞이")], [TriggerEffect("resource_gain",{"resource":"새벽불","amount":int(r.extra_scale)})]
    return None
