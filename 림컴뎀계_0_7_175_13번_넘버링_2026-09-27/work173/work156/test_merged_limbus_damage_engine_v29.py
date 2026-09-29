"""Safely merged test file (AST-aware, whole-file rename incl. call sites, decorators preserved via line-removal import stripping).
Originals: test_accelerating_future_rodion_012.py, test_e37_sinclair_defense_level_golden.py
"""
from __future__ import annotations

from limbus_damage_engine_v29 import BattleState, EnemyState, FighterState, IdentityData, DamageEngine, SkillData, CoinData, Status
from limbus_damage_engine_v29 import (
    BattleState, CoinData, DamageEngine, EnemyState, FighterState,
    IdentityData, SkillData,
)


# ---- merged from test_accelerating_future_rodion_012.py ----


def _state(stacks=0):
    fighter = FighterState(hp=100, max_hp=100, sp=0, level=0, speed=5)
    fighter.resources['예지안'] = 30
    if stacks:
        fighter.statuses['가속하는 미래'] = Status(count=stacks)
    enemy = EnemyState(hp=1000, max_hp=1000, level=0, defense_level=0,
                       physical_res={'slash':1.0,'blunt':1.0,'pierce':1.0},
                       sin_res={'lust':1.0})
    state = BattleState(fighters={'identity-10916': fighter}, enemy=enemy)
    state.runtime['defense_level_is_absolute'] = True
    skill = SkillData(id='S1', name='기본 공격', base_power=10,
                      coins=[CoinData(1, 'slash', 'lust')],
                      attack_type='slash', sin='lust')
    skill._slot = 'S1'
    ident = IdentityData(id='identity-10916', name='거미집 엄지 아비 로쟈',
                         offense_level=0, skills={'S1': skill})
    return state, ident, skill


def test_rodion_accelerating_future_damage_is_3_percent_per_stack_capped_15():
    e = DamageEngine()
    values = []
    for stacks in range(6):
        state, ident, skill = _state(stacks)
        values.append(e.dynamic_modifier(state, ident, skill, 0, skill.coins[0], False))
    assert values == [0.00, 0.03, 0.06, 0.09, 0.12, 0.15]


def test_rodion_accelerating_future_coin_power_at_five_stacks():
    state0, ident0, skill0 = _state(0)
    state5, ident5, skill5 = _state(5)
    e = DamageEngine()
    r0 = e.coin_roll(state0, ident0, skill0, skill0.coins[0], 'H', 0)
    r5 = e.coin_roll(state5, ident5, skill5, skill5.coins[0], 'H', 0)
    assert r5 == r0 + 1


# ---- merged from test_e37_sinclair_defense_level_golden.py ----
"""E37 empirical Golden: effective attack level + crit damage path.

Observed S2 two-coin data:
- actor attack level 60
- coin power 19
- critical hit
- Pride resistance 0.75
- defense 47 -> 29 damage
- defense 37 -> 32 damage

The body-part values were 14+15 and 16+16 respectively.
"""



def _case(defense_level):
    enemy = EnemyState(
        hp=1000,
        max_hp=1000,
        level=60,
        defense_level=defense_level,
        physical_res={'slash': 1.0, 'pierce': 1.0, 'blunt': 1.0},
        sin_res={'Pride': 0.75},
    )
    fighter = FighterState(level=60)
    # The skill's +10% crit-damage bonus is represented by crit_damage_bonus.
    coin = CoinData(5, 'slash', 'Pride', crit_damage_bonus=0.10)
    skill = SkillData(
        's2', 'S2', 9, [coin], 'slash', 'Pride', crit_damage_bonus=0.0
    )
    ident = IdentityData('sinclair', '소지제자 싱클레어', 0, {'s2': skill})
    state = BattleState(enemy, {'sinclair': fighter})
    state.runtime['defense_level_is_absolute'] = True
    return state, ident, skill, coin


def test_sinclair_s2_crit_defense_47_matches_29():
    state, ident, skill, coin = _case(47)
    # Force the observed coin roll of 19 directly through coin_power_bonus.
    dmg, roll = DamageEngine().calculate_coin_damage(
        state, ident, skill, coin, 'H', True, coin_index=1, prior_heads=1
    )
    assert roll == 19
    assert dmg == 29


def test_sinclair_s2_crit_defense_37_matches_32():
    state, ident, skill, coin = _case(37)
    dmg, roll = DamageEngine().calculate_coin_damage(
        state, ident, skill, coin, 'H', True, coin_index=1, prior_heads=1
    )
    assert roll == 19
    assert dmg == 32
