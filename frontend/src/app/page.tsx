"use client";

import React from "react";
import { Header } from "@/components/Header";
import { Sidebar } from "@/components/Sidebar";
import { useSimulation } from "@/lib/simulationStore";
import { OverviewView } from "@/components/pages/OverviewView";
import { EventExplorerView } from "@/components/pages/EventExplorerView";
import { IncidentDetailView } from "@/components/pages/IncidentDetailView";
import { AdaptiveLabView } from "@/components/pages/AdaptiveLabView";
import { ExperimentsView } from "@/components/pages/ExperimentsView";
import { AuditLogView } from "@/components/pages/AuditLogView";
import { InspectEventModal } from "@/components/shared/InspectEventModal";

export default function Home() {
  const { activeTab } = useSimulation();

  return (
    <div className="min-h-screen bg-[#06090e] text-slate-100 flex flex-col cyber-grid">
      <Header />
      <div className="flex flex-1">
        <Sidebar />
        <main className="flex-1 overflow-y-auto">
          {activeTab === "overview" && <OverviewView />}
          {activeTab === "explorer" && <EventExplorerView />}
          {activeTab === "incident-detail" && <IncidentDetailView />}
          {activeTab === "adaptive-lab" && <AdaptiveLabView />}
          {activeTab === "experiments" && <ExperimentsView />}
          {activeTab === "audit" && <AuditLogView />}
        </main>
      </div>
      <InspectEventModal />
    </div>
  );
}
