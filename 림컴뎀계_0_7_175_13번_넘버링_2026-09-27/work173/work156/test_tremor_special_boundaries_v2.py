import json
from copy import deepcopy
from identity_catalog_v29 import IdentityCatalogV29
from one_turn_solver_v29 import OneTurnSolverV29
from skill_text_parser_v19 import SkillTextParserV19

CAT='identity_catalog_v2.json'

def _identity(i):
    d=json.load(open(CAT)); return next(x for x in d['identities'] if x['id']==i)

def _skill_raw(i,sid):
    return next(s for s in _identity(i)['skills'] if s['id']==sid)

def test_11216_added_coin_rule_is_split_from_added_coin_hit_effect():
    raw=_skill_raw('identity-11216','112162')['effects']
    parsed, rep=SkillTextParserV19().parse(raw,3)
    assert not rep.unsupported
    rules=parsed['added_coin_rules']
    assert len(rules)==1
    rule=rules[0]
    assert rule['condition']=={'type':'resource_gte','resource':'새벽불','value':20}
    assert rule['source_coin_index']==2
    assert rule['unbreakable'] is True
    assert rule['effects'][0]['type']=='tremor_burst'
    assert rule['effects'][0]['condition']=={'type':'added_coin_hit'}
    assert rule['effects'][0]['count_cost']==1

def test_11216_added_coin_executes_and_consumes_explicit_count():
    cat=IdentityCatalogV29.from_json(CAT)
    ident=cat.build_identity('identity-11216')
    skill=ident.skills['S2']
    solver=OneTurnSolverV29()
    state=solver.build_state({'allies':{ident.id:{'resources':{'새벽불':20}}},
                              'enemy':{'hp':1000,'max_hp':1000,'statuses':{'Tremor':{'potency':5,'count':3}}}}, {ident.id:ident})
    final_state, damage, trace=solver._execute_unopposed_coins_with_triggers(state,ident,skill,['H','H','H'],0,False)
    coins=[e for e in final_state.event_log if e.get('event')=='coin' and e.get('skill')=='112162']
    bursts=[e for e in final_state.event_log if e.get('event')=='tremor_burst']
    assert len(coins)==4
    assert bursts and bursts[-1]['count_after']==6
    assert final_state.enemy.statuses['Tremor'].count==6

def test_10414_replacement_uses_existing_loneliness_and_skips_new_application():
    cat=IdentityCatalogV29.from_json(CAT)
    ident=cat.build_identity('identity-10414')
    skill=ident.skills['S3']
    solver=OneTurnSolverV29()
    state=solver.build_state({'allies':{ident.id:{}},
                              'enemy':{'hp':1000,'max_hp':1000,'statuses':{'고독':{'potency':1,'count':1},'Tremor':{'potency':5,'count':3}}}}, {ident.id:ident})
    solver.core.machine.engine.simulate_coin(state,ident,skill,skill.coins[2],'H',False,3,0)
    assert state.enemy.statuses['고독'].count==1
    assert state.enemy.statuses['Tremor'].count==2
    assert any(e.get('event')=='tremor_burst' for e in state.event_log)
