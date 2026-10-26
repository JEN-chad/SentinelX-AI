"""SentinelX AI - Incident Simulator Scenarios (Phase 9)

Defines reproducible cyber threat and benign scenarios modeling operational consequences,
threat behavior, and ground truth labels.
CRITICAL SAFETY INVARIANT: Ground truth labels are strictly isolated from agent and policy inputs.
"""

from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class ScenarioStep(BaseModel):
    """Step profile representing observable telemetry at a specific time step."""
    step_number: int
    observable_risk: float = Field(..., ge=0.0, le=1.0)
    observable_confidence: float = Field(..., ge=0.0, le=1.0)
    traffic_volume_mbps: float = Field(..., ge=0.0)
    packet_rate: float = Field(..., ge=0.0)
    recurrence_count: int = Field(default=1, ge=1)
    description: str


class Scenario(BaseModel):
    """Specification of an incident simulation scenario."""
    scenario_id: str
    name: str
    description: str
    ground_truth_label: str  # e.g. "BENIGN", "DOS", "PORT_SCAN", "BRUTE_FORCE", "EXFILTRATION"
    target_asset: str
    source_asset: str
    asset_criticality: int = Field(default=3, ge=1, le=5)
    initial_threat_level: float = Field(default=0.5, ge=0.0, le=1.0)
    initial_service_health: float = Field(default=100.0, ge=0.0, le=100.0)
    steps: List[ScenarioStep]
    disruption_weight: float = Field(default=1.0, ge=0.1)
    threat_growth_rate: float = Field(default=0.1, ge=0.0)

    @property
    def total_steps(self) -> int:
        return len(self.steps)


# ============================================================================
# Canonical Scenario Catalogue
# ============================================================================

SCENARIO_BENIGN_BURST = Scenario(
    scenario_id="scen-benign-burst",
    name="High-Volume Database Backup Sync",
    description=(
        "Legitimate high-throughput data synchronization between internal database and backup cluster. "
        "High volume triggers heuristic false alarms, but ground truth is entirely benign."
    ),
    ground_truth_label="BENIGN",
    target_asset="192.168.10.15",
    source_asset="192.168.10.25",
    asset_criticality=4,
    initial_threat_level=0.05,
    initial_service_health=100.0,
    disruption_weight=2.0,  # High disruption if falsely blocked!
    threat_growth_rate=0.0,
    steps=[
        ScenarioStep(
            step_number=1,
            observable_risk=0.35,
            observable_confidence=0.55,
            traffic_volume_mbps=450.0,
            packet_rate=12000.0,
            recurrence_count=1,
            description="Initial burst of high-throughput TCP flows on port 5432.",
        ),
        ScenarioStep(
            step_number=2,
            observable_risk=0.45,
            observable_confidence=0.60,
            traffic_volume_mbps=780.0,
            packet_rate=19000.0,
            recurrence_count=2,
            description="Sustained backup streaming; heuristic classifier flags volumetric anomaly.",
        ),
        ScenarioStep(
            step_number=3,
            observable_risk=0.48,
            observable_confidence=0.62,
            traffic_volume_mbps=820.0,
            packet_rate=21000.0,
            recurrence_count=3,
            description="Peak data transfer volume; legitimate internal credentials utilized.",
        ),
        ScenarioStep(
            step_number=4,
            observable_risk=0.30,
            observable_confidence=0.50,
            traffic_volume_mbps=320.0,
            packet_rate=8000.0,
            recurrence_count=4,
            description="Backup sync tapering off; connections closing normally.",
        ),
        ScenarioStep(
            step_number=5,
            observable_risk=0.10,
            observable_confidence=0.40,
            traffic_volume_mbps=15.0,
            packet_rate=400.0,
            recurrence_count=4,
            description="Routine maintenance window completed successfully.",
        ),
    ],
)

SCENARIO_BRUTE_FORCE = Scenario(
    scenario_id="scen-brute-force",
    name="SSH / Authentication Credential Stuffing",
    description=(
        "Distributed automated dictionary attack targeting corporate bastion host. "
        "Rapid authentication failures with escalating risk if left unmitigated."
    ),
    ground_truth_label="BRUTE_FORCE",
    target_asset="192.168.10.5",
    source_asset="192.168.10.50",
    asset_criticality=3,
    initial_threat_level=0.40,
    initial_service_health=100.0,
    disruption_weight=1.0,
    threat_growth_rate=0.15,
    steps=[
        ScenarioStep(
            step_number=1,
            observable_risk=0.52,
            observable_confidence=0.70,
            traffic_volume_mbps=2.5,
            packet_rate=450.0,
            recurrence_count=3,
            description="Initial series of failed SSH login handshakes from remote IP.",
        ),
        ScenarioStep(
            step_number=2,
            observable_risk=0.68,
            observable_confidence=0.82,
            traffic_volume_mbps=6.0,
            packet_rate=1200.0,
            recurrence_count=8,
            description="Credential stuffing rate surges; 150 failed attempts/minute detected.",
        ),
        ScenarioStep(
            step_number=3,
            observable_risk=0.82,
            observable_confidence=0.88,
            traffic_volume_mbps=8.5,
            packet_rate=1800.0,
            recurrence_count=15,
            description="Password spraying targets administrative root accounts.",
        ),
        ScenarioStep(
            step_number=4,
            observable_risk=0.91,
            observable_confidence=0.92,
            traffic_volume_mbps=11.0,
            packet_rate=2400.0,
            recurrence_count=24,
            description="Threat actor leverages compromised service credential; lateral probe imminent.",
        ),
        ScenarioStep(
            step_number=5,
            observable_risk=0.95,
            observable_confidence=0.96,
            traffic_volume_mbps=14.0,
            packet_rate=3000.0,
            recurrence_count=35,
            description="Host compromise in progress; internal pivoting observed.",
        ),
    ],
)

SCENARIO_PORT_SWEEP = Scenario(
    scenario_id="scen-port-sweep",
    name="Reconnaissance Port Sweep",
    description=(
        "Systematic horizontal and vertical SYN/FIN scanning probe across internal network subnet. "
        "Attacker mapping open services and vulnerable daemon versions."
    ),
    ground_truth_label="PORT_SCAN",
    target_asset="192.168.10.20",
    source_asset="192.168.10.110",
    asset_criticality=2,
    initial_threat_level=0.30,
    initial_service_health=100.0,
    disruption_weight=0.8,
    threat_growth_rate=0.10,
    steps=[
        ScenarioStep(
            step_number=1,
            observable_risk=0.45,
            observable_confidence=0.65,
            traffic_volume_mbps=1.2,
            packet_rate=600.0,
            recurrence_count=2,
            description="Rapid half-open TCP SYN requests detected across standard ports 21, 22, 80.",
        ),
        ScenarioStep(
            step_number=2,
            observable_risk=0.58,
            observable_confidence=0.75,
            traffic_volume_mbps=2.8,
            packet_rate=1400.0,
            recurrence_count=6,
            description="Broad port sweep across 1024-4096 range; reset packets accumulated.",
        ),
        ScenarioStep(
            step_number=3,
            observable_risk=0.72,
            observable_confidence=0.85,
            traffic_volume_mbps=4.5,
            packet_rate=2200.0,
            recurrence_count=12,
            description="Service fingerprinting requests directed at exposed web and RPC ports.",
        ),
        ScenarioStep(
            step_number=4,
            observable_risk=0.78,
            observable_confidence=0.88,
            traffic_volume_mbps=5.0,
            packet_rate=2500.0,
            recurrence_count=18,
            description="Vulnerability probes probing CVE-2021-44228 endpoints.",
        ),
        ScenarioStep(
            step_number=5,
            observable_risk=0.85,
            observable_confidence=0.90,
            traffic_volume_mbps=5.5,
            packet_rate=2700.0,
            recurrence_count=25,
            description="Reconnaissance complete; attacker staging targeted exploit payloads.",
        ),
    ],
)

SCENARIO_HIGH_DDOS = Scenario(
    scenario_id="scen-high-ddos",
    name="High-Volume Distributed DoS / Slowloris Flood",
    description=(
        "Massive volumetric application-layer denial of service flooding web server connection pools. "
        "Threat directly degrades service availability; unmitigated attack leads to complete downtime."
    ),
    ground_truth_label="DOS",
    target_asset="192.168.10.5",
    source_asset="192.168.10.50",
    asset_criticality=4,
    initial_threat_level=0.75,
    initial_service_health=100.0,
    disruption_weight=1.5,
    threat_growth_rate=0.25,
    steps=[
        ScenarioStep(
            step_number=1,
            observable_risk=0.78,
            observable_confidence=0.85,
            traffic_volume_mbps=350.0,
            packet_rate=25000.0,
            recurrence_count=4,
            description="Slowloris header exhaustion begins; HTTP worker thread latency climbs.",
        ),
        ScenarioStep(
            step_number=2,
            observable_risk=0.88,
            observable_confidence=0.92,
            traffic_volume_mbps=750.0,
            packet_rate=55000.0,
            recurrence_count=10,
            description="Connection pool 80% saturated; legitimate requests experience 504 timeouts.",
        ),
        ScenarioStep(
            step_number=3,
            observable_risk=0.95,
            observable_confidence=0.97,
            traffic_volume_mbps=1200.0,
            packet_rate=95000.0,
            recurrence_count=20,
            description="Full volumetric flood; ingress pipeline dropping packets; service degradation severe.",
        ),
        ScenarioStep(
            step_number=4,
            observable_risk=0.98,
            observable_confidence=0.99,
            traffic_volume_mbps=1800.0,
            packet_rate=140000.0,
            recurrence_count=35,
            description="Target web daemon unresponsive; memory thrashing on host.",
        ),
        ScenarioStep(
            step_number=5,
            observable_risk=0.99,
            observable_confidence=0.99,
            traffic_volume_mbps=2200.0,
            packet_rate=180000.0,
            recurrence_count=50,
            description="Critical outage; web service completely unavailable.",
        ),
    ],
)

SCENARIO_DATA_EXFILTRATION = Scenario(
    scenario_id="scen-data-exfiltration",
    name="Sensitive Customer Data Exfiltration",
    description=(
        "Covert outbound data exfiltration over encrypted tunnels from crown-jewel customer database. "
        "Severe asset criticality requires immediate decisive containment."
    ),
    ground_truth_label="EXFILTRATION",
    target_asset="192.168.10.50",
    source_asset="192.168.10.200",
    asset_criticality=5,
    initial_threat_level=0.70,
    initial_service_health=100.0,
    disruption_weight=2.5,
    threat_growth_rate=0.20,
    steps=[
        ScenarioStep(
            step_number=1,
            observable_risk=0.72,
            observable_confidence=0.80,
            traffic_volume_mbps=45.0,
            packet_rate=3200.0,
            recurrence_count=2,
            description="Unusual encrypted SSL/TLS session established to untrusted external ASN.",
        ),
        ScenarioStep(
            step_number=2,
            observable_risk=0.84,
            observable_confidence=0.88,
            traffic_volume_mbps=120.0,
            packet_rate=8500.0,
            recurrence_count=5,
            description="Sustained bulk data transfer; SQL dump signatures detected in packet payloads.",
        ),
        ScenarioStep(
            step_number=3,
            observable_risk=0.93,
            observable_confidence=0.94,
            traffic_volume_mbps=260.0,
            packet_rate=19000.0,
            recurrence_count=11,
            description="Exfiltration acceleration; 5GB confidential records transferred.",
        ),
        ScenarioStep(
            step_number=4,
            observable_risk=0.97,
            observable_confidence=0.98,
            traffic_volume_mbps=410.0,
            packet_rate=31000.0,
            recurrence_count=18,
            description="Secondary staging host engaged to distribute egress load.",
        ),
        ScenarioStep(
            step_number=5,
            observable_risk=0.99,
            observable_confidence=0.99,
            traffic_volume_mbps=550.0,
            packet_rate=42000.0,
            recurrence_count=26,
            description="Major regulatory breach in progress; critical assets compromised.",
        ),
    ],
)

SCENARIOS_MAP: Dict[str, Scenario] = {
    SCENARIO_BENIGN_BURST.scenario_id: SCENARIO_BENIGN_BURST,
    SCENARIO_BRUTE_FORCE.scenario_id: SCENARIO_BRUTE_FORCE,
    SCENARIO_PORT_SWEEP.scenario_id: SCENARIO_PORT_SWEEP,
    SCENARIO_HIGH_DDOS.scenario_id: SCENARIO_HIGH_DDOS,
    SCENARIO_DATA_EXFILTRATION.scenario_id: SCENARIO_DATA_EXFILTRATION,
}


def get_scenario(scenario_id: str) -> Scenario:
    """Retrieve scenario by ID; raises ValueError if scenario is unknown."""
    if scenario_id not in SCENARIOS_MAP:
        raise ValueError(
            f"Unknown scenario '{scenario_id}'. Available: {list(SCENARIOS_MAP.keys())}"
        )
    return SCENARIOS_MAP[scenario_id]


def list_scenarios() -> List[Scenario]:
    """Return all available reproducible scenarios."""
    return list(SCENARIOS_MAP.values())
