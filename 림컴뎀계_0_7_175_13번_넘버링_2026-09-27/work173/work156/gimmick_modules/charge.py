"""Generic Charge keyword module metadata.

Special resources such as Ring Finger's 생체 재료 are represented by the same
ResourceRuntime semantics as Charge; identity modules only provide their
identity-specific acquisition/consumption rules.
"""
MODULE_NAME = "charge"
DISPLAY_NAME = "충전"
RESOURCE_ALIASES = ("충전", "생체 재료")

def metadata() -> dict:
    return {"name": MODULE_NAME, "display_name": DISPLAY_NAME, "resource_aliases": list(RESOURCE_ALIASES)}
