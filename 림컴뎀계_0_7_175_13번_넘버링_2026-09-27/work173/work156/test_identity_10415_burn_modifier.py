from types import SimpleNamespace
import json

from passive_compiler_v29 import compile_clause_template
from passive_runtime_v29_base import IdentityDeadCondition, BasicAttackSkillCondition
from keyword_runtime_v1 import KeywordRuntime
from limbus_damage_engine_v29 import Status


def _source_clause():
    catalog = json.load(open('identity_catalog_v2.json', encoding='utf-8'))
    for ident in catalog['identities']:
        if ident.get('id') == 'identity-10415':
            text = '\n'.join(p.get('effect','') for p in ident.get('passives', []))
            for line in text.splitlines():
                if '중지 제자 이스마엘 : 방어 레벨 2 증가, 기본 스킬로 부여하는 화상 위력 +1' in line:
                    return line.strip()
    raise AssertionError('source clause not found')


def test_exact_source_compiles_as_skill_scoped_burn_modifier():
    clause = _source_clause()
    rule, reasons, unsupported = compile_clause_template(clause)
    assert rule is not None
    assert not unsupported
    assert rule.trigger.value == 'CoinHit'
    assert any(isinstance(c, IdentityDeadCondition) and c.identity_id == 'identity-10814'
               for c in (rule.condition.conditions if hasattr(rule.condition, 'conditions') else (rule.condition,)))
    assert any(isinstance(c, BasicAttackSkillCondition)
               for c in (rule.condition.conditions if hasattr(rule.condition, 'conditions') else (rule.condition,)))
    assert any(type(e).__name__ == 'ModifyContext' and e.field == 'burn_potency_bonus'
               for e in rule.effects)


def test_dead_ishmael_and_basic_skill_gate_burn_bonus():
    class State:
        pass
    state = State()
    state.fighters = {
        'identity-10814': SimpleNamespace(hp=0),
        'identity-10415': SimpleNamespace(hp=100),
    }
    state.enemy = SimpleNamespace(statuses={})
    state.event_log = []
    event = SimpleNamespace(ctx={'skill_slot': 'S1', 'skill': SimpleNamespace(id='104151')})
    assert IdentityDeadCondition('identity-10814').check(event, state, 'identity-10415')
    assert BasicAttackSkillCondition().check(event, state, 'identity-10415')

    target = state.enemy
    KeywordRuntime.add(target, 'Burn', 4, 2, state=state, event=event, source_id='identity-10415')
    assert target.statuses['Burn'].potency == 4

    event.ctx['burn_potency_bonus'] = 1
    KeywordRuntime.add(target, 'Burn', 4, 2, state=state, event=event, source_id='identity-10415')
    assert target.statuses['Burn'].potency == 9
    assert target.statuses['Burn'].count == 4
