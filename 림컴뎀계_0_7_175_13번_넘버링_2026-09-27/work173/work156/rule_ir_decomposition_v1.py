"""E35-5 conservative compound-clause decomposition.

This module does not invent semantics. It segments Korean passive text into
candidate condition/trigger/target/effect fragments so the RuleIR compiler can
later lower each fragment through existing contracts. Every fragment retains
source text and confidence; unknown fragments remain opaque.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
import re
from typing import List

@dataclass(frozen=True)
class ClauseFragment:
    text: str
    role: str
    confidence: str = "low"

@dataclass(frozen=True)
class Decomposition:
    source_text: str
    fragments: tuple[ClauseFragment, ...]
    needs_compound_lowering: bool

_TRIGGER_PATTERNS = [
    (r"(?:턴|전투|스테이지)\s*(?:시작|종료)", "trigger"),
    (r"(?:공격|스킬|코인)\s*(?:시작|종료|적중|사용)\s*시", "trigger"),
    (r"(?:피격|사망|처치|흐트러짐|합\s*승리|합\s*패배).*?시", "trigger"),
]
_CONDITION_PATTERNS = [
    r"(?:이면|이면,|일 때|있으면|없으면|경우|조건|이상|이하|미만|초과|때문에|보유 중)",
]
_TARGET_PATTERNS = [
    r"(?:아군|적|대상|인격|본체|부위|슬롯).*?(?:1명|2명|3명|가장|무작위|소속)",
]
_EFFECT_PATTERNS = [
    r"(?:얻음|얻는다|얻고|부여|증가|감소|변경|발동|사용함|공격|회복|소모|전가)",
]

def _role(text: str) -> str:
    for p, role in _TRIGGER_PATTERNS:
        if re.search(p, text): return role
    if any(re.search(p, text) for p in _CONDITION_PATTERNS): return "condition"
    if any(re.search(p, text) for p in _TARGET_PATTERNS): return "target"
    if any(re.search(p, text) for p in _EFFECT_PATTERNS): return "effect"
    return "opaque"

def decompose_clause(text: str) -> Decomposition:
    text = str(text).strip()
    # Only split at high-confidence connective boundaries. Parenthesized timing
    # notes are preserved as part of the source fragment rather than guessed.
    parts = [p.strip() for p in re.split(r"\s*(?:;|\n|,\s*(?=(?:그리고|또는|추가로|대신|이후|해당)))\s*", text) if p.strip()]
    if len(parts) == 1:
        # Common Korean passive clauses use '/' to enumerate independent effects.
        parts = [p.strip() for p in re.split(r"\s*/\s*", text) if p.strip()]
    frags = tuple(ClauseFragment(p, _role(p), "high" if _role(p) != "opaque" else "low") for p in parts)
    roles = {f.role for f in frags}
    return Decomposition(text, frags, len(frags) > 1 or len(roles - {"effect", "opaque"}) > 0)

def to_dict(d: Decomposition) -> dict:
    x = asdict(d)
    x["fragments"] = [asdict(f) for f in d.fragments]
    return x
