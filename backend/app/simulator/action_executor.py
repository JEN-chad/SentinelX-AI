"""SentinelX AI - Simulated Action Executor

Executes permitted actions strictly against simulated sandbox state.
CRITICAL SAFETY RULE: Under no circumstances does this module connect to, modify,
or execute commands against real endpoints, switches, or firewalls.
"""

from datetime import datetime, timezone
import random
import time
from typing import Dict, Optional, Set
from pydantic import BaseModel, Field

from app.safety.action_catalogue import ACTION_CATALOGUE, get_action_spec
from app.schemas.common import ActionType


class SimulationOutcome(BaseModel):
    """Structured result of executing a response action in the simulator."""
    outcome_id: str
    incident_id: str
    action: ActionType
    target_asset: str
    containment_success: bool
    operational_disruption_cost: float
    response_delay_ms: float
    reward: float
    simulated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class SimulatedActionExecutor:
    """Manages virtual simulated containment states and outcome evaluation."""

    def __init__(self, random_seed: Optional[int] = 42):
        if random_seed is not None:
            random.seed(random_seed)
        # Sandbox state
        self.simulated_blocked_hosts: Set[str] = set()
        self.simulated_monitored_hosts: Set[str] = set()
        self.history: Dict[str, SimulationOutcome] = {}

    def execute(
        self,
        incident_id: str,
        action: ActionType,
        target_asset: str,
        is_attack: bool = True,
    ) -> SimulationOutcome:
        """Apply permitted response strictly within simulated asset boundary."""
        start_time = time.perf_counter()
        spec = get_action_spec(action)
        if not spec:
            raise ValueError(f"Unknown action '{action}' cannot be simulated.")

        now = datetime.now(timezone.utc)
        outcome_id = f"out-{now.strftime('%Y%m%d%H%M%S%f')[-8:]}"

        # Update virtual simulation sandbox
        if action == ActionType.SIMULATE_BLOCK:
            self.simulated_blocked_hosts.add(target_asset)
            # High probability of successful simulated containment
            containment_success = True
            disruption = spec.operational_disruption_cost  # e.g., 12.0
        elif action == ActionType.INCREASE_MONITORING:
            self.simulated_monitored_hosts.add(target_asset)
            containment_success = not is_attack  # monitoring alone doesn't contain active flood
            disruption = spec.operational_disruption_cost  # e.g., 1.5
        elif action == ActionType.RAISE_ALERT or action == ActionType.ESCALATE_FOR_APPROVAL:
            containment_success = not is_attack
            disruption = 0.0
        else:
            containment_success = False
            disruption = 0.0

        # Response latency in simulation (ms)
        elapsed_ms = (time.perf_counter() - start_time) * 1000.0
        simulated_delay_ms = round(15.0 + random.uniform(5.0, 25.0) + elapsed_ms, 2)

        # Reward model: benefit - disruption - false_action
        if is_attack and containment_success:
            reward = round(100.0 - disruption - (simulated_delay_ms * 0.05), 2)
        elif not is_attack and action == ActionType.SIMULATE_BLOCK:
            # Unnecessary disruption penalty on benign flow
            reward = round(-50.0 - disruption, 2)
        else:
            reward = round(10.0 - disruption, 2)

        outcome = SimulationOutcome(
            outcome_id=outcome_id,
            incident_id=incident_id,
            action=action,
            target_asset=target_asset,
            containment_success=containment_success,
            operational_disruption_cost=disruption,
            response_delay_ms=simulated_delay_ms,
            reward=reward,
            simulated_at=now,
        )

        self.history[incident_id] = outcome
        return outcome

    def rollback(self, incident_id: str, target_asset: str) -> bool:
        """Revert virtual containment action on simulated target asset."""
        if target_asset in self.simulated_blocked_hosts:
            self.simulated_blocked_hosts.remove(target_asset)
            return True
        if target_asset in self.simulated_monitored_hosts:
            self.simulated_monitored_hosts.remove(target_asset)
            return True
        return False
