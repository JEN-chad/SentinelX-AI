"""SentinelX AI - Threat Detection Agent

Specialized agent wrapping machine-learning threat detection models.
CRITICAL SAFETY RULE: The Detection Agent NEVER executes or directly triggers mitigations.
"""

from datetime import datetime, timezone
import time
from typing import Any, Dict, Optional

from app.detection.inference import ThreatDetectionService
from app.schemas.agents import AgentRunResult, AgentTask
from app.schemas.common import AgentName, AgentRunStatus
from app.schemas.detections import DetectionResult
from app.schemas.events import NormalizedEvent
from app.schemas.evidence import EvidenceReference, EvidenceType
from .base import BaseAgent


class DetectionAgent(BaseAgent):
    """Detection Agent consuming flow events, running ML inference, and producing evidence."""

    def __init__(self, service: Optional[ThreatDetectionService] = None, version: str = "1.0.0"):
        super().__init__(agent_name=AgentName.DETECTION_AGENT, version=version)
        self.service = service or ThreatDetectionService()

    def run(self, task: AgentTask, context: Dict[str, Any]) -> AgentRunResult:
        start_time = time.perf_counter()
        now = datetime.now(timezone.utc)
        run_id = f"run-det-{now.strftime('%Y%m%d%H%M%S%f')[-8:]}"

        event: Optional[NormalizedEvent] = context.get("event")
        if not event:
            duration_ms = float(round((time.perf_counter() - start_time) * 1000.0, 3))
            return AgentRunResult(
                agent_run_id=run_id,
                agent_name=self.agent_name,
                incident_id=task.incident_id,
                status=AgentRunStatus.FAILED,
                findings=[],
                proposed_actions=[],
                conflict_flags=["MISSING_EVENT_IN_CONTEXT"],
                summary="Detection Agent failed: No normalized event provided in execution context.",
                structured_output={},
                duration_ms=duration_ms,
                created_at=now,
            )

        try:
            # 1. Run threat detection inference
            detection: DetectionResult = self.service.score_event(event)
            anomaly_score = detection.anomaly_score or 0.0

            # 2. Build structured evidence reference
            findings = []
            is_anomaly = (anomaly_score >= 0.5) or (detection.predicted_class != "BENIGN")

            evidence = EvidenceReference(
                evidence_id=f"evd-{run_id}-01",
                event_id=event.event_id,
                supporting_event_ids=[event.event_id],
                evidence_type=EvidenceType.ANOMALY_SIGNAL,
                is_inferred=False,
                description=(
                    f"Model '{detection.model_version}' classified event as '{detection.predicted_class}' "
                    f"with confidence {detection.class_scores.get(detection.predicted_class, anomaly_score):.2f} "
                    f"and anomaly score {anomaly_score:.2f}."
                ),
                confidence=anomaly_score if is_anomaly else (1.0 - anomaly_score),
                source_component="detection_agent",
                metadata={
                    "detection_id": detection.detection_id,
                    "predicted_class": detection.predicted_class,
                    "class_scores": detection.class_scores,
                    "evidence_feature_names": detection.evidence_feature_names,
                    "inference_duration_ms": detection.inference_duration_ms,
                },
                timestamp=now,
            )
            findings.append(evidence)

            summary = (
                f"Detection completed in {detection.inference_duration_ms:.2f}ms. "
                f"Classified as '{detection.predicted_class}' with {int(anomaly_score * 100)}% anomaly confidence. "
                f"Top explanatory signals: {', '.join(detection.evidence_feature_names)}."
            )

            duration_ms = float(round((time.perf_counter() - start_time) * 1000.0, 3))

            return AgentRunResult(
                agent_run_id=run_id,
                agent_name=self.agent_name,
                incident_id=task.incident_id,
                status=AgentRunStatus.COMPLETED,
                findings=findings,
                # STRICT SAFETY: Never propose actions from detection alone
                proposed_actions=[],
                conflict_flags=[],
                summary=summary,
                structured_output={
                    "detection": detection.model_dump(mode="json"),
                    "anomaly_score": anomaly_score,
                    "is_anomaly": is_anomaly,
                },
                duration_ms=duration_ms,
                created_at=now,
            )
        except Exception as e:
            duration_ms = float(round((time.perf_counter() - start_time) * 1000.0, 3))
            return AgentRunResult(
                agent_run_id=run_id,
                agent_name=self.agent_name,
                incident_id=task.incident_id,
                status=AgentRunStatus.FAILED,
                findings=[],
                proposed_actions=[],
                conflict_flags=[f"INFERENCE_ERROR: {str(e)}"],
                summary=f"Detection agent failed during inference: {str(e)}",
                structured_output={"error": str(e)},
                duration_ms=duration_ms,
                created_at=now,
            )
