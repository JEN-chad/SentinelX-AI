"""SentinelX AI - Incident State Machine

Enforces strict lifecycle state transitions and prevents unauthorized workflow progression.
"""

from typing import Set
from app.schemas.common import IncidentStatus
from app.schemas.incidents import VALID_TRANSITIONS, can_transition


class IncidentStateMachine:
    """Evaluates and validates incident lifecycle transitions."""

    @staticmethod
    def get_allowed_next_states(current_status: IncidentStatus) -> Set[IncidentStatus]:
        """Return the set of valid next states from the given status."""
        return VALID_TRANSITIONS.get(current_status, set())

    @staticmethod
    def validate_transition(current_status: IncidentStatus, target_status: IncidentStatus) -> None:
        """Validate whether the transition is permitted. Raises ValueError if invalid."""
        if not can_transition(current_status, target_status):
            allowed = [s.value for s in VALID_TRANSITIONS.get(current_status, set())]
            raise ValueError(
                f"State transition rejected: Cannot move incident from '{current_status.value}' "
                f"to '{target_status.value}'. Permitted transitions: {allowed}"
            )
