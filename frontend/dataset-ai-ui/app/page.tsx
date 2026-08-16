"use client";

import { useRef, useState } from "react";
import GalaxyBackground from "@/components/GalaxyBackground";
import Navbar from "@/components/Navbar";
import SearchBox from "@/components/SearchBox";
import AgentFlow, { type AgentStage } from "@/components/AgentFlow";
import LoadingAnimation from "@/components/LoadingAnimation";
import ExplanationCard from "@/components/ExplanationCard";
import DatasetCard from "@/components/DatasetCard";
import { discover, ApiError, type DiscoverResponse } from "@/services/api";

const STAGE_SEQUENCE: AgentStage[] = ["nlp", "discovery", "evaluation"];
const STAGE_STEP_MS = 700;

export default function Home() {
  const [loading, setLoading] = useState(false);
  const [stage, setStage] = useState<AgentStage>("idle");
  const [result, setResult] = useState<DiscoverResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const stageTimer = useRef<ReturnType<typeof setInterval> | null>(null);

  const hasActivity = loading || result !== null || error !== null;

  async function handleSearch(query: string) {
    setLoading(true);
    setError(null);
    setResult(null);

    let stepIndex = 0;
    setStage(STAGE_SEQUENCE[0]);
    stageTimer.current = setInterval(() => {
      stepIndex = Math.min(stepIndex + 1, STAGE_SEQUENCE.length - 1);
      setStage(STAGE_SEQUENCE[stepIndex]);
    }, STAGE_STEP_MS);

    try {
      const response = await discover(query, 6);
      setResult(response);
      setStage("done");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not reach the backend. Is it running on :8000?");
      setStage("idle");
    } finally {
      if (stageTimer.current) clearInterval(stageTimer.current);
      setLoading(false);
    }
  }

  return (
    <div className="relative flex min-h-screen flex-col">
      <GalaxyBackground />
      <Navbar />

      {/* Before the first search the hero sits centred in the viewport rather
          than stranded at the top above a large void; once results exist it
          reflows to the top so the list gets the space. */}
      <main
        className={`flex flex-1 flex-col items-center gap-10 px-6 pb-20 sm:px-10 ${
          hasActivity ? "pt-8" : "justify-center pb-32"
        }`}
      >
        <div className="flex flex-col items-center gap-3 text-center">
          <h1 className="text-4xl font-bold tracking-tight sm:text-6xl">
            DATA <span className="text-gradient">NEBULA</span> AI
          </h1>
          <p className="max-w-xl text-sm text-white/50 sm:text-base">
            Describe what you need in plain language. NLP, Discovery, and Evaluation agents
            find and explain the best-matching datasets.
          </p>
        </div>

        <SearchBox onSearch={handleSearch} loading={loading} />

        {(loading || stage === "done") && (
          <div className="flex flex-col items-center gap-3">
            <AgentFlow stage={stage} />
            {loading && <LoadingAnimation stage={stage} />}
          </div>
        )}

        {error && (
          <div className="glass max-w-xl border-red-400/30 px-5 py-4 text-center text-sm text-red-300">
            {error}
          </div>
        )}

        {result && (
          <div className="flex w-full max-w-4xl flex-col gap-6">
            <ExplanationCard understanding={result.understanding} />
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              {result.recommendations.map((item, index) => (
                <DatasetCard key={`${item.dataset.source}-${item.dataset.id}`} item={item} index={index} />
              ))}
            </div>
            {result.recommendations.length === 0 && (
              <p className="text-center text-sm text-white/40">No matching datasets found — try rephrasing.</p>
            )}
          </div>
        )}
      </main>
    </div>
  );
}
