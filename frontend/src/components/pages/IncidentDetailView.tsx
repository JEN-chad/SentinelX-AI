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
} from "lucide-react";
import { useSimulation } from "@/lib/simulationStore";
import { ActionType, SimulationOutcome } from "@/lib/types";

export function IncidentDetailView() {
  const {
    incidents,
    selectedIncidentId,
    setSelectedIncidentId,
    approveIncidentAction,
    simulateIncidentResponse,
  } = useSimulation();

  const currentIncident =
    incidents.find((i) => i.incident_id === selectedIncidentId) || incidents[0];

  const [activeAgentTab, setActiveAgentTab] = useState<string>("detection");
  const [approvalNote, setApprovalNote] = useState<string>("");
  const [latestOutcome, setLatestOutcome] = useState<SimulationOutcome | null>(null);
  const [isExecutingSim, setIsExecutingSim] = useState(false);

  if (!currentIncident) {
    return (
      <div className="p-8 text-center text-slate-400 font-mono">
        No active incident selected.
      </div>
    );
  }

  const handleSimulate = async (action: ActionType) => {
    setIsExecutingSim(true);
    // Simulate brief network delay
    setTimeout(() => {
      const outcome = simulateIncidentResponse(currentIncident.incident_id, action);
      setLatestOutcome(outcome);
      setIsExecutingSim(false);
    }, 400);
  };

  const handleApprove = () => {
    approveIncidentAction(
      currentIncident.incident_id,
      approvalNote || "Security analyst approved simulated response block."
    );
  };

  return (
    <div className="space-y-5 p-6 max-w-7xl mx-auto">
      {/* Incident Switcher and Status Bar */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-2 border-b border-slate-800">
        <div>
          <div className="flex items-center gap-2">
            <span className="font-mono text-sm font-bold text-slate-100">
              INCIDENT TRIAGE & REASONING TRACE:
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
            {currentIncident.risk_score.toFixed(2)} / 1.00
          </div>
          <p className="text-[10px] font-mono text-slate-500 mt-1">
            Combines model confidence & asset criticality
          </p>
        </div>

        <div className="p-4 rounded-xl bg-[#0b1220] border border-slate-800">
          <span className="text-[10px] font-mono text-slate-400 uppercase">Target Asset</span>
          <div className="text-sm font-bold font-mono text-slate-200 mt-1 truncate">
            {currentIncident.target_asset || "192.168.10.5"}
          </div>
          <p className="text-[10px] font-mono text-slate-500 mt-1">
            Criticality: TIER 1 CORE GATEWAY
          </p>
        </div>

        <div className="p-4 rounded-xl bg-[#0b1220] border border-slate-800">
          <span className="text-[10px] font-mono text-slate-400 uppercase">MITRE ATT&amp;CK Mapping</span>
          <div className="text-sm font-bold font-mono text-amber-400 mt-1">
            {currentIncident.mitre_technique || "T1498.001 - Network DoS"}
          </div>
          <p className="text-[10px] font-mono text-slate-500 mt-1">
            Uncertainty Index: &plusmn;0.08
          </p>
        </div>

        <div className="p-4 rounded-xl bg-[#0b1220] border border-slate-800">
          <span className="text-[10px] font-mono text-slate-400 uppercase">Linked Evidence</span>
          <div className="text-sm font-bold font-mono text-cyan-400 mt-1">
            {currentIncident.event_ids.length} Correlated Flows
          </div>
          <p className="text-[10px] font-mono text-slate-500 mt-1">
            {currentIncident.evidence.length} Provenance References
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
            { id: "rl", label: "Agent E: RL Response Policy", icon: BrainCircuit },
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
          {activeAgentTab === "detection" && (
            <div className="space-y-4">
              <div className="p-4 rounded-lg bg-[#070d18] border border-slate-800 space-y-2">
                <div className="flex items-center justify-between text-cyan-300 font-semibold">
                  <span>Inference Engine Output: Random Forest Baseline v1.0</span>
                  <span className="text-slate-400 text-[11px]">Latency: 14.2ms</span>
                </div>
                <p className="text-slate-300 font-sans text-xs">
                  Model identified signature characteristics of Layer-7 Slowloris attack with 94.2% confidence. Ground truth label: <strong className="text-amber-400">DoS-Slowloris</strong>.
                </p>
              </div>

              {/* Top Explanatory Feature Importance */}
              <div className="space-y-2">
                <span className="text-slate-400 uppercase text-[10px] font-bold">
                  Top Contributing Model Features:
                </span>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                  <div className="p-3 rounded bg-slate-900 border border-slate-800">
                    <span className="text-slate-500 text-[10px]">flow_bytes_per_sec</span>
                    <div className="text-cyan-300 font-bold mt-0.5">14,820.5 B/s</div>
                    <span className="text-[10px] text-slate-400">Contribution: +38.4%</span>
                  </div>
                  <div className="p-3 rounded bg-slate-900 border border-slate-800">
                    <span className="text-slate-500 text-[10px]">fwd_packet_length_mean</span>
                    <div className="text-cyan-300 font-bold mt-0.5">42.0 Bytes</div>
                    <span className="text-[10px] text-slate-400">Contribution: +27.1%</span>
                  </div>
                  <div className="p-3 rounded bg-slate-900 border border-slate-800">
                    <span className="text-slate-500 text-[10px]">flow_duration</span>
                    <div className="text-cyan-300 font-bold mt-0.5">124,800 μs</div>
                    <span className="text-[10px] text-slate-400">Contribution: +18.5%</span>
                  </div>
                </div>
              </div>
            </div>
          )}

          {activeAgentTab === "investigation" && (
            <div className="space-y-4">
              <div className="p-4 rounded-lg bg-[#070d18] border border-slate-800 space-y-2">
                <div className="flex items-center justify-between text-blue-300 font-semibold">
                  <span>Correlation and Temporal Clustering</span>
                  <span className="text-slate-400 text-[11px]">Window: 6.1s</span>
                </div>
                <p className="text-slate-300 font-sans text-xs">
                  Agent correlated 3 separate flow records from source IP 192.168.10.50 targeting destination port 80. Repeated incomplete HTTP request headers indicate automated socket starvation.
                </p>
              </div>

              {/* Linked Evidence Chain */}
              <div className="space-y-2">
                <span className="text-slate-400 uppercase text-[10px] font-bold">
                  Evidence Traceability Chain:
                </span>
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
              </div>
            </div>
          )}

          {activeAgentTab === "risk" && (
            <div className="space-y-4">
              <div className="p-4 rounded-lg bg-[#070d18] border border-slate-800 space-y-2">
                <div className="text-amber-300 font-semibold">Impact Calculus &amp; Threat Prioritization</div>
                <p className="text-slate-300 font-sans text-xs">
                  Risk score 0.88 derived from High Attack Probability (0.94) &times; Critical Asset Weight (0.95) &minus; Containment Factor. Disruption to API gateway would affect 4 downstream microservices.
                </p>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div className="p-3 rounded bg-slate-900 border border-slate-800">
                  <span className="text-slate-500 text-[10px]">Service Disruption Likelihood</span>
                  <div className="text-rose-400 font-bold text-lg mt-0.5">85% Without Mitigation</div>
                </div>
                <div className="p-3 rounded bg-slate-900 border border-slate-800">
                  <span className="text-slate-500 text-[10px]">Calculated Exposure Window</span>
                  <div className="text-amber-400 font-bold text-lg mt-0.5">Immediate Triage Required</div>
                </div>
              </div>
            </div>
          )}

          {activeAgentTab === "mitigation" && (
            <div className="space-y-4">
              <div className="p-4 rounded-lg bg-[#070d18] border border-slate-800 space-y-2">
                <div className="text-emerald-300 font-semibold">Action Catalogue Recommendation</div>
                <p className="text-slate-300 font-sans text-xs">
                  Mitigation agent proposed candidate action: <strong className="text-emerald-400 font-mono">simulate_block</strong> against 192.168.10.50. Consequential action triggers human-in-the-loop approval gate.
                </p>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                <div className="p-3 rounded bg-slate-900 border border-slate-800">
                  <span className="text-slate-500 text-[10px]">Expected Containment Benefit</span>
                  <div className="text-emerald-400 font-bold text-lg mt-0.5">+92.0% Containment</div>
                </div>
                <div className="p-3 rounded bg-slate-900 border border-slate-800">
                  <span className="text-slate-500 text-[10px]">Operational Disruption Cost</span>
                  <div className="text-amber-400 font-bold text-lg mt-0.5">12.0 Disruption Penalty</div>
                </div>
                <div className="p-3 rounded bg-slate-900 border border-slate-800">
                  <span className="text-slate-500 text-[10px]">Reversibility State</span>
                  <div className="text-cyan-400 font-bold text-lg mt-0.5">Instant Rollback</div>
                </div>
              </div>
            </div>
          )}

          {activeAgentTab === "rl" && (
            <div className="space-y-4">
              <div className="p-4 rounded-lg bg-[#070d18] border border-slate-800 space-y-2">
                <div className="text-purple-300 font-semibold">Reinforcement Learning Policy State (MDP)</div>
                <p className="text-slate-300 font-sans text-xs">
                  Current policy: <strong>Q-Table v1.02</strong>. State discretized to [High Threat, High Confidence, High Criticality]. Highest expected cumulative reward selects <strong className="text-purple-300">simulate_block</strong>.
                </p>
              </div>

              <div className="p-3 rounded bg-slate-900 border border-slate-800 space-y-2">
                <div className="text-slate-400 text-[10px] font-bold uppercase">
                  Action Q-Values for Discretized State:
                </div>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
                  <div className="p-2 bg-slate-950 rounded border border-slate-800">
                    <span className="text-slate-500 text-[10px]">raise_alert</span>
                    <div className="text-slate-300 font-bold">Q: +1.20</div>
                  </div>
                  <div className="p-2 bg-slate-950 rounded border border-slate-800">
                    <span className="text-slate-500 text-[10px]">increase_monitoring</span>
                    <div className="text-slate-300 font-bold">Q: +4.80</div>
                  </div>
                  <div className="p-2 bg-slate-950 rounded border border-slate-800">
                    <span className="text-slate-500 text-[10px]">escalate_for_approval</span>
                    <div className="text-slate-300 font-bold">Q: +7.60</div>
                  </div>
                  <div className="p-2 bg-purple-950/60 rounded border border-purple-700">
                    <span className="text-purple-300 text-[10px] font-bold">simulate_block (BEST)</span>
                    <div className="text-purple-300 font-bold">Q: +9.40</div>
                  </div>
                </div>
              </div>
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
        {currentIncident.status === "response_proposed" && (
          <div className="p-4 rounded-lg bg-amber-950/20 border border-amber-700/40 space-y-3 font-mono text-xs">
            <div className="flex items-center gap-2 text-amber-300 font-bold">
              <Lock className="w-4 h-4 text-amber-400" />
              <span>Human Analyst Approval Gate Required for 'simulate_block'</span>
            </div>
            <p className="text-slate-300 font-sans text-xs">
              Consequential actions require human authorization before simulation execution. Real firewalls and production endpoints are never contacted.
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
            {currentIncident.allowed_actions.map((act) => (
              <button
                key={act}
                disabled={isExecutingSim}
                onClick={() => handleSimulate(act)}
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
                <span className="text-emerald-400 font-bold">SUCCESS (Threat Isolated)</span>
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
