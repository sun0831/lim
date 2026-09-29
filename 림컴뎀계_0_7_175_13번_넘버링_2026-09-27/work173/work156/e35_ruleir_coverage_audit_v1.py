"""E35-2: Clause -> RuleIR coverage audit over the canonical gap corpus.

This audit measures structural compilation coverage only. It does not claim
that a compiled RuleIR is gameplay-complete; runtime semantics still belong to
existing runtimes and later E36/golden validation.
"""
from __future__ import annotations
import json
from collections import Counter
from pathlib import Path
from rule_ir_compiler_v1 import compile_text
from passive_compiler_v29 import split_clauses
from primitive_registry_v1 import DEFAULT_REGISTRY


def run(input_path: str = "GIMMICK_GAP_REPORT_v4.json") -> dict:
    data = json.loads(Path(input_path).read_text(encoding="utf-8"))
    rows = []
    total_clauses = total_rules = total_unsupported = 0
    category_clauses = Counter(); category_rules = Counter()
    primitive_counts = Counter(); unsupported_reasons = Counter()
    unknown_primitives = Counter()
    for i, gap in enumerate(data.get("gaps", [])):
        text = str(gap.get("source_text", ""))
        clauses = split_clauses(text)
        total_clauses += len(clauses)
        converted = 0
        rule_ids = []
        for j, clause in enumerate(clauses):
            rules, reasons, unsupported = compile_text(clause, str(gap.get("identity_id", "unknown")), f"gap:{i}:{j}")
            if rules:
                converted += 1
                for r in rules:
                    rule_ids.append(r.rule_id)
                    for pid in r.metadata.get("primitive_contracts", []):
                        primitive_counts[pid] += 1
                        if DEFAULT_REGISTRY.get(pid) is None:
                            unknown_primitives[pid] += 1
            else:
                for reason in unsupported:
                    unsupported_reasons[reason] += 1
        total_rules += converted
        total_unsupported += len(clauses) - converted
        cats = gap.get("categories", [])
        for cat in cats:
            category_clauses[cat] += len(clauses)
            category_rules[cat] += converted
        rows.append({
            "identity_id": gap.get("identity_id"),
            "identity_name": gap.get("identity_name"),
            "passive_name": gap.get("passive_name"),
            "categories": cats,
            "clauses": len(clauses),
            "converted_clauses": converted,
            "unsupported_clauses": len(clauses) - converted,
            "rule_ids": rule_ids,
        })
    return {
        "version": "E35-2",
        "scope": "GIMMICK_GAP_REPORT_v4.json / gaps",
        "record_count": len(rows),
        "total_clauses": total_clauses,
        "converted_clauses": total_rules,
        "unsupported_clauses": total_unsupported,
        "clause_conversion_rate_percent": round(total_rules / total_clauses * 100, 2) if total_clauses else 0,
        "category": {
            k: {"clauses": category_clauses[k], "converted": category_rules[k],
                "rate_percent": round(category_rules[k] / category_clauses[k] * 100, 2)}
            for k in sorted(category_clauses)
        },
        "primitive_contract_usage": dict(sorted(primitive_counts.items())),
        "unknown_primitive_contracts": dict(sorted(unknown_primitives.items())),
        "unsupported_reasons": dict(sorted(unsupported_reasons.items())),
        "records": rows,
    }


if __name__ == "__main__":
    result = run()
    Path("E35_RULEIR_COVERAGE_AUDIT.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: result[k] for k in ("record_count", "total_clauses", "converted_clauses", "unsupported_clauses", "clause_conversion_rate_percent")}, ensure_ascii=False))
