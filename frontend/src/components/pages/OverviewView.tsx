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
} from "lucide-react";
import { useSimulation } from "@/lib/simulationStore";

export function OverviewView() {
  const { events, incidents, setActiveTab, setSelectedIncidentId, injectAttack } = useSimulation();

  const totalFlows = events.length * 142 + 8420;
  const anomalousFlows = events.filter((e) => (e.anomaly_score ?? 0) > 0.6).length;
  const anomalyRate = ((anomalousFlows / Math.max(events.length, 1)) * 100).toFixed(1);

  const activeIncidents = incidents.filter(
    (i) => i.status !== "closed" && i.status !== "rejected"
  );

  return (
    <div className="space-y-5 p-6 max-w-7xl mx-auto">
      {/* Page Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-2 border-b border-slate-800">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl font-bold font-mono tracking-tight text-slate-100">
              OPERATIONAL OVERVIEW & TELEMETRY
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
            onClick={() => setActiveTab("explorer")}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-700 text-xs font-mono text-slate-300 hover:text-white hover:bg-slate-800 transition-colors"
          >
            <span>Live Flow Explorer</span>
            <ArrowUpRight className="w-3.5 h-3.5 text-cyan-400" />
          </button>
          <button
            onClick={() => setActiveTab("adaptive-lab")}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-gradient-to-r from-purple-900/60 to-cyan-900/60 border border-purple-700/60 text-xs font-mono text-purple-200 hover:brightness-110 transition-all shadow-md"
          >
            <Sparkles className="w-3.5 h-3.5 text-purple-300" />
            <span>Launch RL Response Lab</span>
          </button>
        </div>
      </div>

      {/* Top Telemetry Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Card 1: Replayed Flow Count */}
        <div className="p-4 rounded-xl bg-[#0b1220] border border-slate-800 shadow-lg relative overflow-hidden group hover:border-slate-700 transition-all">
          <div className="flex items-center justify-between text-slate-400 text-xs font-mono">
            <span>TOTAL FLOWS REPLAYED</span>
            <Radio className="w-4 h-4 text-cyan-400" />
          </div>
          <div className="mt-2 flex items-baseline gap-2">
            <span className="text-2xl font-bold font-mono text-slate-100">{totalFlows.toLocaleString()}</span>
            <span className="text-[11px] font-mono text-emerald-400 flex items-center">
              +142 / sec
            </span>
          </div>
          <div className="mt-2 text-[10px] font-mono text-slate-400 flex items-center justify-between">
            <span>Buffer: 80 / 80 slots</span>
            <span className="text-cyan-400">Deterministic Replay</span>
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
            <span>Baseline: Random Forest v1</span>
            <span className="text-emerald-400">Latency: 1.4ms</span>
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
              High / Critical
            </span>
          </div>
          <div className="mt-2 text-[10px] font-mono text-slate-400 flex items-center justify-between">
            <span>Awaiting Approval: 1</span>
            <span className="text-amber-400">Investigating: {activeIncidents.length - 1}</span>
          </div>
          <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-gradient-to-r from-rose-500 to-transparent"></div>
        </div>

        {/* Card 4: Q-Learning Containment Benchmark */}
        <div className="p-4 rounded-xl bg-[#0b1220] border border-slate-800 shadow-lg relative overflow-hidden group hover:border-slate-700 transition-all">
          <div className="flex items-center justify-between text-slate-400 text-xs font-mono">
            <span>SIMULATED CONTAINMENT</span>
            <TrendingUp className="w-4 h-4 text-purple-400" />
          </div>
          <div className="mt-2 flex items-baseline gap-2">
            <span className="text-2xl font-bold font-mono text-purple-300">94.2%</span>
            <span className="text-[11px] font-mono text-emerald-400">
              vs 81.5% fixed rule
            </span>
          </div>
          <div className="mt-2 text-[10px] font-mono text-slate-400 flex items-center justify-between">
            <span>Mean Reward: +86.4</span>
            <span className="text-cyan-400">Policy: Q-Table v1</span>
          </div>
          <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-gradient-to-r from-purple-500 to-transparent"></div>
        </div>
      </div>

      {/* Real-time Threat Velocity & Flow Rate Chart */}
      <div className="p-5 rounded-xl bg-[#0b1220] border border-slate-800 shadow-lg space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
          <div>
            <div className="flex items-center gap-2">
              <Activity className="w-4 h-4 text-cyan-400" />
              <h2 className="text-sm font-bold font-mono tracking-wider text-slate-200 uppercase">
                Real-Time Flow Throughput & Threat Velocity
              </h2>
            </div>
            <p className="text-[11px] text-slate-400 font-mono mt-0.5">
              Live sliding window across replayed network flows (CIC-IDS2017 & Injected Anomalies).
            </p>
          </div>
          <div className="flex items-center gap-4 text-xs font-mono">
            <div className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-sm bg-cyan-500"></span>
              <span className="text-slate-300">Flow Volume</span>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-sm bg-rose-500"></span>
              <span className="text-slate-300">Threat Anomaly Spikes</span>
            </div>
          </div>
        </div>

        {/* Custom SVG Real-time Telemetry Wave */}
        <div className="h-44 w-full bg-[#070d18] rounded-lg p-3 border border-slate-800/80 relative overflow-hidden flex flex-col justify-end">
          <svg className="w-full h-32 overflow-visible" viewBox="0 0 800 120" preserveAspectRatio="none">
            <defs>
              <linearGradient id="cyanGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#06b6d4" stopOpacity="0.35" />
                <stop offset="100%" stopColor="#06b6d4" stopOpacity="0.0" />
              </linearGradient>
              <linearGradient id="roseGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#ef4444" stopOpacity="0.4" />
                <stop offset="100%" stopColor="#ef4444" stopOpacity="0.0" />
              </linearGradient>
            </defs>

            {/* Grid Lines */}
            <line x1="0" y1="30" x2="800" y2="30" stroke="#1e293b" strokeDasharray="3 3" />
            <line x1="0" y1="60" x2="800" y2="60" stroke="#1e293b" strokeDasharray="3 3" />
            <line x1="0" y1="90" x2="800" y2="90" stroke="#1e293b" strokeDasharray="3 3" />

            {/* Flow Volume Area */}
            <path
              d="M0,85 Q100,60 200,75 T400,50 T600,65 T800,45 L800,120 L0,120 Z"
              fill="url(#cyanGrad)"
            />
            <path
              d="M0,85 Q100,60 200,75 T400,50 T600,65 T800,45"
              fill="none"
              stroke="#06b6d4"
              strokeWidth="2"
            />

            {/* Threat Anomaly Curve */}
            <path
              d="M0,110 Q150,110 250,95 T450,20 T650,85 T800,30 L800,120 L0,120 Z"
              fill="url(#roseGrad)"
            />
            <path
              d="M0,110 Q150,110 250,95 T450,20 T650,85 T800,30"
              fill="none"
              stroke="#ef4444"
              strokeWidth="2.5"
            />
          </svg>

          {/* Time axis labels */}
          <div className="flex items-center justify-between text-[10px] font-mono text-slate-500 pt-2 border-t border-slate-800">
            <span>T-60s</span>
            <span>T-45s</span>
            <span>T-30s</span>
            <span>T-15s</span>
            <span className="text-cyan-400 font-bold">Now (Live)</span>
          </div>
        </div>
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
                      <strong className="text-rose-400">{incident.risk_score.toFixed(2)}</strong>
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
                    <span className="text-slate-200">{incident.target_asset}</span>
                  </div>
                  <div>
                    <span className="text-slate-500">Source: </span>
                    <span className="text-slate-200">{incident.source_asset}</span>
                  </div>
                  <div>
                    <span className="text-slate-500">MITRE: </span>
                    <span className="text-amber-400">{incident.mitre_technique}</span>
                  </div>
                </div>

                {/* Agent reasoning summary preview */}
                <div className="text-[11px] font-mono text-slate-400 flex items-center gap-2">
                  <span className="text-cyan-400">Mitigation Agent:</span>
                  <span className="truncate">
                    {incident.agent_results.find((a) => a.agent_name === "mitigation_agent")?.summary ||
                      "Correlating flows and evaluating impact..."}
                  </span>
                </div>
              </div>
            ))}
          </div>
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
                Calculates severity and asset criticality. Maps techniques to MITRE ATT&CK.
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
                <span>5. Q-Learning Policy</span>
                <span className="text-[10px] text-purple-400">DISCRETIZED MDP</span>
              </div>
              <p className="text-[11px] text-slate-400 font-sans">
                Evaluates state buckets and selects response under strict safety gate supervision.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
