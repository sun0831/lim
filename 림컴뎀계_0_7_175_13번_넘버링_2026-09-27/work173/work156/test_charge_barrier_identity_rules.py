from types import SimpleNamespace
from limbus_damage_engine_v29 import BattleState, EnemyState, FighterState, SkillData
from resource_runtime_v1 import ResourceRuntime, ResourceSpec
from special_gimmick_v2 import GimmickRegistry


def _ident(iid, name, effects, attack_type='slash'):
    s=SkillData(id=f'{iid}-s1', name='S1', base_power=1, coins=[], attack_type=attack_type, sin='wrath')
    s._slot='S1'; s._source_effects=list(effects)
    x=SimpleNamespace(id=iid,name=name,full_name=name,affiliation=['W CORP'],skills={s.id:s},passives=[])
    return x


def _state(fighters):
    e=EnemyState(hp=10,max_hp=10)
    s=BattleState(fighters={str(chr(65+i)):f for i,f in enumerate(fighters)},enemy=e)
    s.runtime['resource_runtime']=ResourceRuntime({'충전':ResourceSpec('충전',minimum=0,maximum=10), '충전 역장':ResourceSpec('충전 역장',minimum=0,maximum=99)})
    return s


def test_kill_charge_barrier_compiles_and_materializes_shield():
    ident=_ident('A','W사 3등급 정리 요원',['3코인 [적 처치 시] 충전 역장 5 얻음'])
    g=GimmickRegistry([ident], {'A':[]}, available_identity_ids=['A'])
    kinds=[r.kind for r in g.rules]
    assert 'kill_charge_barrier' in kinds
    f=FighterState(hp=100,max_hp=100,charge=0,is_wcorp=True)
    s=_state([f])
    g.after_kill(s,ident,next(iter(ident.skills.values())),{'target_died':True})
    assert s.runtime['resource_runtime'].get(f,'충전 역장') == 5
    assert f.charge_barrier_shield == 25


def test_battle_start_charge_power_cap_materializes():
    ident=_ident('A','CCA',['[전투 시작시] 충전 역장을 (2 + 자신의 충전 위력)만큼 얻음 (최대 6, 턴당 1회)'])
    f=FighterState(hp=100,max_hp=100,charge_potency=5,is_wcorp=False)
    s=_state([f]); g=GimmickRegistry([ident], {'A':[]}, available_identity_ids=['A'])
    g.after_lifecycle_event(s, {'event':'battle_start','identity_id':'A'}, {'A':ident}, 0)
    assert s.runtime['resource_runtime'].get(f,'충전 역장') == 6
    assert f.charge_barrier_shield == 18


def test_next_turn_fixed_charge_barrier_is_reserved_after_hit():
    ident=_ident('A','W사 2등급 정리 요원',['3코인 [적중시] 다음 턴에 충전 역장 2를 얻음'])
    f=FighterState(hp=100,max_hp=100); s=_state([f]); g=GimmickRegistry([ident], {'A':[]}, available_identity_ids=['A'])
    g.after_coin(s,ident,next(iter(ident.skills.values())),3,10)
    assert s.runtime.get('next_turn_state',{}).get('fighters',{}).get('A',{}).get('충전 역장') == 2

def test_charge_spend_barrier_targets_lowest_hp_ally():
    from types import SimpleNamespace
    from special_gimmick_v2 import GimmickRegistry
    from limbus_damage_engine_v29 import FighterState
    a=_ident('A','W사 3등급 정리 요원',[]); b=_ident('B','Ally B',[])
    fa=FighterState(hp=100,max_hp=100,charge=5); fb=FighterState(hp=20,max_hp=100,charge=0)
    s=BattleState(fighters={'A':fa,'B':fb},enemy=EnemyState(hp=100,max_hp=100))
    s.runtime['resource_runtime']=ResourceRuntime({'충전':ResourceSpec('충전',minimum=0,maximum=10),'충전 역장':ResourceSpec('충전 역장',minimum=0,maximum=99)})
    g=GimmickRegistry([a,b], {'A':[{'effect':'스킬로 충전 횟수를 소모할 때, 현재 체력 비율이 가장 낮은 아군 1명에게 충전 역장 3 부여'}], 'B':[]}, available_identity_ids=['A','B'])
    # synthetic passive is intentionally in the same source shape as catalog.
    s.runtime['identity_map']={'A':a,'B':b}
    from event_runtime_v1 import after_resource_event
    fa.charge=3
    out=after_resource_event(g,s,{'event':'resource_cumulative_consumed','identity_id':'A','resource':'충전','amount':2,'cumulative_before':0,'cumulative_after':2,'reason':'skill:S1:consume'},{'A':a,'B':b},1)
    assert s.runtime['resource_runtime'].get(fb,'충전 역장') == 3


def test_team_leader_charge_spend_barrier_targets_self_plus_two_lowest_charge():
    from event_runtime_v1 import after_resource_event
    a=_ident('A','W사 3등급 정리 요원 팀장',[]); b=_ident('B','B',[]); c=_ident('C','C',[])
    fighters=[FighterState(hp=100,max_hp=100,charge=6),FighterState(hp=100,max_hp=100,charge=1),FighterState(hp=100,max_hp=100,charge=2),FighterState(hp=100,max_hp=100,charge=9)]
    s=BattleState(fighters={'A':fighters[0],'B':fighters[1],'C':fighters[2],'D':fighters[3]},enemy=EnemyState(hp=100,max_hp=100))
    s.runtime['resource_runtime']=ResourceRuntime({'충전':ResourceSpec('충전',minimum=0,maximum=10),'충전 역장':ResourceSpec('충전 역장',minimum=0,maximum=99)})
    a.passives=[{'effect':'- 충전 횟수를 소모했다면, 자신과 충전 횟수를 가장 적게 보유한 아군 2명에게 충전 역장을 (충전 + 2) 부여 (최대 8, 턴 당 최대 2회 발동)'}]
    g=GimmickRegistry([a,b,c], {'A':a.passives,'B':[],'C':[]}, available_identity_ids=['A','B','C','D'])
    after_resource_event(g,s,{'event':'resource_cumulative_consumed','identity_id':'A','resource':'충전','amount':1,'cumulative_before':0,'cumulative_after':1,'reason':'skill:S1:consume'},{'A':a,'B':b,'C':c},1)
    rr=s.runtime['resource_runtime']
    assert rr.get(s.fighters['A'],'충전 역장') == 8
    assert rr.get(s.fighters['B'],'충전 역장') == 8
    assert rr.get(s.fighters['C'],'충전 역장') == 8

def test_wcorp_2nd_grade_s3_charge_spend_targets_two_lowest_hp_allies():
    ident=_ident('A','W사 2등급 정리 요원',['[사용시] 자신의 충전 횟수가 10 이상이면, 충전 횟수를 전부 소모하여 자신을 포함하여 현재 체력 비율이 낮은 아군 2명에게 (소모한 충전 횟수/2)만큼 충전 역장 부여 (소수점 버림)'])
    b=_ident('B','B',[]); c=_ident('C','C',[])
    fa=FighterState(hp=90,max_hp=100,charge=0); fb=FighterState(hp=20,max_hp=100,charge=0); fc=FighterState(hp=50,max_hp=100,charge=0)
    s=BattleState(fighters={'A':fa,'B':fb,'C':fc},enemy=EnemyState(hp=100,max_hp=100))
    s.runtime['resource_runtime']=ResourceRuntime({'충전':ResourceSpec('충전',minimum=0,maximum=10),'충전 역장':ResourceSpec('충전 역장',minimum=0,maximum=99)})
    g=GimmickRegistry([ident,b,c], {'A':[],'B':[],'C':[]}, available_identity_ids=['A','B','C'])
    ident.skills[next(iter(ident.skills))]._slot='S3'
    out=g.after_skill(ident,next(iter(ident.skills.values())),{'state':s,'fighter':fa,'consumed_resources':{'충전':11},'actual_damage':1})
    assert s.runtime['resource_runtime'].get(fb,'충전 역장') == 5
    assert s.runtime['resource_runtime'].get(fc,'충전 역장') == 5
    assert s.runtime['resource_runtime'].get(fa,'충전 역장') == 0


def test_wcorp_3rd_grade_kill_barrier_requires_fourth_coin_and_15_charge_spend():
    ident=_ident('A','W사 3등급 정리 요원',['4코인 [적 처치 시] 스킬 사용시 충전 횟수를 15 소모했다면, 자신과 자신을 제외한 무작위 아군 1명에게 충전 역장 7 부여'])
    b=_ident('B','B',[]); c=_ident('C','C',[])
    fa=FighterState(hp=100,max_hp=100,charge=0); fb=FighterState(hp=100,max_hp=100,charge=0); fc=FighterState(hp=100,max_hp=100,charge=0)
    s=BattleState(fighters={'A':fa,'B':fb,'C':fc},enemy=EnemyState(hp=1,max_hp=1))
    s.runtime['resource_runtime']=ResourceRuntime({'충전':ResourceSpec('충전',minimum=0,maximum=10),'충전 역장':ResourceSpec('충전 역장',minimum=0,maximum=99)})
    g=GimmickRegistry([ident,b,c], {'A':[],'B':[],'C':[]}, available_identity_ids=['A','B','C'])
    s.runtime['current_action_resource_consumption']={'충전':15}
    g.after_kill(s,ident,next(iter(ident.skills.values())),{'coin_index':4,'consumed_resources':{'충전':15}})
    assert s.runtime['resource_runtime'].get(fa,'충전 역장') == 7
    allies=[s.runtime['resource_runtime'].get(fb,'충전 역장'),s.runtime['resource_runtime'].get(fc,'충전 역장')]
    assert allies in ([7,0],[0,7])


def test_aedd_charge_barrier_is_substituted_to_high_voltage_shell():
    from resource_runtime_v1 import ResourceRuntime, ResourceSpec
    from types import SimpleNamespace
    st = SimpleNamespace(fighters={}, runtime={'charge_barrier_substitution': {'identity-11215': '고전압 외피'}}, event_log=[])
    f = SimpleNamespace(id='identity-11215', resources={}, shield=0.0, charge_barrier_shield=0.0)
    st.fighters[f.id] = f
    rr = ResourceRuntime({'충전 역장': ResourceSpec('충전 역장', minimum=0, maximum=99),
                          '고전압 외피': ResourceSpec('고전압 외피', minimum=0, maximum=99)})
    rr.gain_charge_barrier(f, 3, state=st, reason='rule:test')
    assert rr.get(f, '충전 역장') == 0
    assert rr.get(f, '고전압 외피') == 3
    assert f.shield == 0
    assert f.charge_barrier_shield == 0
    assert any(e.get('event') == 'resource_substitution' for e in st.event_log)


def test_non_aedd_charge_barrier_still_materializes_normally():
    from resource_runtime_v1 import ResourceRuntime, ResourceSpec
    from types import SimpleNamespace
    st = SimpleNamespace(fighters={}, runtime={'charge_barrier_substitution': {}}, event_log=[])
    f = SimpleNamespace(id='other', resources={}, shield=0.0, charge_barrier_shield=0.0, is_wcorp=False)
    st.fighters[f.id] = f
    rr = ResourceRuntime({'충전 역장': ResourceSpec('충전 역장', minimum=0, maximum=99)})
    rr.gain_charge_barrier(f, 2, state=st, reason='rule:test')
    assert rr.get(f, '충전 역장') == 2
    assert f.shield == 6
    assert f.charge_barrier_shield == 6
