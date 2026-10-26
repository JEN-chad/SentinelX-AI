"""SentinelX AI - Multi-Objective RL Reward Calculator (Phase 10)

Calculates scalar reward balancing threat containment against operational disruption,
false action penalties, damage, and response latency.
"""

from typing import Optional
from pydantic import BaseModel, Field

from app.schemas.common import ActionType
from app.simulator.transition_model import TransitionOutcome


class RewardWeights(BaseModel):
    """Configurable weights for the multi-objective reward formulation."""
    containment_bonus: float = Field(default=80.0, description="Bonus for containing real threat")
    benign_safe_bonus: float = Field(default=30.0, description="Bonus for completing benign scenario safely")
    false_block_penalty: float = Field(default=50.0, description="Penalty for blocking a benign asset")
    disruption_multiplier: float = Field(default=1.0, description="Multiplier for operational disruption cost")
    damage_multiplier: float = Field(default=1.5, description="Multiplier for threat damage to service health")
    delay_step_penalty: float = Field(default=2.0, description="Penalty per step to encourage prompt resolution")


class RewardCalculator:
    """Calculates step and terminal rewards according to formal multi-objective criteria."""

    def __init__(self, weights: Optional[RewardWeights] = None):
        self.weights = weights or RewardWeights()

    def compute_step_reward(
        self,
        transition: TransitionOutcome,
        is_done: bool,
        is_benign: bool,
        current_step: int,
    ) -> float:
        """Compute scalar step reward based on transition outcome and terminal criteria."""
        # 1. Base costs incurred at this step
        disruption_cost = transition.operational_disruption * self.weights.disruption_multiplier
        damage_cost = transition.damage_incurred * self.weights.damage_multiplier
        delay_cost = current_step * self.weights.delay_step_penalty

        reward = -disruption_cost - damage_cost

        # 2. Terminal outcomes
        if is_done:
            if transition.containment_success:
                reward += self.weights.containment_bonus - delay_cost
            elif transition.false_action:
                reward -= self.weights.false_block_penalty
            elif is_benign and not transition.false_action:
                reward += self.weights.benign_safe_bonus
            elif not is_benign and not transition.containment_success:
                # Uncontained threat failure
                reward -= self.weights.containment_bonus * 0.5

        return round(float(reward), 2)
