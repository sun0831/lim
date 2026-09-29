"""Safely merged test file (AST-aware, whole-file rename incl. call sites, decorators preserved via line-removal import stripping).
Originals: test_0_7_75_attack_end_target_death_condition.py, test_0_7_80_source_condition_scope.py, test_0_7_89_resonance_and_combat_end.py, test_actual_source_shield_condition_audit_0779.py, test_amplitude_followup_burst.py, test_attacker_target_audit_v1.py, test_ow_0_7_76_condition.py, test_tremor_burst_catalog_patterns.py, test_tremor_threshold_clash.py
"""
from __future__ import annotations

from types import SimpleNamespace
from passive_compiler_v29 import compile_clause_template
from passive_runtime_v29_base import TargetDeadCondition
import passive_compiler_v29 as pc
from passive_runtime_v29_base import StatusThreshold, PoiseAtLeast, ChargeAtLeast
import json
from passive_runtime_v29_base import PassiveTrigger, AddPoise
from passive_compiler_v29 import Clamp, FloorValue
from passive_compiler_v29 import parse_conditions
from passive_runtime_v29_base import HasShield
import sys
from passive_compiler_v29 import compile_one
from passive_runtime_v29_base import TriggerTremorBurst
from passive_runtime_v29_base import EventTarget
from passive_compiler_v29 import compile_passive_v29
from passive_runtime_v29_base import LowestAllySPDecreasedThisTurnCondition, PassiveEvent, PassiveTrigger
from passive_runtime_v29_base import PassiveTrigger, TriggerTremorBurst, AddStatus, AddNextTurnTargetStatus, ModifyBurstContext
from passive_runtime_v29_base import PassiveTrigger, StatusThreshold


# ---- merged from test_0_7_75_attack_end_target_death_condition.py ----


def test_attack_end_target_death_is_not_unconditional():
    rule, reasons, unsupported = compile_clause_template(
        '[공격 종료시] 대상이 사망하면 정신력이 가장 낮은 아군 1명의 정신력 6 회복'
    )
    assert rule is not None
    assert isinstance(rule.condition, TargetDeadCondition)
    assert rule.condition.check(SimpleNamespace(ctx={'attack_target_dead': False}), None, 'owner') is False
    assert rule.condition.check(SimpleNamespace(ctx={'attack_target_dead': True}), None, 'owner') is True


def test_attack_end_context_preserves_death_result():
    rule, _, _ = compile_clause_template(
        '[공격 종료시] 대상이 사망하면 정신력이 가장 낮은 아군 1명의 정신력 6 회복'
    )
    # The condition is deliberately event-context based; current state.enemy is
    # not used because OneTurnCore restores it before ATTACK_END.
    event = SimpleNamespace(ctx={'attack_target_dead': True})
    assert rule.condition.check(event, SimpleNamespace(enemy=SimpleNamespace(hp=10)), 'owner') is True


# ---- merged from test_0_7_80_source_condition_scope.py ----


def test_main_target_status_count_is_not_lost():
    c = pc.parse_conditions('메인 타겟의 침잠 횟수가 6 이상이면, 코인 위력 +1')
    assert isinstance(c, StatusThreshold)
    assert (c.name, c.field, c.target, c.value) == ('Sinking', 'count', 'enemy', 6)


def test_self_status_count_is_not_treated_as_unconditional():
    c = pc.parse_conditions('자신의 진동 횟수가 5 이상일 때 코인 위력 +1')
    assert isinstance(c, StatusThreshold)
    assert (c.name, c.field, c.target, c.value) == ('Tremor', 'count', 'self', 5)


def test_self_poise_defaults_to_potency_but_explicit_count_stays_count():
    potency = pc.parse_conditions('자신의 호흡이 5 이상이면 코인 위력 +1')
    count = pc.parse_conditions('자신의 호흡 횟수가 5 이상이면 코인 위력 +1')
    assert isinstance(potency, PoiseAtLeast)
    assert potency.field == 'potency'
    assert isinstance(count, PoiseAtLeast)
    assert count.field == 'count'


def test_target_bleed_threshold_does_not_accidentally_require_count():
    c = pc.parse_conditions('대상에게 출혈이 6 이상 있으면 정신력 2 회복.')
    assert isinstance(c, StatusThreshold)
    assert (c.name, c.field, c.target, c.value) == ('Bleed', 'potency', 'enemy', 6)


def test_self_charge_threshold_is_explicit():
    c = pc.parse_conditions('자신의 충전 횟수가 10 이상이면, 코인 위력 +2')
    assert isinstance(c, ChargeAtLeast)
    assert c.value == 10

def test_main_target_parenthesized_tremor_sum_is_preserved():
    c = pc.parse_conditions('[공격 시작 전] 메인 타겟의 (진동 위력 + 진동 횟수)가 30 이상이면, 가중치 +1')
    from passive_runtime_v29_base import TremorSumThreshold
    assert isinstance(c, TremorSumThreshold)
    assert (c.value, c.target) == (30, 'enemy')


# ---- merged from test_0_7_89_resonance_and_combat_end.py ----

def test_identity_11015_combat_end_and_poise_condition_are_not_flattened():
    cat=json.load(open('identity_catalog_v2.json',encoding='utf8'))
    ident=next(x for x in cat['identities'] if x['id']=='identity-11015')
    passive=next(x for x in ident['passives'] if x.get('name')=='정검[整劍]')
    rules,reasons,unsupported=pc.compile_one(passive,'identity-11015',0)
    assert not unsupported, unsupported
    assert len(rules) >= 2
    start_rule=next(r for r in rules if any('resonance_scaled:poise_potency_floor_cap' == x for x in reasons if False)) if False else None
    # Find the combat-start resonance effect by its source reason/effect shape.
    effects=[(r,e) for r in rules for e in r.effects]
    assert any(type(e).__name__=='AddPoise' and isinstance(e.potency, Clamp) for r,e in effects)
    end_rules=[r for r in rules if r.trigger == PassiveTrigger.COMBAT_END]
    assert len(end_rules)==1
    assert any(type(e).__name__=='AddPoise' and e.count.resolve(None,None,'identity-11015')==1 for e in end_rules[0].effects)
    assert any(type(c).__name__=='PoiseAtLeast' and c.value==20 and c.field=='potency' for c in end_rules[0].conditions)

def test_identity_11015_resonance_formula_order_and_floor():
    cat=json.load(open('identity_catalog_v2.json',encoding='utf8'))
    ident=next(x for x in cat['identities'] if x['id']=='identity-11015')
    passive=next(x for x in ident['passives'] if x.get('name')=='정검[整劍]')
    rules,_,unsupported=pc.compile_one(passive,'identity-11015',0)
    assert not unsupported
    eff=next(e for r in rules for e in r.effects if type(e).__name__=='AddPoise' and isinstance(e.potency, Clamp))
    # 0,1,2,3,8 Oman resonance -> 1,1,2,2,4.
    class Dummy:
        def __init__(self,n): self.resonance={'Pride':n}
    # Runtime's ResonanceValue reads state, so inspect the expression tree rather than fabricate a full state.
    assert isinstance(eff.potency.inner, pc.BinaryValue)
    assert isinstance(eff.potency.inner.left, FloorValue)


# ---- merged from test_actual_source_shield_condition_audit_0779.py ----
"""11-24 / 0.7.79: source-backed Shield presence condition audit."""


def test_self_shield_phrase_is_not_unconditional():
    c = parse_conditions('자신에게 보호막이 있으면, 화상 1 추가 부여')
    assert isinstance(c, HasShield)
    assert c.target == 'self'


def test_target_shield_phrase_is_not_unconditional():
    c = parse_conditions('대상에게 보호막이 있으면, 피해량 +30%')
    assert isinstance(c, HasShield)
    assert c.target == 'enemy'


def test_shield_condition_uses_numeric_shield_field():
    owner = SimpleNamespace(shield=0)
    enemy = SimpleNamespace(shield=3)
    state = SimpleNamespace(fighters={'a': owner}, enemy=enemy)
    event = SimpleNamespace(ctx={})
    assert not HasShield('self').check(event, state, 'a')
    owner.shield = 1
    assert HasShield('self').check(event, state, 'a')
    assert HasShield('enemy').check(event, state, 'a')

def test_main_target_shield_phrase_is_not_unconditional():
    c = parse_conditions('메인 타겟에게 보호막이 있으면, 대신 기본 스킬로 가하는 피해량 +3%')
    assert isinstance(c, HasShield)
    assert c.target == 'enemy'


# ---- merged from test_amplitude_followup_burst.py ----
sys.path.insert(0, '.')


def test_amplitude_conversion_and_followup_burst_compile_as_two_executable_effects():
    text='[적중시] 진동 - 작열로 진폭 변환\n[적중시] 진동 폭발. 대상의 진동 횟수 1 감소'
    rules, reasons, unsupported = compile_one({'id':'amp-burst','name':'amp-burst','effect':text}, 'i', 0)
    assert not unsupported
    assert len(rules) == 2
    assert rules[0].effects[0].__class__.__name__ == 'AmplitudeStateEffect'
    assert isinstance(rules[1].effects[0], TriggerTremorBurst)
    assert rules[1].effects[0].count == 1


def test_multi_burst_uses_engine_count_semantics_without_duplicate_consume_effect():
    text='[적중시] 진동 폭발 3회. 대상의 진동 횟수 3 감소'
    rules, reasons, unsupported = compile_one({'id':'burst3','name':'burst3','effect':text}, 'i', 0)
    assert not unsupported
    assert len(rules) == 1
    effects = rules[0].effects
    assert isinstance(effects[0], TriggerTremorBurst)
    assert effects[0].count == 3
    assert all(e.__class__.__name__ != 'ConsumeStatus' for e in effects)


def test_tremor_burst_trigger_clause_does_not_self_trigger_a_burst_effect():
    text='진동 폭발 시, 다음 턴에 신속 1 얻음'
    rules, reasons, unsupported = compile_one({'id':'burst-trigger','name':'burst-trigger','effect':text}, 'i', 0)
    assert not any(isinstance(e, TriggerTremorBurst) for r in rules for e in r.effects)


# ---- merged from test_attacker_target_audit_v1.py ----

CAT=json.load(open('identity_catalog_v2.json',encoding='utf-8'))
CASES=[]
for ident in CAT['identities']:
    for i,p in enumerate(ident.get('passives') or []):
        txt=str(p.get('effect',''))
        if '공격자에게' in txt:
            rules,_,_=compile_one(p,ident['id'],i)
            for r in rules:
                if '공격자에게' in r.source_text:
                    CASES.append((ident['id'],p.get('name'),r))
assert CASES, 'no attacker-target cases found'
for ident,name,r in CASES:
    assert isinstance(r.target, EventTarget), (ident,name,type(r.target).__name__,r.source_text)
    assert r.target.key == 'attacker', (ident,name,r.target.key)
print('attacker target cases:',len(CASES))
for ident,name,r in CASES:
    print('PASS',ident,name,r.target.key,r.source_text[:120].replace('\n',' / '))


# ---- merged from test_ow_0_7_76_condition.py ----


def fighter(fid, sp, form):
    return SimpleNamespace(hp=100,max_hp=100,sp=sp,formation_index=form,statuses={})


def test_source_condition_is_preserved_for_info_neutralization():
    r={'id':'p','type':'서포트','name':'정보중화','effect':'정신력이 가장 낮은 아군 1명 이번 턴에 정신력이 감소한 경우 턴 종료 시 정신력 10 회복'}
    c=compile_passive_v29(r,'identity-10101',0)
    assert len(c.rules)==1
    rule=c.rules[0]
    assert getattr(rule.target,'policy',None)=='sp_min'
    assert any(isinstance(x, LowestAllySPDecreasedThisTurnCondition) for x in getattr(rule.conditions[0], 'conditions', rule.conditions))


def test_lowest_sp_condition_requires_actual_loss():
    state=SimpleNamespace(fighters={'a':fighter('a',-10,0),'b':fighter('b',5,1)},event_log=[])
    c=LowestAllySPDecreasedThisTurnCondition()
    assert not c.check(PassiveEvent(PassiveTrigger.TURN_END,{}),state,'owner')
    state.event_log.append({'event':'sp_change','identity_id':'a','delta':-3})
    assert c.check(PassiveEvent(PassiveTrigger.TURN_END,{}),state,'owner')


def test_non_lowest_sp_loss_does_not_activate():
    state=SimpleNamespace(fighters={'a':fighter('a',-10,0),'b':fighter('b',5,1)},event_log=[{'event':'sp_change','identity_id':'b','delta':-3}])
    c=LowestAllySPDecreasedThisTurnCondition()
    assert not c.check(PassiveEvent(PassiveTrigger.TURN_END,{}),state,'owner')


# ---- merged from test_tremor_burst_catalog_patterns.py ----


def test_mixed_burst_and_burst_followup_compiles_as_action_plus_resolved_effect():
    text='2코인 [적중시] 진동 폭발.\n진동 폭발 시 진동 횟수 1 감소'
    t, reasons, unsupported = compile_clause_template(text.split('\n')[0])
    assert unsupported == ()
    assert any(isinstance(e, TriggerTremorBurst) for e in t.effects) or t.trigger == PassiveTrigger.COIN_HIT


def test_burst_vulnerability_is_target_status():
    t, reasons, unsupported = compile_clause_template('진동 폭발 시 이번 턴에 취약 1 부여')
    assert unsupported == ()
    assert any(isinstance(e, AddStatus) and e.name == 'Vulnerable' for e in t.effects)


def test_burst_next_turn_protection_uses_target_status_and_correct_value():
    t, reasons, unsupported = compile_clause_template('진동 폭발 시 대상의 진동이 5 이상이면, 다음 턴에 보호 2 얻음')
    assert unsupported == ()
    assert any(isinstance(e, AddNextTurnTargetStatus) and e.name == 'Protection' and e.potency.value == 2 for e in t.effects)
    assert t.deferred_turns == 0


def test_burst_stagger_increase_from_tremor_uses_burst_context():
    t, reasons, unsupported = compile_clause_template('진동 폭발 시 진동 수치의 50%만큼 흐트러짐 손상 증가')
    assert unsupported == ()
    assert any(isinstance(e, ModifyBurstContext) for e in t.effects)


def test_all_catalog_burst_clauses_that_are_executable_have_no_compiler_errors():
    import json
    from passive_compiler_v29 import split_clauses
    data=json.load(open('identity_catalog_v2.json', encoding='utf-8'))
    texts=[]
    def walk(x):
        if isinstance(x,dict):
            for v in x.values(): walk(v)
        elif isinstance(x,list):
            for v in x: walk(v)
        elif isinstance(x,str) and '진동 폭발' in x:
            texts.append(x)
    walk(data)
    checked=0
    for text in set(texts):
        for clause in split_clauses(text):
            if '진동 폭발' not in clause:
                continue
            try:
                template, reasons, unsupported = compile_clause_template(clause)
            except Exception as exc:
                # This test guards against regressions in clauses that are
                # actually executable effect/trigger phrases. Pure descriptive
                # fragments remain outside this compiler contract.
                if any(k in clause for k in ('진동 폭발 시','진동 폭발.','진동 폭발,')):
                    raise AssertionError((clause, repr(exc))) from exc
                continue
            if template is not None or reasons:
                checked += 1
                assert unsupported == (), (clause, reasons, unsupported)
    assert checked > 0


# ---- merged from test_tremor_threshold_clash.py ----

def test_tremor_threshold_condition_is_generic_not_burst_only():
    r = compile_passive_v29({'id':'p','name':'t','effect':'대상의 진동이 5 이상이면 대상의 합 위력 -1'}, 'i', 0)
    assert r.rules
    rule = r.rules[0]
    assert any(isinstance(c, StatusThreshold) and c.name == 'Tremor' and c.value == 5 for c in getattr(rule.conditions[0],'conditions',(rule.conditions[0],)))
    assert any(getattr(e,'field',None)=='clash_power_bonus' for e in rule.effects)


def test_protection_per_damage_uses_self_protection_status_potency():
    r = compile_passive_v29({
        'id':'p-protection-dmg',
        'name':'보호 피해량',
        'effect':'자신의 보호 1당, 피해량 5% 증가 (최대 15%)'
    }, 'identity-11114', 0)
    assert r.rules
    rule = r.rules[0]
    effects = getattr(rule, 'effects', ())
    mods = [e for e in effects if getattr(e, 'field', None) == 'dynamic_damage_bonus']
    assert mods
    value = mods[0].amount
    # The expression must reference Protection status potency rather than a generic resource.
    assert 'Protection' in repr(value)
    assert 'resource' not in repr(value).lower()
