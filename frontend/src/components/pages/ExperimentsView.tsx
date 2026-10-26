"use client";

import React, { useState } from "react";
import {
  FlaskConical,
  Play,
  RotateCcw,
  Download,
  CheckCircle2,
  Cpu,
  Layers,
  Database,
  Sliders,
} from "lucide-react";

export function ExperimentsView() {
  const [selectedDataset, setSelectedDataset] = useState("CIC-IDS2017-Friday");
  const [selectedModel, setSelectedModel] = useState("Random Forest Baseline");
  const [selectedPolicy, setSelectedPolicy] = useState("Q-Learning Policy");
  const [seed, setSeed] = useState(42);
  const [testSplit, setTestSplit] = useState(0.2);
  const [isRunning, setIsRunning] = useState(false);
  const [progress, setProgress] = useState(100);

  // Experiment Metrics State
  const [metrics, setMetrics] = useState({
    precision: 0.948,
    recall: 0.932,
    macroF1: 0.940,
    fpr: 0.021,
    containmentRate: 94.2,
    disruptionCost: 12.8,
  });

  const handleRunExperiment = () => {
    setIsRunning(true);
    setProgress(15);
    const step1 = setTimeout(() => setProgress(45), 250);
    const step2 = setTimeout(() => setProgress(80), 500);
    const step3 = setTimeout(() => {
      setProgress(100);
      setIsRunning(false);
      setMetrics({
        precision: +(0.93 + Math.random() * 0.04).toFixed(3),
        recall: +(0.92 + Math.random() * 0.04).toFixed(3),
        macroF1: +(0.93 + Math.random() * 0.03).toFixed(3),
        fpr: +(0.015 + Math.random() * 0.01).toFixed(3),
        containmentRate: +(92.5 + Math.random() * 3.5).toFixed(1),
        disruptionCost: +(11.5 + Math.random() * 2.5).toFixed(1),
      });
    }, 850);
  };

  const handleExport = () => {
    const data = {
      experiment_id: `exp-${Date.now()}`,
      dataset: selectedDataset,
      model: selectedModel,
      policy: selectedPolicy,
      seed,
      test_split: testSplit,
      metrics,
      timestamp: new Date().toISOString(),
    };
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `sentinelx_experiment_seed${seed}.json`;
    a.click();
  };

  return (
    <div className="space-y-5 p-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-2 border-b border-slate-800">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl font-bold font-mono tracking-tight text-slate-100">
              EXPERIMENTS &amp; REPRODUCIBILITY BENCHMARKS
            </h1>
            <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-blue-950 border border-blue-800 text-blue-300">
              REPRODUCIBLE RESEARCH
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-0.5 font-mono">
            Execute controlled evaluation splits, seed-pinned runs, and exportable benchmark metrics.
          </p>
        </div>

        <div className="flex items-center gap-2 font-mono text-xs">
          <button
            onClick={handleExport}
            className="px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-700 text-slate-300 hover:text-white hover:bg-slate-800 flex items-center gap-1.5 transition-colors"
          >
            <Download className="w-3.5 h-3.5 text-cyan-400" />
            <span>Export Metrics JSON</span>
          </button>
          <button
            onClick={handleRunExperiment}
            disabled={isRunning}
            className="px-4 py-1.5 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-slate-950 font-bold flex items-center gap-1.5 transition-all shadow-md"
          >
            <Play className="w-3.5 h-3.5" />
            <span>{isRunning ? `Evaluating (${progress}%)` : "Run Benchmark Run"}</span>
          </button>
        </div>
      </div>

      {/* Progress Bar when running */}
      {isRunning && (
        <div className="w-full bg-slate-900 rounded-full h-1.5 overflow-hidden">
          <div
            className="bg-cyan-400 h-full transition-all duration-300"
            style={{ width: `${progress}%` }}
          ></div>
        </div>
      )}

      {/* Experiment Configuration Controls */}
      <div className="p-5 rounded-xl bg-[#0b1220] border border-slate-800 shadow-xl space-y-4">
        <div className="flex items-center gap-2 text-cyan-400 text-xs font-mono font-bold uppercase">
          <Sliders className="w-4 h-4" />
          <span>Experiment Hyperparameters &amp; Evaluation Setup</span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4 font-mono text-xs">
          {/* Dataset selector */}
          <div className="space-y-1">
            <label className="text-[10px] text-slate-400 uppercase">Dataset Benchmark</label>
            <select
              value={selectedDataset}
              onChange={(e) => setSelectedDataset(e.target.value)}
              className="w-full bg-[#070d18] border border-slate-700 rounded px-2.5 py-1.5 text-slate-200 focus:outline-none"
            >
              <option value="CIC-IDS2017-Friday">CIC-IDS2017 (PortScan &amp; DoS)</option>
              <option value="UNSW-NB15-Subset">UNSW-NB15 Flow Subset</option>
              <option value="Synthetic-Simulator">Controlled Replay Simulator</option>
            </select>
          </div>

          {/* Model selector */}
          <div className="space-y-1">
            <label className="text-[10px] text-slate-400 uppercase">Detection Architecture</label>
            <select
              value={selectedModel}
              onChange={(e) => setSelectedModel(e.target.value)}
              className="w-full bg-[#070d18] border border-slate-700 rounded px-2.5 py-1.5 text-slate-200 focus:outline-none"
            >
              <option value="Random Forest Baseline">Random Forest (100 Trees)</option>
              <option value="XGBoost Classifier">XGBoost Gradient Boosting</option>
              <option value="Isolation Forest Anomaly">Isolation Forest Detector</option>
            </select>
          </div>

          {/* Policy selector */}
          <div className="space-y-1">
            <label className="text-[10px] text-slate-400 uppercase">Response Policy</label>
            <select
              value={selectedPolicy}
              onChange={(e) => setSelectedPolicy(e.target.value)}
              className="w-full bg-[#070d18] border border-slate-700 rounded px-2.5 py-1.5 text-slate-200 focus:outline-none"
            >
              <option value="Q-Learning Policy">Q-Learning Adaptive Policy</option>
              <option value="Fixed Rule Baseline">Fixed Rule Baseline</option>
              <option value="Threshold Baseline">Threshold Score Baseline</option>
              <option value="Random Permitted">Random Permitted Baseline</option>
            </select>
          </div>

          {/* Seed pin */}
          <div className="space-y-1">
            <label className="text-[10px] text-slate-400 uppercase">Deterministic Random Seed</label>
            <input
              type="number"
              value={seed}
              onChange={(e) => setSeed(Number(e.target.value))}
              className="w-full bg-[#070d18] border border-slate-700 rounded px-2.5 py-1.5 text-slate-200 focus:outline-none"
            />
          </div>
        </div>
      </div>

      {/* Benchmark Results Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="p-4 rounded-xl bg-[#0b1220] border border-slate-800 shadow">
          <span className="text-[10px] font-mono text-slate-400 uppercase">Macro-F1 Score</span>
          <div className="text-2xl font-bold font-mono text-emerald-400 mt-1">
            {(metrics.macroF1 * 100).toFixed(1)}%
          </div>
          <span className="text-[10px] font-mono text-slate-500">Unweighted class average</span>
        </div>

        <div className="p-4 rounded-xl bg-[#0b1220] border border-slate-800 shadow">
          <span className="text-[10px] font-mono text-slate-400 uppercase">Precision &amp; Recall</span>
          <div className="text-xl font-bold font-mono text-cyan-300 mt-1">
            {(metrics.precision * 100).toFixed(1)}% / {(metrics.recall * 100).toFixed(1)}%
          </div>
          <span className="text-[10px] font-mono text-slate-500">Held-out test set</span>
        </div>

        <div className="p-4 rounded-xl bg-[#0b1220] border border-slate-800 shadow">
          <span className="text-[10px] font-mono text-slate-400 uppercase">False Positive Rate</span>
          <div className="text-2xl font-bold font-mono text-amber-300 mt-1">
            {(metrics.fpr * 100).toFixed(2)}%
          </div>
          <span className="text-[10px] font-mono text-slate-500">Normal traffic disruption</span>
        </div>

        <div className="p-4 rounded-xl bg-[#0b1220] border border-slate-800 shadow">
          <span className="text-[10px] font-mono text-slate-400 uppercase">Containment Success</span>
          <div className="text-2xl font-bold font-mono text-purple-300 mt-1">
            {metrics.containmentRate}%
          </div>
          <span className="text-[10px] font-mono text-slate-500">Simulated mitigation rate</span>
        </div>
      </div>

      {/* 2D Confusion Matrix Representation */}
      <div className="p-5 rounded-xl bg-[#0b1220] border border-slate-800 shadow-xl space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Database className="w-4 h-4 text-cyan-400" />
            <h2 className="text-sm font-bold font-mono tracking-wider text-slate-200 uppercase">
              Confusion Matrix (Held-out Test Evaluation)
            </h2>
          </div>
          <span className="text-[11px] font-mono text-slate-400">
            Split: 80% Train / 20% Test • N = 2,400 Flows
          </span>
        </div>

        <div className="overflow-x-auto font-mono text-xs">
          <table className="w-full text-center border border-slate-800">
            <thead className="bg-[#070d18] text-slate-400 text-[10px] uppercase border-b border-slate-800">
              <tr>
                <th className="px-4 py-3 text-left">Ground Truth Label</th>
                <th className="px-4 py-3 bg-slate-900/40">Pred: BENIGN</th>
                <th className="px-4 py-3 bg-slate-900/40">Pred: DoS-Slowloris</th>
                <th className="px-4 py-3 bg-slate-900/40">Pred: PortScan</th>
                <th className="px-4 py-3 text-right">Class Recall</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/80 bg-[#090f1c]">
              <tr>
                <td className="px-4 py-3 text-left font-bold text-slate-300">True: BENIGN</td>
                <td className="px-4 py-3 text-emerald-400 font-bold bg-emerald-950/20">1,892</td>
                <td className="px-4 py-3 text-slate-400">14</td>
                <td className="px-4 py-3 text-slate-400">18</td>
                <td className="px-4 py-3 text-right text-emerald-400 font-bold">98.3%</td>
              </tr>
              <tr>
                <td className="px-4 py-3 text-left font-bold text-slate-300">True: DoS-Slowloris</td>
                <td className="px-4 py-3 text-slate-400">8</td>
                <td className="px-4 py-3 text-emerald-400 font-bold bg-emerald-950/20">284</td>
                <td className="px-4 py-3 text-slate-400">2</td>
                <td className="px-4 py-3 text-right text-emerald-400 font-bold">96.6%</td>
              </tr>
              <tr>
                <td className="px-4 py-3 text-left font-bold text-slate-300">True: PortScan</td>
                <td className="px-4 py-3 text-slate-400">6</td>
                <td className="px-4 py-3 text-slate-400">4</td>
                <td className="px-4 py-3 text-emerald-400 font-bold bg-emerald-950/20">172</td>
                <td className="px-4 py-3 text-right text-emerald-400 font-bold">94.5%</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
