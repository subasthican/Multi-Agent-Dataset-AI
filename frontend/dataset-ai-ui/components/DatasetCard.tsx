"use client";

import { motion } from "framer-motion";
import { Boxes, Database, ExternalLink, FlaskConical, Globe } from "lucide-react";
import type { EvaluatedDataset } from "@/services/api";

const SOURCE_BADGES = {
  catalog: { icon: Database, className: "bg-nebula-cyan/15 text-nebula-cyan" },
  kaggle: { icon: Globe, className: "bg-nebula-pink/15 text-nebula-pink" },
  openml: { icon: FlaskConical, className: "bg-nebula-purple/15 text-nebula-purple" },
  huggingface: { icon: Boxes, className: "bg-nebula-amber/15 text-nebula-amber" },
} as const;

// Label for the "View on ..." link — a live source always names the actual
// platform; a catalog entry's admin-provided reference could point
// anywhere, so it gets a generic label instead.
const SOURCE_LINK_LABEL: Record<keyof typeof SOURCE_BADGES, string> = {
  catalog: "View source",
  kaggle: "View on Kaggle",
  openml: "View on OpenML",
  huggingface: "View on Hugging Face",
};

export default function DatasetCard({ item, index }: { item: EvaluatedDataset; index: number }) {
  const { dataset, score, explanation } = item;
  const badge = SOURCE_BADGES[dataset.source];

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.06, duration: 0.35 }}
      className="glass flex flex-col gap-4 p-5"
    >
      <div className="flex items-start justify-between gap-3">
        {/* Live source titles are arbitrary external text and can be long or
            unbroken, so this has to be allowed to wrap rather than overflow. */}
        <h3 className="min-w-0 flex-1 text-base font-semibold break-words text-white">{dataset.name}</h3>
        <span
          className={`flex shrink-0 items-center gap-1 rounded-full px-2 py-1 text-[10px] uppercase tracking-wide ${badge.className}`}
        >
          <badge.icon className="h-3 w-3" />
          {dataset.source}
        </span>
      </div>

      <div className="flex flex-wrap gap-2 text-xs text-white/60">
        <span className="rounded-full border border-white/10 px-2 py-0.5">{dataset.domain}</span>
        <span className="rounded-full border border-white/10 px-2 py-0.5">{dataset.task}</span>
      </div>

      <p className="flex-1 text-sm leading-5 break-words text-white/50">{dataset.description}</p>

      <div>
        <div className="mb-1 flex items-center justify-between text-xs text-white/50">
          <span>Match Score</span>
          <span className="font-mono text-nebula-cyan">{score.toFixed(1)}%</span>
        </div>
        <div className="h-1.5 w-full overflow-hidden rounded-full bg-white/10">
          <motion.div
            initial={{ width: 0 }}
            animate={{ width: `${Math.min(score, 100)}%` }}
            transition={{ duration: 0.6, ease: "easeOut" }}
            className="h-full rounded-full bg-gradient-to-r from-nebula-cyan to-nebula-purple"
          />
        </div>
      </div>

      <p className="text-xs text-white/40">{explanation}</p>

      {/* Only rendered when a real link exists — never a fake/disabled link
          for a curated catalog entry with no admin-provided reference.
          Downloading itself happens on that source's own page (their own
          auth/quota/ToS apply), not proxied through this app. */}
      {dataset.url && (
        <a
          href={dataset.url}
          target="_blank"
          rel="noopener noreferrer"
          className="btn-secondary flex items-center justify-center gap-1.5 self-start rounded-lg px-3 py-1.5 text-xs"
        >
          {SOURCE_LINK_LABEL[dataset.source]}
          <ExternalLink className="h-3 w-3" />
        </a>
      )}
    </motion.div>
  );
}
