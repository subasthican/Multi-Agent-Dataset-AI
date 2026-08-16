"use client";

import Link from "next/link";
import { Sparkles, User } from "lucide-react";
import { useAuth } from "@/contexts/AuthContext";

export default function Navbar() {
  const { user, loading } = useAuth();

  return (
    <nav className="flex items-center justify-between px-6 py-5 sm:px-10">
      <Link href="/" className="flex items-center gap-2">
        <Sparkles className="h-5 w-5 text-nebula-cyan" />
        <span className="text-lg font-semibold tracking-wide">
          DATA <span className="text-gradient">NEBULA</span> AI
        </span>
      </Link>

      <div className="flex items-center gap-4 text-sm">
        <Link href="/pricing" className="hidden text-white/50 transition-colors hover:text-white sm:block">
          Pricing
        </Link>

        {loading ? null : user ? (
          <Link
            href="/profile"
            className="flex items-center gap-2 rounded-full border border-white/10 px-3 py-1.5 text-white/70 transition-colors hover:border-white/30 hover:text-white"
          >
            <User className="h-4 w-4" />
            {user.name}
          </Link>
        ) : (
          <div className="flex items-center gap-2">
            <Link href="/login" className="text-white/60 transition-colors hover:text-white">
              Sign In
            </Link>
            <Link
              href="/register"
              className="rounded-full bg-gradient-to-r from-nebula-cyan to-nebula-purple px-3 py-1.5 font-medium text-black"
            >
              Sign Up
            </Link>
          </div>
        )}
      </div>
    </nav>
  );
}
