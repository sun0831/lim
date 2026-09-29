"""Lazy module classification/loading for one-turn gimmick rules.

The calculator distinguishes two orthogonal axes:
  * generic combat keywords (Charge/Bleed/Poise/Tremor/Burn/Rupture/Sinking)
  * identity/faction gimmick modules (Dawn Office/Middle/Pequod/Ring/...)

A resource that behaves like an existing generic keyword stays in that keyword
module.  For example, Ring Finger's ``생체 재료`` is a Charge-compatible
resource; Ring only supplies its acquisition/consumption rules.

This module intentionally contains classification metadata only.  It does not
own combat math, which remains in ResourceRuntime/TriggerRuntime/DamageEngine.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Any
import importlib
import json
from pathlib import Path

GENERIC_KEYWORDS = {
    "충전": "charge",
    "출혈": "bleed",
    "호흡": "poise",
    "진동": "tremor",
    "화상": "burn",
    "파열": "rupture",
    "침잠": "sinking",
}

# Affiliation/name aliases used by the catalog.  Keep aliases data-oriented so
# adding a new identity does not require another parser branch.
GROUP_ALIASES = {
    "dawn_office": ("DAWN", "새벽 사무소"),
    "blade_lineage": ("BLADE LINEAGE", "검계"),
    "thumb": ("THUMB FINGER", "엄지"),
    "middle": ("MIDDLE FINGER", "중지"),
    "ring": ("RING FINGER", "약지"),
    "index": ("INDEX FINGER", "검지"),
    "pequod": ("PEQUOD CREW", "피쿼드호", "피쿼드"),
    "black_cloud": ("BLACK CLOUD", "흑운회"),
    "spider_house": ("SPIDER HOUSE", "거미집"),
    "seven": ("SEVEN", "세븐 협회"),
    "zwei": ("ZWEI", "츠바이 협회"),
    "liu": ("LIU", "리우 협회"),
    "n_corp": ("N사", "N사 광신도"),
    "w_corp": ("W CORP", "W사"),
    "full_stop": ("FULL STOP", "마침표 사무소"),
    "la_mancha_land": ("LA MANCHA LAND", "라만차랜드"),
}

AFFILIATION_BOUND_RESOURCES = {
    "dawn_office": ("새벽불", "불꽃나비의 관"),
    "index": ("검지의 지령",),
    "middle": ("중지 - 원한", "중지식 강화 문신", "원한 문신", "앙갚음 장부"),
}

KEYWORD_EQUIVALENT_RESOURCES = {
    "생체 재료": "charge",
}

MANIFEST_PATH = Path(__file__).with_name("identity_module_manifest_v1.json")

def _load_manifest() -> dict[str, dict]:
    try:
        raw = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        return {str(x["identity_id"]): x for x in raw.get("identities", [])}
    except (OSError, ValueError, TypeError, KeyError):
        return {}

IDENTITY_MODULE_MANIFEST = _load_manifest()

@dataclass(frozen=True)
class IdentityModuleManifest:
    identity_id: str
    keywords: tuple[str, ...] = ()
    gimmick_modules: tuple[str, ...] = ()
    resources: tuple[str, ...] = ()
    combat_affiliations: tuple[str, ...] = ()

    @property
    def keyword_modules(self) -> tuple[str, ...]:
        """Generic seven-keyword modules only."""
        return self.keywords

    @property
    def affiliation_modules(self) -> tuple[str, ...]:
        """Combat-relevant affiliation modules only.

        Raw catalog affiliations are intentionally not used as combat modules.
        This axis contains only affiliations whose presence/skills/passives
        can change the one-turn combat calculation.
        """
        return self.combat_affiliations or self.gimmick_modules

    @property
    def modules(self) -> tuple[str, ...]:
        """Backward-compatible union of both independent axes."""
        return tuple(dict.fromkeys((*self.keyword_modules, *self.affiliation_modules)))


def _text_blob(identity: Any) -> str:
    parts = [
        str(getattr(identity, "name", "") or ""),
        str(getattr(identity, "full_name", "") or ""),
        str(getattr(identity, "fullName", "") or ""),
        " ".join(str(x) for x in (getattr(identity, "affiliation", []) or [])),
        " ".join(str(x) for x in (getattr(identity, "keywords", []) or [])),
        " ".join(str(x) for x in (getattr(identity, "resources", []) or [])),
    ]
    for p in getattr(identity, "passives", []) or []:
        if isinstance(p, dict):
            parts.extend(str(p.get(k, "") or "") for k in ("name", "effect", "condition"))
    for s in (getattr(identity, "skills", {}) or {}).values():
        parts.extend([str(getattr(s, "name", "") or ""), str(getattr(s, "effect", "") or "")])
        parts.extend(str(x) for x in (getattr(s, "_source_effects", []) or []))
    return "\n".join(parts)


def _affiliations(identity: Any) -> set[str]:
    vals = getattr(identity, "affiliation", []) or []
    if isinstance(vals, str):
        vals = [vals]
    return {str(x).strip().upper() for x in vals if str(x).strip()}


def resolve_identity_manifest(identity: Any) -> IdentityModuleManifest:
    """Resolve the modules required by one selected identity.

    The generated catalog manifest is authoritative when present.  Runtime
    fallback remains for legacy/custom identity objects used by unit tests.
    Keywords and affiliation/gimmick modules are intentionally independent
    multi-label axes.
    """
    iid = str(getattr(identity, "id", ""))
    entry = IDENTITY_MODULE_MANIFEST.get(iid)
    if entry:
        return IdentityModuleManifest(
            iid,
            tuple(entry.get("keywords", ())),
            tuple(entry.get("gimmick_modules", ())),
            tuple(entry.get("resources", ())),
            tuple(entry.get("combat_affiliations", entry.get("gimmick_modules", ()))),
        )

    text = _text_blob(identity)
    folded = text.upper()
    keywords = []
    raw_keywords = getattr(identity, "keywords", []) or []
    for kw in raw_keywords:
        module = GENERIC_KEYWORDS.get(str(kw).strip())
        if module and module not in keywords:
            keywords.append(module)
    if "생체 재료" in text and "charge" not in keywords:
        keywords.append("charge")

    groups = []
    aff = _affiliations(identity)
    for group, aliases in GROUP_ALIASES.items():
        if any(alias.upper() in aff or alias.upper() in folded for alias in aliases):
            groups.append(group)

    resources = [str(resource) for resource in (getattr(identity, "resources", []) or [])]
    if "생체 재료" in text and "생체 재료" not in resources:
        resources.append("생체 재료")
    return IdentityModuleManifest(iid, tuple(keywords), tuple(groups), tuple(dict.fromkeys(resources)), tuple(groups))


class ModuleResolver:
    """Builds a lazy active-module set from the currently selected identities."""
    def __init__(self, identities: Iterable[Any]):
        self.identities = list(identities or [])
        self.manifests = {str(getattr(i, "id", "")): resolve_identity_manifest(i) for i in self.identities}
        self.active_modules = set()
        for manifest in self.manifests.values():
            self.active_modules.update(manifest.modules)
        # Lazy loading: only module providers required by selected identities
        # are imported. Generic keyword modules are tiny metadata providers;
        # faction modules can later own their parser/rule providers without
        # changing the resolver contract.
        self.loaded_module_providers = {"common": importlib.import_module("gimmick_modules.common"), "identity_specific": importlib.import_module("gimmick_modules.identity_specific")}
        for module in sorted(self.active_modules):
            self._load_provider(module)

    def __deepcopy__(self, memo):
        # Provider modules are immutable Python module singletons and must not
        # be recursively copied when solver branches clone combat state.
        import copy
        clone=copy.copy(self)
        clone.identities=copy.deepcopy(self.identities,memo)
        clone.manifests=copy.deepcopy(self.manifests,memo)
        clone.active_modules=set(self.active_modules)
        clone.loaded_module_providers=dict(self.loaded_module_providers)
        memo[id(self)]=clone
        return clone

    def rule_module(self, rule) -> str | None:
        """Resolve concrete rule ownership from the loaded module provider."""
        for module in sorted(self.active_modules):
            provider = self.loaded_module_providers.get(module)
            if provider is None:
                continue
            f = getattr(provider, "owns_resource_gain_rule", None)
            if callable(f) and f(rule):
                return module
            f = getattr(provider, "owns_rule", None)
            if callable(f) and f(rule.kind):
                return module
        return None

    def _load_provider(self, module: str):
        if module in self.loaded_module_providers:
            return self.loaded_module_providers[module]
        try:
            provider = importlib.import_module(f"gimmick_modules.{module}")
        except ModuleNotFoundError:
            provider = None
        self.loaded_module_providers[module] = provider
        return provider

    def enabled(self, module: str, identity_id: str | None = None) -> bool:
        if identity_id is not None:
            manifest = self.manifests.get(str(identity_id))
            return bool(manifest and module in manifest.modules)
        return module in self.active_modules

    def required_for(self, identity_id: str) -> tuple[str, ...]:
        m = self.manifests.get(str(identity_id))
        return m.modules if m else ()

    def summary(self) -> dict:
        active_keywords = sorted({m for x in self.manifests.values() for m in x.keyword_modules})
        active_affiliations = sorted({m for x in self.manifests.values() for m in x.affiliation_modules})
        return {
            "active_modules": sorted(self.active_modules),
            "active_keyword_modules": active_keywords,
            "active_affiliation_modules": active_affiliations,
            "loaded_module_providers": sorted(k for k,v in self.loaded_module_providers.items() if v is not None),
            "identity_manifests": {
                iid: {
                    "keywords": list(m.keyword_modules),
                    "keyword_modules": list(m.keyword_modules),
                    "affiliations": list(m.affiliation_modules),
                    "gimmick_modules": list(m.affiliation_modules),
                    "combat_affiliations": list(m.affiliation_modules),
                    "resources": list(m.resources),
                    "modules": list(m.modules),
                }
                for iid, m in self.manifests.items()
            },
        }
