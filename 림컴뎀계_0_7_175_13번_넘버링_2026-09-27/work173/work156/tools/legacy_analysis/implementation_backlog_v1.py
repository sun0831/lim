"""Generate a conservative rule-implementation backlog from identity data.

This tool does not claim that a textual rule is implemented or unimplemented.
It extracts candidate rule records with status='unknown' so later Runtime/data
mapping can explicitly classify them. This avoids silently treating missing
parsers as implemented.
"""
from __future__ import annotations
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List


def _record(i: Dict[str, Any], location: str, source: str, category: str, index: int) -> Dict[str, Any]:
    return {
        "rule_id": f"catalog:{i.get('id')}:{location}:{index}",
        "identity_id": str(i.get("id", "")),
        "identity_name": str(i.get("fullName", i.get("name", ""))),
        "location": location,
        "category": category,
        "source_text": str(source),
        "status": "unknown",
        "classification": None,
        "runtime": None,
        "dependencies": [],
    }


def extract_backlog(catalog: Dict[str, Any]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for identity in catalog.get("identities", []):
        for si, skill in enumerate(identity.get("skills", []) or []):
            for ei, effect in enumerate(skill.get("effects", []) or []):
                if str(effect).strip():
                    rows.append(_record(identity, f"skill:{skill.get('slot', '')}:{skill.get('id', '')}:effect", effect, "skill_effect", ei))
        for si, skill in enumerate(identity.get("defenseSkills", []) or []):
            for ei, effect in enumerate(skill.get("effects", []) or []):
                if str(effect).strip():
                    rows.append(_record(identity, f"defense:{skill.get('id', '')}:effect", effect, "defense_effect", ei))
        for pi, passive in enumerate(identity.get("passives", []) or []):
            if isinstance(passive, dict):
                source = passive.get("effect", "")
                if str(source).strip():
                    category = "support_passive" if passive.get("type") == "서포트" else "passive"
                    rows.append(_record(identity, f"passive:{pi}:{passive.get('name', '')}", source, category, pi))
    return rows


def write_backlog(catalog_path: str | Path, output_path: str | Path) -> Dict[str, Any]:
    catalog = json.loads(Path(catalog_path).read_text(encoding="utf-8"))
    rows = extract_backlog(catalog)
    payload = {
        "schema_version": "1.0",
        "generated_from": str(catalog_path),
        "status_semantics": {"unknown": "추출만 되었으며 구현 여부를 판정하지 않음"},
        "rule_count": len(rows),
        "rules": rows,
    }
    Path(output_path).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"rule_count": len(rows), "output": str(output_path)}


if __name__ == "__main__":
    root = Path(__file__).resolve().parent
    print(write_backlog(root / "identity_catalog_v2.json", root / "IMPLEMENTATION_BACKLOG_v1.json"))
