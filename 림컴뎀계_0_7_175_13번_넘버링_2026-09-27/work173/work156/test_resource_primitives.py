"""병합 테스트: resource_primitives

원본 파일 (내용은 AST 병합기로 합쳤고 테스트 본문은 바꾸지 않음):
  - test_v130_resource_primitives.py
  - test_v131_resource_clause_decomposer.py
  - test_v132_resource_consumption_audit.py
  - test_v132_resource_semantic_clusters.py
  - test_v133_resource_selector_symmetry.py
  - test_v136_resource_conversion_primitive.py
이름 충돌 helper 는 `이름__vNN` 으로 분리했다. 매핑은 tools/MERGE_MAP.json 참고.
"""
import json
from resource_primitive_v1 import (
    ResourcePrimitive,
    ResourcePrimitiveSpec,
    ResourceRef,
    primitive_from_effect,
    validate,
)
from resource_clause_decomposer_v1 import decompose_clause
from resource_consumption_audit_v1 import ConsumptionClass, classify_consumption_clause
from pathlib import Path



# ======================================================================
# 원본: test_v130_resource_primitives.py
# ======================================================================

def test_trigger_gain_maps_to_common_primitive():
    s = primitive_from_effect('resource_gain', {'resource':'충전','amount':2,'trigger':'after_kill'})
    assert s.primitive is ResourcePrimitive.TRIGGER_GAIN
    assert s.resource.name == '충전'
    assert s.resource.amount == 2

def test_cumulative_gain_schema_is_explicit():
    s = primitive_from_effect('cumulative_resource_gain', {'source_resource':'충전','threshold':10,'reward_resource':'탄환','reward_amount':1})
    assert s.primitive is ResourcePrimitive.CUMULATIVE_SPEND_GAIN
    assert s.threshold == 10
    assert s.reward.name == '탄환'

def test_resource_scaled_modifier_is_not_identity_specific():
    s = primitive_from_effect('resource_scaled_damage_bonus', {'resource':'오혈','multiplier':0.03,'modifier':'damage_percent'})
    assert s.primitive is ResourcePrimitive.RESOURCE_SCALED_MODIFIER
    assert s.multiplier == 0.03

def test_lowest_resource_selector_is_a_target_primitive():
    s = primitive_from_effect('resource_gain_lowest_allies', {'resource':'탄환','amount_base':1})
    assert s.primitive is ResourcePrimitive.LOWEST_RESOURCE_TARGET
    assert s.target_selector == 'lowest'
    assert s.target_side == 'ally'

def test_unknown_effect_is_not_guessed():
    assert primitive_from_effect('예지안_과열_특수처리', {'resource':'예지안'}) is None

def test_schema_rejects_missing_semantics():
    try:
        validate(ResourcePrimitiveSpec(ResourcePrimitive.RESOURCE_SCALED_MODIFIER,
            resource=ResourceRef('충전'), modifier='damage_percent'))
    except ValueError:
        return
    raise AssertionError('missing multiplier must be rejected')

def test_highest_resource_selector_is_symmetric_with_lowest():
    s = primitive_from_effect('highest_resource_selector', {'resource':'충전'})
    assert s.primitive is ResourcePrimitive.HIGHEST_RESOURCE_TARGET
    assert s.target_selector == 'highest'

def test_pure_resource_consumption_trigger_is_distinct_from_cumulative_reward():
    s = primitive_from_effect('resource_consume_trigger', {'resource':'생체 재료','amount':10,'trigger':'on_consume'})
    assert s.primitive is ResourcePrimitive.RESOURCE_CONSUME_TRIGGER
    assert s.reward is None

def test_resource_triggered_skill_swap_is_distinct_from_skill_reclassify():
    s = primitive_from_effect('resource_triggered_skill_swap', {'resource':'조망','source_skill':'기본 스킬','target_skill':'폐장'})
    assert s.primitive is ResourcePrimitive.RESOURCE_TRIGGERED_SKILL_SWAP
    assert s.source_skill == '기본 스킬'
    assert s.target_skill == '폐장'


# ======================================================================
# 원본: test_v131_resource_clause_decomposer.py
# ======================================================================

def kinds(s): return {x.kind.value for x in decompose_clause(s)}

def test_gain_trigger():
    k=kinds('아군 인격 사망시, 앙갚음 장부 3 얻음')
    assert {'trigger','resource_gain'} <= k

def test_cumulative_spend():
    k=kinds('전투 중 누적으로 충전 횟수 10을 소모할 때마다 충전 1 얻음')
    assert {'resource_consume','resource_gain','count_scaling'} <= k

def test_affiliation_lowest():
    k=kinds('중지 소속 아군 중 자원이 가장 적은 대상에게 1 부여')
    assert {'affiliation_count','lowest_resource_selector','resource_gain'} <= k

def test_resource_scaled_damage():
    k=kinds('충전이 2 이상이면 피해량이 충전 x 3%만큼 증가')
    assert {'count_scaling','resource_scaled_modifier'} <= k

def test_zero_skill_transform():
    k=kinds('조망이 0이면 다음 턴 스킬 변경')
    assert {'resource_zero','skill_transform'} <= k

def test_random_scaled():
    k=kinds('무작위 적 1명에게 부여하고 사망한 아군 3명당 1개 추가')
    assert {'random_target','count_scaling'} <= k


# ======================================================================
# 원본: test_v132_resource_consumption_audit.py
# ======================================================================

def test_cumulative_spend_is_not_plain_trigger():
    a=classify_consumption_clause("전투 중 누적으로 자신의 충전 횟수 10을 소모할 때마다 충전 1 얻음")
    assert a.classification is ConsumptionClass.CUMULATIVE_SPEND_REWARD

def test_consume_trigger():
    a=classify_consumption_clause("자신이 중지 - 원한을 5 소모할 때마다 중지식 강화 문신 1 얻음 (턴당 2회)")
    assert a.classification is ConsumptionClass.CONSUME_TRIGGER
    assert a.primitive == "resource_consume_trigger"

def test_consumption_conversion():
    a=classify_consumption_clause("정신력 2, 포자탄[기본] 2 소모하여, 포자탄[산탄] 1 얻음")
    assert a.classification is ConsumptionClass.CONSUME_CONVERSION

def test_consumption_condition():
    a=classify_consumption_clause("탄환을 소모하는 코인을 굴릴 때, 탄환이 없는 경우에도 공격이 취소되지 않음")
    assert a.classification is ConsumptionClass.CONSUME_CONDITION


# ======================================================================
# 원본: test_v132_resource_semantic_clusters.py
# ======================================================================

def test_resource_source_baseline():
    p=Path(__file__).with_name('RESOURCE_SEMANTIC_CLUSTER_E19.json')
    d=json.loads(p.read_text(encoding='utf-8'))
    assert d['record_count']==215
    assert d['unique_source_texts']==214
    assert d['exact_duplicate_records']==1
    assert d['e18_clause_candidate_count']==2043

def test_cluster_method_is_non_additive():
    p=Path(__file__).with_name('RESOURCE_SEMANTIC_CLUSTER_E19.json')
    d=json.loads(p.read_text(encoding='utf-8'))
    assert 'semantic_method' in d
    assert 'not additive' in d['semantic_method']

def test_expected_core_clusters_exist():
    p=Path(__file__).with_name('RESOURCE_SEMANTIC_CLUSTER_E19.json')
    d=json.loads(p.read_text(encoding='utf-8'))
    names={x['cluster'] for x in d['clusters']}
    for n in ('direct_resource_gain','resource_consumption','affiliation_scaled_resource','resource_scaled_modifier','resource_zero_state','resource_skill_transform'):
        assert n in names


# ======================================================================
# 원본: test_v133_resource_selector_symmetry.py
# ======================================================================

def test_highest_resource_selector_preserves_resource_and_side():
    s = primitive_from_effect('highest_resource_selector', {
        'resource': '충전', 'target_side': 'ally', 'target_selector': 'highest'
    })
    assert s.primitive is ResourcePrimitive.HIGHEST_RESOURCE_TARGET
    assert s.resource.name == '충전'
    assert s.target_selector == 'highest'
    assert s.target_side == 'ally'

def test_e21_corpus_contains_explicit_highest_resource_cases():
    p = Path(__file__).with_name('RESOURCE_SELECTOR_SYMMETRY_E21.json')
    data = json.loads(p.read_text(encoding='utf-8'))
    assert data['matched_records'] == 2
    assert {x['resource_semantics'] for x in data['cases']} == {'charge_count', 'ammo_count'}
    assert all(x['mapped_primitive'] == 'highest_resource_selector' for x in data['cases'])

def test_lowest_and_highest_preserve_explicit_target_side():
    low = primitive_from_effect('lowest_resource_selector', {'resource':'충전','target_side':'enemy'})
    high = primitive_from_effect('highest_resource_selector', {'resource':'충전','target_side':'enemy'})
    assert low.target_side == 'enemy'
    assert high.target_side == 'enemy'


# ======================================================================
# 원본: test_v136_resource_conversion_primitive.py
# ======================================================================

def test_fixed_resource_conversion_maps_to_common_primitive():
    s = primitive_from_effect('resource_convert', {
        'source': '포자탄[기본]', 'source_amount': 2,
        'target': '포자탄[산탄]', 'target_amount': 1,
        'conversion_mode': 'fixed'
    })
    assert s.primitive is ResourcePrimitive.RESOURCE_CONVERSION
    assert s.resource.name == '포자탄[기본]'
    assert s.resource.amount == 2
    assert s.reward.name == '포자탄[산탄]'
    assert s.reward.amount == 1
    assert s.conversion_mode == 'fixed'

def test_proportional_consumption_conversion_maps_to_same_primitive():
    s = primitive_from_effect('resource_gain_from_consumed', {
        'source': '가속탄', 'source_per': 1,
        'target': '호흡', 'target_amount': 2
    })
    assert s.primitive is ResourcePrimitive.RESOURCE_CONVERSION
    assert s.conversion_mode == 'proportional'
    assert s.resource.amount == 1
    assert s.reward.amount == 2

def test_conversion_modes_are_explicit():
    for mode in ('fixed', 'proportional', 'substitution', 'transfer'):
        validate(ResourcePrimitiveSpec(
            ResourcePrimitive.RESOURCE_CONVERSION,
            resource=ResourceRef('A', 1), reward=ResourceRef('B', 1),
            conversion_mode=mode
        ))

def test_conversion_rejects_missing_mode():
    try:
        validate(ResourcePrimitiveSpec(
            ResourcePrimitive.RESOURCE_CONVERSION,
            resource=ResourceRef('A', 1), reward=ResourceRef('B', 1)
        ))
    except ValueError:
        return
    raise AssertionError('conversion mode must be explicit')
