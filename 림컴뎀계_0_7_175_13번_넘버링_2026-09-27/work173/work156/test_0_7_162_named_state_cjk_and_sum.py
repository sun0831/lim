import json
from passive_compiler_v29 import compile_one, parse_conditions
from passive_runtime_v29_base import HasStatus, Always, And

def test_cjk_named_state_presence_parses():
    text='자신에게 발각[發角]이 있으면, 적을 공격할 때 기본 스킬 마지막 코인의 피해량 +10%'
    cs=parse_conditions(text)
    assert isinstance(cs, HasStatus) and cs.name=='발각[發角]' and cs.target=='self'

def test_identity_10313_no_fake_named_resource_duplicate():
    cat=json.load(open('identity_catalog_v2.json',encoding='utf8'))['identities']
    ident=next(x for x in cat if x['id']=='identity-10313')
    passive=next(p for p in ident['passives'] if '대상의 파열과 침잠의 합 2당 피해량' in p.get('effect',''))
    rules, reasons, unsupported=compile_one(passive,'identity-10313',0)
    src=next(r for r in rules if r.source_text.startswith('대상의 파열과 침잠의 합'))
    assert len(src.effects)==1
    assert 'named_resource_damage_scaling' not in reasons
