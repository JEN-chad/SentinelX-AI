import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import { SimulationProvider } from "@/lib/simulationStore";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "SentinelX AI — Autonomous Multi-Agent Cyber Defense & RL Response",
  description:
    "Multi-Agentic AI Framework with Autonomous Reasoning and Reinforcement-Guided Adaptive Response for Cyber Threat Detection and Mitigation",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html
      lang="en"
      className={`${geistSans.variable} ${geistMono.variable} h-full dark`}
    >
      <body className="min-h-full bg-[#06090E] text-slate-100 antialiased selection:bg-cyan-500/20 selection:text-cyan-300">
        <SimulationProvider>{children}</SimulationProvider>
      </body>
    </html>
  );
}
