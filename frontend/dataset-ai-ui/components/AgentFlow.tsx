"use client";

import { motion } from "framer-motion";
import ThinkingOrb from "./ThinkingOrb";

export type AgentStage = "idle" | "nlp" | "discovery" | "evaluation" | "done";

// Each stage gets its own accent from the app's existing nebula palette
// (app/globals.css) rather than a flat icon — see ThinkingOrb.
const STAGES: { key: AgentStage; label: string; color: string }[] = [
  { key: "nlp", label: "NLP Agent", color: "#22d3ee" },
  { key: "discovery", label: "Discovery Agent", color: "#7c3aed" },
  { key: "evaluation", label: "Evaluation Agent", color: "#ec4899" },
];

const STAGE_ORDER: AgentStage[] = ["nlp", "discovery", "evaluation", "done"];

export default function AgentFlow({ stage }: { stage: AgentStage }) {
  const currentIndex = STAGE_ORDER.indexOf(stage);

  return (
    <div className="flex items-center justify-center gap-3 sm:gap-6">
      {STAGES.map(({ key, label, color }, index) => {
        const isActive = stage === key;
        const isDone = currentIndex > index || stage === "done";

        return (
          <div key={key} className="flex items-center gap-3 sm:gap-6">
            <div className="flex flex-col items-center gap-2">
              <motion.div
                animate={isActive ? { scale: [1, 1.08, 1] } : { scale: 1 }}
                transition={{ repeat: isActive ? Infinity : 0, duration: 1.2 }}
                className={`glass flex h-12 w-12 items-center justify-center rounded-full ${
                  isActive ? "pulse-ring border-nebula-cyan/60" : isDone ? "border-nebula-cyan/30" : "opacity-40"
                }`}
              >
                <ThinkingOrb color={color} size={32} active={isActive} dimmed={!isActive && !isDone} />
              </motion.div>
              <span className={`text-[11px] ${isActive || isDone ? "text-white/80" : "text-white/30"}`}>
                {label}
              </span>
            </div>
            {index < STAGES.length - 1 && (
              <div className={`h-px w-6 sm:w-12 ${isDone ? "bg-nebula-cyan/50" : "bg-white/10"}`} />
            )}
          </div>
        );
      })}
    </div>
  );
}
