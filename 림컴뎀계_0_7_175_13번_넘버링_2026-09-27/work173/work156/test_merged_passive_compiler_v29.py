"""Safely merged test file (AST-aware, whole-file rename incl. call sites, decorators preserved via line-removal import stripping).
Originals: test_0_7_86_integer_per_floor.py, test_actual_received_damage_scope_0_7_100.py, test_actual_scaling_audit_0_7_84.py, test_actual_source_condition_audit_0778.py, test_actual_source_multi_audit_0781.py, test_audit_0_7_83.py, test_audit_0_7_91_scaling_next_turn.py, test_composite_target_selector.py, test_cross_status_crit_damage_0_7_108.py, test_ow_0_7_72_semantic_mismatch.py, test_ow_0_7_85_scaling_mismatch.py, test_tremor_identity_batch_0743.py
"""
from __future__ import annotations

from passive_compiler_v29 import effects
from passive_compiler_v29 import compile_clause_template
import json
import unittest
import passive_compiler_v29 as pc
from passive_compiler_v29 import parse_conditions
from passive_compiler_v29 import parse_effects
from passive_compiler_v29 import compile_one, AddNextTurnStatus, Clamp, FloorValue
from passive_compiler_v29 import compile_passive_v29


# ---- merged from test_0_7_86_integer_per_floor.py ----

def _expr(text, field):
    es,_=effects(text)
    return [e.amount for e in es if getattr(e,'field',None)==field][-1]

def test_status_per_n_uses_floor():
    v=_expr('대상의 화상 3 당 피해량 +10% (최대 50%)','dynamic_damage_bonus')
    assert type(v.inner.left).__name__ == 'FloorValue'

def test_resource_per_n_uses_floor():
    v=_expr('자신의 찢어진 추억 3당 피해량 +15% (최대 105%)','dynamic_damage_bonus')
    assert type(v.inner.left).__name__ == 'FloorValue'

def test_poise_per_n_coin_power_uses_floor():
    v=_expr('자신의 호흡 5 당 코인 위력 +1 (최대 2)','coin_power_bonus')
    assert type(v.inner.left).__name__ == 'FloorValue'

def test_crit_per_n_uses_floor():
    v=_expr('대상의 파열 3 당 크리티컬 피해량 +2% (최대 30%)','crit_damage_bonus')
    assert type(v.inner.left).__name__ == 'FloorValue'

def test_lost_hp_percent_per_n_uses_floor():
    v=_expr('자신의 잃은 체력 20% 당 피해량 +10% (최대 30%)','dynamic_damage_bonus')
    assert type(v.inner.left).__name__ == 'FloorValue'

def test_tremor_specialized_per_n_uses_floor():
    v=_expr('대상의 진동 위력 6 당 피해량 +5% (최대 15%)','dynamic_damage_bonus')
    assert type(v.inner.left).__name__ == 'FloorValue'


# ---- merged from test_actual_received_damage_scope_0_7_100.py ----

def _fields(text):
    tpl, reasons, missing = compile_clause_template(text)
    assert tpl is not None, (reasons, missing)
    return [e.field for e in tpl.effects], reasons

def test_received_damage_is_not_compiled_as_outgoing_damage():
    fields, reasons = _fields("자신이 받는 피해량 +25%. 가하는 피해량 +25%")
    assert fields.count("incoming_damage_bonus") == 1
    assert fields.count("dynamic_damage_bonus") == 1
    assert "damage_taken_percent" in reasons

def test_received_damage_only_clause_has_no_outgoing_modifier():
    fields, _ = _fields("자신이 받는 피해량 +20%")
    assert fields == ["incoming_damage_bonus"]


# ---- merged from test_actual_scaling_audit_0_7_84.py ----


def _reasons(text):
    _, reasons = effects(text)
    return reasons


def test_status_damage_scaling_preserves_divisor_and_cap():
    r = _reasons('대상의 화상 3 당 피해량 +10% (최대 50%)')
    assert '화상_per_stack_capped' in r
    assert 'damage_percent' not in r


def test_status_damage_scaling_bare_stack_is_one_per_stack_and_capped():
    r = _reasons('대상의 화상당 피해량 +5% (최대 60%)')
    assert '화상_per_stack_capped' in r
    assert 'damage_percent' not in r


def test_charge_multiplier_scaling_survives_status_audit():
    r = _reasons('충전이 2 이상이면, 피해량이 (충전 x 3)%만큼 증가 (최대 15%)')
    assert 'charge_scaling' in r


def test_speed_difference_scaling_survives_status_audit():
    r = _reasons('속도 차이 1 당 5% 피해량 증가 (최대 20%)')
    assert 'speed_difference_scaling' in r


def test_tremor_potency_has_single_specialized_handler():
    r = _reasons('대상의 진동 위력 6 당 피해량 +5% (최대 15%)')
    assert r.count('tremor_potency_damage_scaling') == 1
    assert not any(x == '진동_per_stack_capped' for x in r)

def test_bare_poise_scaling_uses_potency_not_count():
    es, reasons = effects('자신의 호흡 5 당 코인 위력 +1 (최대 2)')
    assert 'poise_coin_power_scaling' in reasons
    value = [e.amount for e in es if getattr(e, 'field', None) == 'coin_power_bonus'][-1]
    assert getattr(value.inner.left.inner.left, 'field', None) == 'poise'


def test_explicit_poise_count_scaling_uses_count():
    es, reasons = effects('자신의 호흡 횟수 3 당 코인 위력 +1 (최대 2)')
    assert 'poise_coin_power_scaling' in reasons
    value = [e.amount for e in es if getattr(e, 'field', None) == 'coin_power_bonus'][-1]
    assert getattr(value.inner.left.inner.left, 'field', None) == 'poise_count'


# ---- merged from test_actual_source_condition_audit_0778.py ----

class TestActualSourceConditionAudit0778(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cat=json.load(open('identity_catalog_v2.json',encoding='utf8'))
        cls.passive=next(p for i in cat['identities'] if i['id']=='identity-10109' for p in i.get('passives',[]) if p.get('name')=='과제평가' and '출혈이 6 이상' in p.get('effect',''))

    def test_bleed_threshold_is_not_unconditional(self):
        rules,_,_=pc.compile_one(self.passive,'identity-10109',0)
        self.assertTrue(rules)
        conds=[]
        for r in rules:
            c=r.conditions[0]
            conds.extend(getattr(c,'conditions',(c,)))
        self.assertTrue(any(type(c).__name__=='StatusThreshold' for c in conds))
        c=[c for c in conds if type(c).__name__=='StatusThreshold'][0]
        self.assertEqual(c.name,'Bleed')
        self.assertEqual(c.value,6)
        self.assertEqual(c.target,'enemy')

if __name__=='__main__': unittest.main()


# ---- merged from test_actual_source_multi_audit_0781.py ----

class TestActualSourceMultiAudit0781(unittest.TestCase):
    def test_target_speed_comparison_does_not_add_owner_speed_floor(self):
        c=parse_conditions('대상보다 속도가 3 이상 빠르면, 코인 위력 +3')
        names=[type(x).__name__ for x in getattr(c,'conditions',(c,))]
        self.assertNotIn('SpeedAtLeast', names)
        self.assertIn('SpeedDifferenceAtLeast', names)

    def test_rupture_potency_and_count_are_conjunctive(self):
        c=parse_conditions('대상의 파열이 15, 파열 횟수가 3 이상이면, 이 스킬의 효과로 파열을 부여하지 않음.')
        names=[type(x).__name__ for x in getattr(c,'conditions',(c,))]
        self.assertIn('StatusPairThreshold', names)
        pair=next(x for x in getattr(c,'conditions',(c,)) if type(x).__name__=='StatusPairThreshold')
        self.assertEqual((pair.name,pair.potency,pair.count,pair.target),('Rupture',15,3,'enemy'))

if __name__=='__main__': unittest.main()

# batch source-audit coverage
class TestActualSourceSumAudit0781(unittest.TestCase):
    def test_same_target_status_sum(self):
        c=parse_conditions('대상의 화상과 출혈의 합이 6 이상이면, 코인 위력 +1')
        self.assertIn('StatusSumThreshold',[type(x).__name__ for x in getattr(c,'conditions',(c,))])
    def test_cross_scope_status_sum(self):
        c=parse_conditions('자신의 호흡과 대상의 출혈의 합이 4 이상이면, 코인 위력 +1')
        self.assertIn('CrossStatusSumThreshold',[type(x).__name__ for x in getattr(c,'conditions',(c,))])
    def test_speed_sum(self):
        c=parse_conditions('자신과 대상의 속도의 합이 6 이상이면, 코인 위력 +1')
        self.assertIn('SpeedSumThreshold',[type(x).__name__ for x in getattr(c,'conditions',(c,))])


# ---- merged from test_audit_0_7_83.py ----

class TestAudit0783ScalingCaps(unittest.TestCase):
    def _reasons(self, text):
        return parse_effects(text)

    def test_charge_potency_haste_cap_uses_second_group(self):
        specs = self._reasons('(충전 위력 / 5)만큼 다음 턴에 신속 얻음 (최대 2)')
        spec = [x for x in specs if x.reason == 'next_turn_status:Haste_charge_potency'][0]
        self.assertIn('Clamp', repr(spec.effect))
        self.assertIn('2', repr(spec.effect))

    def test_poise_count_coin_power_cap(self):
        specs = self._reasons('호흡 횟수 5당 코인 위력 +1 (최대 3)')
        spec = [x for x in specs if x.reason == 'poise_coin_power_scaling'][0]
        r=repr(spec.effect)
        self.assertIn('3', r)
        self.assertNotIn('Const(1)), 0, 1)', r)

    def test_tremor_scaling_uses_percent_group(self):
        specs = self._reasons('대상의 진동 위력 6 당 피해량 +5% (최대 15%)')
        spec = [x for x in specs if x.reason == 'tremor_potency_damage_scaling'][0]
        self.assertIn('0.05', repr(spec.effect))

    def test_rupture_sinking_sum_uses_percent_group(self):
        specs = self._reasons('대상의 파열과 침잠의 합 2당 피해량 +1% (최대 15%)')
        spec = [x for x in specs if x.reason == 'rupture_plus_sinking_per_n'][0]
        self.assertIn('0.01', repr(spec.effect))

if __name__ == '__main__': unittest.main()


# ---- merged from test_audit_0_7_91_scaling_next_turn.py ----


def _passive(effect):
    return {'type':'전투','name':'audit','cost':0,'condition':'보유','effect':effect}


def _owner():
    return {'id':'audit-owner','gameId':'audit-owner','passives':[]}


def _first_effect(effect):
    rules, reasons, unsupported = compile_one(_passive(effect), _owner(), 0)
    assert rules, (reasons, unsupported)
    assert rules[0].effects
    return rules[0].effects[0], reasons, unsupported


def test_poise_per_n_next_turn_haste_is_scaled_and_capped():
    e, reasons, unsupported = _first_effect('턴 종료시 자신의 호흡 10 당, 다음 턴에 신속 1 얻음 (최대 2)')
    assert isinstance(e, AddNextTurnStatus)
    assert e.name == 'Haste'
    assert e.potency.resolve(None, None, 'x') == 0
    assert isinstance(e.count, Clamp)
    assert 'next_turn_status:Haste_poise_scaling' in reasons
    assert unsupported == []


def test_charge_count_per_n_next_turn_haste_is_scaled_and_capped():
    e, reasons, unsupported = _first_effect('턴 종료 시 자신의 충전 횟수 5 당 다음 턴에 신속 1을 얻음. (최대 2)')
    assert isinstance(e, AddNextTurnStatus)
    assert e.name == 'Haste'
    assert 'next_turn_status:Haste_charge_scaling' in reasons
    assert unsupported == []


def test_burn_per_n_next_turn_attack_level_is_scaled_and_capped():
    e, reasons, unsupported = _first_effect('턴 종료 시 자신의 화상 6당, 다음 턴에 공격 레벨 증가 1 얻음 (최대 5)')
    assert isinstance(e, AddNextTurnStatus)
    assert e.name == 'Attack Level Up'
    assert 'next_turn_status:AttackLevel_burn_scaling' in reasons
    assert unsupported == []


# ---- merged from test_composite_target_selector.py ----

def test_fanatic_lowest_sp_selector_is_promoted():
    text='광신 이 있는 아군 중 정신력이 가장 낮은 아군의 피해량 +10%'
    rule, reasons, unsupported = compile_clause_template(text)
    assert rule is not None
    assert getattr(rule, 'target_kind', None) == 'custom'
    spec=getattr(rule, 'target_spec', None)
    assert spec is not None
    assert spec.policy == 'status_present_sp_min:광신'
    assert spec.count == 1


# ---- merged from test_cross_status_crit_damage_0_7_108.py ----


def test_cross_status_crit_damage_without_explicit_potency_words():
    out = parse_effects('4코인 크리티컬 피해량 +(자신의 호흡 + 대상의 화상)% (최대 50%)')
    assert len(out) == 1
    e = out[0]
    assert e.reason == 'cross_status_crit_damage_scaling'
    assert e.effect.field == 'crit_damage_bonus'


def test_cross_status_crit_damage_with_explicit_potency_words():
    out = parse_effects('(자신의 호흡 위력 + 대상의 파열 위력) 1당 크리티컬 피해량 +2% (최대 120%)')
    assert len(out) == 1
    assert out[0].reason == 'cross_status_crit_damage_scaling'


# ---- merged from test_ow_0_7_72_semantic_mismatch.py ----


def _target_policy(record):
    compiled = compile_passive_v29(record, 'support-owner', 0)
    assert compiled.rules
    rule = compiled.rules[0]
    return rule.target, rule.conditions[0]


def test_support_ranked_sp_is_recipient_not_owner_condition():
    target, condition = _target_policy({
        'id': 'p1', 'type': '서포트', 'name': 'x',
        'effect': '정신력이 가장 낮은 아군 1명 관통 스킬의 피해량 +10%'
    })
    assert getattr(target, 'policy', None) == 'sp_min'
    assert type(condition).__name__ != 'AllyRankCondition'


def test_support_ranked_speed_is_recipient_not_owner_condition():
    target, condition = _target_policy({
        'id': 'p2', 'type': '서포트', 'name': 'x',
        'effect': '속도가 가장 낮은 아군 1명 가드 스킬의 최종 위력 +2'
    })
    assert getattr(target, 'policy', None) == 'speed_min'
    assert type(condition).__name__ != 'AllyRankCondition'


def test_support_ranked_max_hp_is_recipient_not_owner_condition():
    target, condition = _target_policy({
        'id': 'p3', 'type': '서포트', 'name': 'x',
        'effect': '최대 체력이 가장 낮은 아군 1명 수비 스킬의 최종 위력 +2'
    })
    assert getattr(target, 'policy', None) == 'max_hp_min'
    assert type(condition).__name__ != 'AllyRankCondition'

def test_support_ranked_enemy_is_not_silently_retargeted_to_owner():
    compiled = compile_passive_v29({
        'id': 'p4', 'type': '서포트', 'name': 'x',
        'effect': '턴 종료 시 속도가 가장 빠른 적 1명에게 다음 턴에 출혈 횟수 1 증가'
    }, 'support-owner', 0)
    assert not compiled.rules
    assert not any(type(r.target).__name__ == 'SelfTarget' for r in compiled.rules)


def test_support_ranked_identity_alias_maps_to_speed_selector():
    target, condition = _target_policy({
        'id': 'p5', 'type': '서포트', 'name': 'x',
        'effect': '속도가 가장 빠른 인격 1명이 공격 적중 시 피해량 +10%'
    })
    assert getattr(target, 'policy', None) == 'speed_max'
    assert type(condition).__name__ != 'AllyRankCondition'


# ---- merged from test_ow_0_7_85_scaling_mismatch.py ----

def reasons(text): return [x.reason for x in parse_effects(text)]

def test_target_lost_hp_is_target_only():
    out=parse_effects('대상의 잃은 체력 1% 당 피해량 +0.3% (최대 30%)')
    assert len(out)==1 and out[0].reason=='target_lost_hp_scaling'

def test_self_lost_hp_is_dynamic_not_flat():
    out=parse_effects('자신의 잃은 체력 1%당 피해량 0.8% 증가')
    assert len(out)==1 and out[0].reason=='lost_hp_scaling'

def test_lost_hp_blocking_and_cap():
    out=parse_effects('3코인 [적중시] 자신의 잃은 체력 20% 당, 피해량 +10% (최대 30%)')
    assert len(out)==1 and out[0].reason=='lost_hp_scaling'
    assert out[0].effect.amount.hi==0.3

def test_speed_difference_crit_damage_is_crit_modifier():
    out=parse_effects('대상과의 속도 차이 1 당 크리티컬 피해량 +5% (최대 30%)')
    assert len(out)==1 and out[0].reason=='speed_difference_crit_damage_scaling'
    assert out[0].effect.field=='crit_damage_bonus'

def test_poise_crit_damage_keeps_cap():
    out=parse_effects('1코인 - 자신의 호흡당 크리티컬 피해량 +3% (최대 60%)')
    assert len(out)==1 and out[0].reason=='poise_crit_damage_scaling'
    assert out[0].effect.amount.hi==0.6

def test_poise_over_20_crit_damage():
    out=parse_effects('자신의 20을 초과하는 호흡 위력 1당 자신의 기본 공격 스킬 크리티컬 피해량 +1% (최대 10%)')
    assert len(out)==1 and out[0].reason=='poise_excess_crit_damage_scaling'

def test_speed_difference_coefficient_and_cap_are_separate():
    out=parse_effects('자신의 속도가 대상보다 빠르면, (대상과의 속도 차이 × 2)%만큼 피해량 증가 (최대 10%)')
    assert len(out)==1 and out[0].reason=='speed_difference_scaling'
    assert out[0].effect.amount.hi==0.10


# ---- merged from test_tremor_identity_batch_0743.py ----

def test_10304_nails_tremor_count_modifier_compiles():
    text='못 이 있는 대상에게 부여하는 진동 횟수 +1'
    t,reasons,unsupported=compile_clause_template(text)
    assert t is not None
    assert 'ncorp_nails_tremor_count_bonus' in reasons
    assert not unsupported
    assert t.trigger.value if hasattr(t.trigger,'value') else True

def test_10304_nails_condition_is_target_status():
    text='못 이 있는 대상에게 부여하는 진동 횟수 +1'
    t,_,_=compile_clause_template(text)
    cond=repr(t.condition)
    assert 'Nails' in cond
    assert 'StatusAtLeast' in cond

def test_10409_stagger_assist_rule_is_catalog_backed():
    import json
    D=json.load(open('identity_catalog_v2.json',encoding='utf8'))
    ident=next(x for x in D['identities'] if x['id']=='identity-10409')
    passive='\n'.join(p.get('effect','') for p in ident.get('passives',[]))
    assert '자신을 제외한 아군의 공격으로 흐트러짐 상태가 된 적을 스킬 1로 공격함' in passive


def test_0_7_134_status_gated_damage_bonus_is_not_unconditional():
    from passive_compiler_v29 import compile_one
    from passive_runtime_v29_base import StatusAtLeast
    rules, _, unsupported = compile_one({'id':'x','effect':'출혈이 부여된 적 공격 시 피해량 +10 %'}, 'identity-test')
    assert not unsupported
    assert len(rules) == 1
    
    def has_bleed_gate(c):
        if isinstance(c, StatusAtLeast):
            return c.name == 'Bleed' and c.target == 'enemy'
        return any(has_bleed_gate(x) for x in getattr(c, 'conditions', ()) )
    assert has_bleed_gate(rules[0].conditions[0])


def test_0_7_134_target_named_resource_ratio_damage_is_dynamic():
    from passive_compiler_v29 import compile_one, ModifyContext, ResourceField
    rules, _, unsupported = compile_one({'id':'x','effect':'흐트러진 대상에게 가하는 피해량 +(대상의 잔향)%'}, 'identity-test')
    assert not unsupported
    effect = rules[0].effects[0]
    assert isinstance(effect, ModifyContext)
    assert isinstance(effect.amount.left, ResourceField)
    assert effect.amount.left.name == '잔향'
    assert effect.amount.left.target == 'enemy'
