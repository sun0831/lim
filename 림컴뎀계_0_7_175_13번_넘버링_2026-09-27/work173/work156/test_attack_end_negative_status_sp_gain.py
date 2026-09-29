from types import SimpleNamespace
from special_gimmick_v2 import GimmickRegistry


def _identity(iid='i', extra=''):
    return SimpleNamespace(
        id=iid, name=iid, full_name=iid, affiliation=['RING FINGER'], skills={},
        passives=[{'type':'전투','name':'p','effect':(
            '공격 적중 시 해당 공격 스킬로 부정적인 효과를 부여했으면, '
            '공격 종료 시 자신의 정신력 4 회복 (턴당 2회)'+extra)}]
    )


def _state(i, sp=0):
    f=SimpleNamespace(id=i.id, sp=sp, max_sp=45, resources={}, statuses={})
    return SimpleNamespace(fighters={i.id:f}, runtime={}, event_log=[])


def test_negative_status_application_is_required():
    i=_identity(); g=GimmickRegistry([i], {i.id:i.passives}, [i.id]); st=_state(i,10)
    skill=SimpleNamespace(id='s',name='S1',_slot='S1',attack_type='참격')
    g.after_skill(i, skill, {'state':st,'actual_damage':10,'negative_status_applied':False})
    assert st.fighters[i.id].sp == 10
    g.after_skill(i, skill, {'state':st,'actual_damage':10,'negative_status_applied':True})
    assert st.fighters[i.id].sp == 14


def test_negative_status_sp_gain_respects_per_turn_limit():
    i=_identity(); g=GimmickRegistry([i], {i.id:i.passives}, [i.id]); st=_state(i,10)
    skill=SimpleNamespace(id='s',name='S1',_slot='S1',attack_type='참격')
    ctx={'state':st,'actual_damage':10,'negative_status_applied':True}
    g.after_skill(i,skill,ctx); g.after_skill(i,skill,ctx); g.after_skill(i,skill,ctx)
    assert st.fighters[i.id].sp == 18


def test_reaching_max_sp_queues_slash_damage_up_for_next_turn():
    i=_identity('i','\n- 이 효과로 정신력 회복 시 자신의 정신력이 최대면, 다음 턴에 참격 피해량 증가 1 얻음 (턴당 1회)')
    g=GimmickRegistry([i], {i.id:i.passives}, [i.id]); st=_state(i,41)
    skill=SimpleNamespace(id='s',name='S1',_slot='S1',attack_type='참격')
    g.after_skill(i,skill,{'state':st,'actual_damage':10,'negative_status_applied':True})
    assert st.fighters[i.id].sp == 45
    assert st.runtime['pending_next_turn_statuses'][i.id]['Slash Damage Up']['potency'] == 10


def test_actual_ring_finger_catalogs_compile_shared_rule():
    import json
    from identity_catalog_v29 import IdentityCatalogV29
    with open('identity_catalog_v2.json', encoding='utf-8') as fh:
        records=json.load(fh)['identities']
    cat=IdentityCatalogV29(records)
    for iid, limit in (('identity-10215',2),('identity-10614',3)):
        ident=cat.build_identity(iid)
        g=GimmickRegistry([ident], {ident.id:ident.passives}, [ident.id])
        rules=[r for r in g.rules if r.kind=='attack_end_negative_status_sp_gain']
        assert len(rules)==1
        assert rules[0].max_activations == limit
        assert rules[0].activation_scope == 'global'
