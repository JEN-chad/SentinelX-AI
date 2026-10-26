"""SentinelX AI - Defensive Response Policies (Phase 10)

Defines the trained Q-learning policy and deterministic baseline policies (Rule-based, Threshold, Random)
for benchmarking adaptive incident response.
CRITICAL SAFETY INVARIANT: Every policy strictly returns actions from the allowlisted catalogue.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, Optional, Union
import numpy as np

from app.schemas.common import ActionType
from app.simulator.environment import Observation
from .q_learning import (
    ACTION_INDEX_TO_TYPE,
    QLearningTrainer,
)
from .state_encoder import ObservationEncoder


class BasePolicy(ABC):
    """Abstract interface for defensive response policies."""

    @property
    @abstractmethod
    def policy_name(self) -> str:
        """Name of the policy algorithm."""
        pass

    @property
    @abstractmethod
    def policy_version(self) -> str:
        """Version tag for reproducibility tracking."""
        pass

    @abstractmethod
    def select_action(self, obs: Observation) -> ActionType:
        """Choose defensive action given an incident observation."""
        pass


class QLearningPolicy(BasePolicy):
    """Trained Tabular Q-Learning defensive response policy in frozen evaluation mode."""

    def __init__(
        self,
        trainer: Optional[QLearningTrainer] = None,
        artifact_path: Optional[Union[str, Path]] = None,
        version: str = "q-learning-v1.0",
    ):
        if trainer is not None:
            self.trainer = trainer
        elif artifact_path is not None and Path(artifact_path).exists():
            self.trainer = QLearningTrainer.load(artifact_path)
        else:
            self.trainer = QLearningTrainer()

        self._version = version
        self.encoder = ObservationEncoder()

    @property
    def policy_name(self) -> str:
        return "QLearningPolicy"

    @property
    def policy_version(self) -> str:
        return self._version

    def select_action(self, obs: Observation) -> ActionType:
        """Evaluate observation greedily with NO exploration (epsilon=0) and NO table updates."""
        state_idx = self.encoder.encode(obs)
        action_idx = self.trainer.select_action(state_idx, explore=False)
        return ACTION_INDEX_TO_TYPE[action_idx]


class RuleBasedPolicy(BasePolicy):
    """Expert rule heuristic baseline balancing asset sensitivity against threat severity."""

    def __init__(self, version: str = "rule-baseline-v1.0"):
        self._version = version

    @property
    def policy_name(self) -> str:
        return "RuleBasedPolicy"

    @property
    def policy_version(self) -> str:
        return self._version

    def select_action(self, obs: Observation) -> ActionType:
        """Heuristic rule:
        - If risk >= 0.70 and asset criticality <= 3: immediate simulate_block
        - If risk >= 0.70 and asset criticality > 3: escalate_for_approval (sensitive crown-jewel)
        - If risk >= 0.40: increase_monitoring
        - Else: raise_alert
        """
        if obs.observable_risk >= 0.70:
            if obs.asset_criticality <= 3:
                return ActionType.SIMULATE_BLOCK
            else:
                return ActionType.ESCALATE_FOR_APPROVAL
        elif obs.observable_risk >= 0.40:
            return ActionType.INCREASE_MONITORING
        else:
            return ActionType.RAISE_ALERT


class ThresholdPolicy(BasePolicy):
    """Static risk threshold baseline: blocks anything above threshold, alerts below."""

    def __init__(self, threshold: float = 0.60, version: str = "threshold-baseline-v1.0"):
        self.threshold = threshold
        self._version = version

    @property
    def policy_name(self) -> str:
        return "ThresholdPolicy"

    @property
    def policy_version(self) -> str:
        return self._version

    def select_action(self, obs: Observation) -> ActionType:
        if obs.observable_risk >= self.threshold:
            return ActionType.SIMULATE_BLOCK
        return ActionType.RAISE_ALERT


class RandomPermittedPolicy(BasePolicy):
    """Stochastic baseline randomly choosing among allowlisted actions for empirical control."""

    def __init__(self, seed: int = 42, version: str = "random-baseline-v1.0"):
        self.rng = np.random.RandomState(seed)
        self._version = version
        self.actions = [
            ActionType.RAISE_ALERT,
            ActionType.INCREASE_MONITORING,
            ActionType.ESCALATE_FOR_APPROVAL,
            ActionType.SIMULATE_BLOCK,
        ]

    @property
    def policy_name(self) -> str:
        return "RandomPermittedPolicy"

    @property
    def policy_version(self) -> str:
        return self._version

    def select_action(self, obs: Observation) -> ActionType:
        idx = int(self.rng.randint(0, len(self.actions)))
        return self.actions[idx]
