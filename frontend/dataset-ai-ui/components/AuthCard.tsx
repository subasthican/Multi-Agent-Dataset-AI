"use client";

import type { ReactNode } from "react";
import { motion } from "framer-motion";
import Link from "next/link";
import GalaxyBackground from "./GalaxyBackground";
import Navbar from "./Navbar";

export default function AuthCard({
  title,
  subtitle,
  children,
  footer,
}: {
  title: string;
  subtitle?: string;
  children: ReactNode;
  footer?: ReactNode;
}) {
  return (
    <div className="relative flex min-h-screen flex-col">
      <GalaxyBackground />
      <Navbar />
      <main className="flex flex-1 items-center justify-center px-6 py-10">
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.35 }}
          className="glass-strong glow-purple w-full max-w-sm p-8"
        >
          <h1 className="text-center text-2xl font-semibold">{title}</h1>
          {subtitle && <p className="mt-2 text-center text-sm text-white/50">{subtitle}</p>}
          <div className="mt-6 flex flex-col gap-4">{children}</div>
          {footer && <div className="mt-6 text-center text-xs text-white/40">{footer}</div>}
        </motion.div>
      </main>
    </div>
  );
}

export function AuthInput({
  label,
  ...props
}: React.InputHTMLAttributes<HTMLInputElement> & { label: string }) {
  return (
    <label className="flex flex-col gap-1.5 text-sm">
      <span className="text-white/60">{label}</span>
      <input
        {...props}
        className="rounded-xl border border-white/10 bg-white/5 px-4 py-2.5 text-white placeholder:text-white/30 transition-shadow duration-200 focus:border-nebula-cyan/50 focus:shadow-[0_0_0_3px_rgba(34,211,238,0.15)] focus:outline-none"
      />
    </label>
  );
}

export function AuthButton({
  children,
  loading,
  ...props
}: React.ButtonHTMLAttributes<HTMLButtonElement> & { loading?: boolean }) {
  return (
    <button
      {...props}
      disabled={props.disabled || loading}
      className={`btn-primary mt-2 rounded-xl px-4 py-2.5 text-sm ${props.className ?? ""}`}
    >
      {loading ? "Please wait..." : children}
    </button>
  );
}

export function AuthError({ message }: { message: string | null }) {
  if (!message) return null;
  return <p className="rounded-lg border border-red-400/30 bg-red-400/10 px-3 py-2 text-xs text-red-300">{message}</p>;
}

export function AuthLink({ href, children }: { href: string; children: ReactNode }) {
  return (
    <Link href={href} className="text-nebula-cyan hover:underline">
      {children}
    </Link>
  );
}
