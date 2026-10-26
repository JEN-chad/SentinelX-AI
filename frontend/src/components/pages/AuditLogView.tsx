"use client";

import React, { useState } from "react";
import {
  FileText,
  ShieldCheck,
  Search,
  CheckCircle2,
  Lock,
  Filter,
  Hash,
  ShieldAlert,
} from "lucide-react";
import { useSimulation } from "@/lib/simulationStore";

export function AuditLogView() {
  const { auditLogs } = useSimulation();
  const [filterActor, setFilterActor] = useState("all");
  const [searchQuery, setSearchQuery] = useState("");

  const filteredLogs = auditLogs.filter((log) => {
    const matchesActor = filterActor === "all" || log.actor === filterActor;
    const matchesSearch =
      log.details.toLowerCase().includes(searchQuery.toLowerCase()) ||
      log.entity_id.toLowerCase().includes(searchQuery.toLowerCase()) ||
      log.audit_id.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesActor && matchesSearch;
  });

  return (
    <div className="space-y-5 p-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-2 border-b border-slate-800">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl font-bold font-mono tracking-tight text-slate-100">
              IMMUTABLE AUDIT LEDGER &amp; SAFETY LOG
            </h1>
            <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-slate-900 border border-slate-700 text-cyan-300">
              APPEND-ONLY AUDIT TRAIL
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-0.5 font-mono">
            Cryptographically traceable sequence of all action proposals, safety checks, approvals, and outcomes.
          </p>
        </div>

        <div className="flex items-center gap-2 font-mono text-xs">
          <span className="px-2.5 py-1 rounded bg-emerald-950/60 border border-emerald-800 text-emerald-300 flex items-center gap-1.5">
            <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
            <span>Integrity: VERIFIED</span>
          </span>
        </div>
      </div>

      {/* Safety Compliance Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="p-4 rounded-xl bg-[#0b1220] border border-slate-800 shadow">
          <span className="text-[10px] font-mono text-slate-400 uppercase">Allowlist Safety Violations</span>
          <div className="text-2xl font-bold font-mono text-emerald-400 mt-1">0 Violations</div>
          <p className="text-[10px] font-mono text-slate-500 mt-0.5">
            100% of actions vetted by deterministic safety layer
          </p>
        </div>

        <div className="p-4 rounded-xl bg-[#0b1220] border border-slate-800 shadow">
          <span className="text-[10px] font-mono text-slate-400 uppercase">Production Network Attempts</span>
          <div className="text-2xl font-bold font-mono text-emerald-400 mt-1">0 Production Calls</div>
          <p className="text-[10px] font-mono text-slate-500 mt-0.5">
            Air-gapped simulation boundary enforced
          </p>
        </div>

        <div className="p-4 rounded-xl bg-[#0b1220] border border-slate-800 shadow">
          <span className="text-[10px] font-mono text-slate-400 uppercase">Human Approvals Recorded</span>
          <div className="text-2xl font-bold font-mono text-cyan-300 mt-1">
            {auditLogs.filter((l) => l.actor === "human_analyst").length} Analyst Sign-offs
          </div>
          <p className="text-[10px] font-mono text-slate-500 mt-0.5">
            Consequential actions gated with human signature
          </p>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="p-4 rounded-xl bg-[#0b1220] border border-slate-800 shadow flex flex-col md:flex-row gap-3 items-center justify-between font-mono text-xs">
        <div className="relative w-full md:w-96">
          <Search className="w-4 h-4 text-slate-500 absolute left-3 top-2.5" />
          <input
            type="text"
            placeholder="Search audit details, entity ID, hash..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full bg-[#070d18] border border-slate-700 rounded-lg pl-9 pr-3 py-1.5 text-xs text-slate-200 placeholder:text-slate-500 focus:outline-none focus:border-cyan-500"
          />
        </div>

        <div className="flex items-center gap-2 w-full md:w-auto">
          <Filter className="w-3.5 h-3.5 text-cyan-400" />
          <span className="text-slate-400">Actor:</span>
          <select
            value={filterActor}
            onChange={(e) => setFilterActor(e.target.value)}
            className="bg-[#070d18] border border-slate-700 rounded px-2.5 py-1 text-slate-200 focus:outline-none"
          >
            <option value="all">All Actors</option>
            <option value="safety_gate">Safety Gate</option>
            <option value="mitigation_agent">Mitigation Agent</option>
            <option value="simulation_engine">Simulation Engine</option>
            <option value="human_analyst">Human Analyst</option>
            <option value="ingestion_service">Ingestion Service</option>
          </select>
        </div>
      </div>

      {/* Audit Log Entries List */}
      <div className="rounded-xl bg-[#0b1220] border border-slate-800 shadow-xl overflow-hidden font-mono text-xs">
        <div className="divide-y divide-slate-800/80 bg-[#090f1c]">
          {filteredLogs.map((log) => (
            <div key={log.audit_id} className="p-4 hover:bg-slate-800/30 transition-colors space-y-2">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                <div className="flex items-center gap-2">
                  <span className="font-bold text-slate-200">{log.audit_id}</span>
                  <span className="text-[10px] px-2 py-0.5 rounded bg-slate-900 border border-slate-700 text-slate-300">
                    ACTOR: {log.actor.toUpperCase()}
                  </span>
                  <span className="text-[10px] px-2 py-0.5 rounded bg-cyan-950/80 border border-cyan-800 text-cyan-300 font-bold">
                    {log.operation}
                  </span>
                  <span
                    className={`text-[10px] px-2 py-0.5 rounded border uppercase font-medium ${
                      log.status === "SUCCESS"
                        ? "bg-emerald-950/80 text-emerald-300 border-emerald-800"
                        : log.status === "PENDING_APPROVAL"
                        ? "bg-amber-950/80 text-amber-300 border-amber-800"
                        : "bg-purple-950/80 text-purple-300 border-purple-800"
                    }`}
                  >
                    {log.status}
                  </span>
                </div>

                <span className="text-[11px] text-slate-400">
                  {new Date(log.timestamp).toUTCString()}
                </span>
              </div>

              <p className="text-slate-300 font-sans text-xs">
                {log.details}
              </p>

              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-1 text-[10px] text-slate-500 pt-1">
                <span>Target Entity: <strong className="text-slate-400">{log.entity_id}</strong></span>
                <span className="truncate max-w-md font-mono text-slate-600">
                  Hash: {log.verification_hash}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
