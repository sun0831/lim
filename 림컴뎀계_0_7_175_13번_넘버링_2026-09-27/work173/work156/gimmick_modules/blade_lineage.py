"""Combat affiliation module: 검계."""
MODULE_NAME = "blade_lineage"
DISPLAY_NAME = "검계"
RULE_KINDS = [
    "blade_bonguk_start",
    "blade_bonguk_poise_support",
    "blade_bonguk_self_poise_bonus",
    "blade_lowest_poise_support",
    "blade_hongmaehwa_crit",
    "blade_bonguk_transfer",
    "blade_bonguk_survival",
    "blade_bonguk_support_crit",
]
RESOURCE_NAMES = ["본국검술", "홍매화"]

def metadata() -> dict:
    return {"name": MODULE_NAME, "display_name": DISPLAY_NAME,
            "rule_kinds": list(RULE_KINDS), "resource_names": list(RESOURCE_NAMES)}

def owns_rule(kind: str) -> bool:
    return kind in RULE_KINDS

def owns_resource(name: str) -> bool:
    return str(name) in RESOURCE_NAMES

def build_trigger(registry, r):
    from trigger_rule_model_v1 import TriggerCondition, TriggerEffect
    k = r.kind
    if k == "blade_bonguk_start":
        return "battle_start", [], [
            TriggerEffect("status_gain_affiliation", {
                "status": "본국검술", "affiliation": "BLADE LINEAGE",
                "exclude_owner": True, "amount": 1, "include_dead": False,
                "owner_id": r.owner_id, "fatal_prevention_once": True}),
            TriggerEffect("register_fatal_prevention", {
                "identity_id": r.owner_id, "uses": 1, "reason": "본국검술"}),
        ]
    if k == "blade_bonguk_survival":
        return "battle_start", [], [TriggerEffect("register_fatal_prevention", {
            "identity_id": r.owner_id, "uses": 1, "reason": "본국검술"})]
    if k == "blade_bonguk_support_crit":
        return "battle_start", [], [TriggerEffect("register_damage_modifier_highest_poise", {
            "kind": "critical_damage_percent",
            "amount": 0.15,
            "attack_type": "slash",
            "critical_only": True,
            "reason": "본국검술 서포트"})]
    if k == "blade_bonguk_poise_support":
        return "after_skill", [
            TriggerCondition("owner_id", r.owner_id),
            TriggerCondition("poise_gained", True),
        ], [TriggerEffect("poise_gain_lowest_affiliation", {
            "affiliation": "BLADE LINEAGE", "exclude_owner": True,
            "count": int(r.extra_scale or 2), "amount": 1,
            "use_count": True, "owner_id": r.owner_id})]
    if k == "blade_bonguk_self_poise_bonus":
        return "after_skill", [
            TriggerCondition("owner_id", r.owner_id),
            TriggerCondition("poise_gained", True),
        ], [TriggerEffect("poise_gain_self_bonus", {
            "amount": int(r.extra_scale or 1), "amount_high": 2,
            "dead_threshold": 5, "member_count_threshold": 3,
            "affiliation": "BLADE LINEAGE", "use_count": True,
            "owner_id": r.owner_id})]
    if k == "blade_bonguk_transfer":
        return "battle_start", [], [TriggerEffect("status_gain_affiliation_ordered", {
            "status": r.skill_hint or "본국검 - 세법 전수", "affiliation": "BLADE LINEAGE",
            "exclude_owner": True, "base_count": 1, "max_count": 2,
            "boost_member_count": 6, "boost_count": 2, "boost_amount": 2, "order": "slowest",
            "owner_id": r.owner_id})]
    if k == "blade_hongmaehwa_crit":
        return "after_coin", [
            TriggerCondition("owner_id", r.owner_id),
            TriggerCondition("generated", False),
        ], [TriggerEffect("hongmaehwa_crit", {
            "threshold": 10, "hongmaehwa_amount": 1, "hongmaehwa_cap": 3,
            "defense_down_amount": 1, "defense_down_cap": 6,
        })]
    if k == "blade_lowest_poise_support":
        return "after_skill", [
            TriggerCondition("owner_id", r.owner_id),
            TriggerCondition("poise_gained", True),
        ], [TriggerEffect("poise_gain_lowest_ally", {
            "amount": int(r.extra_scale or 1), "use_count": True,
            "owner_id": r.owner_id})]
    return None
