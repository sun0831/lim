from passive_compiler_v29 import compile_clause_template
from passive_runtime_v29_base import HasStatus


def test_desperation_negative_sp_damage_requires_desperation_state():
    text = '절망 상태일 때, 기본 스킬로 가하는 피해량이 (-정신력 / 2)%만큼 증가 (최대 20%)'
    rule, reasons, unsupported = compile_clause_template(text)
    assert any(type(c).__name__ == 'HasStatus' and c.name == '절망' and c.target == 'self' for c in getattr(rule.condition, 'conditions', ()))
    assert type(rule.condition).__name__ == 'And'
    assert 'negative_self_sp_scaling' in reasons
    assert not unsupported


def test_real_10913_passive_preserves_desperation_gate():
    import json
    with open('identity_catalog_v2.json', encoding='utf-8') as f:
        cat = json.load(f)
    rec = next(x for x in cat['identities'] if x.get('id') == 'identity-10913')
    passive = next(x for x in rec.get('passives', []) if x.get('name') == '정의의 마법소녀 / 절망의 기사')
    rule, reasons, unsupported = compile_clause_template(passive['effect'])
    assert any(type(c).__name__ == 'HasStatus' and c.name == '절망' and c.target == 'self' for c in getattr(rule.condition, 'conditions', ()))
    assert 'negative_self_sp_scaling' in reasons
    assert not unsupported
