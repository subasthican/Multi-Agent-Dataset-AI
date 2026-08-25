"use client";

import { motion } from "framer-motion";
import Link from "next/link";
import { Check } from "lucide-react";
import GalaxyBackground from "@/components/GalaxyBackground";
import Navbar from "@/components/Navbar";
import { useAuth } from "@/contexts/AuthContext";

interface Tier {
  name: string;
  price: string;
  period?: string;
  description: string;
  features: string[];
  cta: string;
  href: string;
  highlighted?: boolean;
  badge?: string;
}

const TIERS: Tier[] = [
  {
    name: "Free",
    price: "$0",
    description: "For students and individuals exploring datasets.",
    features: [
      "Natural-language dataset search",
      "Curated dataset catalog",
      "Basic Kaggle search",
      "Rule-based fallback when LLM is unavailable",
      "Personalized recommendations from your search history (sign in)",
    ],
    cta: "Get Started",
    href: "/register",
  },
  {
    name: "Pro",
    price: "$19",
    period: "/month",
    description: "For researchers and ML practitioners who search often.",
    features: [
      "Everything in Free",
      "Priority Gemini-powered understanding",
      "Unlimited searches",
      "Multi-source discovery (Kaggle + OpenML + HuggingFace)",
      "Email support",
    ],
    cta: "Upgrade to Pro",
    href: "/profile",
    highlighted: true,
    badge: "Most Popular",
  },
  {
    name: "Enterprise",
    price: "Custom",
    description: "For labs and teams with private datasets and SLAs.",
    features: [
      "Everything in Pro",
      "Team seats & shared workspaces",
      "Private/internal dataset integration",
      "API access",
      "Dedicated support & SLA",
    ],
    cta: "Contact Sales",
    href: "mailto:hello@datanebula.ai",
  },
];

export default function PricingPage() {
  const { user } = useAuth();

  return (
    <div className="relative flex min-h-screen flex-col">
      <GalaxyBackground />
      <Navbar />
      <main className="flex flex-1 flex-col items-center gap-10 px-6 py-16 sm:px-10">
        <div className="flex flex-col items-center gap-3 text-center">
          <h1 className="text-3xl font-bold sm:text-4xl">
            Simple, <span className="text-gradient">transparent</span> pricing
          </h1>
          <p className="max-w-md text-sm text-white/50">
            Start free. Upgrade when you need unlimited, multi-source, priority dataset discovery.
          </p>
        </div>

        <div className="grid w-full max-w-5xl grid-cols-1 items-stretch gap-6 md:grid-cols-3">
          {TIERS.map((tier, index) => (
            <motion.div
              key={tier.name}
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.08 }}
              className={`relative flex flex-col p-6 ${
                tier.highlighted ? "glass-strong glow-purple md:-my-2 md:pt-8" : "glass"
              }`}
            >
              {tier.badge && (
                <span className="absolute -top-3 left-1/2 -translate-x-1/2 rounded-full bg-gradient-to-r from-nebula-cyan to-nebula-purple px-3 py-1 text-[10px] font-semibold uppercase tracking-wider text-black">
                  {tier.badge}
                </span>
              )}

              <h2 className="text-lg font-semibold">{tier.name}</h2>
              {/* Fixed height keeps the price and feature rows aligned across
                  cards whether the description wraps to one line or two. */}
              <p className="mt-1 min-h-[2rem] text-xs leading-4 text-white/45">{tier.description}</p>

              <div className="mt-4 flex items-baseline gap-1">
                <span className="text-3xl font-bold tracking-tight">{tier.price}</span>
                {tier.period && <span className="text-sm text-white/40">{tier.period}</span>}
              </div>

              <div className="mt-5 mb-6 h-px bg-white/10" />

              <ul className="flex flex-1 flex-col gap-2.5 text-sm text-white/65">
                {tier.features.map((feature) => (
                  <li key={feature} className="flex items-start gap-2.5">
                    <Check className="mt-0.5 h-4 w-4 shrink-0 text-nebula-cyan" />
                    <span className="leading-5">{feature}</span>
                  </li>
                ))}
              </ul>

              <Link
                href={user ? tier.href : "/register"}
                className={`mt-8 rounded-xl px-4 py-3 text-center text-sm ${
                  tier.highlighted ? "btn-primary" : "btn-secondary"
                }`}
              >
                {tier.cta}
              </Link>
            </motion.div>
          ))}
        </div>

        <p className="mt-6 max-w-lg text-center text-xs leading-5 text-white/30">
          Target market: students, independent ML practitioners, and small research teams who need faster
          dataset discovery than manual search across Kaggle/OpenML/HuggingFace. Pro tier upgrade billing is
          not yet wired to a payment provider in this build — this page reflects the commercialization plan
          for the report.
        </p>
      </main>
    </div>
  );
}
