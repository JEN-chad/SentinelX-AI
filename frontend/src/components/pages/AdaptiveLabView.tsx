"use client";

import React, { useState } from "react";
import {
  BrainCircuit,
  TrendingUp,
  Cpu,
  Zap,
  Play,
  RotateCcw,
  Sparkles,
  Layers,
  ShieldCheck,
  Scale,
} from "lucide-react";
import { BASELINE_COMPARISONS, RL_Q_TABLE_DATA } from "@/lib/mockData";

export function AdaptiveLabView() {
  const [qTable, setQTable] = useState(RL_Q_TABLE_DATA);
  const [episodeCount, setEpisodeCount] = useState(140);
  const [meanReward, setMeanReward] = useState(86.4);
  const [epsilon, setEpsilon] = useState(0.08); // Exploration rate
  const [isTraining, setIsTraining] = useState(false);

  // Train / Step Episode function updating Q-values and reward
  const handleTrainStep = (numEpisodes = 20) => {
    setIsTraining(true);
    setTimeout(() => {
      setEpisodeCount((prev) => prev + numEpisodes);
      setMeanReward((prev) => +(prev + 0.45 * Math.random()).toFixed(1));
      setEpsilon((prev) => Math.max(0.02, +(prev * 0.95).toFixed(3)));

      setQTable((prev) =>
        prev.map((row) => ({
          ...row,
          sim_block: row.best === "simulate_block" ? +(row.sim_block + 0.25).toFixed(1) : row.sim_block,
          escalate: row.best === "escalate_for_approval" ? +(row.escalate + 0.2).toFixed(1) : row.escalate,
        }))
      );
      setIsTraining(false);
    }, 300);
  };

  const handleReset = () => {
    setQTable(RL_Q_TABLE_DATA);
    setEpisodeCount(100);
    setMeanReward(82.0);
    setEpsilon(0.15);
  };

  return (
    <div className="space-y-5 p-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-2 border-b border-slate-800">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl font-bold font-mono tracking-tight text-slate-100">
              ADAPTIVE RESPONSE LAB (RL WORKBENCH)
            </h1>
            <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-purple-950 border border-purple-800 text-purple-300">
              TABULAR Q-LEARNING MDP
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-0.5 font-mono">
            Optimizing the trade-off between simulated threat containment and operational disruption.
          </p>
        </div>

        {/* Action Buttons */}
        <div className="flex items-center gap-2 font-mono text-xs">
          <button
            onClick={() => handleTrainStep(1)}
            disabled={isTraining}
            className="px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-700 text-slate-200 hover:bg-slate-800 flex items-center gap-1.5 transition-colors"
          >
            <Play className="w-3.5 h-3.5 text-cyan-400" />
            <span>Step 1 Episode</span>
          </button>
          <button
            onClick={() => handleTrainStep(50)}
            disabled={isTraining}
            className="px-3 py-1.5 rounded-lg bg-purple-950 hover:bg-purple-900 border border-purple-700 text-purple-200 font-bold flex items-center gap-1.5 transition-all shadow-md"
          >
            <Sparkles className="w-3.5 h-3.5 text-purple-400" />
            <span>Train 50 Episodes</span>
          </button>
          <button
            onClick={handleReset}
            className="p-1.5 rounded-lg bg-slate-900 border border-slate-800 text-slate-400 hover:text-white transition-colors"
            title="Reset Policy"
          >
            <RotateCcw className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* RL Training Metrics Bar */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="p-4 rounded-xl bg-[#0b1220] border border-slate-800 shadow">
          <span className="text-[10px] font-mono text-slate-400 uppercase">Simulated Episodes</span>
          <div className="text-2xl font-bold font-mono text-slate-100 mt-1">{episodeCount}</div>
          <span className="text-[10px] font-mono text-purple-400">Controlled Simulator</span>
        </div>

        <div className="p-4 rounded-xl bg-[#0b1220] border border-slate-800 shadow">
          <span className="text-[10px] font-mono text-slate-400 uppercase">Mean Cumulative Reward</span>
          <div className="text-2xl font-bold font-mono text-emerald-400 mt-1">+{meanReward}</div>
          <span className="text-[10px] font-mono text-slate-400">&gamma; = 0.95, &alpha; = 0.10</span>
        </div>

        <div className="p-4 rounded-xl bg-[#0b1220] border border-slate-800 shadow">
          <span className="text-[10px] font-mono text-slate-400 uppercase">Exploration Rate (&epsilon;)</span>
          <div className="text-2xl font-bold font-mono text-cyan-400 mt-1">{epsilon}</div>
          <span className="text-[10px] font-mono text-slate-400">Decaying &epsilon;-Greedy</span>
        </div>

        <div className="p-4 rounded-xl bg-[#0b1220] border border-slate-800 shadow">
          <span className="text-[10px] font-mono text-slate-400 uppercase">Objective Formulation</span>
          <div className="text-xs font-bold font-mono text-amber-300 mt-1 truncate">
            R = B_contain - C_disrupt
          </div>
          <span className="text-[10px] font-mono text-slate-400">Explicit penalty weights</span>
        </div>
      </div>

      {/* Tabular Q-Matrix Interactive Table */}
      <div className="p-5 rounded-xl bg-[#0b1220] border border-slate-800 shadow-xl space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <BrainCircuit className="w-4 h-4 text-purple-400" />
            <h2 className="text-sm font-bold font-mono tracking-wider text-slate-200 uppercase">
              Tabular Q-Matrix (State Discretization vs Action Value)
            </h2>
          </div>
          <span className="text-[11px] font-mono text-slate-400">
            Policy Version: <strong className="text-cyan-400">qtable-v1.02</strong>
          </span>
        </div>

        <div className="border border-slate-800 rounded-lg overflow-x-auto font-mono text-xs">
          <table className="w-full text-left">
            <thead className="bg-[#070d18] text-slate-400 text-[10px] uppercase border-b border-slate-800">
              <tr>
                <th className="px-4 py-3">Discretized State Bucket (Threat / Conf / Crit)</th>
                <th className="px-4 py-3">Q(s, raise_alert)</th>
                <th className="px-4 py-3">Q(s, increase_monitoring)</th>
                <th className="px-4 py-3">Q(s, escalate_for_approval)</th>
                <th className="px-4 py-3">Q(s, simulate_block)</th>
                <th className="px-4 py-3 text-right">Optimal Greedy Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/80 bg-[#090f1c]">
              {qTable.map((row, idx) => (
                <tr key={idx} className="hover:bg-slate-800/40 transition-colors">
                  <td className="px-4 py-3 font-medium text-slate-200">{row.state}</td>
                  <td className="px-4 py-3 text-slate-300">+{row.alert.toFixed(2)}</td>
                  <td className="px-4 py-3 text-slate-300">+{row.monitor.toFixed(2)}</td>
                  <td className="px-4 py-3 text-slate-300">+{row.escalate.toFixed(2)}</td>
                  <td className={`px-4 py-3 ${row.sim_block < 0 ? "text-rose-400" : "text-slate-300"}`}>
                    {row.sim_block > 0 ? `+${row.sim_block.toFixed(2)}` : row.sim_block.toFixed(2)}
                  </td>
                  <td className="px-4 py-3 text-right">
                    <span className="px-2.5 py-1 rounded text-[10px] font-bold bg-purple-950 text-purple-300 border border-purple-800">
                      {row.best}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Baseline Comparison Benchmark Table */}
      <div className="p-5 rounded-xl bg-[#0b1220] border border-slate-800 shadow-xl space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Scale className="w-4 h-4 text-cyan-400" />
            <h2 className="text-sm font-bold font-mono tracking-wider text-slate-200 uppercase">
              Baseline Comparison Benchmarks (1000 Simulated Test Episodes)
            </h2>
          </div>
          <span className="text-[11px] font-mono text-slate-400">
            Seeds: 42, 108, 999
          </span>
        </div>

        <div className="border border-slate-800 rounded-lg overflow-x-auto font-mono text-xs">
          <table className="w-full text-left">
            <thead className="bg-[#070d18] text-slate-400 text-[10px] uppercase border-b border-slate-800">
              <tr>
                <th className="px-4 py-3">Defensive Policy</th>
                <th className="px-4 py-3">Simulated Containment Rate</th>
                <th className="px-4 py-3">Unnecessary Action Rate</th>
                <th className="px-4 py-3">Disruption Cost Index</th>
                <th className="px-4 py-3 text-right">Mean Cumulative Reward</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/80 bg-[#090f1c]">
              {BASELINE_COMPARISONS.map((b, idx) => (
                <tr
                  key={idx}
                  className={`hover:bg-slate-800/40 transition-colors ${
                    idx === 0 ? "bg-purple-950/20 font-medium" : ""
                  }`}
                >
                  <td className="px-4 py-3 flex items-center gap-2 text-slate-200">
                    {idx === 0 && <Sparkles className="w-3.5 h-3.5 text-purple-400" />}
                    <span>{b.policy}</span>
                  </td>
                  <td className="px-4 py-3 text-emerald-400 font-bold">{b.containmentRate}%</td>
                  <td className="px-4 py-3 text-amber-400">{b.falseActionRate}%</td>
                  <td className="px-4 py-3 text-rose-300">{b.disruptionCost}</td>
                  <td className="px-4 py-3 text-right font-bold text-cyan-300">
                    {b.meanReward > 0 ? `+${b.meanReward}` : b.meanReward}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
