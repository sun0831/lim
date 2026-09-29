"""병합 테스트: boundary_legacy_retirement

원본 파일 (내용은 AST 병합기로 합쳤고 테스트 본문은 바꾸지 않음):
  - test_v101_legacy_retirement_boundary.py
  - test_v102_probabilistic_deferred_runtime_persistence.py
  - test_v103_legacy_event_boundary.py
  - test_v104_fire_event_boundary.py
  - test_v105_production_event_boundary.py
  - test_v106_probabilistic_runtime_boundary.py
  - test_v107_production_trigger_boundary.py
  - test_v108_trigger_model_boundary.py
  - test_v109_legacy_runtime_boundary.py
이름 충돌 helper 는 `이름__vNN` 으로 분리했다. 매핑은 tools/MERGE_MAP.json 참고.
"""
import legacy_event_compat_v1
import re
import ast
from trigger_runtime_v1 import TriggerRule, TriggerCondition, TriggerEffect, TriggerRuntime
from rule_migration_runtime_v1 import RuleMigrationRuntime
from types import SimpleNamespace
from one_turn_solver_v29 import OneTurnSolverV29
from special_gimmick_v2 import GimmickRegistry
from legacy_trigger_adapter_v1 import LegacyTriggerAdapter
from pathlib import Path
from probabilistic_trigger_runtime_v1 import ProbabilisticTriggerRuntime



# ======================================================================
# 원본: test_v101_legacy_retirement_boundary.py
# ======================================================================

def _generic_rule():
    return TriggerRule(
        "retire.generic", "A", "after_skill",
        [TriggerCondition("owner_id", "A")],
        [TriggerEffect("flag", {"key": "migration_retired_probe", "value": True})],
        1, 0, "global", {}, "retirement probe", {}
    )

def test_production_fire_does_not_enter_legacy_for_generic_rule(monkeypatch):
    def fail(*args, **kwargs):
        raise AssertionError("legacy TriggerRuntime executed for migration-safe rule")

    monkeypatch.setattr(TriggerRuntime, "fire", fail)
    ctx = {"identity_id": "A", "owner_id": "A", "condition_flags": {}}
    rows, legacy_count = RuleMigrationRuntime().production_fire([_generic_rule()], "after_skill", ctx)
    assert legacy_count == 0
    assert rows and rows[0]["rule_id"] == "retire.generic"

def test_partition_never_places_migration_safe_rule_in_legacy_bucket():
    safe, deferred = RuleMigrationRuntime().partition([_generic_rule()], "after_skill")
    assert len(safe) == 1
    assert deferred == []

def test_catalog_generic_rules_do_not_fallback_to_legacy(monkeypatch):
    from one_turn_solver_v29 import IdentityCatalogV29
    from special_gimmick_v2 import GimmickRegistry

    def fail(*args, **kwargs):
        raise AssertionError("legacy TriggerRuntime executed for retired catalog rule")

    monkeypatch.setattr(TriggerRuntime, "fire", fail)
    cat = IdentityCatalogV29.from_json("identity_catalog_v2.json")
    ids = [cat.build_identity(k, offense_level=0) for k in cat.records]
    reg = GimmickRegistry(ids)
    events = sorted({str(r.event) for r in reg.trigger_rules})
    for event in events:
        reg._fire_migrated_event(event, {"event": event})
        assert reg._last_legacy_fallback_count == 0

def test_production_boundary_fails_fast_if_a_deferred_rule_is_introduced():
    deferred = TriggerRule(
        "retire.deferred", "A", "after_skill",
        [], [TriggerEffect("not_a_generic_effect", {})],
        1, 0, "global", {}, "deferred probe", {}
    )
    try:
        RuleMigrationRuntime().production_fire([deferred], "after_skill", {"identity_id": "A"})
    except RuntimeError as exc:
        assert "deferred rules" in str(exc)
    else:
        raise AssertionError("production boundary accepted a deferred rule")


# ======================================================================
# 원본: test_v102_probabilistic_deferred_runtime_persistence.py
# ======================================================================

def _state(runtime):
    fighter = SimpleNamespace(hp=100, max_hp=100, resources={}, statuses={}, sp=0)
    enemy = SimpleNamespace(id='enemy_1', hp=100, max_hp=100, statuses={})
    return SimpleNamespace(
        fighters={'A': fighter}, enemy=enemy, runtime=runtime,
        event_log=[], turn_damage=0,
    )

def test_deferred_probabilistic_runtime_is_branch_persistent():
    # A deliberately deferred effect keeps the legacy compatibility runtime
    # alive.  The second event must see the activation consumed by the first.
    rule = TriggerRule(
        'deferred-persist', 'A', 'after_coin',
        [TriggerCondition('always')],
        [TriggerEffect('not_a_generic_effect', {'value': 1})],
        max_activations=1,
    )
    runtime = SimpleNamespace(rules=[rule])
    state = _state({})
    calc = OneTurnSolverV29()

    first = calc._fire_probabilistic_trigger_event(
        runtime, 'after_coin', {'identity_id': 'A'}, state
    )
    second = calc._fire_probabilistic_trigger_event(
        runtime, 'after_coin', {'identity_id': 'A'}, state
    )

    assert len(first) == 1
    assert second == []
    assert 'probabilistic_deferred_trigger_runtime' in state.runtime

def test_all_generic_probabilistic_path_does_not_create_legacy_runtime():
    rule = TriggerRule(
        'generic-probe', 'A', 'after_coin',
        [TriggerCondition('always')],
        [TriggerEffect('flag', {'key': 'x', 'value': True})],
        max_activations=1,
    )
    runtime = SimpleNamespace(rules=[rule])
    state = _state({})
    calc = OneTurnSolverV29()

    out = calc._fire_probabilistic_trigger_event(
        runtime, 'after_coin', {'identity_id': 'A'}, state
    )

    assert out and out[0].get('executed_generic') is True
    assert 'probabilistic_deferred_trigger_runtime' not in state.runtime

def test_deferred_runtime_activation_survives_branch_deepcopy():
    import copy
    rule = TriggerRule(
        'deferred-copy', 'A', 'after_coin',
        [TriggerCondition('always')],
        [TriggerEffect('not_a_generic_effect', {'value': 1})],
        max_activations=1,
    )
    runtime = SimpleNamespace(rules=[rule])
    state = _state({})
    calc = OneTurnSolverV29()

    first = calc._fire_probabilistic_trigger_event(
        runtime, 'after_coin', {'identity_id': 'A'}, state
    )
    assert len(first) == 1

    branch = copy.deepcopy(state)
    second = calc._fire_probabilistic_trigger_event(
        runtime, 'after_coin', {'identity_id': 'A'}, branch
    )
    assert second == []
    assert branch.runtime['probabilistic_deferred_trigger_runtime'].activation_ledger.counts.get('deferred-copy') == 1


# ======================================================================
# 원본: test_v103_legacy_event_boundary.py
# ======================================================================

def test_legacy_event_handlers_are_extracted_from_registry():
    for name in (
        'after_received_attack', 'after_kill', 'after_coin',
        'after_resource_event', 'after_lifecycle_event',
    ):
        method = getattr(GimmickRegistry, name)
        assert method.__module__ == 'special_gimmick_v2'
        assert hasattr(legacy_event_compat_v1, name)

def test_compatibility_module_is_explicitly_separate():
    assert legacy_event_compat_v1.__doc__
    assert 'Compatibility-only' in legacy_event_compat_v1.__doc__

def test_legacy_trigger_adapter_is_external_to_registry():
    reg = GimmickRegistry([])
    adapter = LegacyTriggerAdapter(reg.trigger_rules)
    assert adapter.rules == reg.trigger_rules
    assert not hasattr(reg, 'trigger_runtime')
    assert not hasattr(reg, 'fire_event_compat')


# ======================================================================
# 원본: test_v104_fire_event_boundary.py
# ======================================================================

def _generic_rule__v104_fire():
    return TriggerRule('boundary.generic', 'A', 'after_skill', [TriggerCondition('owner_id', 'A')], [TriggerEffect('flag', {'key': 'boundary_probe', 'value': True})], 1, 0, 'global', {}, 'boundary probe', {})

def test_fire_event_is_production_ir_entrypoint(monkeypatch):
    reg = GimmickRegistry([])
    reg.trigger_rules = [_generic_rule__v104_fire()]

    def fail(*args, **kwargs):
        raise AssertionError('fire_event entered Legacy TriggerRuntime')
    monkeypatch.setattr(TriggerRuntime, 'fire', fail)
    rows = reg.fire_event('after_skill', {'identity_id': 'A', 'owner_id': 'A', 'condition_flags': {}})
    assert rows and rows[0]['rule_id'] == 'boundary.generic'
    assert rows[0]['migration_execution_deferred'] is True
    assert reg._last_legacy_fallback_count == 0

def test_legacy_compatibility_is_explicitly_external(monkeypatch):
    reg = GimmickRegistry([])
    reg.trigger_rules = []
    seen = []

    def fake_fire(rules, event, ctx):
        seen.append((rules, event, ctx))
        return ["compat"]

    monkeypatch.setattr("legacy_trigger_adapter_v1.fire", fake_fire)
    assert LegacyTriggerAdapter(reg.trigger_rules).fire("after_skill", {"x": 1}) == ["compat"]
    assert seen == [([], "after_skill", {"x": 1})]


# ======================================================================
# 원본: test_v105_production_event_boundary.py
# ======================================================================

def test_production_registry_does_not_import_legacy_event_compat():
    source = Path("special_gimmick_v2.py").read_text(encoding="utf-8")
    assert "from legacy_event_compat_v1 import" not in source
    assert "import legacy_event_compat_v1" not in source

def test_legacy_event_compat_is_wrapper_only():
    source = Path("legacy_event_compat_v1.py").read_text(encoding="utf-8")
    assert "Compatibility-only wrappers" in source
    assert "def after_skill" not in source
    assert "def after_coin" not in source

def test_production_event_runtime_contains_live_handlers():
    source = Path("event_runtime_v1.py").read_text(encoding="utf-8")
    for name in (
        "def after_skill",
        "def after_received_attack",
        "def after_kill",
        "def after_coin",
        "def after_resource_event",
        "def after_lifecycle_event",
    ):
        assert name in source


# ======================================================================
# 원본: test_v106_probabilistic_runtime_boundary.py
# ======================================================================

def test_solver_probability_path_uses_new_runtime_not_legacy_trigger_runtime():
    source = Path('one_turn_solver_v29.py').read_text(encoding='utf-8')
    assert 'from trigger_runtime_v1 import TriggerRuntime' not in source
    assert not re.search(r'\bTriggerRuntime\s*\(', source)

def test_probability_runtime_factory_returns_new_runtime():
    runtime = OneTurnSolverV29()._probabilistic_trigger_runtime([])
    assert isinstance(runtime, ProbabilisticTriggerRuntime)


# ======================================================================
# 원본: test_v107_production_trigger_boundary.py
# ======================================================================

def test_production_registry_has_no_top_level_legacy_trigger_import():
    tree = ast.parse(Path('special_gimmick_v2.py').read_text(encoding='utf-8'))
    for node in tree.body:
        if isinstance(node, ast.Import):
            assert all(alias.name != 'trigger_runtime_v1' for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            assert node.module != 'trigger_runtime_v1'

def test_legacy_trigger_runtime_is_not_exposed_by_production_registry():
    source = Path('special_gimmick_v2.py').read_text(encoding='utf-8')
    assert 'def trigger_runtime(self):' not in source
    assert 'fire_event_compat' not in source
    assert 'legacy_trigger_compat_v1' not in source


# ======================================================================
# 원본: test_v108_trigger_model_boundary.py
# ======================================================================

def _top_level_imports(path):
    tree = ast.parse(Path(path).read_text(encoding='utf-8'))
    return [n for n in tree.body if isinstance(n, (ast.Import, ast.ImportFrom))]

def test_solver_uses_trigger_data_model_not_legacy_runtime():
    source = Path('one_turn_solver_v29.py').read_text(encoding='utf-8')
    assert 'from trigger_rule_model_v1 import TriggerRule, TriggerCondition, TriggerEffect' in source
    assert 'from trigger_runtime_v1 import TriggerRule' not in source

def test_trigger_runtime_reexports_shared_data_model():
    source = Path('trigger_runtime_v1.py').read_text(encoding='utf-8')
    assert 'from trigger_rule_model_v1 import TriggerCondition, TriggerEffect, TriggerRule' in source

def test_model_has_no_runtime_dependency():
    imports = _top_level_imports('trigger_rule_model_v1.py')
    for node in imports:
        module = node.module if isinstance(node, ast.ImportFrom) else ''
        assert module != 'trigger_runtime_v1'


# ======================================================================
# 원본: test_v109_legacy_runtime_boundary.py
# ======================================================================

def test_production_special_gimmick_does_not_import_legacy_runtime():
    source = Path('special_gimmick_v2.py').read_text(encoding='utf-8')
    assert 'from trigger_runtime_v1 import' not in source
    assert 'import trigger_runtime_v1' not in source
    assert 'legacy_trigger_compat_v1' not in source
    assert 'legacy_trigger_adapter_v1' not in source

def test_only_compat_adapter_imports_legacy_runtime():
    root = Path('.')
    offenders = []
    for p in root.glob('*.py'):
        if p.name.startswith('test_') or p.name in {'golden_rule_parity_v1.py', 'trigger_runtime_v1.py', 'legacy_trigger_compat_v1.py'}:
            continue
        source = p.read_text(encoding='utf-8')
        if 'from trigger_runtime_v1 import' in source or 'import trigger_runtime_v1' in source:
            offenders.append(p.name)
    assert offenders == []

def test_compat_adapter_is_explicit():
    source = Path('legacy_trigger_compat_v1.py').read_text(encoding='utf-8')
    assert 'compatibility' in source.lower()
    assert 'TriggerRuntime' in source
