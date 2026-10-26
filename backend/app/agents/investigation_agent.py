"""SentinelX AI - Investigation and Correlation Agent

Specialized agent correlating multi-event evidence chains, constructing
chronological timelines, and surfacing contradictory or missing telemetry.
"""

from datetime import datetime, timezone
import time
from typing import Any, Dict, List, Optional

from app.schemas.agents import AgentRunResult, AgentTask
from app.schemas.common import AgentName, AgentRunStatus
from app.schemas.events import NormalizedEvent
from app.schemas.evidence import EvidenceReference, EvidenceType
from app.services.correlation_service import CorrelationService
from app.services.timeline_service import TimelineService
from .base import BaseAgent


class InvestigationAgent(BaseAgent):
    """Investigation Agent correlating related events and assembling incident evidence chains."""

    def __init__(
        self,
        correlation_service: Optional[CorrelationService] = None,
        timeline_service: Optional[TimelineService] = None,
        version: str = "1.0.0",
    ):
        super().__init__(agent_name=AgentName.INVESTIGATION_AGENT, version=version)
        self.correlation_service = correlation_service or CorrelationService()
        self.timeline_service = timeline_service or TimelineService()

    def run(self, task: AgentTask, context: Dict[str, Any]) -> AgentRunResult:
        start_time = time.perf_counter()
        now = datetime.now(timezone.utc)
        run_id = f"run-inv-{now.strftime('%Y%m%d%H%M%S%f')[-8:]}"

        seed_event: Optional[NormalizedEvent] = context.get("seed_event")
        candidates: List[NormalizedEvent] = context.get("candidate_events", [])

        if not seed_event:
            duration_ms = float(round((time.perf_counter() - start_time) * 1000.0, 3))
            return AgentRunResult(
                agent_run_id=run_id,
                agent_name=self.agent_name,
                incident_id=task.incident_id,
                status=AgentRunStatus.FAILED,
                findings=[],
                proposed_actions=[],
                conflict_flags=["MISSING_SEED_EVENT"],
                summary="Investigation Agent failed: No seed event provided in context.",
                structured_output={},
                duration_ms=duration_ms,
                created_at=now,
            )

        # 1. Correlate candidate events using deterministic rules
        matches = self.correlation_service.correlate_candidates(
            seed=seed_event,
            candidates=candidates,
            time_window_seconds=task.parameters.get("time_window_seconds", 600),
        )

        all_incident_events = [seed_event] + [evt for evt, _ in matches]

        # 2. Build chronological timeline
        timeline_entries = self.timeline_service.build_timeline(all_incident_events)

        # 3. Detect evidence gaps and conflicts
        gaps, conflicts = self.timeline_service.detect_evidence_gaps_and_conflicts(all_incident_events)

        # 4. Synthesize structured evidence references
        findings: List[EvidenceReference] = []

        # Timeline cluster evidence
        timeline_evidence = EvidenceReference(
            evidence_id=f"evd-{run_id}-cluster",
            event_id=seed_event.event_id,
            supporting_event_ids=[e.event_id for e in all_incident_events],
            evidence_type=EvidenceType.TIMELINE_CLUSTER,
            is_inferred=True,
            description=(
                f"Aggregated {len(all_incident_events)} flows into a coherent timeline cluster "
                f"spanning {seed_event.source_asset} -> {seed_event.target_asset}."
            ),
            confidence=0.90,
            source_component="investigation_agent",
            metadata={
                "event_count": len(all_incident_events),
                "timespan_seconds": (
                    all_incident_events[-1].event_time - all_incident_events[0].event_time
                ).total_seconds(),
            },
            timestamp=now,
        )
        findings.append(timeline_evidence)

        # Individual correlation match evidence
        for evt, match in matches:
            findings.append(
                EvidenceReference(
                    evidence_id=f"evd-{run_id}-{evt.event_id.replace('evt-', '')}",
                    event_id=evt.event_id,
                    supporting_event_ids=[seed_event.event_id, evt.event_id],
                    evidence_type=EvidenceType.OBSERVED_EVENT,
                    is_inferred=False,
                    description=f"Correlated via rule '{match.rule_name}': {match.reason}",
                    confidence=match.confidence,
                    source_component="correlation_service",
                    metadata={"rule_name": match.rule_name},
                    timestamp=now,
                )
            )

        duration_ms = float(round((time.perf_counter() - start_time) * 1000.0, 3))

        summary = (
            f"Correlated {len(matches)} additional events with seed {seed_event.event_id}. "
            f"Total linked evidence: {len(all_incident_events)} flows. "
            f"Observed recurrence: {len(all_incident_events)} instances across {seed_event.target_asset}."
        )
        if gaps:
            summary += f" Detected telemetry gaps: {', '.join(gaps)}."

        return AgentRunResult(
            agent_run_id=run_id,
            agent_name=self.agent_name,
            incident_id=task.incident_id,
            status=AgentRunStatus.COMPLETED,
            findings=findings,
            proposed_actions=[],
            conflict_flags=conflicts + gaps,
            summary=summary,
            structured_output={
                "correlated_event_ids": [e.event_id for e in all_incident_events],
                "timeline": [t.model_dump(mode="json") for t in timeline_entries],
                "evidence_gaps": gaps,
                "correlation_matches": [
                    {"event_id": m.event_id, "rule": m.rule_name, "reason": m.reason}
                    for _, m in matches
                ],
                "recurrence_count": len(all_incident_events),
            },
            duration_ms=duration_ms,
            created_at=now,
        )
