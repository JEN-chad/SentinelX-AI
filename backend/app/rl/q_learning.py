"""SentinelX AI - Tabular Q-Learning Algorithm (Phase 10)

NumPy-based tabular Q-learning implementation with epsilon-greedy exploration,
configurable learning rate, discount factor, and reproducible seeds.
"""

from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np
from pydantic import BaseModel, Field

from app.schemas.common import ActionType
from app.simulator.environment import IncidentSimulatorEnv
from .reward import RewardCalculator
from .state_encoder import ObservationEncoder, TOTAL_DISCRETE_STATES

NUM_ACTIONS = 4

ACTION_INDEX_TO_TYPE: Dict[int, ActionType] = {
    0: ActionType.RAISE_ALERT,
    1: ActionType.INCREASE_MONITORING,
    2: ActionType.ESCALATE_FOR_APPROVAL,
    3: ActionType.SIMULATE_BLOCK,
}

ACTION_TYPE_TO_INDEX: Dict[ActionType, int] = {
    ActionType.RAISE_ALERT: 0,
    ActionType.INCREASE_MONITORING: 1,
    ActionType.ESCALATE_FOR_APPROVAL: 2,
    ActionType.SIMULATE_BLOCK: 3,
}


class QLearningHyperparameters(BaseModel):
    """Hyperparameters for Tabular Q-Learning."""
    learning_rate: float = Field(default=0.1, ge=0.001, le=1.0)
    discount_factor: float = Field(default=0.95, ge=0.0, le=1.0)
    epsilon_start: float = Field(default=1.0, ge=0.0, le=1.0)
    epsilon_min: float = Field(default=0.05, ge=0.0, le=1.0)
    epsilon_decay: float = Field(default=0.99, ge=0.8, le=1.0)
    episodes: int = Field(default=300, ge=10, le=10000)
    random_seed: int = Field(default=42)


class TrainingReport(BaseModel):
    """Structured report returned upon Q-learning training completion."""
    policy_version: str
    episodes_trained: int
    final_epsilon: float
    mean_reward_first_50: float
    mean_reward_last_50: float
    total_steps: int
    training_duration_ms: float
    created_at: str


class QLearningTrainer:
    """Manages Q-table storage, Bellman TD updates, epsilon-greedy exploration, and training loops."""

    def __init__(
        self,
        hyperparameters: Optional[QLearningHyperparameters] = None,
        q_table: Optional[np.ndarray] = None,
    ):
        self.params = hyperparameters or QLearningHyperparameters()
        self.rng = np.random.RandomState(self.params.random_seed)
        if q_table is not None:
            if q_table.shape != (TOTAL_DISCRETE_STATES, NUM_ACTIONS):
                raise ValueError(
                    f"Q-table shape {q_table.shape} does not match expected ({TOTAL_DISCRETE_STATES}, {NUM_ACTIONS})."
                )
            self.q_table = q_table.astype(np.float64)
        else:
            self.q_table = np.zeros((TOTAL_DISCRETE_STATES, NUM_ACTIONS), dtype=np.float64)

        self.epsilon = self.params.epsilon_start
        self.encoder = ObservationEncoder()
        self.reward_calculator = RewardCalculator()

    def update_q_value(
        self,
        state_idx: int,
        action_idx: int,
        reward: float,
        next_state_idx: int,
        is_done: bool,
    ) -> float:
        """Apply Bellman equation Q-value update. Returns the absolute TD error.
        Q(s, a) <- Q(s, a) + alpha * [r + gamma * max_a' Q(s', a') - Q(s, a)]
        """
        current_q = self.q_table[state_idx, action_idx]
        if is_done:
            td_target = reward
        else:
            best_next_q = np.max(self.q_table[next_state_idx])
            td_target = reward + self.params.discount_factor * best_next_q

        td_error = td_target - current_q
        self.q_table[state_idx, action_idx] = current_q + self.params.learning_rate * td_error
        return float(abs(td_error))

    def select_action(self, state_idx: int, explore: bool = True) -> int:
        """Select action index 0..3 using epsilon-greedy (explore=True) or greedy (explore=False)."""
        if explore and (self.rng.uniform(0.0, 1.0) < self.epsilon):
            return int(self.rng.randint(0, NUM_ACTIONS))

        # Greedy choice: pick action maximizing Q(s, a); break ties deterministically
        q_values = self.q_table[state_idx]
        max_val = np.max(q_values)
        candidates = np.where(q_values == max_val)[0]
        return int(candidates[0])

    def train(
        self,
        env: IncidentSimulatorEnv,
        num_episodes: Optional[int] = None,
    ) -> Tuple[np.ndarray, TrainingReport]:
        """Execute Q-learning training loop over the environment."""
        import time
        start_time = time.perf_counter()
        episodes = num_episodes or self.params.episodes
        episode_rewards: List[float] = []
        total_steps = 0

        for ep in range(episodes):
            obs = env.reset(seed=self.params.random_seed + ep)
            state_idx = self.encoder.encode(obs)
            done = False
            ep_reward = 0.0

            while not done:
                action_idx = self.select_action(state_idx, explore=True)
                next_obs, step_reward, done, _ = env.step(action_idx)
                next_state_idx = self.encoder.encode(next_obs)

                self.update_q_value(state_idx, action_idx, step_reward, next_state_idx, done)

                state_idx = next_state_idx
                ep_reward += step_reward
                total_steps += 1

            episode_rewards.append(ep_reward)

            # Decay epsilon
            self.epsilon = max(self.params.epsilon_min, self.epsilon * self.params.epsilon_decay)

        duration_ms = (time.perf_counter() - start_time) * 1000.0
        n_slice = min(50, len(episode_rewards))
        report = TrainingReport(
            policy_version=f"qtable-v1.0-ep{episodes}",
            episodes_trained=episodes,
            final_epsilon=round(self.epsilon, 4),
            mean_reward_first_50=round(float(np.mean(episode_rewards[:n_slice])), 2),
            mean_reward_last_50=round(float(np.mean(episode_rewards[-n_slice:])), 2),
            total_steps=total_steps,
            training_duration_ms=round(duration_ms, 2),
            created_at=datetime.now(timezone.utc).isoformat(),
        )

        return self.q_table, report

    def to_dict(self) -> Dict[str, Any]:
        """Serialize Q-table and metadata to dictionary."""
        return {
            "policy_version": f"qtable-v1.0-seed{self.params.random_seed}",
            "hyperparameters": self.params.model_dump(),
            "q_table": self.q_table.tolist(),
            "n_states": TOTAL_DISCRETE_STATES,
            "n_actions": NUM_ACTIONS,
            "action_mapping": {str(k): v.value for k, v in ACTION_INDEX_TO_TYPE.items()},
            "exported_at": datetime.now(timezone.utc).isoformat(),
        }

    def save(self, filepath: Union[str, Path]) -> None:
        """Save Q-table artifact to JSON file."""
        path = Path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load(cls, filepath: Union[str, Path]) -> "QLearningTrainer":
        """Load Q-table artifact from JSON file."""
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        params = QLearningHyperparameters(**data.get("hyperparameters", {}))
        q_table = np.array(data["q_table"], dtype=np.float64)
        return cls(hyperparameters=params, q_table=q_table)
