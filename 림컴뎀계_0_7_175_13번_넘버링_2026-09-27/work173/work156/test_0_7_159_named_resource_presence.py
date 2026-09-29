import json
from passive_compiler_v29 import compile_passive_v15

def test_0_7_159_named_resource_presence_gates_damage():
    record={"type":"전투","name":"부수고","affinity":"","cost":0,
            "condition":"","effect":"눈물 벼리기를 3개 보유하였다면, 기본 공격 스킬을 사용하여 적에게 마지막 코인 적중 전에 눈물 벼리기를 전부 소모하여 침잠 3, 침잠 횟수 3을 부여하고 해당 코인의 피해량 +50%"}
    r=compile_passive_v15(record,'identity-10913',0)
    rules=[x for x in r.rules if '해당 코인의 피해량 +50%' in x.source_text]
    assert rules
    cond=rules[0].conditions[0]
    assert type(cond).__name__=='ResourceAtLeast'
    assert cond.name=='눈물 벼리기' and cond.value==3 and cond.target=='self'
