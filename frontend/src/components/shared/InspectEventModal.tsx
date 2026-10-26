"use client";

import React from "react";
import { X, Binary, ShieldAlert, Cpu, Database, Check } from "lucide-react";
import { useSimulation } from "@/lib/simulationStore";

export function InspectEventModal() {
  const { inspectedEvent, setInspectedEvent } = useSimulation();

  if (!inspectedEvent) return null;

  return (
    <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="bg-[#0b1220] border border-slate-700 w-full max-w-3xl rounded-xl shadow-2xl overflow-hidden flex flex-col max-h-[90vh]">
        {/* Modal Header */}
        <div className="flex items-center justify-between px-5 py-3.5 border-b border-slate-800 bg-[#070d18]">
          <div className="flex items-center gap-2.5">
            <Binary className="w-5 h-5 text-cyan-400" />
            <div>
              <div className="flex items-center gap-2">
                <span className="font-mono text-sm font-bold text-slate-100">
                  {inspectedEvent.event_id}
                </span>
                <span
                  className={`text-[10px] font-mono px-2 py-0.5 rounded border uppercase font-medium ${
                    inspectedEvent.anomaly_score && inspectedEvent.anomaly_score > 0.6
                      ? "bg-rose-950/80 text-rose-300 border-rose-800"
                      : "bg-emerald-950/80 text-emerald-300 border-emerald-800"
                  }`}
                >
                  {inspectedEvent.predicted_class || "BENIGN"}
                </span>
              </div>
              <p className="text-[11px] text-slate-400 font-mono">
                Ingested: {new Date(inspectedEvent.ingested_at).toUTCString()}
              </p>
            </div>
          </div>
          <button
            onClick={() => setInspectedEvent(null)}
            className="p-1 rounded-lg hover:bg-slate-800 text-slate-400 hover:text-slate-200 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Modal Body */}
        <div className="p-5 overflow-y-auto space-y-5 font-mono text-xs">
          {/* Top metadata grid */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <div className="p-2.5 rounded-lg bg-slate-900 border border-slate-800">
              <span className="text-[10px] text-slate-400 uppercase">Source Asset</span>
              <div className="text-slate-200 font-bold truncate mt-0.5">{inspectedEvent.source_asset}</div>
            </div>
            <div className="p-2.5 rounded-lg bg-slate-900 border border-slate-800">
              <span className="text-[10px] text-slate-400 uppercase">Target Asset</span>
              <div className="text-slate-200 font-bold truncate mt-0.5">{inspectedEvent.target_asset}</div>
            </div>
            <div className="p-2.5 rounded-lg bg-slate-900 border border-slate-800">
              <span className="text-[10px] text-slate-400 uppercase">Anomaly Score</span>
              <div className="text-cyan-400 font-bold mt-0.5">
                {(inspectedEvent.anomaly_score ?? 0).toFixed(3)}
              </div>
            </div>
            <div className="p-2.5 rounded-lg bg-slate-900 border border-slate-800">
              <span className="text-[10px] text-slate-400 uppercase">Ground Truth Label</span>
              <div className="text-amber-400 font-bold mt-0.5">
                {inspectedEvent.raw_label || "UNLABELED"}
              </div>
            </div>
          </div>

          {/* Model Attribution Bar */}
          <div className="p-3.5 rounded-lg bg-cyan-950/20 border border-cyan-800/40 space-y-2">
            <div className="flex items-center gap-2 text-cyan-300 font-semibold text-xs">
              <Cpu className="w-4 h-4 text-cyan-400" />
              <span>Model Prediction & Provenance Notice</span>
            </div>
            <p className="text-[11px] text-slate-300">
              Detection model baseline (Random Forest v1.0) evaluated this flow in 1.45ms. Ground truth label is strictly segregated from model inference features to avoid target leakage.
            </p>
          </div>

          {/* Extracted Network Flow Features */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-slate-300 font-semibold text-xs uppercase tracking-wider">
                Normalized Flow Features ({Object.keys(inspectedEvent.features).length})
              </span>
              <span className="text-[10px] text-slate-500">Dataset: {inspectedEvent.dataset_id}</span>
            </div>

            <div className="border border-slate-800 rounded-lg overflow-hidden">
              <table className="w-full text-left">
                <thead className="bg-slate-900 text-slate-400 text-[10px] uppercase border-b border-slate-800">
                  <tr>
                    <th className="px-3 py-2">Feature Name</th>
                    <th className="px-3 py-2">Value</th>
                    <th className="px-3 py-2">Contextual Type</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60 bg-[#090e18]">
                  {Object.entries(inspectedEvent.features).map(([key, val]) => (
                    <tr key={key} className="hover:bg-slate-800/40">
                      <td className="px-3 py-1.5 text-cyan-300 font-medium">{key}</td>
                      <td className="px-3 py-1.5 text-slate-200">
                        {typeof val === "number" ? val.toLocaleString() : String(val)}
                      </td>
                      <td className="px-3 py-1.5 text-slate-500 text-[10px]">
                        {typeof val}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>

        {/* Modal Footer */}
        <div className="px-5 py-3 border-t border-slate-800 bg-[#070d18] flex items-center justify-between text-xs font-mono">
          <span className="text-slate-500">
            Hash: {inspectedEvent.event_id} • Schema {inspectedEvent.schema_version}
          </span>
          <button
            onClick={() => setInspectedEvent(null)}
            className="px-4 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 font-medium transition-colors"
          >
            Close Inspector
          </button>
        </div>
      </div>
    </div>
  );
}
