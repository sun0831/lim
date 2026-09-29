import json, sys
from pathlib import Path
from types import SimpleNamespace
sys.path.insert(0, str(Path(__file__).resolve().parent))

from passive_compiler_v29 import compile_passive_v15
from passive_runtime_v29_base import PassiveEvent, PassiveRuntime, PassiveTrigger

CATALOG = str(Path(__file__).resolve().parent / 'identity_catalog_v2.json')

def _passive():
    data = json.load(open(CATALOG, encoding='utf-8'))['identities']
    ident = next(x for x in data if x['id'] == 'identity-10712')
    raw = next(x for x in ident['passives'] if x['name'] == '흑운도')
    return compile_passive_v15(raw, ident['id']).rules[0]

def _state(full_hp=True, defense_used=False):
    enemy = SimpleNamespace(id='enemy', hp=100 if full_hp else 80, max_hp=100, statuses={})
    owner = SimpleNamespace(id='identity-10712', hp=100, max_hp=100, statuses={})
    return SimpleNamespace(
        enemy=enemy,
        fighters={'identity-10712': owner},
        runtime={
            'turn_defense_skill_used_enemy': defense_used,
            'condition_flags': {},
        },
        event_log=[],
    )

def test_blackcloud_preserves_source_or_relation():
    rule = _passive()
    assert type(rule.conditions[0]).__name__ == 'Or'
    assert {type(c).__name__ for c in rule.conditions[0].conditions} == {
        'DefenseSkillUsedThisTurn', 'TargetMaxHPAtAttackStart'
    }

def test_blackcloud_attack_start_full_hp_triggers_damage_modifier():
    rule = _passive(); state = _state(full_hp=True, defense_used=False)
    ctx = {'state': state, 'skill': SimpleNamespace(attack_type='slash'), 'target': state.enemy}
    runtime = PassiveRuntime(); runtime.register(rule)
    runtime.emit(PassiveTrigger.BEFORE_ATTACK, ctx, state)
    assert ctx['dynamic_damage_bonus'] == 0.10

def test_blackcloud_enemy_defense_history_triggers_even_after_hp_loss():
    rule = _passive(); state = _state(full_hp=False, defense_used=True)
    ctx = {'state': state, 'skill': SimpleNamespace(attack_type='slash'), 'target': state.enemy}
    runtime = PassiveRuntime(); runtime.register(rule)
    runtime.emit(PassiveTrigger.BEFORE_ATTACK, ctx, state)
    assert ctx['dynamic_damage_bonus'] == 0.10

def test_blackcloud_does_not_trigger_when_neither_condition_is_met():
    rule = _passive(); state = _state(full_hp=False, defense_used=False)
    ctx = {'state': state, 'skill': SimpleNamespace(attack_type='slash'), 'target': state.enemy}
    runtime = PassiveRuntime(); runtime.register(rule)
    runtime.emit(PassiveTrigger.BEFORE_ATTACK, ctx, state)
    assert ctx.get('dynamic_damage_bonus', 0.0) == 0.0
