"use client";

import React from "react";
import {
  LayoutDashboard,
  Binary,
  AlertTriangle,
  BrainCircuit,
  FlaskConical,
  FileText,
  ShieldCheck,
  CheckCircle,
  Network,
  Cpu,
} from "lucide-react";
import { NavTab, useSimulation } from "@/lib/simulationStore";

interface NavItem {
  id: NavTab;
  label: string;
  sublabel: string;
  icon: React.ElementType;
  badge?: string;
  badgeColor?: string;
}

export function Sidebar() {
  const { activeTab, setActiveTab, incidents } = useSimulation();

  const activeIncidentCount = incidents.filter(
    (i) => i.status !== "closed" && i.status !== "rejected"
  ).length;

  const navItems: NavItem[] = [
    {
      id: "overview",
      label: "Overview",
      sublabel: "Threat posture & telemetry",
      icon: LayoutDashboard,
    },
    {
      id: "explorer",
      label: "Event Explorer",
      sublabel: "Raw flow stream & features",
      icon: Binary,
      badge: "LIVE",
      badgeColor: "bg-emerald-950 text-emerald-400 border-emerald-800",
    },
    {
      id: "incident-detail",
      label: "Incident Triage",
      sublabel: "Multi-Agent reasoning trace",
      icon: AlertTriangle,
      badge: `${activeIncidentCount} Active`,
      badgeColor: "bg-rose-950 text-rose-300 border-rose-800",
    },
    {
      id: "adaptive-lab",
      label: "Adaptive Response Lab",
      sublabel: "Q-Learning & Baselines",
      icon: BrainCircuit,
      badge: "RL",
      badgeColor: "bg-purple-950 text-purple-300 border-purple-800",
    },
    {
      id: "experiments",
      label: "Experiments",
      sublabel: "Evaluation & Benchmarks",
      icon: FlaskConical,
    },
    {
      id: "audit",
      label: "Audit & Safety Log",
      sublabel: "Immutable decision ledger",
      icon: FileText,
      badge: "Verified",
      badgeColor: "bg-slate-800 text-slate-300 border-slate-700",
    },
  ];

  return (
    <aside className="w-64 border-r border-slate-800/80 bg-[#070b13] flex flex-col shrink-0 min-h-[calc(100vh-69px)] select-none">
      {/* Navigation Links */}
      <div className="p-3 space-y-1.5 flex-1">
        <div className="text-[10px] font-mono uppercase tracking-wider font-semibold text-slate-500 px-3 pt-2 pb-1">
          Operations Console
        </div>
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = activeTab === item.id;
          return (
            <button
              key={item.id}
              onClick={() => setActiveTab(item.id)}
              className={`w-full text-left px-3 py-2.5 rounded-lg flex items-center justify-between transition-all group ${
                isActive
                  ? "bg-cyan-950/40 border border-cyan-800/60 text-cyan-300 shadow-[0_0_15px_rgba(6,182,212,0.1)]"
                  : "text-slate-400 hover:text-slate-200 hover:bg-slate-900 border border-transparent"
              }`}
            >
              <div className="flex items-center gap-2.5">
                <Icon
                  className={`w-4 h-4 transition-colors ${
                    isActive ? "text-cyan-400" : "text-slate-500 group-hover:text-slate-300"
                  }`}
                />
                <div>
                  <div className={`text-xs font-medium font-sans ${isActive ? "text-slate-100 font-semibold" : ""}`}>
                    {item.label}
                  </div>
                  <div className="text-[10px] text-slate-500 font-mono tracking-tight leading-3">
                    {item.sublabel}
                  </div>
                </div>
              </div>
              {item.badge && (
                <span
                  className={`text-[9px] font-mono px-1.5 py-0.5 rounded border uppercase tracking-wider ${
                    item.badgeColor || "bg-slate-800 text-slate-300 border-slate-700"
                  }`}
                >
                  {item.badge}
                </span>
              )}
            </button>
          );
        })}
      </div>

      {/* Multi-Agent Subsystem Telemetry Status */}
      <div className="p-3 border-t border-slate-800/80 bg-[#06090e]/60 space-y-2">
        <div className="flex items-center justify-between text-[10px] font-mono uppercase tracking-wider text-slate-400 font-semibold">
          <span>Agent Pipeline</span>
          <span className="flex items-center gap-1 text-emerald-400">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 radar-dot"></span>
            SYNCED
          </span>
        </div>

        <div className="space-y-1.5 text-[11px] font-mono">
          <div className="flex items-center justify-between px-2 py-1 bg-slate-900/80 rounded border border-slate-800 text-slate-300">
            <span className="flex items-center gap-1.5 text-slate-400">
              <Cpu className="w-3 h-3 text-cyan-400" />
              <span>A. Detection</span>
            </span>
            <span className="text-[10px] text-cyan-400 font-medium">RF-v1.0 (94%)</span>
          </div>

          <div className="flex items-center justify-between px-2 py-1 bg-slate-900/80 rounded border border-slate-800 text-slate-300">
            <span className="flex items-center gap-1.5 text-slate-400">
              <Network className="w-3 h-3 text-blue-400" />
              <span>B. Investigation</span>
            </span>
            <span className="text-[10px] text-blue-400 font-medium">Clustering</span>
          </div>

          <div className="flex items-center justify-between px-2 py-1 bg-slate-900/80 rounded border border-slate-800 text-slate-300">
            <span className="flex items-center gap-1.5 text-slate-400">
              <AlertTriangle className="w-3 h-3 text-amber-400" />
              <span>C. Risk Assessment</span>
            </span>
            <span className="text-[10px] text-amber-400 font-medium">MITRE ATT&CK</span>
          </div>

          <div className="flex items-center justify-between px-2 py-1 bg-slate-900/80 rounded border border-slate-800 text-slate-300">
            <span className="flex items-center gap-1.5 text-slate-400">
              <ShieldCheck className="w-3 h-3 text-emerald-400" />
              <span>D. Mitigation Plan</span>
            </span>
            <span className="text-[10px] text-emerald-400 font-medium">Catalogue OK</span>
          </div>

          <div className="flex items-center justify-between px-2 py-1 bg-slate-900/80 rounded border border-slate-800 text-slate-300">
            <span className="flex items-center gap-1.5 text-slate-400">
              <BrainCircuit className="w-3 h-3 text-purple-400" />
              <span>E. RL Policy</span>
            </span>
            <span className="text-[10px] text-purple-400 font-medium">Q-Table v1.02</span>
          </div>
        </div>

        {/* Safety Gate status banner */}
        <div className="mt-2 p-2 rounded bg-cyan-950/30 border border-cyan-800/40 text-[10px] font-mono text-cyan-300">
          <div className="flex items-center gap-1 font-semibold text-cyan-200">
            <CheckCircle className="w-3 h-3 text-cyan-400" />
            <span>DETERMINISTIC SAFETY GATE</span>
          </div>
          <div className="text-slate-400 mt-0.5">
            Production Actions: <span className="text-rose-400 font-bold">BLOCKED</span>
          </div>
        </div>
      </div>
    </aside>
  );
}
