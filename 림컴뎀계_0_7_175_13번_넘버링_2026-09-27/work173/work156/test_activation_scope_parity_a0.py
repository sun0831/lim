"""A0 강화: activation scope 특성화(characterization) / parity 테스트.

목적: A3(TriggerRule.activation_buckets 제거)·A4(solver sync/restore 제거) 전에
현재 동작을 서로 다른 ID 컨텍스트로 고정한다. 리팩터링으로 값이 바뀌면 여기서 잡힌다.

비교 대상 2개
  ledger  = ActivationLedger        (실행 상태의 단일 소유자)
  runtime = ActivationRuntime       (RuleIR 경로, ledger 위에서 동작)

구성
  1. parity        : production 형태 컨텍스트(actor_id 없음)에서 3개가 완전히 같은가
  2. 공유 행렬     : 스코프별로 "어떤 컨텍스트끼리 같은 버킷을 쓰는가"를 의미 수준에서 고정
  3. turn_cap      : 실제 카탈로그 규칙(gimmick:39/40) 형태의 이중 예산
  4. 카탈로그 재고 : A1 감사 수치(55개 규칙, 스코프 분포)가 현재 카탈로그와 같은지
"""
import copy
from collections import Counter

import pytest

from activation_ledger_v1 import ActivationLedger
from activation_runtime_v1 import ActivationRuntime
from rule_ir_v1 import RuleIR

SCOPES = (
    "global",
    "per_turn",              # 카탈로그 규칙 2개가 사용 (gimmick:1, gimmick:26). 동작은 global 과 같은 단일 버킷.
    "per_identity",
    "per_actor",
    "per_skill",
    "per_target",
    "per_identity_target",
    "per_actor_target",
)


def ctx(identity="A", skill="S1", target="T1"):
    """production 형태: trigger_identity_id == identity_id, actor_id 는 넘기지 않는다."""
    return {"trigger_identity_id": identity, "identity_id": identity,
            "skill_id": skill, "target_id": target}


CONTEXTS = {
    "base": ctx(),
    "other_identity": ctx(identity="B"),
    "other_skill": ctx(skill="S2"),
    "other_target": ctx(target="T2"),
    "other_all": ctx("B", "S2", "T2"),
}

# base 를 1번 소비(limit=1)했을 때 '같은 버킷이라서 막히는' 컨텍스트 (base 자신은 항상 포함)
SHARED_WITH_BASE = {
    "global": {"other_identity", "other_skill", "other_target", "other_all"},
    "per_turn": {"other_identity", "other_skill", "other_target", "other_all"},
    "per_identity": {"other_skill", "other_target"},
    "per_actor": {"other_skill", "other_target"},
    "per_skill": {"other_identity", "other_target"},
    "per_target": {"other_identity", "other_skill"},
    "per_identity_target": {"other_skill"},
    "per_actor_target": {"other_skill"},
}


class Trio:
    """같은 입력으로 ledger / runtime 을 동시에 구동한다."""

    def __init__(self, scope, limit=1, turn_cap=None):
        meta = {} if turn_cap is None else {"turn_cap": turn_cap}
        rid = f"r:{scope}"
        self.turn_cap = turn_cap
        self.ledger = ActivationLedger()
        self.ir = RuleIR(rid, "A", "e", activation_limit=limit, activation_scope=scope, metadata=dict(meta))
        self.runtime = ActivationRuntime(self.ledger)
        self.rid = rid

    def eligible(self, c):
        return {
            "ledger": self.ledger.eligible(self.ir, c, turn_cap=self.turn_cap),
            "runtime": self.runtime.eligible(self.ir, c),
        }

    def consume(self, c):
        self.runtime.consume(self.ir, c)

    def state(self):
        def led(l):
            return (l.total_count(self.rid),
                    {k: v for (rid, k), v in l.buckets.items() if rid == self.rid})
        return led(self.ledger)

    def reset(self):
        self.runtime.reset()


def assert_all_agree(trio, names=None, where=""):
    for name in (names or CONTEXTS):
        e = trio.eligible(CONTEXTS[name])
        assert e["ledger"] == e["runtime"], f"production eligibility 불일치 {where} ctx={name}: {e}"
    assert trio.ledger.snapshot() == trio.runtime.ledger.snapshot(), f"production 상태 불일치 {where}"


# ─────────────────────────── 1. parity (production 형태 컨텍스트) ───────────────────────────
@pytest.mark.parametrize("scope", SCOPES)
def test_initial_state_parity(scope):
    t = Trio(scope)
    assert_all_agree(t, where="초기")
    assert all(all(v for v in t.eligible(c).values()) for c in CONTEXTS.values())
    assert t.state() == (0, {})


@pytest.mark.parametrize("scope", SCOPES)
def test_bucket_sharing_matrix_limit_one(scope):
    """base 1회 소비 후 어떤 컨텍스트가 막히는지 — 의미 수준 기대값과 3개 구현 모두 일치."""
    t = Trio(scope, limit=1)
    t.consume(CONTEXTS["base"])
    blocked_expected = {"base"} | SHARED_WITH_BASE[scope]
    for name, c in CONTEXTS.items():
        e = t.eligible(c)
        for impl, ok in e.items():
            assert ok == (name not in blocked_expected), f"{scope}/{impl}/{name}: eligible={ok}"
    assert_all_agree(t, where="limit1 소비 후")


@pytest.mark.parametrize("scope", SCOPES)
def test_limit_two_budget_and_snapshots(scope):
    t = Trio(scope, limit=2)
    base = CONTEXTS["base"]
    t.consume(base)
    assert all(t.eligible(base).values()), "limit 2: 1회 소비 후에도 가능"
    assert_all_agree(t, where="1회")
    t.consume(base)
    assert not any(t.eligible(base).values()), "limit 2: 2회 소비 후 불가"
    assert_all_agree(t, where="2회")
    assert t.state()[0] == 2


@pytest.mark.parametrize("scope", SCOPES)
def test_scripted_production_sequence_stays_in_lockstep(scope):
    """production 처럼 eligible 일 때만 consume 하는 순서로 돌려도 매 단계 3개 구현이 같다."""
    t = Trio(scope, limit=2)
    order = ["base", "other_target", "other_identity", "other_skill", "base",
             "other_all", "other_target", "base", "other_skill", "other_identity"]
    consumed = 0
    for i, name in enumerate(order):
        c = CONTEXTS[name]
        e = t.eligible(c)
        assert e["ledger"] == e["runtime"], f"step{i}/{name}: {e}"
        if e["ledger"]:
            t.consume(c)
            consumed += 1
        assert_all_agree(t, where=f"step{i}/{name}")
    assert t.state()[0] == consumed


@pytest.mark.parametrize("scope", SCOPES)
def test_reset_clears_everything(scope):
    t = Trio(scope, limit=1)
    for c in CONTEXTS.values():
        if all(t.eligible(c).values()):
            t.consume(c)
    t.reset()
    assert t.state() == (0, {})
    assert t.state() == (0, {})
    assert_all_agree(t, where="reset 후")


@pytest.mark.parametrize("scope", SCOPES)
def test_activation_runtime_delegates_scope_accounting_to_ledger(scope):
    """Runtime has no second scope-key implementation; both use the same ledger."""
    t = Trio(scope)
    assert t.runtime.ledger is t.ledger
    assert not hasattr(t.runtime, "_scope_key")
    for c in CONTEXTS.values():
        assert t.runtime.eligible(t.ir, c) == t.ledger.eligible(t.ir, c, turn_cap=t.turn_cap)


# ─────────────────────────── 2. ledger 고유 성질 ───────────────────────────
def test_per_actor_target_isolation_a_t1_a_t2_b_t1():
    """A/T1, A/T2, B/T1 이 서로 다른 버킷 (production 키, 그리고 actor_id 만 쓰는 호출 모두)."""
    for make in (
        lambda who, tgt: {"trigger_identity_id": who, "identity_id": who, "target_id": tgt},
        lambda who, tgt: {"actor_id": who, "target_id": tgt},
    ):
        rule = RuleIR("iso", "A", "e", activation_limit=1, activation_scope="per_actor_target")
        led = ActivationLedger()
        a_t1, a_t2, b_t1 = make("A", "T1"), make("A", "T2"), make("B", "T1")
        assert led.eligible(rule, a_t1)
        led.consume(rule, a_t1)
        assert not led.eligible(rule, a_t1)
        assert led.eligible(rule, a_t2)
        assert led.eligible(rule, b_t1)
        assert led.buckets[("iso", "A|T1")] == 1
        assert ("iso", "A|T2") not in led.buckets and ("iso", "B|T1") not in led.buckets


def test_clone_forks_full_state_for_probability_branches():
    rule = RuleIR("fork", "A", "e", activation_limit=1, activation_scope="per_target")
    led = ActivationLedger()
    led.consume(rule, CONTEXTS["base"])
    branch = led.clone()
    branch.consume(rule, CONTEXTS["other_target"])
    assert led.snapshot()["counts"] == {"fork": 1}
    assert branch.snapshot()["counts"] == {"fork": 2}
    assert led.eligible(rule, CONTEXTS["other_target"])          # 원본은 영향 없음
    assert not branch.eligible(rule, CONTEXTS["other_target"])


def test_snapshot_round_trip():
    rule = RuleIR("snap", "A", "e", activation_limit=2, activation_scope="per_identity_target")
    led = ActivationLedger()
    for name in ("base", "base", "other_identity", "other_target"):
        led.consume(rule, CONTEXTS[name])
    again = ActivationLedger.from_snapshot(copy.deepcopy(led.snapshot()))
    assert again.snapshot() == led.snapshot()
    for c in CONTEXTS.values():
        assert again.eligible(rule, c) == led.eligible(rule, c)


# ─────────────────────────── 3. turn_cap 이중 예산 ───────────────────────────
@pytest.mark.parametrize("cap", (1, 2), ids=["gimmick38_like_cap1", "gimmick39_like_cap2"])
def test_per_target_limit_one_with_turn_cap(cap):
    """카탈로그의 gimmick:39(cap 1) / gimmick:40(cap 2): 타깃별 1회 + 턴 전체 최대 cap 회."""
    t = Trio("per_target", limit=1, turn_cap=cap)
    targets = [ctx(target="T1"), ctx(target="T2"), ctx(target="T3")]
    fired = []
    for i, c in enumerate(targets):
        e = t.eligible(c)
        assert e["ledger"] == e["runtime"], f"T{i+1}: {e}"
        if e["ledger"]:
            t.consume(c)
            fired.append(f"T{i+1}")
    assert fired == ["T1", "T2"][:cap]
    assert not any(t.eligible(targets[0]).values()), "T1 재검사: 타깃 예산 소진"
    assert t.ledger.snapshot() == t.runtime.ledger.snapshot()
    assert t.state()[0] == cap
    buckets = t.state()[1]
    assert buckets == {f"T{i}": 1 for i in range(1, cap + 1)}


# ─────────────────────────── 4. 카탈로그 재고 (A1 감사 수치 고정) ───────────────────────────
def test_catalog_activation_inventory_matches_a1_audit():
    from one_turn_solver_v29 import IdentityCatalogV29
    from special_gimmick_v2 import GimmickRegistry
    cat = IdentityCatalogV29.from_json("identity_catalog_v2.json")
    reg = GimmickRegistry([cat.build_identity(k, offense_level=0) for k in cat.records])
    rules = reg.trigger_rules
    # 2026-09-24 현재 catalog 기준. 0.7.x에서 실제 identity 규칙이 추가되면서
    # 과거 A1 감사 기준과 분리한다. 현재 catalog inventory는 73개다.
    assert len(rules) == 73
    assert Counter(r.activation_scope for r in rules) == {
        "global": 67, "per_turn": 2, "per_identity": 1, "per_target": 2, "per_skill": 1}

    # turn_cap은 현재 catalog의 metadata에서 실제 선언된 규칙만 고정한다.
    capped = {r.id: (r.activation_scope, r.max_activations, r.metadata["turn_cap"])
              for r in rules if (r.metadata or {}).get("turn_cap")}
    assert capped == {
        "gimmick:53": ("per_target", 1, 1),
        "gimmick:54": ("per_target", 1, 2),
    }
