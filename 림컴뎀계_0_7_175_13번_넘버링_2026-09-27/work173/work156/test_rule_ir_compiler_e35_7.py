from rule_ir_compiler_v1 import compile_clause
from rule_ir_contract_lowering_v1 import lower_contract_clause

def test_e35_7_resource_trigger_contract():
    r=lower_contract_clause("턴 시작 시 정신력 10 증가", "I", "r")
    assert r.trigger=="turn_start"
    assert r.effects[0].params["primitive_id"]=="resource_effect"

def test_e35_7_status_contract():
    r=compile_clause("적중 시 출혈 3 부여", "I", "r")[0]
    assert r.effects[0].params["primitive_id"]=="status_effect"

def test_e35_7_damage_modifier_contract():
    r=compile_clause("적중 시 피해량 +10%", "I", "r")[0]
    assert r.effects[0].params["primitive_id"]=="damage_modifier_effect"

def test_e35_7_unknown_not_fabricated():
    rules,_,unsupported=__import__('rule_ir_compiler_v1').compile_record({'id':'x','name':'x','effect':'불안정한 격정을 얻음.'},'I')
    assert not rules or rules[0].status!='implemented' or unsupported
