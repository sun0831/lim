import json
from passive_compiler_v29 import compile_one
from passive_runtime_v29_base import HasStatus, ModifyContext


def _passive():
    cat=json.load(open('identity_catalog_v2.json',encoding='utf-8'))
    for ident in cat['identities']:
        if ident['id']=='identity-10615':
            return next(p for p in ident['passives'] if p['name']=='추쇄건[推刷巾]')
    raise AssertionError('passive missing')


def test_speed_damage_modifier_is_doubled_only_when_named_status_exists():
    rules, reasons, unsupported = compile_one(_passive(),'identity-10615',0)
    speed_rules=[r for r in rules if r.source_text.startswith('자신의 속도가')]
    doubled=[r for r in rules if '2배로 적용' in r.source_text]
    assert speed_rules
    assert doubled
    assert any(isinstance(e, ModifyContext) and e.field=='dynamic_damage_bonus' for e in doubled[0].effects)
    assert isinstance(doubled[0].conditions, HasStatus) and doubled[0].conditions.name=='포박 [홍루]' and doubled[0].conditions.target=='enemy'
    assert 'conditional_damage_modifier_double' in reasons
