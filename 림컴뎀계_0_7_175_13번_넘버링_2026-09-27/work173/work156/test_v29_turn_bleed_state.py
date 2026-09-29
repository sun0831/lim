def _catalog():
    from one_turn_solver_v29 import IdentityCatalogV29
    records=[{'id':'a','name':'A','offense_level':0,
      'stats':{'level':60,'speed':10,'hp':1000,'hpBase':1000,'defenseLevel':0,'resistances':{}},
      'skills':{'S1':{'id':'S1','name':'S1','base_power':10,'coin_powers':[1],'coin_count':1,
        'coins':[{'coin_power':1,'damage_type':'slash','sin':'lust'}],'attack_type':'slash','sin':'lust'}},'passives':[]}]
    cat=IdentityCatalogV29(records)
    return {'a':cat.build_identity('a')}


def test_full_turn_bleed_count_carries_between_probabilistic_actions():
    from one_turn_solver_v29 import OneTurnSolverV29
    sc={'enemy':{'hp':1000,'max_hp':1000,'level':60,'defense_level':0,
        'physical_res':{'slash':1,'pierce':1,'blunt':1},'sin_res':{'lust':1},
        'statuses':{'Bleed':{'potency':1,'count':10}}},
        'allies':{'a':{'sp':0,'hp':1000,'max_hp':1000}},
        'actions':[
          {'identity_id':'a','skill_id':'S1','faces':['H'],
           'bleed_clash_probability':{'initial_defender_coins':3,'skill_power':10,
             'outcome_probabilities':[{'win':1,'draw':0,'loss':0}]}},
          {'identity_id':'a','skill_id':'S1','faces':['H'],
           'bleed_clash_probability':{'initial_defender_coins':1,'skill_power':10,
             'outcome_probabilities':[{'win':1,'draw':0,'loss':0}]}}
        ], 'passive_mode':'off'}
    r=OneTurnSolverV29().solve(sc,_catalog())
    tb=r['turn_bleed_state']
    assert tb['actions'][0]['incoming_distribution']=={10:1.0}
    assert tb['actions'][0]['outgoing_distribution']=={4:1.0}
    assert tb['actions'][1]['incoming_distribution']=={4:1.0}
    assert tb['actions'][1]['outgoing_distribution']=={3:1.0}
    assert tb['expected_final_bleed_count']==3.0
