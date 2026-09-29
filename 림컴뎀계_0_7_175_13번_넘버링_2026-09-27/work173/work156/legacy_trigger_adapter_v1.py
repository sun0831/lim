"""Explicit compatibility adapter for the retired TriggerRuntime.

Production combat code must not import or expose the legacy trigger runtime.
Tests that still need historical behavior instantiate this adapter directly.
"""
from legacy_trigger_compat_v1 import fire

class LegacyTriggerAdapter:
    def __init__(self, rules):
        self.rules = list(rules)
    def fire(self, event, ctx=None):
        return fire(self.rules, event, dict(ctx or {}))
    def reset_turn(self):
        return None
