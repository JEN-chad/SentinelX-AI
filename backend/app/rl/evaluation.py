"""SentinelX AI - Policy Evaluation Runner and Baseline Comparison (Phase 10)

Executes frozen evaluation of defensive response policies across held-out scenario seeds.
Guarantees fair comparison by evaluating all policies on identical scenario sequences without learning updates.
"""

from typing import Any, Dict, List, Optional
import numpy as np
from pydantic import BaseModel, Field

from app.simulator.environment import IncidentSimulatorEnv
from app.simulator.outcome_evaluator import EpisodeOutcome
from .policy import BasePolicy


class PolicyEvaluationMetrics(BaseModel):
    """Aggregate benchmark metrics for an evaluated defensive policy."""
    policy_name: str
    policy_version: str
    episodes_evaluated: int
    mean_reward: float
    std_reward: float
    containment_rate: float = Field(..., ge=0.0, le=1.0, description="Proportion of attacks successfully contained")
    false_action_rate: float = Field(..., ge=0.0, le=1.0, description="Proportion of benign scenarios disrupted")
    mean_disruption_cost: float = Field(..., ge=0.0)
    mean_damage_cost: float = Field(..., ge=0.0)
    mean_steps: float = Field(..., ge=0.0)
    scenario_breakdown: Dict[str, Dict[str, Any]] = Field(default_factory=dict)


class PolicyEvaluator:
    """Runs frozen evaluation loops without parameter or Q-table updates."""

    @staticmethod
    def evaluate(
        policy: BasePolicy,
        env: IncidentSimulatorEnv,
        num_episodes: int = 50,
        start_seed: int = 2000,
    ) -> PolicyEvaluationMetrics:
        """Run policy on held-out scenario seeds without learning updates."""
        rewards: List[float] = []
        containment_successes: List[bool] = []
        false_actions: List[bool] = []
        disruptions: List[float] = []
        damages: List[float] = []
        steps_list: List[int] = []

        scenario_records: Dict[str, List[EpisodeOutcome]] = {}

        for i in range(num_episodes):
            seed = start_seed + i
            obs = env.reset(seed=seed)
            scenario_id = env.current_scenario.scenario_id
            if scenario_id not in scenario_records:
                scenario_records[scenario_id] = []

            done = False
            ep_reward = 0.0

            while not done:
                action = policy.select_action(obs)
                next_obs, step_reward, done, _ = env.step(action)
                ep_reward += step_reward
                obs = next_obs

            outcome = env.get_episode_outcome()
            rewards.append(ep_reward)
            containment_successes.append(outcome.containment_success)
            false_actions.append(outcome.false_action)
            disruptions.append(outcome.total_disruption_cost)
            damages.append(outcome.total_damage_cost)
            steps_list.append(outcome.total_steps)
            scenario_records[scenario_id].append(outcome)

        # Attack scenario containment rate
        attack_outcomes = [
            out for sublist in scenario_records.values() for out in sublist if out.ground_truth_label != "BENIGN"
        ]
        containment_rate = (
            sum(1 for o in attack_outcomes if o.containment_success) / len(attack_outcomes)
            if attack_outcomes
            else 0.0
        )

        # Benign scenario false action rate
        benign_outcomes = [
            out for sublist in scenario_records.values() for out in sublist if out.ground_truth_label == "BENIGN"
        ]
        false_action_rate = (
            sum(1 for o in benign_outcomes if o.false_action) / len(benign_outcomes)
            if benign_outcomes
            else 0.0
        )

        # Per-scenario breakdown
        breakdown: Dict[str, Dict[str, Any]] = {}
        for scen_id, outcomes in scenario_records.items():
            scen_rewards = [o.net_reward for o in outcomes]
            scen_disruptions = [o.total_disruption_cost for o in outcomes]
            breakdown[scen_id] = {
                "count": len(outcomes),
                "mean_reward": round(float(np.mean(scen_rewards)), 2),
                "mean_disruption": round(float(np.mean(scen_disruptions)), 2),
                "contained_count": sum(1 for o in outcomes if o.containment_success),
                "false_action_count": sum(1 for o in outcomes if o.false_action),
            }

        return PolicyEvaluationMetrics(
            policy_name=policy.policy_name,
            policy_version=policy.policy_version,
            episodes_evaluated=num_episodes,
            mean_reward=round(float(np.mean(rewards)), 2),
            std_reward=round(float(np.std(rewards)), 2),
            containment_rate=round(containment_rate, 4),
            false_action_rate=round(false_action_rate, 4),
            mean_disruption_cost=round(float(np.mean(disruptions)), 2),
            mean_damage_cost=round(float(np.mean(damages)), 2),
            mean_steps=round(float(np.mean(steps_list)), 2),
            scenario_breakdown=breakdown,
        )

    @classmethod
    def compare_policies(
        cls,
        policies: List[BasePolicy],
        env: IncidentSimulatorEnv,
        num_episodes: int = 50,
        start_seed: int = 2000,
    ) -> Dict[str, PolicyEvaluationMetrics]:
        """Compare multiple policies on identical held-out episode seeds."""
        results: Dict[str, PolicyEvaluationMetrics] = {}
        for p in policies:
            results[p.policy_name] = cls.evaluate(
                policy=p,
                env=env,
                num_episodes=num_episodes,
                start_seed=start_seed,
            )
        return results
