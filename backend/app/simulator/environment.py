"""SentinelX AI - Incident Simulator Environment (Phase 9)

Provides a standard simulation environment modeling threat progression, operational consequences,
and defensive responses with strict seed reproducibility.
CRITICAL SAFETY INVARIANT: Ground truth labels are stored strictly in private simulator state
and NEVER exposed in the public agent observation dictionary.
"""

from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np
from pydantic import BaseModel, Field

from app.schemas.common import ActionType
from .outcome_evaluator import EpisodeOutcome, OutcomeEvaluator
from .scenarios import Scenario, get_scenario, list_scenarios
from .transition_model import TransitionModel, TransitionOutcome


class Observation(BaseModel):
    """Observable telemetry exposed to detection models, agents, and RL policies.
    CRITICAL: Does NOT contain ground truth scenario label.
    """
    step: int
    observable_risk: float = Field(..., ge=0.0, le=1.0)
    observable_confidence: float = Field(..., ge=0.0, le=1.0)
    asset_criticality: int = Field(..., ge=1, le=5)
    recurrence_count: int = Field(default=1, ge=1)
    service_health: float = Field(..., ge=0.0, le=100.0)
    is_approval_pending: bool = False
    is_blocked: bool = False
    previous_action: Optional[str] = None


class EpisodeStepRecord(BaseModel):
    """Complete audit record for a single simulation step."""
    step: int
    observation: Observation
    action: str
    transition: TransitionOutcome
    step_reward: float


class IncidentSimulatorEnv:
    """Gymnasium-style environment for incident simulation and RL policy training."""

    def __init__(self, scenarios: Optional[List[Scenario]] = None, seed: int = 42):
        self.scenarios = scenarios or list_scenarios()
        self.scenarios_map = {s.scenario_id: s for s in self.scenarios}
        self.seed_val = seed
        self.rng = np.random.RandomState(seed)
        self.transition_model = TransitionModel(rng=self.rng)

        # Environment State (Reset in reset())
        self.current_scenario: Optional[Scenario] = None
        self.current_step_idx: int = 0
        self.current_threat_level: float = 0.0
        self.current_service_health: float = 100.0
        self.is_contained: bool = False
        self.is_approval_pending: bool = False
        self.is_blocked: bool = False
        self.previous_action: Optional[str] = None

        self.history: List[EpisodeStepRecord] = []
        self.transitions: List[TransitionOutcome] = []

    def seed(self, seed: int) -> None:
        """Set random seed for deterministic reproducibility."""
        self.seed_val = seed
        self.rng = np.random.RandomState(seed)
        self.transition_model.set_seed(seed)

    def reset(
        self,
        scenario_id: Optional[str] = None,
        seed: Optional[int] = None,
    ) -> Observation:
        """Reset environment to the beginning of a designated or random scenario."""
        if seed is not None:
            self.seed(seed)

        if scenario_id:
            if scenario_id not in self.scenarios_map:
                raise ValueError(
                    f"Unknown scenario_id '{scenario_id}'. Available: {list(self.scenarios_map.keys())}"
                )
            self.current_scenario = self.scenarios_map[scenario_id]
        else:
            # Pick a scenario deterministically via RNG
            chosen_idx = self.rng.randint(0, len(self.scenarios))
            self.current_scenario = self.scenarios[chosen_idx]

        self.current_step_idx = 0
        self.current_threat_level = self.current_scenario.initial_threat_level
        self.current_service_health = self.current_scenario.initial_service_health
        self.is_contained = False
        self.is_approval_pending = False
        self.is_blocked = False
        self.previous_action = None

        self.history = []
        self.transitions = []

        return self._get_observation()

    def step(
        self,
        action: Union[ActionType, str, int],
    ) -> Tuple[Observation, float, bool, Dict[str, Any]]:
        """Apply defensive action, advance simulator state, and return (obs, reward, done, info)."""
        if self.current_scenario is None:
            raise RuntimeError("Environment must be reset() before calling step().")

        # Map integer action index (0..3) to ActionType enum if passed as int
        if isinstance(action, int):
            action_list = [
                ActionType.RAISE_ALERT,
                ActionType.INCREASE_MONITORING,
                ActionType.ESCALATE_FOR_APPROVAL,
                ActionType.SIMULATE_BLOCK,
            ]
            if 0 <= action < len(action_list):
                action = action_list[action]
            else:
                raise ValueError(f"Action integer {action} out of bounds (must be 0..3).")

        current_obs = self._get_observation()

        # 1. Execute state transition through transition model
        transition = self.transition_model.step(
            action=action,
            current_threat_level=self.current_threat_level,
            current_service_health=self.current_service_health,
            is_already_contained=self.is_contained,
            scenario=self.current_scenario,
        )

        # 2. Update environment state variables
        self.current_threat_level = transition.threat_level
        self.current_service_health = transition.service_health
        self.is_contained = transition.is_contained
        self.previous_action = transition.action.value

        if transition.action == ActionType.SIMULATE_BLOCK:
            self.is_blocked = True
        elif transition.action == ActionType.ESCALATE_FOR_APPROVAL:
            self.is_approval_pending = True

        self.transitions.append(transition)
        self.current_step_idx += 1

        # 3. Calculate Step Reward
        # Step reward penalizes disruption and damage
        step_reward = round(
            -(transition.operational_disruption) - (transition.damage_incurred * 1.5),
            2,
        )

        # 4. Check Termination Condition
        # Episode ends if:
        # a) Threat is successfully contained
        # b) Scenario steps are exhausted
        # c) Service health drops to 0 (system outage)
        # d) A benign scenario was blocked (episode halts on false action)
        is_done = False
        if transition.containment_success:
            is_done = True
            step_reward += 80.0  # Terminal containment bonus
        elif transition.false_action:
            is_done = True
            step_reward -= 50.0  # Terminal false block penalty
        elif self.current_service_health <= 0.0:
            is_done = True
            step_reward -= 40.0  # Outage penalty
        elif self.current_step_idx >= self.current_scenario.total_steps:
            is_done = True
            if self.current_scenario.ground_truth_label == "BENIGN":
                step_reward += 30.0  # Successfully completed benign scenario without false block
            else:
                step_reward -= 30.0  # Threat ran its course uncontained

        # Record step in episode history
        record = EpisodeStepRecord(
            step=self.current_step_idx,
            observation=current_obs,
            action=transition.action.value,
            transition=transition,
            step_reward=step_reward,
        )
        self.history.append(record)

        next_obs = self._get_observation()
        info = {
            "scenario_id": self.current_scenario.scenario_id,
            "ground_truth_label": self.current_scenario.ground_truth_label,
            "containment_success": transition.containment_success,
            "false_action": transition.false_action,
            "disruption_cost": transition.operational_disruption,
            "transition_reason": transition.reason,
        }

        return next_obs, step_reward, is_done, info

    def get_episode_outcome(self) -> EpisodeOutcome:
        """Compute structured outcome summary for the completed episode."""
        if not self.current_scenario:
            raise RuntimeError("No episode has been run yet.")
        return OutcomeEvaluator.evaluate(self.current_scenario, self.transitions)

    def _get_observation(self) -> Observation:
        """Construct observable state dictionary excluding ground truth."""
        scenario = self.current_scenario
        step_idx = min(self.current_step_idx, scenario.total_steps - 1)
        step_profile = scenario.steps[step_idx]

        return Observation(
            step=self.current_step_idx + 1,
            observable_risk=step_profile.observable_risk,
            observable_confidence=step_profile.observable_confidence,
            asset_criticality=scenario.asset_criticality,
            recurrence_count=step_profile.recurrence_count,
            service_health=self.current_service_health,
            is_approval_pending=self.is_approval_pending,
            is_blocked=self.is_blocked,
            previous_action=self.previous_action,
        )
