"""Architecture contract/audit helpers for 림컴뎀계 0.6.6.

The audit is deliberately structural: it checks that solver results expose the
analyzer contract (requested/resolved/triggered actions, breakdowns, state
snapshots, next-turn state, and event log) without changing damage rules.
"""
from __future__ import annotations
from typing import Any, Dict, Iterable, List

REQUIRED_RESULT_KEYS = (
    'requested_plan', 'actions', 'damage_by_identity', 'damage_by_skill',
    'event_log', 'state_diff', 'next_turn_state',
)
REQUIRED_ACTION_KEYS = (
    'action_type', 'requested_action', 'resolved_action', 'generated',
    'identity_id', 'skill_id', 'coins', 'state_at_action_start',
    'state_at_action_end', 'state_diff',
)


def audit_result(result: Dict[str, Any]) -> Dict[str, Any]:
    missing = [k for k in REQUIRED_RESULT_KEYS if k not in result]
    action_missing: Dict[str, List[str]] = {}
    for i, action in enumerate(result.get('actions', []) or [], 1):
        miss = [k for k in REQUIRED_ACTION_KEYS if k not in action]
        if miss:
            action_missing[str(i)] = miss
    return {
        'ok': not missing and not action_missing,
        'missing_result_keys': missing,
        'action_missing_keys': action_missing,
        'action_count': len(result.get('actions', []) or []),
        'requested_count': len(result.get('requested_plan', []) or []),
        'triggered_count': sum(1 for a in result.get('actions', []) or [] if a.get('action_type') == 'triggered'),
    }


def first_divergence(expected: Iterable[Dict[str, Any]], actual: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
    """Return the first differing event/action field between two traces."""
    e, a = list(expected), list(actual)
    n = min(len(e), len(a))
    for idx in range(n):
        if e[idx] != a[idx]:
            keys = sorted(set(e[idx]) | set(a[idx]))
            for key in keys:
                if e[idx].get(key) != a[idx].get(key):
                    return {'found': True, 'index': idx, 'field': key,
                            'expected': e[idx].get(key), 'actual': a[idx].get(key)}
            return {'found': True, 'index': idx, 'field': '<record>',
                    'expected': e[idx], 'actual': a[idx]}
    if len(e) != len(a):
        return {'found': True, 'index': n, 'field': '<length>', 'expected': len(e), 'actual': len(a)}
    return {'found': False, 'index': None, 'field': None, 'expected': None, 'actual': None}
