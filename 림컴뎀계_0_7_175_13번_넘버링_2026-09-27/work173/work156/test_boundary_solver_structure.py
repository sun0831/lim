"""병합 테스트: boundary_solver_structure

원본 파일 (내용은 AST 병합기로 합쳤고 테스트 본문은 바꾸지 않음):
  - test_v101_action_runtime_boundary.py
  - test_v110_generated_action_effect_aliases.py
  - test_v111_engine_conversion_audit.py
  - test_v112_activation_ledger.py
  - test_v113_coin_execution_core.py
  - test_v113_turn_execution_context.py
  - test_v114_action_target_boundary.py
  - test_v114_solver_module_split.py
  - test_v114_solver_phase_boundaries.py
  - test_v115_action_resolution_boundary.py
  - test_v116_action_execution_boundary.py
  - test_v117_trigger_action_boundary.py
이름 충돌 helper 는 `이름__vNN` 으로 분리했다. 매핑은 tools/MERGE_MAP.json 참고.
"""
import inspect
from types import SimpleNamespace
from action_queue_v1 import ActionQueue
from effect_runtime_v1 import EffectRuntime, EffectCommand
from effect_executor_v1 import EffectExecutor
from rule_ir_v1 import EffectIR, RuleIR, ConditionIR
from pathlib import Path
from one_turn_solver_v29 import IdentityCatalogV29, OneTurnSolverV29, ResolvedAction
from special_gimmick_v2 import GimmickRegistry
from rule_migration_runtime_v1 import RuleMigrationRuntime
from activation_ledger_v1 import ActivationLedger
from limbus_damage_engine_v29 import (
    BattleState,
    EnemyState,
    FighterState,
    IdentityData,
    SkillData,
    CoinData,
    Status,
)
from rule_runtime_v1 import RuleRuntime
from trigger_rule_model_v1 import TriggerRule, TriggerCondition, TriggerEffect
from probabilistic_trigger_runtime_v1 import ProbabilisticTriggerRuntime
from unittest.mock import patch
from coin_execution_core_v1 import CoinExecutionCore
from copy import deepcopy
from identity_catalog_v29 import IdentityCatalogV29 as IdentityCatalogV29__v114_solver
from skill_text_parser_v19 import ParseReport, SkillTextParserV19
from resource_runtime_v1 import ResourceRuntime
from trigger_action_execution_v1 import TriggerActionExecutionBoundary



# ======================================================================
# 원본: test_v101_action_runtime_boundary.py
# ======================================================================

def test_generated_action_boundary_inherits_explicit_source_target():
    q = ActionQueue.from_scenario([{
        'identity_id': 'A', 'skill_id': 'A-S1',
        'target_policy': 'lowest_hp', 'target_ids': ['enemy-2'],
    }])
    source = q.pop()
    generated, queued = q.enqueue_generated(
        source, 'B', 'B-S2', 'assist', source_event='after_skill',
        target_policy='main', target_index=None, target_ids=None,
        trigger_kind='assist',
    )
    assert queued is True
    assert generated.generated is True
    assert generated.target_policy == 'lowest_hp'
    assert generated.target_ids == ['enemy-2']

def test_generated_action_boundary_prefers_explicit_generated_target():
    q = ActionQueue.from_scenario([{
        'identity_id': 'A', 'skill_id': 'A-S1',
        'target_policy': 'lowest_hp', 'target_ids': ['enemy-2'],
    }])
    source = q.pop()
    generated, queued = q.enqueue_generated(
        source, 'B', 'B-S2', 'assist', source_event='after_skill',
        target_policy='enemy_main', target_index=0, target_ids=['enemy-1'],
        trigger_kind='assist',
    )
    assert queued is True
    assert generated.target_policy == 'enemy_main'
    assert generated.target_index == 0
    assert generated.target_ids == ['enemy-1']

def test_generated_action_boundary_preserves_requested_order():
    q = ActionQueue.from_scenario([
        {'identity_id': 'A', 'skill_id': 'A-S1'},
        {'identity_id': 'C', 'skill_id': 'C-S1'},
    ])
    source = q.pop()
    generated, queued = q.enqueue_generated(
        source, 'B', 'B-S1', 'support', source_event='after_skill',
        trigger_kind='support',
    )
    assert queued is True
    assert q.pop() is generated
    assert q.pop().identity_id == 'C'


# ======================================================================
# 원본: test_v110_generated_action_effect_aliases.py
# ======================================================================

def test_generated_action_aliases_are_generic_executable():
    for kind in ("assist_action", "extra_action", "trigger_action", "queue_action"):
        assert EffectRuntime.is_generic_executable(kind)
        assert EffectRuntime.category_for(kind) == "action"

def test_generated_action_alias_normalizes_to_queue_action():
    cmd = EffectCommand("assist_action", {"identity_id": "B", "skill_id": "S1"}, "r1", "action")
    normalized = EffectExecutor._normalize_generated_action(cmd)
    assert normalized.kind == "queue_action"
    assert normalized.params["identity_id"] == "B"
    assert normalized.params["skill_id"] == "S1"
    assert normalized.params["trigger_kind"] == "assist_action"


# ======================================================================
# 원본: test_v111_engine_conversion_audit.py
# ======================================================================

def _registry():
    cat = IdentityCatalogV29.from_json("identity_catalog_v2.json")
    identities = [cat.build_identity(key) for key in cat.records]
    return GimmickRegistry(
        identities,
        {str(i.id): getattr(i, "passives", []) for i in identities},
        [str(i.id) for i in identities],
    )

def test_catalog_trigger_rules_are_fully_common_runtime_safe():
    reg = _registry()
    report = RuleMigrationRuntime().analyze(reg.trigger_rules)
    assert report["total_rules"] == 73
    assert report["fully_generic_rules"] == 73
    assert report["deferred_rules"] == 0
    assert report["unknown_rules"] == 0

def test_production_event_boundary_has_no_direct_legacy_runtime_dependency():
    source = Path("special_gimmick_v2.py").read_text(encoding="utf-8")
    block = source[source.index("    def _fire_migrated_event"):source.index("    def trigger_rules_data")]
    assert "TriggerRuntime(" not in block
    assert "from trigger_runtime_v1 import" not in block


# ======================================================================
# 원본: test_v112_activation_ledger.py
# ======================================================================

def _state():
    return BattleState(EnemyState(100, 100), {"A": FighterState()})

def test_rule_runtime_uses_turn_state_activation_ledger():
    state = _state()
    rule = RuleIR(
        rule_id="once", owner_id="A", trigger="skill_end",
        conditions=(ConditionIR("always"),),
        effects=(EffectIR("resource_gain", {"resource": "charge", "amount": 1}),),
        activation_limit=1, activation_scope="global",
    )
    rt = RuleRuntime()
    ctx = {"state": state, "identity_id": "A", "actor": state.fighters["A"]}
    ev, _ = rt.execute(rule, ctx)
    assert ev.matched
    assert state.activation_ledger.counts == {"once": 1}
    assert rt.activations.counts is state.activation_ledger.counts
    ev2, _ = rt.execute(rule, ctx)
    assert not ev2.matched
    assert ev2.reason == "activation_limit"

def test_probability_runtime_shares_same_turn_ledger_and_per_skill_bucket():
    state = _state()
    rules = [
        TriggerRule(
            "per_skill", "A", "skill_end", [],
            [TriggerEffect("resource_gain", {"resource": "charge", "amount": 1})],
            1, 0, "per_skill", {}, "test", {}
        )
    ]
    rt = ProbabilisticTriggerRuntime(rules)
    ctx = {"state": state, "identity_id": "A", "skill_id": "S1", "skill_name": "S1", "actor": state.fighters["A"]}
    first = rt.fire("skill_end", ctx)
    second = rt.fire("skill_end", ctx)
    assert len(first) == 1
    assert second == []
    assert state.activation_ledger.counts["per_skill"] == 1
    assert state.activation_ledger.buckets[("per_skill", "S1")] == 1
    ctx2 = dict(ctx, skill_id="S2", skill_name="S2")
    third = rt.fire("skill_end", ctx2)
    assert len(third) == 1
    assert state.activation_ledger.buckets[("per_skill", "S2")] == 1

def test_probability_branch_clone_forks_activation_ledger_without_runtime_sync():
    state = _state()
    ledger = state.activation_ledger
    rule = TriggerRule(
        "once", "A", "skill_end", [],
        [TriggerEffect("resource_gain", {"resource": "charge", "amount": 1})],
        1, 0, "global", {}, "test", {}
    )
    rt = ProbabilisticTriggerRuntime([rule], ledger)
    rt.fire("skill_end", {"state": state, "identity_id": "A", "skill_id": "S1", "actor": state.fighters["A"]})
    branch = state.clone()
    assert branch.activation_ledger is not state.activation_ledger
    assert branch.activation_ledger.counts == {"once": 1}
    branch.activation_ledger.reset()
    assert state.activation_ledger.counts == {"once": 1}


# ======================================================================
# 원본: test_v113_coin_execution_core.py
# ======================================================================

def _ids():
    from one_turn_solver_v29 import IdentityCatalogV29
    records = []
    for iid, name, power in [('a','A',10),('b','B',20)]:
        records.append({
            'id': iid, 'name': name, 'offense_level': 0,
            'stats': {'level': 60, 'speed': 10, 'hp': 1000, 'hpBase': 1000,
                      'defenseLevel': 0, 'resistances': {}},
            'skills': {'S1': {'id':'S1','name':'S1','base_power':power,
                              'coin_powers':[1], 'coin_count':1,
                              'coins':[{'coin_power':1,'damage_type':'slash','sin':'lust'}],
                              'attack_type':'slash','sin':'lust'}},
            'passives': []})
    cat = IdentityCatalogV29(records)
    return {x: cat.build_identity(x) for x in ('a','b')}

def test_shared_core_handles_coin_reuse_and_after_skill_in_one_lifecycle():
    solver = OneTurnSolverV29()
    state = SimpleNamespace(enemy=SimpleNamespace(hp=100), runtime={})
    ident = SimpleNamespace(id='a')
    coin = SimpleNamespace(reuse_rules=[])
    skill = SimpleNamespace(coins=[coin], id='S1')
    calls = []

    def sim(st, i, sk, c, face, crit, idx, heads):
        calls.append(idx)
        st.enemy.hp -= 5

    core = CoinExecutionCore(sim)
    core.execute(
        __import__('coin_execution_core_v1').CoinExecutionContext(state, ident, skill, ['H']),
        on_coin=lambda c: calls.append(('after_coin', c.coin_index)),
        on_skill=lambda c, d: calls.append(('after_skill', d)),
    )
    assert calls == [1, ('after_coin', 1), ('after_skill', 5.0)]

def test_deterministic_unopposed_path_calls_shared_coin_core():
    solver = OneTurnSolverV29.__new__(OneTurnSolverV29)
    class FakeEngine:
        @staticmethod
        def simulate_coin(state, identity, skill, coin, face, is_crit, coin_index, prior_heads):
            state.enemy.hp -= 10
        @staticmethod
        def condition_met(*args, **kwargs):
            return False
    solver.core = SimpleNamespace(machine=SimpleNamespace(engine=FakeEngine()))
    a = SimpleNamespace(id='a')
    skill = SimpleNamespace(id='S1', name='A', _slot='S1', coins=[object()])
    state = SimpleNamespace(
        enemy=SimpleNamespace(hp=100, statuses={}, stagger_level=0, stagger_index=0,
                              stagger_thresholds=[], staggered=False),
        fighters={'a': SimpleNamespace(resources={}, statuses={}, ammo=0, hp=100, max_hp=100)},
        runtime={'condition_flags': {}, 'probabilistic_trigger_runtime_template': None,
                 'probabilistic_identity_map': {}}, turn_damage=0)
    with patch.object(CoinExecutionCore, 'execute', autospec=True, wraps=CoinExecutionCore.execute) as spy:
        solver._execute_unopposed_coins_with_triggers(state, a, skill, ['H'], 0)
        assert spy.call_count == 1

def test_generated_action_path_calls_the_same_shared_coin_core():
    solver = OneTurnSolverV29()
    ids = _ids()
    state = solver.build_state({
        'enemy': {'hp':1000,'max_hp':1000,'level':60,'defense_level':0,
                  'physical_res':{'slash':1,'pierce':1,'blunt':1},'sin_res':{'lust':1}},
        'allies': {'a':{'sp':0,'hp':1000,'max_hp':1000}, 'b':{'sp':0,'hp':1000,'max_hp':1000}},
        'actions': []}, ids)
    state.runtime['probabilistic_identity_map'] = ids
    state.runtime['probabilistic_trigger_max_depth'] = 4
    runtime = solver._probabilistic_trigger_runtime([])
    with patch.object(CoinExecutionCore, 'execute', autospec=True, wraps=CoinExecutionCore.execute) as spy:
        damage, _trace = solver._execute_probabilistic_generated_action(
            state, runtime, ids, 'a', ids['a'].skills['S1'], depth=1)
        assert damage > 0
        assert spy.call_count == 1


# ======================================================================
# 원본: test_v113_turn_execution_context.py
# ======================================================================

def _fixture():
    from identity_catalog_v29 import IdentityCatalogV29
    from pathlib import Path
    cat = IdentityCatalogV29.from_json(str(Path(__file__).parent / "identity_catalog_v2.json"))
    identity = cat.build_identity("identity-11216")
    skill = next(iter(identity.skills.values()))
    scenario = {
        "coin_mode": "max",
        "enemy": {"hp": 100000, "max_hp": 100000},
        "actions": [{"identity_id": identity.id, "skill_id": skill.id}],
    }
    return scenario, {identity.id: identity}

def test_prepare_turn_context_contains_execution_state_and_queue():
    scenario, ids = _fixture()
    solver = OneTurnSolverV29()
    ctx = solver._prepare_turn_context(deepcopy(scenario), ids)
    assert ctx.state is not None
    assert ctx.resource_runtime is not None
    assert ctx.action_queue is not None
    assert len(ctx.action_queue.items) == 1
    assert ctx.out == []
    assert ctx.damage_by_identity[ids[next(iter(ids))].id] == 0.0

def test_context_prepare_then_solve_preserves_public_result_contract():
    scenario, ids = _fixture()
    solver = OneTurnSolverV29()
    result = solver.solve(deepcopy(scenario), ids)
    assert "turn_damage" in result
    assert "actions" in result
    assert "next_turn_state" in result


# ======================================================================
# 원본: test_v114_action_target_boundary.py
# ======================================================================

def test_action_target_boundary_honors_request_precedence_and_coin_mapping():
    solver = OneTurnSolverV29()
    scenario = {"target_count": 1, "random_seed": 7}
    class E:
        def __init__(self, i):
            self.id = str(i); self.hp = 100; self.max_hp = 100; self.statuses = {}
    state = type("S", (), {})()
    state.enemy = E("main")
    state.runtime = {"enemy_targets": [
        {"id":"a","index":0,"hp":100,"max_hp":100,"statuses":{}},
        {"id":"b","index":1,"hp":100,"max_hp":100,"statuses":{}},
    ], "random_seed": 7, "target_random_counter": 0, "current_target_count": 1}
    request = type("R", (), {"target_policy": "specific", "target_index": None, "target_ids": ["b"], "target_override_ids": None, "coin_target_ids": None})()
    ctx = solver._resolve_action_target_context(state=state, scenario=scenario, request=request, raw_action={})
    assert ctx["target_selection"]["resolved_ids"] == ["b"]
    request.coin_target_ids = [0]
    ctx = solver._resolve_action_target_context(state=state, scenario=scenario, request=request, raw_action={})
    assert ctx["coin_target_ids"] == ["a"]

def test_target_boundary_preserves_random_counter_between_actions():
    solver = OneTurnSolverV29()
    state = type("S", (), {})()
    state.enemy = type("E", (), {"id":"main","hp":100,"max_hp":100,"statuses":{}})()
    state.runtime = {"enemy_targets":[
        {"id":"a","index":0,"hp":100,"max_hp":100,"statuses":{}},
        {"id":"b","index":1,"hp":100,"max_hp":100,"statuses":{}},
    ], "random_seed": 1, "target_random_counter": 0, "current_target_count": 1}
    req = type("R", (), {"target_policy":"random","target_index":None,"target_ids":None,"target_override_ids":None,"coin_target_ids":None})()
    first = solver._resolve_action_target_context(state=state, scenario={}, request=req, raw_action={})
    second = solver._resolve_action_target_context(state=state, scenario={}, request=req, raw_action={})
    assert state.runtime["target_random_counter"] == 2
    assert first["target_selection"]["resolved_ids"] in (["a"],["b"])
    assert second["target_selection"]["resolved_ids"] in (["a"],["b"])


# ======================================================================
# 원본: test_v114_solver_module_split.py
# ======================================================================

def test_parser_and_catalog_are_extracted_modules():
    assert SkillTextParserV19.__module__ == 'skill_text_parser_v19'
    assert ParseReport.__module__ == 'skill_text_parser_v19'
    assert IdentityCatalogV29__v114_solver.__module__ == 'identity_catalog_v29'
    assert OneTurnSolverV29.__module__ == 'one_turn_solver_v29'

def test_solver_reexports_legacy_import_surface():
    from one_turn_solver_v29 import IdentityCatalogV29 as SolverCatalog
    from one_turn_solver_v29 import SkillTextParserV19 as SolverParser
    assert SolverCatalog is IdentityCatalogV29__v114_solver
    assert SolverParser is SkillTextParserV19


# ======================================================================
# 원본: test_v114_solver_phase_boundaries.py
# ======================================================================

def test_solver_has_explicit_finalization_phase():
    solve_src = inspect.getsource(OneTurnSolverV29.solve)
    finalize_src = inspect.getsource(OneTurnSolverV29._finalize_turn)
    assert "Phase 3: turn finalization / result assembly." in solve_src
    assert "return self._finalize_turn(" in solve_src
    assert "self.core.machine.end_turn(state)" in finalize_src
    assert "return {'requested_plan'" in finalize_src

def test_solver_phase_boundary_does_not_duplicate_finalization_body():
    solve_src = inspect.getsource(OneTurnSolverV29.solve)
    assert "Full-turn Bleed-state DP runs in parallel" not in solve_src
    assert "target_state_output={}" not in solve_src


# ======================================================================
# 원본: test_v115_action_resolution_boundary.py
# ======================================================================

def _fixture__v115_action():
    skill = SkillData('S1', '기본기', 5, [CoinData(2, 'slash', 'lust')], 'slash', 'lust', resource_cost={'탄환': 1})
    ident = IdentityData('id1', '테스트', 0, {'S1': skill}, [])
    fighter = FighterState(level=60, speed=0, sp=0, hp=100, max_hp=100, sin_resources={}, poise=Status(), charge=0, ammo=3, resources={})
    enemy = EnemyState(100, 100, level=60, speed=0, defense_level=0, defense_level_bonus=0, physical_res={'slash': 1, 'pierce': 1, 'blunt': 1}, sin_res={}, statuses={})
    state = BattleState(enemy, {'id1': fighter})
    state.runtime = {'enemy_targets': [{'id': 'main', 'index': 0, 'hp': 100, 'max_hp': 100, 'statuses': {}}], 'current_target_count': 1}
    return (state, ident)

def test_action_resolution_is_explicit_boundary():
    src=inspect.getsource(OneTurnSolverV29.solve)
    assert 'resolved = self._resolve_action(' in src
    assert 'class ResolvedAction' in inspect.getsource(ResolvedAction)

def test_resolve_action_centralizes_skill_faces_resources_and_targets():
    state, ident = _fixture__v115_action()
    solver = OneTurnSolverV29()
    req = type('R', (), {'identity_id': 'id1', 'skill_id': 'S1', 'target_policy': 'main', 'target_index': None, 'target_ids': None, 'target_override_ids': None, 'coin_target_ids': None, 'target_count': None})()
    raw = {'skill_id': 'S1', 'faces': ['H']}
    resolved = solver._resolve_action(state=state, scenario={}, identity_map={'id1': ident}, request=req, raw_action=raw, mode='max', resource_runtime=ResourceRuntime(), target_count=1)
    assert isinstance(resolved, ResolvedAction)
    assert resolved.identity_id == 'id1' and resolved.skill.id == 'S1'
    assert resolved.faces == ['H']
    assert resolved.consumed_resources['탄환'] == 1
    assert state.fighters['id1'].ammo == 2
    assert resolved.target_ctx['target_selection']['resolved_ids'] == ['main']


# ======================================================================
# 원본: test_v116_action_execution_boundary.py
# ======================================================================

def test_action_execution_boundary_exists():
    assert hasattr(OneTurnSolverV29, '_execute_action_execution')
    src = inspect.getsource(OneTurnSolverV29._execute_action_execution)
    assert 'execute_clash' in src
    assert 'execute_unopposed' in src

def test_solve_delegates_execution_boundary():
    src = inspect.getsource(OneTurnSolverV29.solve)
    assert '_execute_action_execution(' in src
    assert 'self.core.execute_clash(' not in src
    assert 'self.core.execute_unopposed(' not in src


# ======================================================================
# 원본: test_v117_trigger_action_boundary.py
# ======================================================================

class Q:
    def __init__(self): self.calls=[]
    def triggered_from(self,*args,**kwargs): self.calls.append(('from',args,kwargs)); return ('generated', args, kwargs)
    def enqueue_triggered(self,x): self.calls.append(('enqueue',x)); return 'queued'

class G:
    identity_id='G'; skill_id='S'; reason='r'; forced_faces=['H']; target_policy=None
    target_index=None; target_ids=None; target_override_ids=None; coin_target_ids=None; trigger_kind='after_clash'

def test_trigger_boundary_preserves_target_inheritance():
    q=Q(); b=TriggerActionExecutionBoundary(q)
    req=type('R',(),dict(target_policy='main',target_index=2,target_ids=['E'],target_override_ids=['E'],coin_target_ids=['E1']))()
    r=b.enqueue_from_gimmick(req,G(),source_event='after_clash')
    assert r.queued=='queued'
    kw=q.calls[0][2]
    assert kw['target_policy']=='main' and kw['target_index']==2
    assert kw['target_ids']==['E'] and kw['target_override_ids']==['E']
    assert kw['coin_target_ids']==['E1']

def test_trigger_boundary_uses_explicit_generated_target():
    q=Q(); b=TriggerActionExecutionBoundary(q)
    req=type('R',(),dict(target_policy='main',target_index=2,target_ids=['E'],target_override_ids=['E'],coin_target_ids=['E1']))()
    g=G(); g.target_policy='lowest_hp'; g.target_index=4; g.target_ids=['X']; g.target_override_ids=['X']; g.coin_target_ids=['X1']
    b.enqueue_from_gimmick(req,g,source_event='after_clash')
    kw=q.calls[0][2]
    assert kw['target_policy']=='lowest_hp' and kw['target_index']==4
    assert kw['target_ids']==['X'] and kw['target_override_ids']==['X'] and kw['coin_target_ids']==['X1']
