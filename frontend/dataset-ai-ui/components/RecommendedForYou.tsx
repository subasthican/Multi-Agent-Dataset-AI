"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { Sparkles } from "lucide-react";
import { useAuth } from "@/contexts/AuthContext";
import { getRecommendations, type RecommendationResponse } from "@/services/api";
import DatasetCard from "./DatasetCard";

export default function RecommendedForYou() {
  const { user } = useAuth();
  const [data, setData] = useState<RecommendationResponse | null>(null);

  useEffect(() => {
    if (!user) return;
    let cancelled = false;

    getRecommendations(3)
      .then((response) => {
        if (!cancelled) setData(response);
      })
      .catch(() => {
        if (!cancelled) setData(null);
      });

    return () => {
      cancelled = true;
    };
  }, [user]);

  if (!user || !data) return null;

  return (
    <motion.section
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      className="flex w-full max-w-4xl flex-col gap-4"
    >
      <div className="flex items-center gap-2 text-sm text-white/60">
        <Sparkles className="h-4 w-4 text-nebula-purple" />
        {data.search_count > 0 ? (
          <span>
            Recommended for you — based on your <span className="text-white/90">{data.based_on_domain}</span> +{" "}
            <span className="text-white/90">{data.based_on_task}</span> searches
          </span>
        ) : (
          <span>Search a few times and personalized recommendations will show up here.</span>
        )}
      </div>

      {data.recommendations.length > 0 && (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
          {data.recommendations.map((item, index) => (
            <DatasetCard key={`rec-${item.dataset.source}-${item.dataset.id}`} item={item} index={index} />
          ))}
        </div>
      )}
    </motion.section>
  );
}
