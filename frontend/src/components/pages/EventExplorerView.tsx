"use client";

import React, { useState } from "react";
import {
  Binary,
  Search,
  Filter,
  Eye,
  ArrowRight,
  Database,
  Radio,
  Clock,
  RotateCcw,
} from "lucide-react";
import { useSimulation } from "@/lib/simulationStore";
import { NormalizedEvent } from "@/lib/types";

export function EventExplorerView() {
  const { events, setInspectedEvent, isStreaming, toggleStreaming } = useSimulation();

  const [searchQuery, setSearchQuery] = useState("");
  const [filterType, setFilterType] = useState<string>("all");
  const [filterSeverity, setFilterSeverity] = useState<string>("all");

  const filteredEvents = events.filter((evt) => {
    // Search query matches
    const matchesSearch =
      evt.event_id.toLowerCase().includes(searchQuery.toLowerCase()) ||
      evt.source_asset.toLowerCase().includes(searchQuery.toLowerCase()) ||
      evt.target_asset.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (evt.predicted_class || "").toLowerCase().includes(searchQuery.toLowerCase()) ||
      (evt.raw_label || "").toLowerCase().includes(searchQuery.toLowerCase());

    // Type filter
    const matchesType =
      filterType === "all" ||
      (filterType === "anomalous" && (evt.anomaly_score ?? 0) > 0.6) ||
      (filterType === "benign" && (evt.anomaly_score ?? 0) <= 0.6);

    // Label filter
    const matchesLabel =
      filterSeverity === "all" ||
      evt.predicted_class?.toLowerCase().includes(filterSeverity.toLowerCase());

    return matchesSearch && matchesType && matchesLabel;
  });

  return (
    <div className="space-y-5 p-6 max-w-7xl mx-auto">
      {/* Page Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-2 border-b border-slate-800">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl font-bold font-mono tracking-tight text-slate-100">
              EVENT EXPLORER & FLOW STREAM
            </h1>
            <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-emerald-950 border border-emerald-800 text-emerald-300 flex items-center gap-1.5">
              <span className={`w-1.5 h-1.5 rounded-full ${isStreaming ? "bg-emerald-400 radar-dot" : "bg-amber-400"}`}></span>
              {isStreaming ? "REPLAY INGESTING" : "PAUSED"}
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-0.5 font-mono">
            High-density network flow records, feature extractions, and model inference scores.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={toggleStreaming}
            className="px-3 py-1.5 rounded bg-slate-900 border border-slate-700 text-xs font-mono text-slate-300 hover:text-white"
          >
            {isStreaming ? "Pause Ingest" : "Resume Ingest"}
          </button>
        </div>
      </div>

      {/* Search and Filters Bar */}
      <div className="p-4 rounded-xl bg-[#0b1220] border border-slate-800 shadow-lg flex flex-col md:flex-row gap-3 items-center justify-between">
        <div className="relative w-full md:w-96">
          <Search className="w-4 h-4 text-slate-500 absolute left-3 top-2.5" />
          <input
            type="text"
            placeholder="Filter by Event ID, IP, or Label..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full bg-[#070d18] border border-slate-700 rounded-lg pl-9 pr-3 py-1.5 text-xs font-mono text-slate-200 placeholder:text-slate-500 focus:outline-none focus:border-cyan-500"
          />
        </div>

        <div className="flex items-center gap-3 w-full md:w-auto">
          <div className="flex items-center gap-1 text-xs font-mono text-slate-400">
            <Filter className="w-3.5 h-3.5 text-cyan-400" />
            <span>Class:</span>
            <select
              value={filterType}
              onChange={(e) => setFilterType(e.target.value)}
              className="bg-[#070d18] border border-slate-700 rounded px-2 py-1 text-xs font-mono text-slate-200 focus:outline-none"
            >
              <option value="all">All Events</option>
              <option value="anomalous">Anomalous Only (&gt;0.6)</option>
              <option value="benign">Benign Only</option>
            </select>
          </div>

          <div className="flex items-center gap-1 text-xs font-mono text-slate-400">
            <span>Label:</span>
            <select
              value={filterSeverity}
              onChange={(e) => setFilterSeverity(e.target.value)}
              className="bg-[#070d18] border border-slate-700 rounded px-2 py-1 text-xs font-mono text-slate-200 focus:outline-none"
            >
              <option value="all">All Attack Classes</option>
              <option value="slowloris">DoS-Slowloris</option>
              <option value="portscan">PortScan</option>
              <option value="benign">BENIGN</option>
            </select>
          </div>

          {(searchQuery || filterType !== "all" || filterSeverity !== "all") && (
            <button
              onClick={() => {
                setSearchQuery("");
                setFilterType("all");
                setFilterSeverity("all");
              }}
              className="p-1.5 rounded hover:bg-slate-800 text-slate-400 hover:text-slate-200 text-xs font-mono flex items-center gap-1"
              title="Reset Filters"
            >
              <RotateCcw className="w-3.5 h-3.5" />
            </button>
          )}
        </div>
      </div>

      {/* Events Stream Table */}
      <div className="rounded-xl bg-[#0b1220] border border-slate-800 shadow-xl overflow-hidden font-mono text-xs">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead className="bg-[#070d18] text-slate-400 text-[10px] uppercase border-b border-slate-800 tracking-wider">
              <tr>
                <th className="px-4 py-3">Event ID</th>
                <th className="px-4 py-3">Timestamp (UTC)</th>
                <th className="px-4 py-3">Network Path (Src &rarr; Dst)</th>
                <th className="px-4 py-3">Predicted Class</th>
                <th className="px-4 py-3">Anomaly Score</th>
                <th className="px-4 py-3">Ground Truth</th>
                <th className="px-4 py-3 text-right">Inspection</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/80 bg-[#090f1c]">
              {filteredEvents.length === 0 ? (
                <tr>
                  <td colSpan={7} className="px-4 py-8 text-center text-slate-500">
                    No network flows match the selected filter criteria.
                  </td>
                </tr>
              ) : (
                filteredEvents.map((evt) => {
                  const isHighRisk = (evt.anomaly_score ?? 0) > 0.6;
                  return (
                    <tr
                      key={evt.event_id}
                      className="hover:bg-slate-800/40 transition-colors group cursor-pointer"
                      onClick={() => setInspectedEvent(evt)}
                    >
                      <td className="px-4 py-2.5 font-bold text-slate-200 flex items-center gap-1.5">
                        <Binary className="w-3.5 h-3.5 text-cyan-400" />
                        <span>{evt.event_id}</span>
                      </td>

                      <td className="px-4 py-2.5 text-slate-400 text-[11px]">
                        {new Date(evt.event_time).toLocaleTimeString()}
                      </td>

                      <td className="px-4 py-2.5">
                        <div className="flex items-center gap-1.5 text-slate-300">
                          <span className={isHighRisk ? "text-rose-300 font-medium" : "text-slate-300"}>
                            {evt.source_asset}
                          </span>
                          <ArrowRight className="w-3 h-3 text-slate-600" />
                          <span className="text-slate-400">{evt.target_asset}</span>
                        </div>
                      </td>

                      <td className="px-4 py-2.5">
                        <span
                          className={`px-2 py-0.5 rounded text-[10px] font-semibold border ${
                            isHighRisk
                              ? "bg-rose-950/80 text-rose-300 border-rose-800"
                              : "bg-emerald-950/80 text-emerald-300 border-emerald-800"
                          }`}
                        >
                          {evt.predicted_class || "BENIGN"}
                        </span>
                      </td>

                      <td className="px-4 py-2.5">
                        <div className="flex items-center gap-2">
                          <div className="w-16 h-1.5 bg-slate-800 rounded-full overflow-hidden">
                            <div
                              className={`h-full ${
                                isHighRisk ? "bg-rose-500" : "bg-emerald-400"
                              }`}
                              style={{ width: `${Math.round((evt.anomaly_score ?? 0) * 100)}%` }}
                            ></div>
                          </div>
                          <span
                            className={
                              isHighRisk ? "text-rose-400 font-bold" : "text-emerald-400"
                            }
                          >
                            {(evt.anomaly_score ?? 0).toFixed(2)}
                          </span>
                        </div>
                      </td>

                      <td className="px-4 py-2.5">
                        <span className="text-amber-400/90 text-[11px]">
                          {evt.raw_label || "UNLABELED"}
                        </span>
                      </td>

                      <td className="px-4 py-2.5 text-right">
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            setInspectedEvent(evt);
                          }}
                          className="px-2 py-1 rounded bg-slate-800 hover:bg-slate-700 text-cyan-300 hover:text-cyan-200 transition-colors inline-flex items-center gap-1 text-[11px]"
                        >
                          <Eye className="w-3 h-3" />
                          <span>Inspect</span>
                        </button>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>

        {/* Table footer */}
        <div className="px-4 py-2.5 border-t border-slate-800 bg-[#070d18] text-[11px] text-slate-400 flex items-center justify-between">
          <span>Showing {filteredEvents.length} events in active buffer</span>
          <span>Buffer capacity: 80 events (FIFO window)</span>
        </div>
      </div>
    </div>
  );
}
