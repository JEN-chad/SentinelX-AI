"""SentinelX AI - Controlled Incident Simulator Module (Phase 8 & 9)"""

from .action_executor import SimulatedActionExecutor, SimulationOutcome
from .environment import EpisodeStepRecord, IncidentSimulatorEnv, Observation
from .outcome_evaluator import EpisodeOutcome, OutcomeEvaluator
from .scenarios import (
    Scenario,
    ScenarioStep,
    get_scenario,
    list_scenarios,
    SCENARIO_BENIGN_BURST,
    SCENARIO_BRUTE_FORCE,
    SCENARIO_PORT_SWEEP,
    SCENARIO_HIGH_DDOS,
    SCENARIO_DATA_EXFILTRATION,
)
from .transition_model import TransitionModel, TransitionOutcome

__all__ = [
    "SimulatedActionExecutor",
    "SimulationOutcome",
    "Scenario",
    "ScenarioStep",
    "get_scenario",
    "list_scenarios",
    "TransitionModel",
    "TransitionOutcome",
    "OutcomeEvaluator",
    "EpisodeOutcome",
    "IncidentSimulatorEnv",
    "Observation",
    "EpisodeStepRecord",
    "SCENARIO_BENIGN_BURST",
    "SCENARIO_BRUTE_FORCE",
    "SCENARIO_PORT_SWEEP",
    "SCENARIO_HIGH_DDOS",
    "SCENARIO_DATA_EXFILTRATION",
]
