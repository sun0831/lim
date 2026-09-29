import json
from identity_catalog_v29 import IdentityCatalogV29
from one_turn_solver_v29 import OneTurnSolverV29

CAT="identity_catalog_v2.json"

def test_added_coin_is_exposed_in_action_trace_with_origin():
    cat=IdentityCatalogV29.from_json(CAT)
    ident=cat.build_identity("identity-11216")
    skill=ident.skills["S2"]
    solver=OneTurnSolverV29()
    state=solver.build_state({
        "allies":{ident.id:{"resources":{"새벽불":20}}},
        "enemy":{"hp":1000,"max_hp":1000,"statuses":{"Tremor":{"potency":5,"count":3}}}},
        {ident.id:ident})
    final_state, damage, trace=solver._execute_unopposed_coins_with_triggers(state,ident,skill,["H","H","H"],0,False)
    coins=[e for e in final_state.event_log if e.get("event")=="coin" and e.get("skill")=="112162"]
    assert len(coins)==4
    assert coins[:3] and all(e.get("is_added_coin") is False for e in coins[:3])
    assert coins[3].get("is_added_coin") is True
    assert coins[3].get("coin_origin")=="added"
