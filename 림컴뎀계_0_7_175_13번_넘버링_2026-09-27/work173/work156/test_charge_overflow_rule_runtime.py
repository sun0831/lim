from limbus_damage_engine_v29 import IdentityData, SkillData, CoinData
from one_turn_solver_v29 import OneTurnSolverV29


def _identity(passive_text):
    return IdentityData(
        id='x', name='X', offense_level=60,
        skills={'S1': SkillData(
            id='S1', name='S1', base_power=10,
            coins=[CoinData(0, 'slash', 'lust')],
            attack_type='slash', sin='lust',
            resource_gain={'충전': 5},
        )},
        passives=[{'id': 'p', 'name': 'overcap', 'effect': passive_text}],
    )


def _solve(identity, charge):
    scenario = {
        'coin_mode': 'fixed',
        'resource_specs': {'충전': {'maximum': 10}, '충전 역장': {'maximum': 99}},
        'allies': {'x': {'sp': 0, 'charge': charge}},
        'enemy': {'hp': 1000, 'max_hp': 1000, 'level': 60,
                  'defense_level': 60, 'physical_res': {'slash': 1}},
        'actions': [{'identity_id': 'x', 'skill_id': 'S1', 'faces': ['H']}],
    }
    return OneTurnSolverV29().solve(scenario, {'x': identity})


def test_charge_overflow_support_rule_enters_next_turn_charge_field():
    text = ('전투 시작시 편성 순서가 가장 빠른 아군이 자신의 스킬로 '
            '충전 횟수 최대치를 초과하여 충전 횟수를 얻으면, 초과한 충전 횟수 1 당 '
            '다음 턴에 충전 역장 1 얻음 (최대 3. E.G.O 스킬 포함)')
    r = _solve(_identity(text), 8)
    assert r['next_turn_state']['fighters']['x']['충전 역장'] == 3
    assert any(e.get('event') == 'next_turn_resource_gain' and e.get('amount') == 3
               for e in r['event_log'])


def test_charge_overflow_damage_bonus_is_same_skill_only_and_capped():
    text = ('자신의 스킬로 충전 횟수 최대치를 초과하여 충전 횟수를 얻으면, '
            '최대치를 초과한 충전 횟수 1 당 해당 스킬 피해량 +3% (최대 15%)')
    r1 = _solve(_identity(text), 8)   # overflow 3 -> +9%
    r2 = _solve(_identity(text), 10)  # overflow 5 -> +15%
    assert r1['actions'][0]['skill_id'] == 'S1'
    assert any(e.get('event') == 'charge_overflow_skill_damage_bonus' and e.get('damage_bonus') == 0.09
               for e in r1['event_log'])
    assert any(e.get('event') == 'charge_overflow_skill_damage_bonus' and e.get('damage_bonus') == 0.15
               for e in r2['event_log'])
    assert r2['turn_damage'] > r1['turn_damage']
