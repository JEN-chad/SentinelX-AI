"use client";

import React from "react";
import {
  ShieldAlert,
  Activity,
  Zap,
  Radio,
  Cpu,
  Layers,
  ArrowUpRight,
  TrendingUp,
  AlertOctagon,
  Clock,
  Sparkles,
  Play,
  CheckCircle2,
  AlertCircle,
} from "lucide-react";
import { useSimulation } from "@/lib/simulationStore";

export function OverviewView() {
  const {
    events,
    incidents,
    setActiveTab,
    setSelectedIncidentId,
    triggerReplay,
    isLoading,
    backendConnected,
  } = useSimulation();

  const totalFlows = events.length;
  const anomalousFlows = events.filter(
    (e) => (e.raw_label && e.raw_label !== "BENIGN") || (e.anomaly_score ?? 0) > 0.5
  ).length;
  const anomalyRate = totalFlows > 0 ? ((anomalousFlows / totalFlows) * 100).toFixed(1) : "0.0";

  const activeIncidents = incidents.filter(
    (i) => i.status !== "closed" && i.status !== "rejected"
  );
  const awaitingApproval = incidents.filter((i) => i.status === "approval_required").length;
  const investigatingCount = incidents.filter(
    (i) => i.status === "investigating" || i.status === "scored"
  ).length;
  const simulatedCount = incidents.filter(
    (i) => i.status === "outcome_recorded" || i.status === "closed"
  ).length;

  return (
    <div className="space-y-5 p-6 max-w-7xl mx-auto">
      {/* Backend Status Banner */}
      {!backendConnected && (
        <div className="p-3 rounded-lg bg-rose-950/40 border border-rose-800 text-rose-300 font-mono text-xs flex items-center justify-between">
          <div className="flex items-center gap-2">
            <AlertCircle className="w-4 h-4 text-rose-400 shrink-0" />
            <span>
              <strong>Backend Disconnected:</strong> Ensure FastAPI server is running on{" "}
              <code>http://127.0.0.1:8000</code>.
            </span>
          </div>
          <span className="text-[11px] text-slate-400">Offline Fallback</span>
        </div>
      )}

      {/* Page Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-2 border-b border-slate-800">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl font-bold font-mono tracking-tight text-slate-100">
              OPERATIONAL OVERVIEW &amp; TELEMETRY
            </h1>
            <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-cyan-950 border border-cyan-800 text-cyan-300">
              OFFLINE REPLAY
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-0.5 font-mono">
            Autonomous threat detection, agentic reasoning pipeline, and reinforcement response metrics.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => triggerReplay(25)}
            disabled={isLoading}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-emerald-950 hover:bg-emerald-900 border border-emerald-700 text-xs font-mono text-emerald-200 transition-colors shadow-sm disabled:opacity-50"
          >
            <Play className="w-3.5 h-3.5 text-emerald-400" />
            <span>{isLoading ? "Streaming..." : "Replay 25 Flows"}</span>
          </button>
          <button
            onClick={() => setActiveTab("explorer")}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-700 text-xs font-mono text-slate-300 hover:text-white hover:bg-slate-800 transition-colors"
          >
            <span>Live Flow Explorer</span>
            <ArrowUpRight className="w-3.5 h-3.5 text-cyan-400" />
          </button>
        </div>
      </div>

      {/* Top Telemetry Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Card 1: Replayed Flow Count */}
        <div className="p-4 rounded-xl bg-[#0b1220] border border-slate-800 shadow-lg relative overflow-hidden group hover:border-slate-700 transition-all">
          <div className="flex items-center justify-between text-slate-400 text-xs font-mono">
            <span>DATABASE FLOWS</span>
            <Radio className="w-4 h-4 text-cyan-400" />
          </div>
          <div className="mt-2 flex items-baseline gap-2">
            <span className="text-2xl font-bold font-mono text-slate-100">{totalFlows}</span>
            <span className="text-[11px] font-mono text-cyan-400">
              replayed records
            </span>
          </div>
          <div className="mt-2 text-[10px] font-mono text-slate-400 flex items-center justify-between">
            <span>Dataset: CIC-IDS2017</span>
            <span className="text-emerald-400">{backendConnected ? "Live Ingest" : "Standby"}</span>
          </div>
          <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-gradient-to-r from-cyan-500 to-transparent"></div>
        </div>

        {/* Card 2: Anomaly Scoring Velocity */}
        <div className="p-4 rounded-xl bg-[#0b1220] border border-slate-800 shadow-lg relative overflow-hidden group hover:border-slate-700 transition-all">
          <div className="flex items-center justify-between text-slate-400 text-xs font-mono">
            <span>ANOMALY DETECTION RATE</span>
            <Activity className="w-4 h-4 text-amber-400" />
          </div>
          <div className="mt-2 flex items-baseline gap-2">
            <span className="text-2xl font-bold font-mono text-amber-300">{anomalyRate}%</span>
            <span className="text-[11px] font-mono text-slate-400">
              ({anomalousFlows} anomalous)
            </span>
          </div>
          <div className="mt-2 text-[10px] font-mono text-slate-400 flex items-center justify-between">
            <span>Model: Random Forest v1</span>
            <span className="text-emerald-400">Calibrated: Yes</span>
          </div>
          <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-gradient-to-r from-amber-500 to-transparent"></div>
        </div>

        {/* Card 3: Active Incidents Under Triage */}
        <div className="p-4 rounded-xl bg-[#0b1220] border border-slate-800 shadow-lg relative overflow-hidden group hover:border-slate-700 transition-all">
          <div className="flex items-center justify-between text-slate-400 text-xs font-mono">
            <span>ACTIVE INCIDENTS</span>
            <AlertOctagon className="w-4 h-4 text-rose-400" />
          </div>
          <div className="mt-2 flex items-baseline gap-2">
            <span className="text-2xl font-bold font-mono text-rose-400">{activeIncidents.length}</span>
            <span className="text-[11px] font-mono text-rose-300">
              Under Triage
            </span>
          </div>
          <div className="mt-2 text-[10px] font-mono text-slate-400 flex items-center justify-between">
            <span>Awaiting Approval: {awaitingApproval}</span>
            <span className="text-amber-400">Investigating: {investigatingCount}</span>
          </div>
          <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-gradient-to-r from-rose-500 to-transparent"></div>
        </div>

        {/* Card 4: Mitigated Incidents */}
        <div className="p-4 rounded-xl bg-[#0b1220] border border-slate-800 shadow-lg relative overflow-hidden group hover:border-slate-700 transition-all">
          <div className="flex items-center justify-between text-slate-400 text-xs font-mono">
            <span>SIMULATED MITIGATIONS</span>
            <TrendingUp className="w-4 h-4 text-purple-400" />
          </div>
          <div className="mt-2 flex items-baseline gap-2">
            <span className="text-2xl font-bold font-mono text-purple-300">{simulatedCount}</span>
            <span className="text-[11px] font-mono text-emerald-400">
              outcomes recorded
            </span>
          </div>
          <div className="mt-2 text-[10px] font-mono text-slate-400 flex items-center justify-between">
            <span>Safety Gate: Permitted</span>
            <span className="text-cyan-400">Virtual Sandbox</span>
          </div>
          <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-gradient-to-r from-purple-500 to-transparent"></div>
        </div>
      </div>

      {/* Real-time Flow Throughput & Ingested Flow Timeline */}
      <div className="p-5 rounded-xl bg-[#0b1220] border border-slate-800 shadow-lg space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
          <div>
            <div className="flex items-center gap-2">
              <Activity className="w-4 h-4 text-cyan-400" />
              <h2 className="text-sm font-bold font-mono tracking-wider text-slate-200 uppercase">
                Network Flow Distribution by Source &amp; Label
              </h2>
            </div>
            <p className="text-[11px] text-slate-400 font-mono mt-0.5">
              Live records persisted from offline replay dataset (CIC-IDS2017).
            </p>
          </div>
          <div className="flex items-center gap-4 text-xs font-mono">
            <div className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-sm bg-cyan-500"></span>
              <span className="text-slate-300">BENIGN Flows</span>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-sm bg-rose-500"></span>
              <span className="text-slate-300">Attacks (Slowloris/PortScan)</span>
            </div>
          </div>
        </div>

        {/* Dynamic Event Stream Preview Bars */}
        {events.length === 0 ? (
          <div className="h-32 rounded-lg bg-[#070d18] border border-slate-800 flex flex-col items-center justify-center text-center p-4">
            <Radio className="w-6 h-6 text-slate-600 mb-1 animate-pulse" />
            <p className="text-xs text-slate-400 font-mono">
              No network flows in database yet.
            </p>
            <button
              onClick={() => triggerReplay(25)}
              className="mt-2 px-3 py-1 bg-cyan-950 text-cyan-300 hover:bg-cyan-900 border border-cyan-800 rounded text-xs font-mono"
            >
              Start Replay Now
            </button>
          </div>
        ) : (
          <div className="space-y-2">
            <div className="grid grid-cols-12 gap-1 h-14 p-2 bg-[#070d18] rounded-lg border border-slate-800 items-end">
              {events.slice(0, 24).map((evt, idx) => {
                const isAttack = evt.raw_label && evt.raw_label !== "BENIGN";
                const heightPct = isAttack ? 95 : 30 + (idx % 4) * 12;
                return (
                  <div
                    key={evt.event_id || idx}
                    className="flex flex-col items-center h-full justify-end group relative"
                  >
                    <div
                      style={{ height: `${heightPct}%` }}
                      className={`w-full rounded-sm transition-all ${
                        isAttack
                          ? "bg-rose-500 hover:bg-rose-400"
                          : "bg-cyan-600/70 hover:bg-cyan-500"
                      }`}
                    ></div>
                    {/* Hover tooltip */}
                    <div className="absolute bottom-full mb-1 hidden group-hover:block z-20 bg-slate-900 border border-slate-700 text-[10px] font-mono text-slate-200 px-2 py-1 rounded shadow-lg whitespace-nowrap">
                      {evt.event_id} ({evt.raw_label || "FLOW"})
                    </div>
                  </div>
                );
              })}
            </div>
            <div className="flex items-center justify-between text-[10px] font-mono text-slate-500 px-1">
              <span>Oldest in buffer</span>
              <span>Showing last {Math.min(events.length, 24)} flows</span>
              <span className="text-cyan-400 font-bold">Latest Ingested</span>
            </div>
          </div>
        )}
      </div>

      {/* Two Column Grid: Active Incidents & Multi-Agent Architecture Trace */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
        {/* Left Column (2 cols): Active Incident Triage Feed */}
        <div className="lg:col-span-2 p-5 rounded-xl bg-[#0b1220] border border-slate-800 shadow-lg space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <AlertOctagon className="w-4 h-4 text-rose-400" />
              <h2 className="text-sm font-bold font-mono tracking-wider text-slate-200 uppercase">
                Active Incidents Requiring Evaluation
              </h2>
            </div>
            <span className="text-[11px] font-mono text-slate-400">
              Showing {activeIncidents.length} active
            </span>
          </div>

          {activeIncidents.length === 0 ? (
            <div className="p-8 rounded-lg bg-[#070d18] border border-slate-800 text-center font-mono text-xs text-slate-400 space-y-2">
              <CheckCircle2 className="w-8 h-8 text-emerald-400 mx-auto" />
              <div className="text-slate-200 font-bold">No Active Threats or Incidents</div>
              <p className="text-slate-400 text-[11px] max-w-md mx-auto">
                Replay flows from the sample dataset containing attack patterns to trigger the Detection Agent.
              </p>
              <button
                onClick={() => triggerReplay(25)}
                className="mt-2 px-3 py-1.5 bg-emerald-950 text-emerald-300 border border-emerald-800 rounded hover:bg-emerald-900"
              >
                Replay Attack Flows
              </button>
            </div>
          ) : (
            <div className="space-y-3">
              {activeIncidents.map((incident) => (
                <div
                  key={incident.incident_id}
                  className="p-4 rounded-lg bg-[#070d18] border border-slate-800 hover:border-slate-700 transition-all space-y-3"
                >
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-xs font-bold text-slate-100">
                        {incident.incident_id}
                      </span>
                      <span
                        className={`text-[10px] font-mono px-2 py-0.5 rounded border uppercase font-medium ${
                          incident.severity === "critical"
                            ? "bg-rose-950 text-rose-300 border-rose-800"
                            : incident.severity === "high"
                            ? "bg-orange-950 text-orange-300 border-orange-800"
                            : "bg-amber-950 text-amber-300 border-amber-800"
                        }`}
                      >
                        {incident.severity}
                      </span>
                      <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700">
                        STATUS: {incident.status.toUpperCase()}
                      </span>
                    </div>

                    <div className="flex items-center gap-2">
                      <span className="text-[11px] font-mono text-slate-400">
                        Risk Score:{" "}
                        <strong className="text-rose-400">
                          {incident.risk_score?.toFixed(2) ?? "N/A"}
                        </strong>
                      </span>
                      <button
                        onClick={() => {
                          setSelectedIncidentId(incident.incident_id);
                          setActiveTab("incident-detail");
                        }}
                        className="px-2.5 py-1 text-xs font-mono rounded bg-cyan-950 text-cyan-300 hover:bg-cyan-900 border border-cyan-800 flex items-center gap-1 transition-colors"
                      >
                        <span>Investigate</span>
                        <ArrowUpRight className="w-3 h-3" />
                      </button>
                    </div>
                  </div>

                  <div className="text-xs text-slate-300 font-sans font-medium">
                    {incident.title}
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 text-[11px] font-mono text-slate-400 bg-slate-900/60 p-2 rounded border border-slate-800/80">
                    <div>
                      <span className="text-slate-500">Target Asset: </span>
                      <span className="text-slate-200">{incident.target_asset || "N/A"}</span>
                    </div>
                    <div>
                      <span className="text-slate-500">Source: </span>
                      <span className="text-slate-200">{incident.source_asset || "N/A"}</span>
                    </div>
                    <div>
                      <span className="text-slate-500">MITRE: </span>
                      <span className="text-amber-400">{incident.mitre_technique || "Pending"}</span>
                    </div>
                  </div>

                  {/* Agent reasoning summary preview */}
                  <div className="text-[11px] font-mono text-slate-400 flex items-center gap-2">
                    <span className="text-cyan-400">Trace:</span>
                    <span className="truncate">
                      {incident.agent_results && incident.agent_results.length > 0
                        ? incident.agent_results[incident.agent_results.length - 1].summary
                        : "Detection created. Ready for multi-agent reasoning."}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Right Column (1 col): Multi-Agent Architecture Lifecycle */}
        <div className="p-5 rounded-xl bg-[#0b1220] border border-slate-800 shadow-lg space-y-4">
          <div className="flex items-center gap-2">
            <Layers className="w-4 h-4 text-cyan-400" />
            <h2 className="text-sm font-bold font-mono tracking-wider text-slate-200 uppercase">
              Agentic Pipeline Trace
            </h2>
          </div>
          <p className="text-[11px] text-slate-400 font-mono">
            Separation of concerns between detection, investigation, risk, and response policy.
          </p>

          <div className="space-y-3 font-mono text-xs">
            <div className="p-3 rounded-lg bg-slate-900/90 border border-slate-800 space-y-1">
              <div className="flex items-center justify-between text-cyan-300 font-semibold">
                <span>1. Detection Agent</span>
                <span className="text-[10px] text-emerald-400">ACTIVE</span>
              </div>
              <p className="text-[11px] text-slate-400 font-sans">
                Consumes model inference and anomaly scores. Binds event provenance references.
              </p>
            </div>

            <div className="p-3 rounded-lg bg-slate-900/90 border border-slate-800 space-y-1">
              <div className="flex items-center justify-between text-blue-300 font-semibold">
                <span>2. Investigation Agent</span>
                <span className="text-[10px] text-emerald-400">ACTIVE</span>
              </div>
              <p className="text-[11px] text-slate-400 font-sans">
                Clusters related events by source/target and builds timeline sequences.
              </p>
            </div>

            <div className="p-3 rounded-lg bg-slate-900/90 border border-slate-800 space-y-1">
              <div className="flex items-center justify-between text-amber-300 font-semibold">
                <span>3. Risk Assessment Agent</span>
                <span className="text-[10px] text-emerald-400">ACTIVE</span>
              </div>
              <p className="text-[11px] text-slate-400 font-sans">
                Calculates severity and asset criticality. Maps techniques to MITRE ATT&amp;CK.
              </p>
            </div>

            <div className="p-3 rounded-lg bg-slate-900/90 border border-slate-800 space-y-1">
              <div className="flex items-center justify-between text-emerald-300 font-semibold">
                <span>4. Mitigation Planning Agent</span>
                <span className="text-[10px] text-emerald-400">ACTIVE</span>
              </div>
              <p className="text-[11px] text-slate-400 font-sans">
                Restricted to fixed action catalogue. Estimates disruption vs containment cost.
              </p>
            </div>

            <div className="p-3 rounded-lg bg-slate-900/90 border border-slate-800 space-y-1">
              <div className="flex items-center justify-between text-purple-300 font-semibold">
                <span>5. Deterministic Safety Gate</span>
                <span className="text-[10px] text-purple-400">SIMULATION ONLY</span>
              </div>
              <p className="text-[11px] text-slate-400 font-sans">
                Blocks unauthorized actions. Mandates human analyst approval for containment.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
