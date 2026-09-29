from limbus_damage_engine_v29 import FighterState, EnemyState
from one_turn_solver_v29 import OneTurnSolverV29


def test_manual_hp_inputs_apply_independently_to_ally_and_enemy():
    solver = OneTurnSolverV29()
    class Ident:
        _catalog_level = 60
        _scenario_speed = 8
        affiliation = []
    ids = {'ally': Ident()}
    state = solver.build_state({
        'allies': {'ally': {'hp': 321, 'max_hp': 777}},
        'enemy': {'hp': 1234, 'max_hp': 2345},
        'actions': [],
    }, ids)
    assert state.fighters['ally'].hp == 321
    assert state.fighters['ally'].max_hp == 777
    assert state.enemy.hp == 1234
    assert state.enemy.max_hp == 2345


def test_manual_hp_values_are_not_derived_from_identity_data():
    class Ident:
        _catalog_level = 60
        _scenario_speed = 8
        affiliation = []
    solver = OneTurnSolverV29()
    state = solver.build_state({
        'allies': {'ally': {'hp': 17, 'max_hp': 29}},
        'enemy': {'hp': 31, 'max_hp': 47},
        'actions': [],
    }, {'ally': Ident()})
    assert (state.fighters['ally'].hp, state.fighters['ally'].max_hp) == (17, 29)
    assert (state.enemy.hp, state.enemy.max_hp) == (31, 47)
