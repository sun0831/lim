import json
from passive_compiler_v29 import compile_passive_v29
from passive_runtime_v29_base import HasStatus, And

def _has_named_state(conditions, name, target):
    for c in conditions:
        if isinstance(c, HasStatus) and c.name == name and c.target == target:
            return True
        if isinstance(c, And) and _has_named_state(c.conditions, name, target):
            return True
    return False


def _passive(iid, effect):
    return {"id": f"{iid}:p0", "name": "test", "type": "전투", "condition": "", "effect": effect}


def test_self_named_state_damage_gate():
    p = _passive("identity-10411", "자신에게 각력【묘】가 있으면 가하는 피해량 +5%")
    out = compile_passive_v29(p, "identity-10411", 0)
    assert len(out.rules) == 1
    assert _has_named_state(out.rules[0].conditions, "각력【묘】", "self")


def test_target_named_state_damage_gate():
    p = _passive("identity-10411", "대상에게 주살【신속】이 있으면 가하는 피해량 +5%")
    out = compile_passive_v29(p, "identity-10411", 0)
    assert len(out.rules) == 1
    assert _has_named_state(out.rules[0].conditions, "주살【신속】", "enemy")


def test_combined_named_state_gates():
    p = _passive("identity-11112", "자신에게 각력【묘】가 있고 대상에게 주살【신속】이 있으면 각력【묘】당 가하는 피해량 +5% (최대 15%)")
    out = compile_passive_v29(p, "identity-11112", 0)
    assert len(out.rules) == 1
    assert _has_named_state(out.rules[0].conditions, "각력【묘】", "self")
    assert _has_named_state(out.rules[0].conditions, "주살【신속】", "enemy")
