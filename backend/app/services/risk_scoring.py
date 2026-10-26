"""SentinelX AI - Transparent Risk Assessment Scoring Engine

Computes documented, multi-factor risk estimates from detection confidence,
event recurrence, asset criticality, and telemetry completeness.
"""

from typing import Any, Dict, List, Optional, Tuple
from pydantic import BaseModel, Field

from .risk_policy import (
    DEFAULT_ASSET_CRITICALITIES,
    DEFAULT_FALLBACK_CRITICALITY,
    MITRE_ATTACK_MAP,
    map_risk_to_severity,
)
from app.schemas.common import SeverityLevel


class RiskComponentWeights(BaseModel):
    weight_detection: float = 0.45
    weight_recurrence: float = 0.25
    weight_criticality: float = 0.30


class RiskScoreBreakdown(BaseModel):
    detection_score: float
    detection_contribution: float
    recurrence_count: int
    recurrence_contribution: float
    target_asset: str
    asset_criticality: float
    criticality_contribution: float
    total_raw_risk: float
    final_bounded_risk: float
    severity: SeverityLevel
    rationale: str
    missing_evidence_notes: List[str] = Field(default_factory=list)


class RiskScoringService:
    """Service computing transparent risk estimates according to documented formulas."""

    def __init__(self, weights: Optional[RiskComponentWeights] = None):
        self.weights = weights or RiskComponentWeights()

    def assess_risk(
        self,
        detection_score: float,
        predicted_class: str,
        target_asset: str,
        recurrence_count: int = 1,
        telemetry_gaps: Optional[List[str]] = None,
        asset_criticalities: Optional[Dict[str, float]] = None,
    ) -> Tuple[float, SeverityLevel, RiskScoreBreakdown, Optional[Dict[str, str]]]:
        """Calculate multi-factor risk score and map to severity classification.
        
        Formula:
            Risk = (w_det * det_score) + (w_rec * min(rec_count / 5, 1.0)) + (w_crit * asset_crit)
            Bounded in [0.0, 1.0].
        """
        criticality_map = asset_criticalities or DEFAULT_ASSET_CRITICALITIES
        asset_crit = criticality_map.get(target_asset, DEFAULT_FALLBACK_CRITICALITY)

        # 1. Detection score component (0.0 - 1.0)
        bounded_det = max(0.0, min(1.0, float(detection_score)))
        det_contrib = round(self.weights.weight_detection * bounded_det, 4)

        # 2. Event Recurrence component (saturates at 5 repeated flows)
        normalized_rec = min(float(recurrence_count) / 5.0, 1.0)
        rec_contrib = round(self.weights.weight_recurrence * normalized_rec, 4)

        # 3. Target Asset Criticality component
        crit_contrib = round(self.weights.weight_criticality * asset_crit, 4)

        raw_risk = det_contrib + rec_contrib + crit_contrib
        final_risk = round(max(0.0, min(1.0, raw_risk)), 2)

        severity = map_risk_to_severity(final_risk)

        gaps = telemetry_gaps or []
        rationale = (
            f"Risk score {final_risk:.2f} derived from detection confidence {bounded_det:.2f} "
            f"({det_contrib:.2f}), event recurrence {recurrence_count}x ({rec_contrib:.2f}), "
            f"and target asset '{target_asset}' criticality {asset_crit:.2f} ({crit_contrib:.2f})."
        )
        if gaps:
            rationale += f" Evaluated with {len(gaps)} telemetry gaps: {'; '.join(gaps)}."

        mitre_info = MITRE_ATTACK_MAP.get(predicted_class)

        breakdown = RiskScoreBreakdown(
            detection_score=bounded_det,
            detection_contribution=det_contrib,
            recurrence_count=recurrence_count,
            recurrence_contribution=rec_contrib,
            target_asset=target_asset,
            asset_criticality=asset_crit,
            criticality_contribution=crit_contrib,
            total_raw_risk=round(raw_risk, 4),
            final_bounded_risk=final_risk,
            severity=severity,
            rationale=rationale,
            missing_evidence_notes=gaps,
        )

        return final_risk, severity, breakdown, mitre_info
