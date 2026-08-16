import { Sparkles } from "lucide-react";

export default function Navbar() {
  return (
    <nav className="flex items-center justify-between px-6 py-5 sm:px-10">
      <div className="flex items-center gap-2">
        <Sparkles className="h-5 w-5 text-nebula-cyan" />
        <span className="text-lg font-semibold tracking-wide">
          DATA <span className="text-gradient">NEBULA</span> AI
        </span>
      </div>
      <div className="hidden text-xs text-white/50 sm:block">
        Multi-Agent Dataset Discovery
      </div>
    </nav>
  );
}
