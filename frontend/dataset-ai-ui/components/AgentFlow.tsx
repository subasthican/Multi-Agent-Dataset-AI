"use client";

import { Brain, Compass, Sparkles } from "lucide-react";
import { motion } from "framer-motion";

export type AgentStage = "idle" | "nlp" | "discovery" | "evaluation" | "done";

const STAGES: { key: AgentStage; label: string; icon: typeof Brain }[] = [
  { key: "nlp", label: "NLP Agent", icon: Brain },
  { key: "discovery", label: "Discovery Agent", icon: Compass },
  { key: "evaluation", label: "Evaluation Agent", icon: Sparkles },
];

const STAGE_ORDER: AgentStage[] = ["nlp", "discovery", "evaluation", "done"];

export default function AgentFlow({ stage }: { stage: AgentStage }) {
  const currentIndex = STAGE_ORDER.indexOf(stage);

  return (
    <div className="flex items-center justify-center gap-3 sm:gap-6">
      {STAGES.map(({ key, label, icon: Icon }, index) => {
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
                <Icon className={`h-5 w-5 ${isActive || isDone ? "text-nebula-cyan" : "text-white/40"}`} />
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
