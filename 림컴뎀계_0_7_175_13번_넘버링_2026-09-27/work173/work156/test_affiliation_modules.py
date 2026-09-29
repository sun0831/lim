"""병합 테스트: affiliation_modules

원본 파일 (내용은 AST 병합기로 합쳤고 테스트 본문은 바꾸지 않음):
  - test_v66_module_loading.py
  - test_v67_identity_module_manifest.py
  - test_v68_combat_affiliation_classification.py
  - test_v68_keyword_affiliation_file_split.py
  - test_v69_affiliation_keyword_classification.py
  - test_v70_rule_module_split.py
  - test_v71_full_combat_affiliation_axis.py
  - test_v72_affiliation_runtime.py
  - test_v95_generic_affiliation_resource.py
이름 충돌 helper 는 `이름__vNN` 으로 분리했다. 매핑은 tools/MERGE_MAP.json 참고.
"""
import json
from types import SimpleNamespace
from gimmick_module_registry_v1 import ModuleResolver, resolve_identity_manifest
from special_gimmick_v2 import GimmickRegistry, GimmickRule
from pathlib import Path
from copy import deepcopy
from affiliation_runtime_v1 import AffiliationResolver
from effect_runtime_v1 import EffectRuntime
from effect_executor_v1 import EffectExecutor
from rule_migration_runtime_v1 import RuleMigrationRuntime
from trigger_runtime_v1 import TriggerRule, TriggerCondition, TriggerEffect



# ======================================================================
# 원본: test_v66_module_loading.py
# ======================================================================

def ident(i, name, affiliation=(), keywords=(), resources=(), passives=()):
    return SimpleNamespace(
        id=i, name=name, full_name=name, affiliation=list(affiliation),
        keywords=list(keywords), resources=list(resources), passives=list(passives),
        skills={},
    )

def test_bio_material_is_charge_keyword_and_ring_is_identity_module():
    ring = ident('ring1', '거미집 약지 아비', ('RING FINGER', 'SPIDER HOUSE'), (), ('생체 재료',))
    m = resolve_identity_manifest(ring)
    assert 'charge' in m.keywords
    assert 'ring' in m.gimmick_modules
    assert '생체 재료' in m.resources
    assert 'bio_material' not in m.modules

def test_only_selected_identity_modules_are_loaded():
    dawn = ident('d', '새벽 사무소 해결사', ('DAWN',), ('화상',))
    normal = ident('n', '일반 인격', (), ('출혈',))
    resolver = ModuleResolver([dawn, normal])
    assert resolver.enabled('dawn_office')
    assert not resolver.enabled('ring')
    assert resolver.enabled('burn')
    assert resolver.enabled('bleed')
    assert 'dawn_office' in resolver.loaded_module_providers
    assert 'ring' not in resolver.loaded_module_providers

def test_middle_and_pequod_are_identity_modules_not_global_rules():
    middle = ident('m', '중지 작은 형님', ('MIDDLE FINGER',))
    pequod = ident('p', '피쿼드호 선장', ('PEQUOD CREW',))
    normal = ident('n', '일반 인격')
    resolver = ModuleResolver([middle, pequod, normal])
    assert resolver.required_for('m') == ('middle',)
    assert resolver.required_for('p') == ('pequod',)
    assert resolver.required_for('n') == ()

def test_registry_exposes_active_module_manifest():
    ring = ident('ring1', '거미집 약지 아비', ('RING FINGER',), resources=('생체 재료',))
    reg = GimmickRegistry([ring], {ring.id: []}, available_identity_ids=[ring.id])
    assert 'ring' in reg.active_modules
    assert 'charge' in reg.active_modules
    assert reg.module_resolver.required_for(ring.id) == ('charge', 'ring', 'spider_house')

def test_keywords_and_affiliations_are_independent_axes():
    ring_charge = ident('rc', '거미집 약지 인격', ('RING FINGER', 'SPIDER HOUSE'), ('충전',), ('생체 재료',))
    m = resolve_identity_manifest(ring_charge)
    assert m.keyword_modules == ('charge',)
    assert m.affiliation_modules == ('ring', 'spider_house')
    assert set(m.modules) == {'charge', 'ring', 'spider_house'}

def test_manifest_summary_exposes_two_axes_separately():
    dawn = ident('d', '새벽 사무소', ('DAWN',), ('화상',))
    ring = ident('r', '약지', ('RING FINGER',), ('충전',), ('생체 재료',))
    resolver = ModuleResolver([dawn, ring])
    summary = resolver.summary()
    assert summary['active_keyword_modules'] == ['burn', 'charge']
    assert summary['active_affiliation_modules'] == ['dawn_office', 'ring']
    assert summary['identity_manifests']['r']['keyword_modules'] == ['charge']
    assert summary['identity_manifests']['r']['affiliations'] == ['ring']


# ======================================================================
# 원본: test_v67_identity_module_manifest.py
# ======================================================================
ROOT = Path(__file__).resolve().parent

def test_all_identities_have_independent_keyword_and_affiliation_axes():
    manifest = json.loads((ROOT / 'identity_module_manifest_v1.json').read_text(encoding='utf-8'))
    rows = manifest['identities']
    assert len(rows) == 184
    valid = {'charge','bleed','poise','tremor','burn','rupture','sinking'}
    for row in rows:
        assert row['identity_id']
        assert set(row['keywords']) <= valid
        assert isinstance(row['affiliations'], list)
        assert isinstance(row['gimmick_modules'], list)

def test_keyword_counts_are_not_mutually_exclusive():
    manifest = json.loads((ROOT / 'identity_module_manifest_v1.json').read_text(encoding='utf-8'))
    rows = manifest['identities']
    total_labels = sum(len(x['keywords']) for x in rows)
    assert total_labels > len(rows)

def test_bio_material_is_charge_and_ring_is_separate():
    rows = {x['identity_id']: x for x in json.loads((ROOT / 'identity_module_manifest_v1.json').read_text(encoding='utf-8'))['identities']}
    bio = [x for x in rows.values() if '생체 재료' in x['full_name'] or 'ring' in x['gimmick_modules']]
    assert any('charge' in x['keywords'] and 'ring' in x['gimmick_modules'] for x in bio)


# ======================================================================
# 원본: test_v68_combat_affiliation_classification.py
# ======================================================================

def test_combat_affiliation_is_separate_from_raw_affiliation():
    data=json.loads((ROOT/'identity_module_manifest_v1.json').read_text(encoding='utf-8'))
    for row in data['identities']:
        assert 'affiliations' in row
        assert 'combat_affiliations' in row
        assert set(row['combat_affiliations']) <= set(data['axes']['gimmick_modules'])

def test_known_combat_groups_are_multilabel_and_not_exclusive():
    data=json.loads((ROOT/'identity_module_manifest_v1.json').read_text(encoding='utf-8'))
    rows=data['identities']
    assert sum(len(r['combat_affiliations']) for r in rows) > 0
    assert any(len(r['combat_affiliations']) >= 2 for r in rows)

def test_spider_house_cross_identity_members_are_combat_participants():
    data=json.loads((ROOT/'identity_module_manifest_v1.json').read_text(encoding='utf-8'))
    rows={r['identity_id']:r for r in data['identities']}
    for iid in ['identity-10115','identity-10215','identity-10415','identity-11115']:
        assert 'spider_house' in rows[iid]['combat_affiliations']

def test_pequod_membership_is_combat_relevant_because_captain_targets_pequod_allies():
    data=json.loads((ROOT/'COMBAT_AFFILIATION_AUDIT_0.6.14.json').read_text(encoding='utf-8'))
    assert len(data['modules']['pequod']['members']) == 3

def test_custom_identity_uses_known_combat_affiliation_axis():
    x=SimpleNamespace(id='x',name='피쿼드호 선원',full_name='피쿼드호 선원',affiliation=['PEQUOD CREW'],keywords=[],resources=[],passives=[],skills={})
    m=resolve_identity_manifest(x)
    assert 'pequod' in m.affiliation_modules


# ======================================================================
# 원본: test_v68_keyword_affiliation_file_split.py
# ======================================================================

def test_identity_keyword_affiliation_matrix_covers_catalog():
    root=Path(__file__).parent
    cat=json.loads((root/'identity_catalog_v2.json').read_text(encoding='utf-8'))
    matrix=json.loads((root/'identity_keyword_affiliation_matrix_v1.json').read_text(encoding='utf-8'))
    assert matrix['identity_count']==len(cat['identities'])==184
    assert {x['identity_id'] for x in matrix['identities']}=={x['id'] for x in cat['identities']}
    assert matrix['axes']['generic_keywords']==['charge','bleed','poise','tremor','burn','rupture','sinking']

def test_affiliation_rule_ownership_is_module_local():
    import gimmick_modules.middle as middle
    import gimmick_modules.ring as ring
    import gimmick_modules.spider_house as spider
    import gimmick_modules.black_cloud as black_cloud
    import gimmick_modules.pequod as pequod
    import gimmick_modules.dawn_office as dawn
    assert middle.owns_rule('middle_revenge_hit')
    assert ring.owns_rule('bio_material_skill_damage')
    assert spider.owns_rule('foresight_start')
    assert black_cloud.owns_rule('blackcloud_received_s1')
    assert pequod.owns_rule('captain_right_assist')
    class R:
        kind='resource_gain'; source_text='새벽불 2 얻음'
    assert dawn.owns_resource_gain_rule(R())


# ======================================================================
# 원본: test_v69_affiliation_keyword_classification.py
# ======================================================================
ROOT__v69_affiliation = Path(__file__).parent

def load(name):
    return json.loads((ROOT__v69_affiliation / name).read_text(encoding='utf-8'))

def test_affiliation_taxonomy_confirms_cross_identity_groups():
    d=load('affiliation_taxonomy_v1.json')['affiliations']
    expected={'blade_lineage','thumb','index','middle','ring','pequod','black_cloud','spider_house','seven','zwei','liu','n_corp','w_corp','full_stop','la_mancha_land','dawn_office'}
    assert expected <= {k for k,v in d.items() if v['combat_relevance']=='confirmed'}

def test_lore_only_groups_are_not_auto_promoted_by_membership_alone():
    d=load('affiliation_taxonomy_v1.json')['affiliations']
    for k in ['cinq','dieci','shi','devyat','oufi','pinky','lce']:
        assert d[k]['combat_relevance']=='unverified'

def test_bio_material_is_charge_equivalent_only():
    d=load('keyword_resource_classification_v1.json')
    rows={x['resource_name']:x for x in d['resources']}
    assert rows['생체 재료']['classification']=='keyword_equivalent'
    assert rows['생체 재료']['keyword']=='charge'
    for name in ['탄환','지령','얽힘','문신','열기','예지안','가속탄','불꽃나비의 관','새벽불','짝패']:
        if name in rows:
            assert rows[name]['classification']=='dedicated_resource'

def test_manifest_marks_bio_material_identities():
    d=load('identity_module_manifest_v1.json')['identities']
    m={x['identity_id']:x for x in d}
    assert m['identity-10215']['keyword_equivalent_resources']==['생체 재료']
    assert m['identity-10614']['keyword_equivalent_resources']==['생체 재료']


# ======================================================================
# 원본: test_v70_rule_module_split.py
# ======================================================================

def ident__v70_rule(i, name='x', affiliation=(), keywords=(), resources=()):
    return SimpleNamespace(id=i, name=name, full_name=name, affiliation=list(affiliation), keywords=list(keywords), resources=list(resources), passives=[], skills={})

def test_common_and_identity_specific_providers_are_separate():
    from gimmick_modules import common, identity_specific
    assert common.owns_rule('assist')
    assert common.owns_rule('extra_damage')
    assert identity_specific.owns_rule('forced_skill')
    assert identity_specific.owns_rule('reused_status_damage')
    assert not common.owns_rule('forced_skill')
    assert not identity_specific.owns_rule('assist')

def test_registry_routes_non_affiliation_rules_to_split_providers():
    a = ident__v70_rule('a')
    reg = GimmickRegistry([a], {a.id: []}, available_identity_ids=[a.id])
    common_kinds = {'assist', 'stagger_assist', 'support_left_assist', 'support_right_assist', 'ally_hit_followup', 'received_attack_followup', 'clash_loss_followup', 'defense_clash_loss_followup', 'kill_resource_gain', 'kill_resource_distribute', 'kill_lowest_ally_heal', 'enemy_death_lowest_ally_heal', 'target_death_resource_gain', 'lowest_ammo_poise', 'extra_damage', 'resource_start', 'cumulative_resource_gain'}
    identity_kinds = {'enemy_hp_followup', 'forced_skill', 'conditional_assist', 'reused_status_damage'}
    for kind in common_kinds:
        assert reg.module_resolver.loaded_module_providers['common'].owns_rule(kind)
    for kind in identity_kinds:
        assert reg.module_resolver.loaded_module_providers['identity_specific'].owns_rule(kind)

def test_module_resolver_deepcopy_keeps_provider_modules_shallow():
    a = ident__v70_rule('a', keywords=('출혈',))
    resolver = ModuleResolver([a])
    clone = deepcopy(resolver)
    assert clone is not resolver
    assert clone.loaded_module_providers['common'] is resolver.loaded_module_providers['common']
    assert clone.loaded_module_providers['identity_specific'] is resolver.loaded_module_providers['identity_specific']
    assert clone.loaded_module_providers['bleed'] is resolver.loaded_module_providers['bleed']

def test_affiliation_rules_still_precede_generic_split_rules():
    a = ident__v70_rule('a', affiliation=('RING FINGER',), resources=('생체 재료',))
    reg = GimmickRegistry([a], {a.id: []}, available_identity_ids=[a.id])
    rule = GimmickRule(a.id, '생체 재료 획득', 'bio_material_skill_damage', (), a.name, '생체 재료', 99, 0)
    rule.module = 'ring'
    built = reg.module_resolver.loaded_module_providers['ring'].build_trigger(reg, rule)
    assert built and built[0] == 'after_skill'


# ======================================================================
# 원본: test_v71_full_combat_affiliation_axis.py
# ======================================================================
CONFIRMED={'black_cloud','blade_lineage','dawn_office','full_stop','index','la_mancha_land','liu','middle','n_corp','pequod','ring','seven','spider_house','thumb','w_corp','zwei'}

def test_all_confirmed_affiliations_are_present_on_manifest_axis():
    data=json.loads((ROOT/'identity_module_manifest_v1.json').read_text(encoding='utf8'))
    rows=data['identities']
    seen={x for r in rows for x in r['combat_affiliations']}
    assert seen == CONFIRMED
    assert all(set(r['gimmick_modules']) == set(r['combat_affiliations']) for r in rows)

def test_confirmed_affiliation_membership_matches_taxonomy():
    manifest=json.loads((ROOT/'identity_module_manifest_v1.json').read_text(encoding='utf8'))
    taxonomy=json.loads((ROOT/'affiliation_taxonomy_v1.json').read_text(encoding='utf8'))
    rows={r['identity_id']:set(r['combat_affiliations']) for r in manifest['identities']}
    for aid,e in taxonomy['affiliations'].items():
        if e['combat_relevance'] != 'confirmed':
            continue
        expected=set(e['members'])
        actual={iid for iid,tags in rows.items() if aid in tags}
        assert actual == expected, aid

def test_custom_identity_fallback_recognizes_expanded_affiliation_axis():
    for alias, module in [('BLADE LINEAGE','blade_lineage'),('THUMB FINGER','thumb'),('INDEX FINGER','index'),('SEVEN','seven'),('ZWEI','zwei'),('LIU','liu'),('N사','n_corp'),('W CORP','w_corp'),('FULL STOP','full_stop'),('LA MANCHA LAND','la_mancha_land')]:
        x=SimpleNamespace(id='x',name='x',full_name='x',affiliation=[alias],keywords=[],resources=[],passives=[],skills={})
        assert module in resolve_identity_manifest(x).affiliation_modules


# ======================================================================
# 원본: test_v72_affiliation_runtime.py
# ======================================================================

def ident__v72_affiliation(i, aff):
    return SimpleNamespace(id=i, affiliation=[aff], name=i, full_name=i)

def test_members_and_count_are_formation_stable():
    ids = [ident__v72_affiliation('a', 'BLADE LINEAGE'), ident__v72_affiliation('b', 'OTHER'), ident__v72_affiliation('c', 'BLADE LINEAGE')]
    r = AffiliationResolver(ids, ['a', 'b', 'c'])
    assert [x.identity_id for x in r.members('BLADE LINEAGE')] == ['a', 'c']
    assert r.count('BLADE LINEAGE') == 2

def test_lowest_selection_reuses_generic_affiliation_axis():
    ids = [ident__v72_affiliation('a', 'RING FINGER'), ident__v72_affiliation('b', 'RING FINGER'), ident__v72_affiliation('c', 'OTHER')]
    r = AffiliationResolver(ids, ['a', 'b', 'c'])
    vals = {'a': 5, 'b': 2, 'c': 0}
    x = r.select_lowest('RING FINGER', lambda ident, iid: vals[iid])
    assert x.identity_id == 'b'

def test_dead_filter_and_exclusion():
    ids = [ident__v72_affiliation('a', 'RING FINGER'), ident__v72_affiliation('b', 'RING FINGER')]
    fighters = {'a': SimpleNamespace(hp=0), 'b': SimpleNamespace(hp=10)}
    state = SimpleNamespace(fighters=fighters)
    r = AffiliationResolver(ids, ['a', 'b'])
    assert [x.identity_id for x in r.members('RING FINGER', include_dead=False, state=state, exclude_ids=['b'])] == []
    assert [x.identity_id for x in r.members('RING FINGER', include_dead=False, state=state)] == ['b']


# ======================================================================
# 원본: test_v95_generic_affiliation_resource.py
# ======================================================================

def test_affiliation_count_resource_effect_is_generic():
    assert EffectRuntime.is_generic_executable('resource_gain_affiliation_count')
    assert RuleMigrationRuntime._effect_state('resource_gain_affiliation_count') == 'generic'

def test_affiliation_count_resource_executes_through_common_executor():
    class F:
        def __init__(self, ident):
            self.id = ident
            self.resources = {}
            self.hp = 100
    a = SimpleNamespace(id='A', affiliation=['Ring'])
    b = SimpleNamespace(id='B', affiliation=['Ring'])
    c = SimpleNamespace(id='C', affiliation=['Other'])
    fa, fb, fc = F('A'), F('B'), F('C')
    state = SimpleNamespace(fighters={'A': fa, 'B': fb, 'C': fc}, runtime={}, event_log=[])
    resolver = AffiliationResolver([a, b, c], ['A','B','C'])
    from effect_runtime_v1 import EffectRuntime
    from rule_ir_v1 import EffectIR
    cmd = EffectRuntime().resolve(EffectIR('resource_gain_affiliation_count', {
        'resource':'생체 재료', 'affiliation':'Ring', 'multiplier':2, 'cap':10,
    }), {}, 'rule:test')
    result = EffectExecutor().execute(cmd, {
        'state': state, 'rule_owner_id':'A', 'actor':fa,
        'affiliation_resolver':resolver,
    })
    assert result == 4
    assert fa.resources['생체 재료'] == 4
