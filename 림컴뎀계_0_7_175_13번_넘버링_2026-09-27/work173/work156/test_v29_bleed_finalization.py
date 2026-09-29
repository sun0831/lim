from test_v29_turn_bleed_state import _catalog
from one_turn_solver_v29 import OneTurnSolverV29


def _base_enemy(count=10):
    return {
        'hp': 1000, 'max_hp': 1000, 'level': 60, 'defense_level': 0,
        'physical_res': {'slash': 1, 'pierce': 1, 'blunt': 1},
        'sin_res': {'lust': 1},
        'statuses': {'Bleed': {'potency': 1, 'count': count}},
    }


def test_final_trimmed_bleed_count_uses_terminal_state_not_initial_minus_proc():
    # The action gains Bleed after its probabilistic clash.  Final Count is
    # therefore not derivable from initial_count - total_proc.
    sc = {
        'enemy': _base_enemy(10),
        'allies': {'a': {'sp': 0, 'hp': 1000, 'max_hp': 1000}},
        'actions': [{
            'identity_id': 'a', 'skill_id': 'S1', 'faces': ['H'],
            'bleed_clash_probability': {
                'initial_attacker_coins': 1, 'initial_defender_coins': 1,
                'outcome_probabilities': {'win': 1, 'draw': 0, 'loss': 0},
            },
            'resource_gain': {},
        }],
        'passive_mode': 'off',
    }
    result = OneTurnSolverV29().solve(sc, _catalog())
    tb = result['turn_bleed_state']
    # With a 1-coin enemy win, one Bleed proc is consumed.  No gain is present,
    # so the terminal count is 9 and the trimmed projection must agree exactly.
    assert tb['trimmed_final_bleed_distribution'] == {9: 1.0}
    assert tb['expected_final_bleed_count_trimmed'] == 9.0


def test_infinite_bleed_keeps_terminal_count_fixed_even_after_trim():
    sc = {
        'enemy': _base_enemy(7),
        'allies': {'a': {'sp': 0, 'hp': 1000, 'max_hp': 1000}},
        'bleed_count_infinite': True,
        'actions': [{
            'identity_id': 'a', 'skill_id': 'S1', 'faces': ['H'],
            'bleed_clash_probability': {
                'initial_attacker_coins': 1, 'initial_defender_coins': 2,
                'outcome_probabilities': {'win': 0.5, 'draw': 0.5, 'loss': 0},
            },
        }],
        'passive_mode': 'off',
    }
    result = OneTurnSolverV29().solve(sc, _catalog())
    tb = result['turn_bleed_state']
    assert tb['final_bleed_distribution'] == {7: 1.0}
    assert tb['trimmed_final_bleed_distribution'] == {7: 1.0}
    assert tb['expected_final_bleed_count_trimmed'] == 7.0


def test_turn_trim_is_not_applied_to_intermediate_action_diagnostic():
    sc = {
        'enemy': _base_enemy(10),
        'allies': {'a': {'sp': 0, 'hp': 1000, 'max_hp': 1000}},
        'actions': [{
            'identity_id': 'a', 'skill_id': 'S1', 'faces': ['H'],
            'bleed_clash_probability': {
                'initial_attacker_coins': 1, 'initial_defender_coins': 1,
                'outcome_probabilities': {'win': 1, 'draw': 0, 'loss': 0},
            },
        }],
        'passive_mode': 'off',
    }
    result = OneTurnSolverV29().solve(sc, _catalog())
    bp = result['actions'][0]['bleed_probability']
    assert bp['trim_scope'] == 'action_local_diagnostic_only'
    assert result['turn_bleed_state']['trim_scope'] == 'whole_turn_final_bleed_proc_distribution'
