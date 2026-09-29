from skill_transform_contract_v1 import *

def test_true_swap_routes_to_generic_skill_swap():
    assert route_from_e23_kind('true_skill_swap') is SkillTransformRoute.SKILL_SWAP
    s=swap_spec_from_clause('true_skill_swap','basic','execution',slot_policy='leftmost_below')
    validate_skill_swap(s)
    assert s.timing=='immediate'

def test_next_turn_swap_is_timing_parameter_not_new_runtime():
    s=swap_spec_from_clause('next_turn_skill_swap','basic','S3',slot_policy='leftmost_below')
    assert s.timing=='next_turn_start'

def test_non_swap_routes_are_kept_separate():
    assert route_from_e23_kind('skill_reclassify') is SkillTransformRoute.SKILL_RECLASSIFY
    assert route_from_e23_kind('forced_or_followup_skill') is SkillTransformRoute.FORCED_ACTION
    assert route_from_e23_kind('coin_or_skill_parameter_transform') is SkillTransformRoute.COIN_POWER_TRANSFORM
