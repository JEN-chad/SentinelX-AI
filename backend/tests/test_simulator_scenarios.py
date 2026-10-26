"""SentinelX AI - Phase 9 Tests: Incident Simulator & Outcome Evaluator

Tests scenario definition reproducibility, transition dynamics, ground-truth segregation,
false action penalties on benign scenarios, and invalid action rejection.
"""

import pytest

from app.schemas.common import ActionType
from app.simulator.environment import IncidentSimulatorEnv, Observation
from app.simulator.outcome_evaluator import OutcomeEvaluator
from app.simulator.scenarios import (
    SCENARIO_BENIGN_BURST,
    SCENARIO_BRUTE_FORCE,
    SCENARIO_DATA_EXFILTRATION,
    SCENARIO_HIGH_DDOS,
    SCENARIO_PORT_SWEEP,
    get_scenario,
    list_scenarios,
)
from app.simulator.transition_model import TransitionModel


def test_scenario_catalogue_completeness():
    """Verify all 5 canonical scenarios exist with valid parameters and steps."""
    scenarios = list_scenarios()
    assert len(scenarios) >= 5

    scenario_ids = [s.scenario_id for s in scenarios]
    assert "scen-benign-burst" in scenario_ids
    assert "scen-brute-force" in scenario_ids
    assert "scen-port-sweep" in scenario_ids
    assert "scen-high-ddos" in scenario_ids
    assert "scen-data-exfiltration" in scenario_ids

    for s in scenarios:
        assert s.total_steps >= 4
        assert 1 <= s.asset_criticality <= 5
        assert 0.0 <= s.initial_threat_level <= 1.0
        assert s.initial_service_health == 100.0


def test_ground_truth_label_segregated_from_observation():
    """SAFETY INVARIANT: Policy observation dictionary MUST NEVER contain ground truth label."""
    env = IncidentSimulatorEnv(seed=42)
    obs = env.reset(scenario_id="scen-high-ddos")

    assert isinstance(obs, Observation)
    obs_dict = obs.model_dump()
    assert "ground_truth_label" not in obs_dict
    assert "threat_type" not in obs_dict
    assert "ground_truth" not in obs_dict

    # Check observable features exist
    assert hasattr(obs, "observable_risk")
    assert hasattr(obs, "observable_confidence")
    assert hasattr(obs, "asset_criticality")
    assert hasattr(obs, "recurrence_count")
    assert hasattr(obs, "service_health")


def test_seed_reproducibility():
    """CRITICAL: Same seed and scenario MUST produce exact identical episode trajectories."""
    env1 = IncidentSimulatorEnv(seed=12345)
    env2 = IncidentSimulatorEnv(seed=12345)

    obs1 = env1.reset(scenario_id="scen-high-ddos", seed=12345)
    obs2 = env2.reset(scenario_id="scen-high-ddos", seed=12345)
    assert obs1.model_dump() == obs2.model_dump()

    # Step both environments with identical action sequence
    actions = [ActionType.INCREASE_MONITORING, ActionType.ESCALATE_FOR_APPROVAL, ActionType.SIMULATE_BLOCK]
    for act in actions:
        next_obs1, r1, d1, info1 = env1.step(act)
        next_obs2, r2, d2, info2 = env2.step(act)

        assert next_obs1.model_dump() == next_obs2.model_dump()
        assert r1 == r2
        assert d1 == d2
        assert info1 == info2

    outcome1 = env1.get_episode_outcome()
    outcome2 = env2.get_episode_outcome()
    assert outcome1.model_dump() == outcome2.model_dump()


def test_transition_model_rejects_unknown_action():
    """SAFETY GATE: Simulator must reject actions not in allowlisted ActionType catalogue."""
    tm = TransitionModel()
    scenario = get_scenario("scen-high-ddos")

    with pytest.raises(ValueError, match="rejected invalid or unknown action"):
        tm.step(
            action="format_hard_drive",
            current_threat_level=0.5,
            current_service_health=100.0,
            is_already_contained=False,
            scenario=scenario,
        )

    with pytest.raises(ValueError, match="rejected invalid or unknown action"):
        tm.step(
            action="execute_external_script",
            current_threat_level=0.5,
            current_service_health=100.0,
            is_already_contained=False,
            scenario=scenario,
        )


def test_benign_scenario_incurs_cost_for_unnecessary_blocking():
    """False positive block on benign scenario MUST incur high operational disruption penalty."""
    env = IncidentSimulatorEnv(seed=42)
    env.reset(scenario_id="scen-benign-burst")

    # Applying simulate_block to legitimate backup sync
    next_obs, step_reward, is_done, info = env.step(ActionType.SIMULATE_BLOCK)

    assert info["false_action"] is True
    assert info["containment_success"] is False
    assert info["disruption_cost"] > 20.0  # High disruption
    assert step_reward < -30.0            # Penalty reflected in reward

    outcome = env.get_episode_outcome()
    assert outcome.false_action is True
    assert outcome.net_reward < 0.0
    assert "FAILED: Benign activity" in outcome.summary


def test_attack_scenario_successful_containment():
    """Simulated block on real DoS attack must successfully contain threat with positive reward."""
    env = IncidentSimulatorEnv(seed=42)
    env.reset(scenario_id="scen-high-ddos")

    # Step 1: elevate monitoring
    env.step(ActionType.INCREASE_MONITORING)
    # Step 2: simulate block
    next_obs, step_reward, is_done, info = env.step(ActionType.SIMULATE_BLOCK)

    assert info["containment_success"] is True
    assert info["false_action"] is False
    assert is_done is True  # Attack successfully terminated

    outcome = env.get_episode_outcome()
    assert outcome.containment_success is True
    assert outcome.net_reward > 0.0
    assert "SUCCESS: Threat 'DOS' successfully contained" in outcome.summary


def test_unmitigated_attack_service_health_degradation():
    """If defensive actions only raise passive alerts, attack progresses and damages service health."""
    env = IncidentSimulatorEnv(seed=42)
    env.reset(scenario_id="scen-high-ddos")

    initial_health = env.current_service_health
    for _ in range(3):
        next_obs, step_reward, is_done, _ = env.step(ActionType.RAISE_ALERT)

    # Health must have degraded due to passive alerting
    assert env.current_service_health < initial_health
    assert env.current_threat_level > 0.7
