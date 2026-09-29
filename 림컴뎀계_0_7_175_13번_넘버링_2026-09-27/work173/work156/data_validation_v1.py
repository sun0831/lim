"""Validation helpers for the normalized identity catalog and generated views."""
from __future__ import annotations
from typing import Any, Dict, List

KEYS = ("id", "gameId", "sinnerId", "name", "skills", "passives")

def validate_identity(identity: Dict[str, Any]) -> List[str]:
    errors=[]
    for k in KEYS:
        if k not in identity: errors.append(f"missing:{k}")
    if not identity.get("id"): errors.append("empty:id")
    if not identity.get("sinnerId"): errors.append("empty:sinnerId")
    skills = identity.get("skills") or []
    seen=set()
    for i,s in enumerate(skills):
        sid=str(s.get("id", ""))
        if not sid: errors.append(f"skill[{i}]:missing:id")
        elif sid in seen: errors.append(f"skill[{i}]:duplicate:id:{sid}")
        seen.add(sid)
        cc=s.get("coinCount")
        if cc is not None and int(cc) < 0: errors.append(f"skill[{i}]:negative:coinCount")
        coins=s.get("coinPowers") or []
        if cc is not None and coins and len(coins) != int(cc):
            errors.append(f"skill[{i}]:coinCount_mismatch:{cc}!={len(coins)}")
    return errors

def validate_catalog(catalog: Dict[str, Any]) -> Dict[str, Any]:
    identities=catalog.get("identities") if isinstance(catalog,dict) else None
    errors=[]; ids=set(); duplicate=[]
    if not isinstance(identities,list):
        errors.append("identities:not_list")
        identities=[]
    for i,x in enumerate(identities):
        iid=x.get("id") if isinstance(x,dict) else None
        if iid in ids: duplicate.append(iid)
        ids.add(iid)
        for e in validate_identity(x if isinstance(x,dict) else {}):
            errors.append(f"identity[{i}]={iid}:{e}")
    return {"ok": not errors and not duplicate, "identity_count": len(identities),
            "unique_identity_count": len(ids), "duplicates": duplicate, "errors": errors}
