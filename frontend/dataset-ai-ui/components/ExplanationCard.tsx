"use client";

import { motion } from "framer-motion";
import Link from "next/link";
import type { QueryAnalysisResult } from "@/services/api";
import { useAuth } from "@/contexts/AuthContext";

export default function ExplanationCard({ understanding }: { understanding: QueryAnalysisResult }) {
  const { user } = useAuth();
  return (
    <motion.div
      initial={{ opacity: 0, y: -8 }}
      animate={{ opacity: 1, y: 0 }}
      className="glass flex flex-col gap-3 p-5 text-sm"
    >
      <div className="flex items-center justify-between">
        <span className="text-xs uppercase tracking-wide text-white/40">NLP Agent Understanding</span>
        <span
          className={`rounded-full px-2 py-0.5 text-[10px] uppercase tracking-wide ${
            understanding.understanding_source === "llm"
              ? "bg-nebula-purple/20 text-nebula-purple"
              : "bg-white/10 text-white/50"
          }`}
        >
          {understanding.understanding_source === "llm" ? "Gemini LLM" : "Rule-based fallback"}
        </span>
      </div>
      <div className="flex flex-wrap gap-4 text-xs text-white/60">
        <div>
          <span className="text-white/30">Domain </span>
          <span className="text-white/90">{understanding.domain}</span>
        </div>
        <div>
          <span className="text-white/30">Task </span>
          <span className="text-white/90">{understanding.task}</span>
        </div>
        <div>
          <span className="text-white/30">Data type </span>
          <span className="text-white/90">{understanding.data_type}</span>
        </div>
      </div>
      <div className="flex flex-wrap gap-1.5">
        {understanding.keywords.map((keyword) => (
          <span key={keyword} className="rounded-full border border-white/10 px-2 py-0.5 text-[11px] text-white/50">
            {keyword}
          </span>
        ))}
      </div>
      <p className="text-[11px] text-white/30">
        {user ? (
          <>
            Transparency note: since you&apos;re signed in, this query is saved to power your{" "}
            <Link href="/profile" className="text-nebula-cyan hover:underline">
              personalized recommendations
            </Link>
            . You can clear your search history anytime from your profile.
          </>
        ) : (
          "Transparency note: this query was analyzed but not stored — nothing here is retained after your session."
        )}
      </p>
    </motion.div>
  );
}
