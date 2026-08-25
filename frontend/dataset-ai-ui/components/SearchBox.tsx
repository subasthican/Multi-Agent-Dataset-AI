"use client";

import { useState, type FormEvent } from "react";
import { Search, LoaderCircle } from "lucide-react";

interface SearchBoxProps {
  onSearch: (query: string) => void;
  loading: boolean;
}

const EXAMPLE_QUERIES = [
  "Find healthcare datasets for cancer prediction",
  "I need renewable energy forecasting data",
  "Credit card fraud detection dataset",
];

export default function SearchBox({ onSearch, loading }: SearchBoxProps) {
  const [query, setQuery] = useState("");

  function handleSubmit(event: FormEvent) {
    event.preventDefault();
    if (query.trim() && !loading) {
      onSearch(query.trim());
    }
  }

  return (
    <div className="w-full max-w-2xl">
      <form
        onSubmit={handleSubmit}
        className="glass-strong glow-purple flex items-center gap-3 rounded-2xl p-2 pl-5 transition-shadow duration-300 focus-within:glow-cyan"
      >
        <Search className="h-5 w-5 shrink-0 text-white/50" />
        <input
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          placeholder="Describe your dataset requirement..."
          className="min-w-0 flex-1 bg-transparent py-3 text-sm text-white placeholder:text-white/40 focus:outline-none sm:text-base"
        />
        <button
          type="submit"
          disabled={loading || !query.trim()}
          className="btn-primary flex shrink-0 items-center gap-2 rounded-xl px-4 py-3 text-sm sm:px-6"
        >
          {loading ? <LoaderCircle className="h-4 w-4 animate-spin" /> : null}
          {loading ? "Searching" : "Explore"}
        </button>
      </form>
      <div className="mt-3 flex flex-wrap gap-2">
        {EXAMPLE_QUERIES.map((example) => (
          <button
            key={example}
            type="button"
            onClick={() => {
              setQuery(example);
              onSearch(example);
            }}
            disabled={loading}
            className="rounded-full border border-white/10 px-3 py-1 text-xs text-white/50 transition-colors hover:border-white/30 hover:text-white/80 disabled:opacity-40"
          >
            {example}
          </button>
        ))}
      </div>
    </div>
  );
}
