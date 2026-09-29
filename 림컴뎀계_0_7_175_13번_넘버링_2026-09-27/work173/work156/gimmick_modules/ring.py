"""Combat affiliation module: 약지 (Ring Finger)."""
MODULE_NAME="ring"
DISPLAY_NAME="약지"
RULE_KINDS=["bio_material_skill_damage","bio_material_kill_bonus","bio_material_start"]
RESOURCE_NAMES=["생체 재료"]
def metadata(): return {"name":MODULE_NAME,"display_name":DISPLAY_NAME,"rule_kinds":list(RULE_KINDS),"resource_names":list(RESOURCE_NAMES)}
def owns_rule(kind): return kind in RULE_KINDS
def owns_resource(name): return str(name) in RESOURCE_NAMES
def build_trigger(registry,r):
    from trigger_rule_model_v1 import TriggerCondition, TriggerEffect
    if r.kind=="bio_material_skill_damage":
        return "after_skill", [TriggerCondition("owner_id",r.owner_id),TriggerCondition("actual_damage_gt_zero")], [TriggerEffect("resource_gain",{"resource":"생체 재료","amount":5,"identity_id":r.owner_id})]
    if r.kind=="bio_material_kill_bonus":
        return "after_skill", [TriggerCondition("owner_id",r.owner_id),TriggerCondition("target_died",True)], [TriggerEffect("resource_gain",{"resource":"생체 재료","amount":int(r.extra_scale),"identity_id":r.owner_id})]
    if r.kind=="bio_material_start":
        # Membership/count resolution is delegated to AffiliationResolver in the
        # lifecycle bridge; this module only declares the Ring-specific rule.
        return "battle_start", [], [TriggerEffect("resource_gain_affiliation_count",{"resource":"생체 재료","affiliation":"RING FINGER","multiplier":2,"cap":10,"identity_id":r.owner_id})]
    return None
