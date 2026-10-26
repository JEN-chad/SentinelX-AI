"use client";

import React, { useEffect, useState } from "react";
import {
  ShieldAlert,
  Play,
  Pause,
  Zap,
  Activity,
  Radio,
  Clock,
  Flame,
  Search,
  CheckCircle2,
} from "lucide-react";
import { useSimulation } from "@/lib/simulationStore";

export function Header() {
  const {
    isStreaming,
    streamSpeed,
    toggleStreaming,
    setStreamSpeed,
    injectAttack,
  } = useSimulation();

  const [utcTime, setUtcTime] = useState<string>("");
  const [injectOpen, setInjectOpen] = useState(false);

  useEffect(() => {
    const update = () => {
      const now = new Date();
      setUtcTime(now.toUTCString().replace("GMT", "UTC"));
    };
    update();
    const interval = setInterval(update, 1000);
    return () => clearInterval(interval);
  }, []);

  return (
    <header className="border-b border-slate-800 bg-[#090D16]/95 backdrop-blur-md sticky top-0 z-40 px-4 py-2.5">
      {/* Top Warning Banner: Mandatory Safety Constraint */}
      <div className="flex items-center justify-between text-[11px] font-mono tracking-wide px-3 py-1 bg-amber-500/10 border border-amber-500/25 rounded text-amber-300 mb-2.5">
        <div className="flex items-center gap-2">
          <ShieldAlert className="w-3.5 h-3.5 text-amber-400 shrink-0" />
          <span>
            <strong className="font-semibold text-amber-200">SAFETY BOUNDARY ENFORCED:</strong> Offline Replay & Controlled Simulation Mode. Production firewall & endpoint integrations are strictly disabled.
          </span>
        </div>
        <div className="flex items-center gap-3 shrink-0">
          <span className="text-slate-400">Dataset: <span className="text-slate-200 font-medium">CIC-IDS2017</span></span>
          <span className="text-slate-400">Target: <span className="text-slate-200 font-medium">Local Simulator (Virtual DMZ)</span></span>
        </div>
      </div>

      <div className="flex items-center justify-between">
        {/* Brand identity */}
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-cyan-500/20 to-blue-600/30 border border-cyan-500/40 flex items-center justify-center text-cyan-400 shadow-[0_0_15px_rgba(6,182,212,0.2)]">
            <Radio className="w-5 h-5 text-cyan-400 animate-pulse" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-bold text-base tracking-wider text-slate-100 font-mono">SENTINEL<span className="text-cyan-400">X</span> AI</span>
              <span className="px-1.5 py-0.2 text-[10px] font-mono bg-cyan-950/80 text-cyan-400 border border-cyan-800 rounded">B.Tech Research</span>
              <span className="px-1.5 py-0.2 text-[10px] font-mono bg-emerald-950/80 text-emerald-400 border border-emerald-800 rounded flex items-center gap-1">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-ping"></span>
                SIM ACTIVE
              </span>
            </div>
            <p className="text-[11px] text-slate-400 tracking-tight">Autonomous Multi-Agent Triage & RL-Guided Response Selection</p>
          </div>
        </div>

        {/* Real-time Replay Controls */}
        <div className="flex items-center gap-3">
          {/* Simulation Ticker State */}
          <div className="flex items-center gap-2 px-2.5 py-1.5 rounded-md bg-slate-900/90 border border-slate-800 text-xs font-mono">
            <span className={`w-2 h-2 rounded-full ${isStreaming ? "bg-emerald-400 radar-dot" : "bg-amber-400"}`}></span>
            <span className={isStreaming ? "text-emerald-300 font-medium" : "text-amber-300 font-medium"}>
              {isStreaming ? "STREAMING" : "PAUSED"}
            </span>
            <div className="h-3 w-px bg-slate-700 mx-1"></div>
            {/* Speed multipliers */}
            <div className="flex items-center gap-1">
              {[1, 2, 5].map((speed) => (
                <button
                  key={speed}
                  onClick={() => setStreamSpeed(speed)}
                  className={`px-1.5 py-0.5 rounded text-[10px] font-mono transition-colors ${
                    streamSpeed === speed
                      ? "bg-cyan-500/30 text-cyan-300 font-bold border border-cyan-500/50"
                      : "text-slate-400 hover:text-slate-200 hover:bg-slate-800"
                  }`}
                >
                  {speed}x
                </button>
              ))}
            </div>
          </div>

          {/* Pause / Resume button */}
          <button
            onClick={toggleStreaming}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-mono transition-all border ${
              isStreaming
                ? "bg-slate-900 border-slate-700 text-slate-300 hover:bg-slate-800"
                : "bg-emerald-500/20 border-emerald-500/40 text-emerald-300 hover:bg-emerald-500/30"
            }`}
          >
            {isStreaming ? (
              <>
                <Pause className="w-3.5 h-3.5 text-amber-400" />
                <span>Pause Replay</span>
              </>
            ) : (
              <>
                <Play className="w-3.5 h-3.5 text-emerald-400" />
                <span>Resume Replay</span>
              </>
            )}
          </button>

          {/* Attack Vector Injector Dropdown */}
          <div className="relative">
            <button
              onClick={() => setInjectOpen(!injectOpen)}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-mono bg-rose-950/40 border border-rose-800/60 text-rose-300 hover:bg-rose-900/40 transition-colors"
            >
              <Flame className="w-3.5 h-3.5 text-rose-400" />
              <span>Simulate Attack Burst</span>
            </button>

            {injectOpen && (
              <div className="absolute right-0 mt-2 w-64 bg-[#0d1424] border border-slate-700 rounded-lg shadow-2xl py-1 z-50 text-xs font-mono">
                <div className="px-3 py-1.5 text-[10px] text-slate-400 uppercase tracking-wider font-semibold border-b border-slate-800">
                  Select Attack Pattern
                </div>
                <button
                  onClick={() => {
                    injectAttack("slowloris");
                    setInjectOpen(false);
                  }}
                  className="w-full text-left px-3 py-2 hover:bg-slate-800 flex items-center justify-between text-slate-200"
                >
                  <div>
                    <div className="font-medium text-rose-300">DoS-Slowloris</div>
                    <div className="text-[10px] text-slate-400">Socket starvation HTTP flood</div>
                  </div>
                  <span className="text-[10px] bg-rose-950 text-rose-400 px-1.5 py-0.5 rounded border border-rose-800">L7 Flood</span>
                </button>
                <button
                  onClick={() => {
                    injectAttack("portscan");
                    setInjectOpen(false);
                  }}
                  className="w-full text-left px-3 py-2 hover:bg-slate-800 flex items-center justify-between text-slate-200"
                >
                  <div>
                    <div className="font-medium text-amber-300">SYN Port Scan</div>
                    <div className="text-[10px] text-slate-400">Reconnaissance sweep (1000 ports)</div>
                  </div>
                  <span className="text-[10px] bg-amber-950 text-amber-400 px-1.5 py-0.5 rounded border border-amber-800">Recon</span>
                </button>
                <button
                  onClick={() => {
                    injectAttack("exfiltration");
                    setInjectOpen(false);
                  }}
                  className="w-full text-left px-3 py-2 hover:bg-slate-800 flex items-center justify-between text-slate-200"
                >
                  <div>
                    <div className="font-medium text-purple-300">Data Exfiltration</div>
                    <div className="text-[10px] text-slate-400">Encrypted egress anomaly</div>
                  </div>
                  <span className="text-[10px] bg-purple-950 text-purple-400 px-1.5 py-0.5 rounded border border-purple-800">Egress</span>
                </button>
              </div>
            )}
          </div>

          {/* Clock */}
          <div className="hidden lg:flex items-center gap-1.5 px-2.5 py-1 rounded bg-slate-900 border border-slate-800 text-[11px] font-mono text-slate-400">
            <Clock className="w-3.5 h-3.5 text-cyan-400" />
            <span>{utcTime || "2026-10-14 04:12:00 UTC"}</span>
          </div>
        </div>
      </div>
    </header>
  );
}
