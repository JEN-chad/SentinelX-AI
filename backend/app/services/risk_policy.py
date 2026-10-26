"""SentinelX AI - Risk Assessment Policy and Configuration

Defines asset criticalities, severity thresholds, MITRE ATT&CK technique mappings,
and risk calculation weights.
"""

from typing import Dict
from app.schemas.common import SeverityLevel


# Asset Criticality Ratings [0.0 - 1.0]
# Critical database/web targets receive higher baseline weights
DEFAULT_ASSET_CRITICALITIES: Dict[str, float] = {
    "192.168.10.5": 0.95,   # Core Production Web Server (High Criticality)
    "10.0.0.1": 0.90,       # Corporate Gateway / Active Directory DMZ
    "192.168.10.8": 0.80,   # Internal Database Server
    "192.168.10.12": 0.70,  # Application Backend Node
    "10.0.0.2": 0.60,       # Internal DNS Resolver
}
DEFAULT_FALLBACK_CRITICALITY: float = 0.40  # Standard Workstation / Subnet


# MITRE ATT&CK Technique Mappings by Threat Class
MITRE_ATTACK_MAP: Dict[str, Dict[str, str]] = {
    "DoS-Slowloris": {
        "technique_id": "T1498.001",
        "technique_name": "Network Denial of Service: Direct Network Flood",
        "tactic": "Impact",
    },
    "PortScan": {
        "technique_id": "T1046",
        "technique_name": "Network Service Discovery",
        "tactic": "Discovery",
    },
    "BruteForce-SSH": {
        "technique_id": "T1110.001",
        "technique_name": "Brute Force: Password Guessing",
        "tactic": "Credential Access",
    },
    "DataExfiltration": {
        "technique_id": "T1048.003",
        "technique_name": "Exfiltration Over Alternative Protocol: Symmetric Encrypted Stream",
        "tactic": "Exfiltration",
    },
}


# Severity Bands mapping normalized risk in [0.0, 1.0] to SeverityLevel
def map_risk_to_severity(risk_score: float) -> SeverityLevel:
    """Map a continuous risk score to a categorized severity level."""
    if risk_score >= 0.80:
        return SeverityLevel.CRITICAL
    if risk_score >= 0.60:
        return SeverityLevel.HIGH
    if risk_score >= 0.35:
        return SeverityLevel.MEDIUM
    return SeverityLevel.LOW
