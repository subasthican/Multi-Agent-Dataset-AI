"use client";

import Link from "next/link";
import { Shield, Sparkles, User } from "lucide-react";
import { useAuth } from "@/contexts/AuthContext";

export default function Navbar() {
  const { user, loading } = useAuth();

  return (
    <nav className="flex items-center justify-between gap-4 px-5 py-5 sm:px-10">
      <Link href="/" className="flex shrink-0 items-center gap-2">
        <Sparkles className="h-5 w-5 text-nebula-cyan" />
        <span className="text-base font-semibold tracking-wide sm:text-lg">
          DATA <span className="text-gradient">NEBULA</span> AI
        </span>
      </Link>

      <div className="flex items-center gap-3 text-sm sm:gap-4">
        <Link href="/pricing" className="text-white/50 transition-colors hover:text-white">
          Pricing
        </Link>

        {/* Reserve the row height while auth resolves so the navbar doesn't
            visibly jump when the session check comes back. */}
        {loading ? (
          <div className="h-8 w-20" aria-hidden />
        ) : user ? (
          <>
            {user.is_admin && (
              <Link href="/admin" className="hidden items-center gap-1 text-white/50 transition-colors hover:text-white sm:flex">
                <Shield className="h-4 w-4" />
                Admin
              </Link>
            )}
            <Link
              href="/profile"
              className="flex max-w-[9rem] items-center gap-2 rounded-full border border-white/10 px-3 py-1.5 text-white/70 transition-colors hover:border-white/30 hover:text-white"
            >
              <User className="h-4 w-4 shrink-0" />
              <span className="truncate">{user.name}</span>
            </Link>
          </>
        ) : (
          <div className="flex items-center gap-2 sm:gap-3">
            <Link href="/login" className="text-white/60 transition-colors hover:text-white">
              Sign In
            </Link>
            <Link href="/register" className="btn-primary rounded-full px-4 py-1.5 text-sm">
              Sign Up
            </Link>
          </div>
        )}
      </div>
    </nav>
  );
}
