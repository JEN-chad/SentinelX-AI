"""SentinelX AI - Simulator Transition Model (Phase 9)

Models system state transitions, operational consequences, and threat progression
under defensive actions with seeded pseudo-random uncertainty.
CRITICAL SAFETY INVARIANT: Validates against allowlisted action catalogue; rejects unauthorized actions.
"""

from typing import Optional, Union
import numpy as np
from pydantic import BaseModel, Field

from app.safety.action_catalogue import is_allowed_action
from app.schemas.common import ActionType
from .scenarios import Scenario


class TransitionOutcome(BaseModel):
    """Result of a state transition under an applied defensive action."""
    action: ActionType
    containment_success: bool
    false_action: bool
    operational_disruption: float = Field(..., ge=0.0)
    damage_incurred: float = Field(..., ge=0.0)
    threat_level: float = Field(..., ge=0.0, le=1.0)
    service_health: float = Field(..., ge=0.0, le=100.0)
    is_contained: bool
    reason: str


class TransitionModel:
    """Calculates deterministic or seed-controlled probabilistic state transitions."""

    def __init__(self, rng: Optional[np.random.RandomState] = None):
        self.rng = rng or np.random.RandomState(42)

    def set_seed(self, seed: int) -> None:
        """Reset internal pseudo-random generator for reproducible episodes."""
        self.rng = np.random.RandomState(seed)

    def step(
        self,
        action: Union[ActionType, str],
        current_threat_level: float,
        current_service_health: float,
        is_already_contained: bool,
        scenario: Scenario,
    ) -> TransitionOutcome:
        """Apply defensive action to current simulator state and return transition outcome."""
        # 1. Enforce Action Allowlist Safety Gate
        try:
            action_enum = ActionType(action) if isinstance(action, str) else action
        except (ValueError, KeyError):
            raise ValueError(
                f"Simulator rejected invalid or unknown action '{action}'. "
                f"Permitted catalogue: {[a.value for a in ActionType]}"
            )

        if not is_allowed_action(action_enum.value):
            raise ValueError(
                f"Action '{action_enum.value}' is not permitted by system safety catalogue."
            )

        # 2. If already contained, threat no longer progresses
        if is_already_contained:
            return TransitionOutcome(
                action=action_enum,
                containment_success=True,
                false_action=False,
                operational_disruption=0.0,
                damage_incurred=0.0,
                threat_level=0.0,
                service_health=current_service_health,
                is_contained=True,
                reason="Incident already contained; steady state maintained.",
            )

        is_benign = scenario.ground_truth_label == "BENIGN"

        # 3. Model Action Specific Dynamics
        if action_enum == ActionType.SIMULATE_BLOCK:
            if is_benign:
                # Severe false positive penalty for blocking benign asset
                disruption = 35.0 * (scenario.asset_criticality / 2.0) * scenario.disruption_weight
                return TransitionOutcome(
                    action=action_enum,
                    containment_success=False,
                    false_action=True,
                    operational_disruption=round(disruption, 2),
                    damage_incurred=0.0,
                    threat_level=current_threat_level,
                    service_health=current_service_health,
                    is_contained=False,
                    reason="Unnecessary block applied to benign asset; severe operational disruption incurred.",
                )
            else:
                # Threat scenario: 95% containment probability
                containment_roll = self.rng.uniform(0.0, 1.0)
                if containment_roll < 0.95:
                    disruption = 10.0 * (scenario.asset_criticality / 3.0)
                    return TransitionOutcome(
                        action=action_enum,
                        containment_success=True,
                        false_action=False,
                        operational_disruption=round(disruption, 2),
                        damage_incurred=0.0,
                        threat_level=0.0,
                        service_health=current_service_health,
                        is_contained=True,
                        reason=f"Threat '{scenario.ground_truth_label}' successfully contained via simulated block.",
                    )
                else:
                    # Rare partial evasion
                    reduced_threat = max(0.1, current_threat_level * 0.5)
                    disruption = 10.0 * (scenario.asset_criticality / 3.0)
                    damage = round(6.0 * reduced_threat, 2)
                    new_health = max(0.0, current_service_health - damage)
                    return TransitionOutcome(
                        action=action_enum,
                        containment_success=False,
                        false_action=False,
                        operational_disruption=round(disruption, 2),
                        damage_incurred=damage,
                        threat_level=round(reduced_threat, 3),
                        service_health=round(new_health, 2),
                        is_contained=False,
                        reason="Simulated block partially deflected threat, but adversary evaded perimeter.",
                    )

        elif action_enum == ActionType.INCREASE_MONITORING:
            disruption = 2.0
            if is_benign:
                damage = 0.0
                new_threat = current_threat_level
            else:
                growth = scenario.threat_growth_rate * 0.5  # Slower growth under observation
                new_threat = min(1.0, current_threat_level + growth)
                damage = round(4.0 * new_threat, 2)
            new_health = max(0.0, current_service_health - damage)
            return TransitionOutcome(
                action=action_enum,
                containment_success=False,
                false_action=False,
                operational_disruption=disruption,
                damage_incurred=damage,
                threat_level=round(new_threat, 3),
                service_health=round(new_health, 2),
                is_contained=False,
                reason="Monitoring elevated; telemetry enriched with minimal operational disruption.",
            )

        elif action_enum == ActionType.ESCALATE_FOR_APPROVAL:
            disruption = 1.0  # Latency cost while awaiting human analyst
            if is_benign:
                damage = 0.0
                new_threat = current_threat_level
            else:
                growth = scenario.threat_growth_rate
                new_threat = min(1.0, current_threat_level + growth)
                damage = round(7.0 * new_threat, 2)
            new_health = max(0.0, current_service_health - damage)
            return TransitionOutcome(
                action=action_enum,
                containment_success=False,
                false_action=False,
                operational_disruption=disruption,
                damage_incurred=damage,
                threat_level=round(new_threat, 3),
                service_health=round(new_health, 2),
                is_contained=False,
                reason="Incident escalated for human analyst review; response pending.",
            )

        elif action_enum == ActionType.RAISE_ALERT:
            disruption = 0.0  # Zero disruption
            if is_benign:
                damage = 0.0
                new_threat = current_threat_level
            else:
                growth = scenario.threat_growth_rate * 1.2
                new_threat = min(1.0, current_threat_level + growth)
                damage = round(12.0 * new_threat, 2)
            new_health = max(0.0, current_service_health - damage)
            return TransitionOutcome(
                action=action_enum,
                containment_success=False,
                false_action=False,
                operational_disruption=disruption,
                damage_incurred=damage,
                threat_level=round(new_threat, 3),
                service_health=round(new_health, 2),
                is_contained=False,
                reason="Alert logged to SIEM; passive monitoring permits unmitigated threat progression.",
            )

        raise ValueError(f"Unhandled action type: {action_enum}")
