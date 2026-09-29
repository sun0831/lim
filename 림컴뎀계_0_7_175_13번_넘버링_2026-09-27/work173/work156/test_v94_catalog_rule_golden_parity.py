"""Golden parity over every migration-safe TriggerRule emitted from the catalog."""
from pathlib import Path
import sys

ROOT = Path(__file__).parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from one_turn_solver_v29 import IdentityCatalogV29
from special_gimmick_v2 import GimmickRegistry
from limbus_damage_engine_v29 import BattleState, EnemyState, FighterState, Status
from golden_rule_parity_v1 import assert_golden
from rule_migration_runtime_v1 import RuleMigrationRuntime
from rule_ir_bridge_v1 import trigger_rule_to_ir
from action_queue_v1 import ActionQueue


def _registry():
    cat = IdentityCatalogV29.from_json(str(ROOT / "identity_catalog_v2.json"))
    ids = [cat.build_identity(k, offense_level=0) for k in cat.records]
    return GimmickRegistry(ids)


def _ctx(rule, reg):
    ir = trigger_rule_to_ir(rule)
    owner = str(rule.owner_id)
    fighters = {owner: FighterState(resources={"충전": 20, "예지안": 30})}
    fighters.setdefault("identity-11009", FighterState())
    state = BattleState(EnemyState(1000, 1000), fighters)
    state.enemy.statuses["Burn"] = Status(potency=5, count=5)
    action_queue = ActionQueue.from_scenario([{"identity_id": owner, "skill_id": "S1"}])
    source_action = action_queue.pop()
    identity_map = {str(i.id): i for i in reg.identities}
    ctx = {
        "state": state, "identity_id": owner, "owner_id": owner,
        "action_queue": action_queue, "source_action": source_action,
        "identity_map": identity_map, "event": str(rule.event),
        "actor": fighters[owner], "enemy": state.enemy,
        "actual_damage": 10, "skill_id": "S1", "skill_name": "S1",
        "skill_slot": "S1", "skill_is_defense": False,
        "target_id": "identity-11009", "target_died": True,
        "target_available": True, "available_identity_ids": list(fighters),
        "outcome": "win", "clash_outcome": "win",
        "generated": False, "reuse_index": 1,
        "ammo_spent": 1, "ammo_before": 1, "ammo_after": 0,
        "is_lowest_ammo_identity": True,
        "resource": "충전", "resources": {"충전": 20, "예지안": 30},
        "cumulative_before": 0, "cumulative_after": 10,
        "condition_flags": {}, "statuses": {}, "actor_statuses": {},
        "received_target_id": "identity-11009", "received_target_died": True,
        "received_target_damaged": True, "received_target_max_hp": 100,
        "received_target_hp": 0, "skill_attack_type": "slash",
        "consumed_resources": {"충전": 20}, "coin_index": 4,
        "affiliation_resolver": reg.affiliation_resolver,
    }
    for c in ir.conditions:
        op, a = c.op, c.args
        if op == "resource": ctx["resource"] = a.get("value", "충전")
        elif op in ("resource_gte", "resource_lte"):
            ctx["resource"] = a.get("value", "충전")
            ctx["resources"][str(a.get("value"))] = 20
        elif op == "has_status":
            ctx["statuses"][str(a.get("value"))] = {"count": 5, "potency": 5}
        elif op == "target_id_in": ctx["target_id"] = a.get("value", [owner])[0]
        elif op == "target_available":
            tid = str(a.get("value")); ctx["available_identity_ids"] = list(set(ctx["available_identity_ids"]) | {tid})
        elif op == "killer_id": ctx["killer_id"] = a.get("value")
        elif op == "skill_slot": ctx["skill_slot"] = a.get("value")
        elif op == "coin_index": ctx["coin_index"] = a.get("value")
        elif op == "action_resource_consumed_gte": ctx["consumed_resources"][str(a.get("value"))] = max(int(a.get("field", 0)), 20)
        elif op == "owner_id": ctx["identity_id"] = owner
    return ctx


def test_all_catalog_migration_safe_rules_have_golden_parity():
    reg = _registry()
    migration = RuleMigrationRuntime()
    safe = [r for r in reg.trigger_rules if migration.migration_safe(r)[0]]
    # 0.7.45: 10409 제.지의 newly-staggered support rule이 공통 IR 조건/액션으로 승격되어
    # migration-safe catalog inventory가 66 -> 67로 증가했다.
    assert len(safe) == 73
    for rule in safe:
        result = assert_golden(rule, _ctx(rule, reg))
        assert result.ok, result
