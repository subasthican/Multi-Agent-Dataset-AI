"use client";

import { motion, AnimatePresence } from "framer-motion";
import type { AgentStage } from "./AgentFlow";

const MESSAGES: Record<AgentStage, string> = {
  idle: "",
  nlp: "Understanding your request...",
  discovery: "Searching the dataset universe...",
  evaluation: "Ranking and explaining results...",
  done: "Done.",
};

export default function LoadingAnimation({ stage }: { stage: AgentStage }) {
  const message = MESSAGES[stage];

  return (
    <div className="h-5 text-center text-xs text-white/40">
      <AnimatePresence mode="wait">
        <motion.span
          key={message}
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.2 }}
        >
          {message}
        </motion.span>
      </AnimatePresence>
    </div>
  );
}
