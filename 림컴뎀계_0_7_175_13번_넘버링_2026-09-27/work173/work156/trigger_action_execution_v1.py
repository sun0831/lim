"""C-7 trigger/generated-action boundary.

This module owns the translation from a Trigger/Gimmick generated-action request
into an ActionQueue request.  It deliberately does not execute damage; execution
remains owned by OneTurnSolverV29/ActionQueue so causal ordering is unchanged.
"""
from dataclasses import dataclass

@dataclass(frozen=True)
class TriggerDispatchResult:
    queued: object
    generated: object

class TriggerActionExecutionBoundary:
    """Common boundary for trigger -> generated ActionQueue dispatch."""

    def __init__(self, action_queue):
        self.action_queue = action_queue

    @staticmethod
    def _inherit(request, value, attr):
        if value in (None, '', [], ()):
            return getattr(request, attr)
        return value

    def enqueue_from_gimmick(self, request, generated_action, *, source_event, source_context=None):
        inherit_target = (
            generated_action.target_policy in (None, '', 'main')
            and generated_action.target_index is None
            and generated_action.target_ids is None
            and request.target_policy is not None
        )
        generated = self.action_queue.triggered_from(
            request,
            generated_action.identity_id,
            generated_action.skill_id,
            generated_action.reason,
            source_event=source_event,
            faces=generated_action.forced_faces,
            target_policy=(request.target_policy if inherit_target else generated_action.target_policy),
            target_index=(request.target_index if inherit_target else generated_action.target_index),
            target_ids=(request.target_ids if inherit_target else generated_action.target_ids),
            target_override_ids=(request.target_override_ids if inherit_target else generated_action.target_override_ids),
            coin_target_ids=(request.coin_target_ids if inherit_target else generated_action.coin_target_ids),
            trigger_kind=generated_action.trigger_kind,
        )
        queued = self.action_queue.enqueue_triggered(generated)
        return TriggerDispatchResult(queued=queued, generated=generated)
