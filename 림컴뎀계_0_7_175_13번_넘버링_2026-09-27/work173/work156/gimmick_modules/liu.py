"""Combat affiliation module: 리우.

Classification/ownership lives here so the runtime does not need a monolithic
affiliation map. Empty RULE_KINDS means the affiliation is classified and
lazily loadable, while its concrete rules are still data/parser driven.
"""
MODULE_NAME = 'liu'
DISPLAY_NAME = '리우'
RULE_KINDS = []
RESOURCE_NAMES = []

def metadata() -> dict:
    return {"name": MODULE_NAME, "display_name": DISPLAY_NAME, "rule_kinds": list(RULE_KINDS), "resource_names": list(RESOURCE_NAMES)}

def owns_rule(kind: str) -> bool:
    return kind in RULE_KINDS

def owns_resource(name: str) -> bool:
    return str(name) in RESOURCE_NAMES
