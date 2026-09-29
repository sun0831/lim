"""Compatibility-only wrappers for the retired production event bridge.

The live combat path uses :mod:`event_runtime_v1`. This module remains only
for older external/test callers that imported the former compatibility entry
points directly.
"""

from event_runtime_v1 import (
    after_skill,
    after_received_attack,
    after_kill,
    after_coin,
    after_resource_event,
    after_lifecycle_event,
)

__all__ = [
    "after_skill", "after_received_attack", "after_kill", "after_coin",
    "after_resource_event", "after_lifecycle_event",
]
