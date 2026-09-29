"""Combat affiliation module: 중지 (Middle Finger)."""
MODULE_NAME="middle"
DISPLAY_NAME="중지"
RULE_KINDS=["middle_revenge_hit","middle_ally_death_ledger"]
RESOURCE_NAMES=["중지 - 원한","중지식 강화 문신","원한 문신","앙갚음 장부","원한 스탬핑"]
def metadata(): return {"name":MODULE_NAME,"display_name":DISPLAY_NAME,"rule_kinds":list(RULE_KINDS),"resource_names":list(RESOURCE_NAMES)}
def owns_rule(kind): return kind in RULE_KINDS
def owns_resource(name): return str(name) in RESOURCE_NAMES
def build_trigger(registry,r):
    from trigger_rule_model_v1 import TriggerCondition, TriggerEffect
    mids=[str(x.id) for x in registry.identities if registry._module_enabled("middle",getattr(x,"id",""))]
    if r.kind=="middle_revenge_hit":
        return "after_received_attack", [TriggerCondition("received_target_id_in",mids)], [TriggerEffect("enemy_status_count_gain",{"status":"복수 대상","amount":1}), TriggerEffect("resource_gain",{"resource":"앙갚음 장부 [히스클리프]","amount":1,"identity_id":r.owner_id})]
    if r.kind=="middle_ally_death_ledger":
        return "after_skill", [TriggerCondition("target_died",True),TriggerCondition("target_id_in",mids)], [TriggerEffect("resource_gain",{"resource":"앙갚음 장부 [히스클리프]","amount":3,"identity_id":r.owner_id})]
    return None
