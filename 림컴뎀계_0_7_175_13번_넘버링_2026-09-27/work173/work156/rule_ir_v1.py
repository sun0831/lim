"""Lightweight declarative Rule IR for the 1-turn combat engine.

This layer does not replace existing TriggerRuntime/GimmickRule yet. It gives
new work a stable vocabulary while the legacy bridge remains compatible.
"""
from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, Iterable, List, Optional

@dataclass(frozen=True)
class ConditionIR:
    op: str
    args: Dict[str, Any] = field(default_factory=dict)

@dataclass(frozen=True)
class TargetIR:
    side: str = "self"
    selector: str = "self"
    count: int = 1
    filters: Dict[str, Any] = field(default_factory=dict)

@dataclass(frozen=True)
class EffectIR:
    kind: str
    params: Dict[str, Any] = field(default_factory=dict)

@dataclass(frozen=True)
class RuleIR:
    rule_id: str
    owner_id: str
    trigger: str
    conditions: tuple[ConditionIR, ...] = ()
    target: Optional[TargetIR] = None
    effects: tuple[EffectIR, ...] = ()
    timing: str = "immediate"
    activation_limit: Optional[int] = None
    source_text: str = ""
    dependencies: tuple[str, ...] = ()
    status: str = "unknown"
    activation_scope: str = "global"
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

class RuleDependencyGraph:
    """Small dependency graph used for implementation planning/debugging."""
    def __init__(self, rules: Iterable[RuleIR] = ()):
        self.rules = {r.rule_id: r for r in rules}

    def add(self, rule: RuleIR) -> None:
        self.rules[rule.rule_id] = rule

    def dependencies_of(self, rule_id: str) -> List[str]:
        r = self.rules.get(rule_id)
        return list(r.dependencies) if r else []

    def dependents_of(self, rule_id: str) -> List[str]:
        return [r.rule_id for r in self.rules.values() if rule_id in r.dependencies]

    def unresolved(self, implemented: Iterable[str]) -> List[str]:
        done = set(implemented)
        return [rid for rid, r in self.rules.items() if rid not in done and any(d not in done for d in r.dependencies)]

    def missing_dependencies(self) -> Dict[str, List[str]]:
        known = set(self.rules)
        return {rid: [d for d in r.dependencies if d not in known]
                for rid, r in self.rules.items() if any(d not in known for d in r.dependencies)}

    def execution_order(self, implemented: Iterable[str] = ()) -> List[str]:
        """Return a dependency-safe order for known rules.

        Dependencies are evaluated before dependents. Implemented rules are
        omitted from the returned worklist. Missing dependencies and cycles are
        rejected instead of silently inventing an order.
        """
        done = set(implemented)
        missing = self.missing_dependencies()
        if missing:
            raise ValueError(f"missing rule dependencies: {missing}")
        cycles = self.cycles()
        if cycles:
            raise ValueError(f"rule dependency cycle: {cycles[0]}")
        pending = {rid for rid in self.rules if rid not in done}
        order: List[str] = []
        while pending:
            ready = sorted(rid for rid in pending if all(d in done or d in order for d in self.rules[rid].dependencies))
            if not ready:
                raise ValueError("unable to resolve rule dependency order")
            order.extend(ready)
            pending.difference_update(ready)
        return order

    def cycles(self) -> List[List[str]]:
        """Return dependency cycles as rule-id paths."""
        graph = {rid: [d for d in r.dependencies if d in self.rules] for rid, r in self.rules.items()}
        state: Dict[str, int] = {}
        stack: List[str] = []
        found: List[List[str]] = []

        def visit(node: str) -> None:
            state[node] = 1
            stack.append(node)
            for dep in graph.get(node, []):
                if state.get(dep, 0) == 0:
                    visit(dep)
                elif state.get(dep) == 1 and dep in stack:
                    i = stack.index(dep)
                    found.append(stack[i:] + [dep])
            stack.pop()
            state[node] = 2

        for rid in graph:
            if state.get(rid, 0) == 0:
                visit(rid)
        return found
