from test_v29_turn_bleed_state import _catalog
from one_turn_solver_v29 import OneTurnSolverV29


def test_final_bleed_trim_reweights_correlated_turn_damage():
    sc = {
        'enemy': {
            'hp': 1000, 'max_hp': 1000, 'level': 60, 'defense_level': 60,
            'physical_res': {'slash': 1, 'pierce': 1, 'blunt': 1},
            'sin_res': {'lust': 1},
            'statuses': {'Bleed': {'potency': 1, 'count': 10}},
        },
        'allies': {'a': {'sp': 0, 'hp': 1000, 'max_hp': 1000}},
        'actions': [{
            'identity_id': 'a', 'skill_id': 'S1', 'faces': ['H'],
            'bleed_clash_probability': {
                'initial_attacker_coins': 1,
                'initial_defender_coins': 2,
                'skill_power': 10,
                # Loss: 2 Bleed procs and no surviving unopposed coin.
                # Win: 3 Bleed procs and one unopposed coin, hence damage.
                'outcome_probabilities': {'win': 0.1, 'draw': 0.0, 'loss': 0.9},
            },
        }],
        'passive_mode': 'off',
    }
    result = OneTurnSolverV29().solve(sc, _catalog())
    tb = result['turn_bleed_state']

    assert tb['total_bleed_proc_distribution'] == {2: 0.9, 3: 0.1}
    assert tb['expected_turn_damage_raw'] > tb['expected_turn_damage_trimmed']
    assert abs(tb['expected_turn_damage_raw'] - 0.11) < 1e-9
    assert abs(tb['expected_turn_damage_trimmed'] - (0.05 / 0.9) * 1.1) < 1e-9
    assert tb['joint_bleed_proc_damage'][2]['expected_damage_given_proc'] == 0.0
    assert tb['joint_bleed_proc_damage'][3]['expected_damage_given_proc'] > 0.0
