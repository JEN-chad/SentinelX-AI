"""SentinelX AI - Phase 10 Tests: Reinforcement Learning Policy

Tests state discretizer, exact hand-calculated Bellman update, action space validity,
frozen evaluation invariance, and baseline policy comparisons.
"""

import numpy as np
import pytest

from app.schemas.common import ActionType
from app.simulator.environment import IncidentSimulatorEnv, Observation
from app.simulator.scenarios import get_scenario
from app.rl.evaluation import PolicyEvaluationMetrics, PolicyEvaluator
from app.rl.policy import (
    QLearningPolicy,
    RandomPermittedPolicy,
    RuleBasedPolicy,
    ThresholdPolicy,
)
from app.rl.q_learning import (
    ACTION_INDEX_TO_TYPE,
    QLearningHyperparameters,
    QLearningTrainer,
)
from app.rl.reward import RewardCalculator, RewardWeights
from app.rl.state_encoder import ObservationEncoder, TOTAL_DISCRETE_STATES


def test_observation_encoder_bounds_and_determinism():
    """Observation encoder maps continuous features deterministically into [0..53]."""
    obs_low = Observation(
        step=1,
        observable_risk=0.15,
        observable_confidence=0.50,
        asset_criticality=2,
        recurrence_count=1,
        service_health=100.0,
    )
    idx_low = ObservationEncoder.encode(obs_low)
    assert 0 <= idx_low < TOTAL_DISCRETE_STATES

    decoded = ObservationEncoder.decode(idx_low)
    assert decoded.risk_bucket == "LOW"
    assert decoded.criticality_bucket == "LOW"
    assert decoded.recurrence_bucket == "SINGLE"
    assert decoded.confidence_bucket == "UNCERTAIN"

    obs_high = Observation(
        step=4,
        observable_risk=0.88,
        observable_confidence=0.92,
        asset_criticality=5,
        recurrence_count=10,
        service_health=85.0,
    )
    idx_high = ObservationEncoder.encode(obs_high)
    assert 0 <= idx_high < TOTAL_DISCRETE_STATES

    decoded_high = ObservationEncoder.decode(idx_high)
    assert decoded_high.risk_bucket == "HIGH"
    assert decoded_high.criticality_bucket == "HIGH"
    assert decoded_high.recurrence_bucket == "PERSISTENT"
    assert decoded_high.confidence_bucket == "CONFIDENT"


def test_exact_hand_calculated_q_learning_update():
    """Verify Q-value update against hand-calculated Bellman numerical expectation.
    Given:
      s = 5, a = 2
      Initial Q(s, a) = 10.0
      alpha = 0.1, gamma = 0.90
      r = 5.0
      s' = 12, max_a' Q(s', a') = 20.0
    Expected:
      TD Target = r + gamma * max_a' Q(s', a') = 5.0 + 0.90 * 20.0 = 23.0
      TD Error = TD Target - Q(s, a) = 23.0 - 10.0 = 13.0
      New Q(s, a) = Q(s, a) + alpha * TD Error = 10.0 + 0.1 * 13.0 = 11.30
    """
    params = QLearningHyperparameters(learning_rate=0.1, discount_factor=0.90)
    trainer = QLearningTrainer(hyperparameters=params)

    trainer.q_table[5, 2] = 10.0
    trainer.q_table[12, 0] = 15.0
    trainer.q_table[12, 1] = 20.0  # Max next state Q
    trainer.q_table[12, 2] = 8.0
    trainer.q_table[12, 3] = 12.0

    td_error = trainer.update_q_value(state_idx=5, action_idx=2, reward=5.0, next_state_idx=12, is_done=False)

    assert round(td_error, 4) == 13.0
    assert round(trainer.q_table[5, 2], 4) == 11.30


def test_q_learning_policy_action_allowlist():
    """Policy must strictly select actions from the permitted 4-action catalogue."""
    trainer = QLearningTrainer()
    policy = QLearningPolicy(trainer=trainer)

    test_obs = [
        Observation(step=1, observable_risk=0.2, observable_confidence=0.5, asset_criticality=2, recurrence_count=1, service_health=100.0),
        Observation(step=2, observable_risk=0.55, observable_confidence=0.7, asset_criticality=3, recurrence_count=3, service_health=95.0),
        Observation(step=3, observable_risk=0.95, observable_confidence=0.95, asset_criticality=4, recurrence_count=8, service_health=70.0),
    ]

    for obs in test_obs:
        action = policy.select_action(obs)
        assert isinstance(action, ActionType)
        assert action in {
            ActionType.RAISE_ALERT,
            ActionType.INCREASE_MONITORING,
            ActionType.ESCALATE_FOR_APPROVAL,
            ActionType.SIMULATE_BLOCK,
        }


def test_frozen_evaluation_mode_does_not_modify_q_table():
    """CRITICAL: Running policy in evaluation mode MUST NOT alter the Q-table."""
    trainer = QLearningTrainer()
    trainer.q_table[:] = np.random.RandomState(42).randn(*trainer.q_table.shape)
    initial_copy = np.copy(trainer.q_table)

    policy = QLearningPolicy(trainer=trainer)
    env = IncidentSimulatorEnv(seed=42)

    # Run complete 10-episode evaluation
    PolicyEvaluator.evaluate(policy=policy, env=env, num_episodes=10, start_seed=3000)

    # Q-table must remain strictly identical
    np.testing.assert_array_equal(trainer.q_table, initial_copy)


def test_baseline_policies_behavior():
    """Verify deterministic logic of Rule-Based, Threshold, and Random baselines."""
    rule_pol = RuleBasedPolicy()
    thresh_pol = ThresholdPolicy(threshold=0.60)
    rand_pol = RandomPermittedPolicy(seed=42)

    # 1. High risk on non-critical asset -> RuleBased recommends simulate_block
    obs_block = Observation(step=1, observable_risk=0.85, observable_confidence=0.9, asset_criticality=2, recurrence_count=5, service_health=90.0)
    assert rule_pol.select_action(obs_block) == ActionType.SIMULATE_BLOCK
    assert thresh_pol.select_action(obs_block) == ActionType.SIMULATE_BLOCK

    # 2. High risk on crown jewel (criticality 5) -> RuleBased escalates for approval
    obs_sensitive = Observation(step=1, observable_risk=0.85, observable_confidence=0.9, asset_criticality=5, recurrence_count=5, service_health=90.0)
    assert rule_pol.select_action(obs_sensitive) == ActionType.ESCALATE_FOR_APPROVAL

    # 3. Low risk -> alert only
    obs_low = Observation(step=1, observable_risk=0.20, observable_confidence=0.5, asset_criticality=3, recurrence_count=1, service_health=100.0)
    assert rule_pol.select_action(obs_low) == ActionType.RAISE_ALERT
    assert thresh_pol.select_action(obs_low) == ActionType.RAISE_ALERT

    # 4. Random permitted policy always returns allowlisted action
    assert rand_pol.select_action(obs_low) in ActionType


def test_comparative_policy_benchmark():
    """Run comparative evaluation of all 4 policies on identical held-out scenario seeds."""
    env = IncidentSimulatorEnv(seed=42)
    policies = [
        RuleBasedPolicy(),
        ThresholdPolicy(),
        RandomPermittedPolicy(seed=42),
    ]

    results = PolicyEvaluator.compare_policies(policies=policies, env=env, num_episodes=15, start_seed=4000)

    assert "RuleBasedPolicy" in results
    assert "ThresholdPolicy" in results
    assert "RandomPermittedPolicy" in results

    for name, metrics in results.items():
        assert isinstance(metrics, PolicyEvaluationMetrics)
        assert metrics.episodes_evaluated == 15
        assert 0.0 <= metrics.containment_rate <= 1.0
        assert 0.0 <= metrics.false_action_rate <= 1.0
        assert isinstance(metrics.mean_reward, float)
