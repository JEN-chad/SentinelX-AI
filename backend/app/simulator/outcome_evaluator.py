"""SentinelX AI - Incident Simulator Outcome Evaluator (Phase 9)

Evaluates completed incident simulation episodes, computing containment efficacy,
operational disruption cost, false action penalties, and net reward.
"""

from typing import List, Optional
from pydantic import BaseModel, Field

from app.schemas.common import ActionType
from .scenarios import Scenario
from .transition_model import TransitionOutcome


class EpisodeOutcome(BaseModel):
    """Aggregate evaluation metrics for a single simulation episode."""
    scenario_id: str
    scenario_name: str
    ground_truth_label: str
    total_steps: int
    is_contained: bool
    containment_success: bool
    false_action: bool
    total_disruption_cost: float = Field(..., ge=0.0)
    total_damage_cost: float = Field(..., ge=0.0)
    containment_reward: float
    net_reward: float
    final_service_health: float = Field(..., ge=0.0, le=100.0)
    steps_to_contain: Optional[int] = None
    actions_taken: List[str]
    summary: str


class OutcomeEvaluator:
    """Computes comprehensive evaluation metrics from episode transition history."""

    @staticmethod
    def evaluate(
        scenario: Scenario,
        transition_history: List[TransitionOutcome],
    ) -> EpisodeOutcome:
        """Evaluate full trajectory of transition outcomes against scenario ground truth."""
        total_steps = len(transition_history)
        is_contained = any(t.is_contained for t in transition_history)
        containment_success = any(t.containment_success for t in transition_history)
        false_action = any(t.false_action for t in transition_history)

        total_disruption = sum(t.operational_disruption for t in transition_history)
        total_damage = sum(t.damage_incurred for t in transition_history)
        actions_taken = [t.action.value for t in transition_history]

        # Calculate steps to containment
        steps_to_contain = None
        for idx, t in enumerate(transition_history, 1):
            if t.containment_success:
                steps_to_contain = idx
                break

        # Calculate reward components
        is_benign = scenario.ground_truth_label == "BENIGN"

        if is_benign:
            # Benign scenario: reward is for not disrupting operations
            if false_action:
                containment_reward = -50.0  # False alarm punishment
            else:
                containment_reward = 30.0   # Reward for safe passive observation
        else:
            # Threat scenario: reward is for prompt containment
            if containment_success:
                containment_reward = 80.0
            else:
                containment_reward = -30.0  # Unmitigated breach

        final_health = transition_history[-1].service_health if transition_history else scenario.initial_service_health

        # Net reward calculation
        # net = containment_reward - disruption - damage
        net_reward = round(containment_reward - total_disruption - total_damage, 2)

        # Summary text
        if is_benign:
            if false_action:
                summary = (
                    f"FAILED: Benign activity in '{scenario.name}' was unnecessarily blocked, "
                    f"causing {total_disruption:.1f} operational disruption cost."
                )
            else:
                summary = (
                    f"SUCCESS: Benign activity in '{scenario.name}' was handled without disruptive blocks. "
                    f"Final health: {final_health:.1f}%."
                )
        else:
            if containment_success:
                summary = (
                    f"SUCCESS: Threat '{scenario.ground_truth_label}' successfully contained in "
                    f"step {steps_to_contain}/{total_steps}. Final health: {final_health:.1f}%."
                )
            else:
                summary = (
                    f"FAILED: Threat '{scenario.ground_truth_label}' escaped containment. "
                    f"Total damage incurred: {total_damage:.1f}. Final health: {final_health:.1f}%."
                )

        return EpisodeOutcome(
            scenario_id=scenario.scenario_id,
            scenario_name=scenario.name,
            ground_truth_label=scenario.ground_truth_label,
            total_steps=total_steps,
            is_contained=is_contained,
            containment_success=containment_success,
            false_action=false_action,
            total_disruption_cost=round(total_disruption, 2),
            total_damage_cost=round(total_damage, 2),
            containment_reward=round(containment_reward, 2),
            net_reward=net_reward,
            final_service_health=round(final_health, 2),
            steps_to_contain=steps_to_contain,
            actions_taken=actions_taken,
            summary=summary,
        )
