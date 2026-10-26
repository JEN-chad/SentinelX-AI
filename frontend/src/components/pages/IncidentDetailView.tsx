"use client";

import React, { useState } from "react";
import {
  AlertTriangle,
  ShieldCheck,
  CheckCircle,
  Network,
  Cpu,
  BrainCircuit,
  Lock,
  ArrowRight,
  Layers,
  Sparkles,
  Zap,
  CheckCircle2,
  XCircle,
  FileText,
  Play,
  AlertOctagon,
} from "lucide-react";
import { useSimulation } from "@/lib/simulationStore";
import { ActionType, SimulationOutcome } from "@/lib/types";

export function IncidentDetailView() {
  const {
    incidents,
    selectedIncidentId,
    setSelectedIncidentId,
    investigateIncident,
    assessIncidentRisk,
    planMitigation,
    approveIncidentAction,
    simulateIncidentResponse,
    triggerReplay,
    isLoading,
  } = useSimulation();

  const currentIncident =
    incidents.find((i) => i.incident_id === selectedIncidentId) || incidents[0];

  const [activeAgentTab, setActiveAgentTab] = useState<string>("detection");
  const [approvalNote, setApprovalNote] = useState<string>("");
  const [latestOutcome, setLatestOutcome] = useState<SimulationOutcome | null>(null);
  const [isExecutingSim, setIsExecutingSim] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);

  if (!currentIncident) {
    return (
      <div className="p-12 text-center text-slate-400 font-mono space-y-4 max-w-lg mx-auto">
        <AlertOctagon className="w-12 h-12 text-slate-600 mx-auto" />
        <div className="text-slate-200 text-sm font-bold">No Active Incidents Available</div>
        <p className="text-xs text-slate-400">
          No incidents are stored in the database. Stream network flows from the offline CIC-IDS2017 dataset containing attack patterns to trigger the detection agent.
        </p>
        <button
          onClick={() => triggerReplay(25)}
          disabled={isLoading}
          className="px-4 py-2 rounded bg-cyan-950 text-cyan-300 hover:bg-cyan-900 border border-cyan-800 text-xs font-mono transition-all"
        >
          {isLoading ? "Streaming..." : "Replay 25 Flows"}
        </button>
      </div>
    );
  }

  const detectionAgent = currentIncident.agent_results?.find(
    (a) => a.agent_name === "detection_agent"
  );
  const investigationAgent = currentIncident.agent_results?.find(
    (a) => a.agent_name === "investigation_agent"
  );
  const riskAgent = currentIncident.agent_results?.find(
    (a) => a.agent_name === "risk_agent"
  );
  const mitigationAgent = currentIncident.agent_results?.find(
    (a) => a.agent_name === "mitigation_agent"
  );

  const handleRunInvestigation = async () => {
    setActionError(null);
    try {
      await investigateIncident(currentIncident.incident_id);
    } catch (err: any) {
      setActionError(`Investigation failed: ${err.message}`);
    }
  };

  const handleRunRisk = async () => {
    setActionError(null);
    try {
      await assessIncidentRisk(currentIncident.incident_id);
    } catch (err: any) {
      setActionError(`Risk assessment failed: ${err.message}`);
    }
  };

  const handleRunMitigation = async () => {
    setActionError(null);
    try {
      await planMitigation(currentIncident.incident_id);
    } catch (err: any) {
      setActionError(`Mitigation planning failed: ${err.message}`);
    }
  };

  const handleApprove = async () => {
    setActionError(null);
    try {
      await approveIncidentAction(
        currentIncident.incident_id,
        "simulate_block",
        approvalNote || "Security analyst approved simulated response block."
      );
    } catch (err: any) {
      setActionError(`Approval failed: ${err.message}`);
    }
  };

  const handleSimulate = async (action: ActionType) => {
    setIsExecutingSim(true);
    setActionError(null);
    try {
      const outcome = await simulateIncidentResponse(currentIncident.incident_id, action);
      if (outcome) {
        setLatestOutcome(outcome);
      }
    } catch (err: any) {
      setActionError(`Simulation execution failed: ${err.message}`);
    } finally {
      setIsExecutingSim(false);
    }
  };

  return (
    <div className="space-y-5 p-6 max-w-7xl mx-auto">
      {/* Action Error Banner */}
      {actionError && (
        <div className="p-3 rounded-lg bg-rose-950/60 border border-rose-800 text-rose-300 font-mono text-xs flex items-center justify-between">
          <span>{actionError}</span>
          <button onClick={() => setActionError(null)} className="text-slate-400 hover:text-white">
            &times;
          </button>
        </div>
      )}

      {/* Incident Switcher and Status Bar */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-2 border-b border-slate-800">
        <div>
          <div className="flex items-center gap-2">
            <span className="font-mono text-sm font-bold text-slate-100">
              INCIDENT TRIAGE &amp; REASONING TRACE:
            </span>
            <select
              value={currentIncident.incident_id}
              onChange={(e) => setSelectedIncidentId(e.target.value)}
              className="bg-[#070d18] border border-slate-700 rounded px-2.5 py-1 text-xs font-mono text-cyan-300 font-bold focus:outline-none"
            >
              {incidents.map((inc) => (
                <option key={inc.incident_id} value={inc.incident_id}>
                  {inc.incident_id} - {inc.title.slice(0, 45)}...
                </option>
              ))}
            </select>
          </div>
          <p className="text-xs text-slate-400 mt-0.5 font-mono">
            {currentIncident.title}
          </p>
        </div>

        {/* State Badges */}
        <div className="flex items-center gap-2 font-mono text-xs">
          <span
            className={`px-2.5 py-1 rounded border uppercase font-bold text-[11px] ${
              currentIncident.severity === "critical"
                ? "bg-rose-950 text-rose-300 border-rose-800"
                : currentIncident.severity === "high"
                ? "bg-orange-950 text-orange-300 border-orange-800"
                : "bg-amber-950 text-amber-300 border-amber-800"
            }`}
          >
            {currentIncident.severity} Severity
          </span>
          <span className="px-2.5 py-1 rounded bg-slate-900 border border-slate-700 text-slate-200">
            Lifecycle: <strong className="text-cyan-400">{currentIncident.status.toUpperCase()}</strong>
          </span>
        </div>
      </div>

      {/* Incident Overview Card */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="p-4 rounded-xl bg-[#0b1220] border border-slate-800">
          <span className="text-[10px] font-mono text-slate-400 uppercase">Assessed Risk Score</span>
          <div className="text-2xl font-bold font-mono text-rose-400 mt-1">
            {currentIncident.risk_score != null ? currentIncident.risk_score.toFixed(2) : "0.00"} / 1.00
          </div>
          <p className="text-[10px] font-mono text-slate-500 mt-1">
            Multi-factor weighted calibration
          </p>
        </div>

        <div className="p-4 rounded-xl bg-[#0b1220] border border-slate-800">
          <span className="text-[10px] font-mono text-slate-400 uppercase">Target Asset</span>
          <div className="text-sm font-bold font-mono text-slate-200 mt-1 truncate">
            {currentIncident.target_asset || "192.168.10.5"}
          </div>
          <p className="text-[10px] font-mono text-slate-500 mt-1">
            Source: {currentIncident.source_asset || "Unknown"}
          </p>
        </div>

        <div className="p-4 rounded-xl bg-[#0b1220] border border-slate-800">
          <span className="text-[10px] font-mono text-slate-400 uppercase">MITRE ATT&amp;CK Mapping</span>
          <div className="text-sm font-bold font-mono text-amber-400 mt-1">
            {currentIncident.mitre_technique || "Pending Risk Assessment"}
          </div>
          <p className="text-[10px] font-mono text-slate-500 mt-1">
            Technique attribution
          </p>
        </div>

        <div className="p-4 rounded-xl bg-[#0b1220] border border-slate-800">
          <span className="text-[10px] font-mono text-slate-400 uppercase">Linked Evidence</span>
          <div className="text-sm font-bold font-mono text-cyan-400 mt-1">
            {currentIncident.event_ids?.length || 0} Correlated Flows
          </div>
          <p className="text-[10px] font-mono text-slate-500 mt-1">
            {currentIncident.evidence?.length || 0} Evidence References
          </p>
        </div>
      </div>

      {/* Multi-Agent Deep Reasoning Workspace */}
      <div className="rounded-xl bg-[#0b1220] border border-slate-800 shadow-xl overflow-hidden">
        {/* Agent Tabs */}
        <div className="flex border-b border-slate-800 bg-[#070d18] overflow-x-auto text-xs font-mono">
          {[
            { id: "detection", label: "Agent A: Detection", icon: Cpu },
            { id: "investigation", label: "Agent B: Investigation", icon: Network },
            { id: "risk", label: "Agent C: Risk Assessment", icon: AlertTriangle },
            { id: "mitigation", label: "Agent D: Mitigation Planning", icon: ShieldCheck },
          ].map((tab) => {
            const Icon = tab.icon;
            const isSelected = activeAgentTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveAgentTab(tab.id)}
                className={`flex items-center gap-2 px-4 py-3 border-b-2 font-medium transition-all shrink-0 ${
                  isSelected
                    ? "border-cyan-400 text-cyan-300 bg-cyan-950/20 font-bold"
                    : "border-transparent text-slate-400 hover:text-slate-200 hover:bg-slate-900"
                }`}
              >
                <Icon className="w-3.5 h-3.5" />
                <span>{tab.label}</span>
              </button>
            );
          })}
        </div>

        {/* Tab Content Panes */}
        <div className="p-5 font-mono text-xs space-y-4">
          {/* TAB 1: DETECTION AGENT */}
          {activeAgentTab === "detection" && (
            <div className="space-y-4">
              <div className="p-4 rounded-lg bg-[#070d18] border border-slate-800 space-y-2">
                <div className="flex items-center justify-between text-cyan-300 font-semibold">
                  <span>Detection Agent Execution Trace</span>
                  <span className="text-slate-400 text-[11px]">
                    Status: {detectionAgent ? detectionAgent.status.toUpperCase() : "ACTIVE"}
                  </span>
                </div>
                <p className="text-slate-300 font-sans text-xs">
                  {detectionAgent?.summary ||
                    "Detection Agent instantiated. Inference score calculated using trained Random Forest model (threat_detector_rf_v1.joblib)."}
                </p>
              </div>

              {detectionAgent?.structured_output?.detection && (
                <div className="p-3 rounded bg-slate-900 border border-slate-800 space-y-2">
                  <span className="text-slate-400 uppercase text-[10px] font-bold">
                    Detection Inference Output:
                  </span>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
                    <div className="p-2 bg-slate-950 rounded border border-slate-800">
                      <span className="text-slate-500 text-[10px]">Predicted Class</span>
                      <div className="text-amber-400 font-bold">
                        {detectionAgent.structured_output.detection.predicted_class}
                      </div>
                    </div>
                    <div className="p-2 bg-slate-950 rounded border border-slate-800">
                      <span className="text-slate-500 text-[10px]">Anomaly Score</span>
                      <div className="text-cyan-400 font-bold">
                        {detectionAgent.structured_output.detection.anomaly_score?.toFixed(3)}
                      </div>
                    </div>
                    <div className="p-2 bg-slate-950 rounded border border-slate-800">
                      <span className="text-slate-500 text-[10px]">Model Version</span>
                      <div className="text-slate-300 font-bold">
                        {detectionAgent.structured_output.detection.model_version}
                      </div>
                    </div>
                    <div className="p-2 bg-slate-950 rounded border border-slate-800">
                      <span className="text-slate-500 text-[10px]">Evidence Features</span>
                      <div className="text-slate-300 font-bold">
                        {detectionAgent.structured_output.detection.evidence_feature_names?.length || 0} features
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* TAB 2: INVESTIGATION AGENT */}
          {activeAgentTab === "investigation" && (
            <div className="space-y-4">
              <div className="p-4 rounded-lg bg-[#070d18] border border-slate-800 space-y-2">
                <div className="flex items-center justify-between text-blue-300 font-semibold">
                  <span>Investigation &amp; Correlation Agent</span>
                  {investigationAgent ? (
                    <span className="text-emerald-400 text-[11px]">COMPLETED</span>
                  ) : (
                    <button
                      onClick={handleRunInvestigation}
                      disabled={isLoading}
                      className="px-2.5 py-1 rounded bg-blue-950 text-blue-300 border border-blue-800 hover:bg-blue-900 text-xs"
                    >
                      {isLoading ? "Correlating..." : "Run Investigation Agent"}
                    </button>
                  )}
                </div>
                <p className="text-slate-300 font-sans text-xs">
                  {investigationAgent?.summary ||
                    "Investigation agent correlates host-pair bursts and port sweeps across time windows to detect evidence gaps and assemble attack timelines."}
                </p>
              </div>

              {/* Real Linked Evidence Chain */}
              <div className="space-y-2">
                <span className="text-slate-400 uppercase text-[10px] font-bold">
                  Evidence Traceability Chain ({currentIncident.evidence?.length || 0} items):
                </span>
                {currentIncident.evidence && currentIncident.evidence.length > 0 ? (
                  <div className="space-y-2">
                    {currentIncident.evidence.map((evd) => (
                      <div
                        key={evd.evidence_id}
                        className="p-3 rounded bg-slate-900 border border-slate-800 flex items-start justify-between"
                      >
                        <div>
                          <div className="flex items-center gap-2">
                            <span className="font-bold text-slate-200">{evd.evidence_id}</span>
                            <span className="text-[10px] px-1.5 py-0.5 rounded bg-cyan-950 text-cyan-300 border border-cyan-800">
                              {evd.evidence_type}
                            </span>
                            <span className="text-[10px] px-1.5 py-0.5 rounded bg-slate-800 text-slate-400 border border-slate-700">
                              {evd.is_inferred ? "INFERRED" : "OBSERVED FACT"}
                            </span>
                          </div>
                          <p className="text-slate-300 mt-1 font-sans">{evd.description}</p>
                        </div>
                        <span className="text-emerald-400 font-bold">
                          {(evd.confidence * 100).toFixed(0)}% Conf
                        </span>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="p-4 rounded bg-slate-900/60 border border-slate-800 text-slate-500 text-xs">
                    No secondary evidence linked yet. Run Investigation Agent to correlate candidate flows.
                  </div>
                )}
              </div>
            </div>
          )}

          {/* TAB 3: RISK ASSESSMENT AGENT */}
          {activeAgentTab === "risk" && (
            <div className="space-y-4">
              <div className="p-4 rounded-lg bg-[#070d18] border border-slate-800 space-y-2">
                <div className="flex items-center justify-between text-amber-300 font-semibold">
                  <span>Risk Assessment Agent &amp; MITRE ATT&amp;CK Attribution</span>
                  {riskAgent ? (
                    <span className="text-emerald-400 text-[11px]">ASSESSED</span>
                  ) : (
                    <button
                      onClick={handleRunRisk}
                      disabled={isLoading}
                      className="px-2.5 py-1 rounded bg-amber-950 text-amber-300 border border-amber-800 hover:bg-amber-900 text-xs"
                    >
                      {isLoading ? "Assessing..." : "Run Risk Agent"}
                    </button>
                  )}
                </div>
                <p className="text-slate-300 font-sans text-xs">
                  {riskAgent?.summary ||
                    "Calculates multi-factor risk score combining anomaly confidence, asset criticality weighting, and burst recurrence factor. Maps techniques to MITRE ATT&CK."}
                </p>
              </div>

              {riskAgent?.structured_output && (
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                  <div className="p-3 rounded bg-slate-900 border border-slate-800">
                    <span className="text-slate-500 text-[10px]">Calibrated Risk Score</span>
                    <div className="text-rose-400 font-bold text-lg mt-0.5">
                      {riskAgent.structured_output.risk_score?.toFixed(2)}
                    </div>
                  </div>
                  <div className="p-3 rounded bg-slate-900 border border-slate-800">
                    <span className="text-slate-500 text-[10px]">Calculated Severity</span>
                    <div className="text-amber-400 font-bold text-lg mt-0.5 uppercase">
                      {riskAgent.structured_output.severity}
                    </div>
                  </div>
                  <div className="p-3 rounded bg-slate-900 border border-slate-800">
                    <span className="text-slate-500 text-[10px]">MITRE Technique</span>
                    <div className="text-cyan-400 font-bold text-lg mt-0.5">
                      {riskAgent.structured_output.mitre_technique || "T1498.001"}
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* TAB 4: MITIGATION PLANNING AGENT */}
          {activeAgentTab === "mitigation" && (
            <div className="space-y-4">
              <div className="p-4 rounded-lg bg-[#070d18] border border-slate-800 space-y-2">
                <div className="flex items-center justify-between text-emerald-300 font-semibold">
                  <span>Mitigation Planning Agent &amp; Safety Gate</span>
                  {mitigationAgent ? (
                    <span className="text-emerald-400 text-[11px]">PROPOSED</span>
                  ) : (
                    <button
                      onClick={handleRunMitigation}
                      disabled={isLoading}
                      className="px-2.5 py-1 rounded bg-emerald-950 text-emerald-300 border border-emerald-800 hover:bg-emerald-900 text-xs"
                    >
                      {isLoading ? "Planning..." : "Plan Mitigation"}
                    </button>
                  )}
                </div>
                <p className="text-slate-300 font-sans text-xs">
                  {mitigationAgent?.summary ||
                    "Evaluates the allowlisted action catalogue under deterministic safety constraints. Recommends proportional response and verifies approval requirements."}
                </p>
              </div>

              {mitigationAgent?.structured_output && (
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  <div className="p-3 rounded bg-slate-900 border border-slate-800">
                    <span className="text-slate-500 text-[10px]">Recommended Action</span>
                    <div className="text-emerald-400 font-bold text-lg mt-0.5 font-mono">
                      {mitigationAgent.structured_output.recommended_action}
                    </div>
                  </div>
                  <div className="p-3 rounded bg-slate-900 border border-slate-800">
                    <span className="text-slate-500 text-[10px]">Disruption Cost</span>
                    <div className="text-amber-400 font-bold text-lg mt-0.5">
                      {mitigationAgent.structured_output.disruption_cost} Disruption Penalty
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Safety Gate, Human Approval, and Action Execution Console */}
      <div className="p-5 rounded-xl bg-[#0b1220] border border-slate-800 shadow-xl space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <ShieldCheck className="w-4 h-4 text-cyan-400" />
            <h2 className="text-sm font-bold font-mono tracking-wider text-slate-200 uppercase">
              Response Execution Console &amp; Safety Gate
            </h2>
          </div>
          <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-amber-950/60 text-amber-300 border border-amber-800">
            MANDATORY SIMULATION ONLY
          </span>
        </div>

        {/* Approval Gate Notice */}
        {currentIncident.status === "approval_required" && (
          <div className="p-4 rounded-lg bg-amber-950/20 border border-amber-700/40 space-y-3 font-mono text-xs">
            <div className="flex items-center gap-2 text-amber-300 font-bold">
              <Lock className="w-4 h-4 text-amber-400" />
              <span>Human Analyst Approval Gate Required for 'simulate_block'</span>
            </div>
            <p className="text-slate-300 font-sans text-xs">
              Consequential containment actions require human authorization before simulation execution. Real firewalls and production endpoints are never modified.
            </p>

            <div className="flex flex-col sm:flex-row gap-2">
              <input
                type="text"
                placeholder="Analyst reason / feedback note..."
                value={approvalNote}
                onChange={(e) => setApprovalNote(e.target.value)}
                className="flex-1 bg-[#070d18] border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-amber-500 font-mono"
              />
              <button
                onClick={handleApprove}
                disabled={isLoading}
                className="px-4 py-1.5 rounded-lg bg-amber-600 hover:bg-amber-500 text-slate-900 font-bold transition-colors whitespace-nowrap"
              >
                Sign Off &amp; Authorize Simulation
              </button>
            </div>
          </div>
        )}

        {/* Permitted Action Execution Buttons */}
        <div className="space-y-2 font-mono text-xs">
          <span className="text-slate-400 text-[10px] uppercase font-bold">
            Simulate Permitted Actions (Action Catalogue Allowlist):
          </span>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
            {(currentIncident.allowed_actions || [
              "raise_alert",
              "increase_monitoring",
              "escalate_for_approval",
              "simulate_block",
            ]).map((act) => (
              <button
                key={act}
                disabled={isExecutingSim || isLoading}
                onClick={() => handleSimulate(act as ActionType)}
                className={`p-3 rounded-lg border text-left transition-all ${
                  act === "simulate_block"
                    ? "bg-rose-950/40 border-rose-800 text-rose-300 hover:bg-rose-900/40"
                    : "bg-slate-900 border-slate-700 text-slate-300 hover:bg-slate-800 hover:text-white"
                }`}
              >
                <div className="font-bold">{act}</div>
                <div className="text-[10px] text-slate-400 mt-1">
                  {act === "simulate_block"
                    ? "Isolate socket traffic in simulator"
                    : act === "increase_monitoring"
                    ? "Double sampling telemetry rate"
                    : "Raise analyst priority alert"}
                </div>
              </button>
            ))}
          </div>
        </div>

        {/* Live Simulation Outcome & Reward Feedback */}
        {latestOutcome && (
          <div className="p-4 rounded-lg bg-emerald-950/25 border border-emerald-700/50 space-y-2 font-mono text-xs">
            <div className="flex items-center gap-2 text-emerald-300 font-bold">
              <CheckCircle2 className="w-4 h-4 text-emerald-400" />
              <span>Simulation Outcome Recorded (Outcome ID: {latestOutcome.outcome_id})</span>
            </div>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-[11px] pt-1">
              <div>
                <span className="text-slate-400">Containment: </span>
                <span className="text-emerald-400 font-bold">
                  {latestOutcome.containment_success ? "SUCCESS (Threat Isolated)" : "PARTIAL"}
                </span>
              </div>
              <div>
                <span className="text-slate-400">Response Delay: </span>
                <span className="text-slate-200">{latestOutcome.response_delay_ms} ms</span>
              </div>
              <div>
                <span className="text-slate-400">Disruption Cost: </span>
                <span className="text-amber-400">{latestOutcome.operational_disruption_cost}</span>
              </div>
              <div>
                <span className="text-slate-400">Calculated Reward: </span>
                <span className="text-cyan-400 font-bold">+{latestOutcome.reward} pts</span>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
