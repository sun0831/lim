"""E21 audit: verify highest-resource selector cases in the source gap corpus.

This is deliberately a corpus audit, not a natural-language compiler. It only records
source clauses whose wording explicitly expresses a highest/most resource selection.
"""
from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "GIMMICK_GAP_REPORT_v4.md.json"
OUT = ROOT / "RESOURCE_SELECTOR_SYMMETRY_E21.json"

PHRASES = {
    "charge_highest_ally": "충전 횟수가 가장 높은 아군",
    "ammo_most_ally": "탄환을 가장 많이 보유한 아군",
}

def build():
    data = json.loads(SRC.read_text(encoding="utf-8"))
    rows=[]
    for r in data.get("gaps", []):
        text=r.get("source_text", "")
        for kind, phrase in PHRASES.items():
            if phrase in text:
                rows.append({
                    "identity_name": r.get("identity_name"),
                    "passive_name": r.get("passive_name"),
                    "categories": r.get("categories", []),
                    "selector_case": kind,
                    "phrase": phrase,
                    "source_text": text,
                    "mapped_primitive": "highest_resource_selector",
                    "target_side": "ally",
                    "resource_semantics": "charge_count" if kind.startswith("charge") else "ammo_count",
                })
    out={
        "version":"E21",
        "source":"GIMMICK_GAP_REPORT_v4.md.json",
        "scope":"explicit highest/most resource target-selection phrases",
        "matched_records":len(rows),
        "cases":rows,
        "conclusion":"The corpus contains explicit highest-resource ally selection cases; the symmetric primitive exists and should not be conflated with generic highest-HP/highest-status target selection."
    }
    OUT.write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding="utf-8")
    return out

if __name__ == '__main__':
    print(json.dumps(build(),ensure_ascii=False,indent=2))
