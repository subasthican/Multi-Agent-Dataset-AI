"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import Link from "next/link";
import { Check } from "lucide-react";
import GalaxyBackground from "@/components/GalaxyBackground";
import Navbar from "@/components/Navbar";
import { AuthError } from "@/components/AuthCard";
import { useAuth } from "@/contexts/AuthContext";
import { ApiError, getPlans, type Plan } from "@/services/api";

// Plans with this name get the "Most Popular" treatment — the backend has
// no highlighted/badge field, so this is a cosmetic hook only, not a
// functional distinction. Matches the seeded plan (see plan_seed.py).
const HIGHLIGHTED_PLAN_NAME = "pro";

function isCustomPricing(priceLabel: string): boolean {
  return priceLabel.trim().toLowerCase() === "custom";
}

export default function PricingPage() {
  const { user } = useAuth();
  const [plans, setPlans] = useState<Plan[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getPlans()
      .then(setPlans)
      .catch((err) => setError(err instanceof ApiError ? err.message : "Could not load pricing."));
  }, []);

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

        {error && <AuthError message={error} />}

        {!plans && !error && <p className="text-sm text-white/40">Loading plans...</p>}

        {plans && (
          <div className="grid w-full max-w-5xl grid-cols-1 items-stretch gap-6 md:grid-cols-3">
            {plans.map((plan, index) => {
              const highlighted = plan.name === HIGHLIGHTED_PLAN_NAME;
              const custom = isCustomPricing(plan.price_label);
              const isCurrentPlan = user?.plan === plan.name;

              return (
                <motion.div
                  key={plan.id}
                  initial={{ opacity: 0, y: 16 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.08 }}
                  className={`relative flex flex-col p-6 ${
                    highlighted ? "glass-strong glow-purple md:-my-2 md:pt-8" : "glass"
                  }`}
                >
                  {highlighted && (
                    <span className="absolute -top-3 left-1/2 -translate-x-1/2 rounded-full bg-gradient-to-r from-nebula-cyan to-nebula-purple px-3 py-1 text-[10px] font-semibold uppercase tracking-wider text-black">
                      Most Popular
                    </span>
                  )}

                  <h2 className="text-lg font-semibold">{plan.display_name}</h2>
                  <p className="mt-1 min-h-[2rem] text-xs leading-4 text-white/45">{plan.description}</p>

                  <div className="mt-4 flex items-baseline gap-1">
                    <span className="text-3xl font-bold tracking-tight">{plan.price_label}</span>
                    {plan.period && <span className="text-sm text-white/40">{plan.period}</span>}
                  </div>

                  <div className="mt-5 mb-6 h-px bg-white/10" />

                  <ul className="flex flex-1 flex-col gap-2.5 text-sm text-white/65">
                    {plan.features.map((feature) => (
                      <li key={feature} className="flex items-start gap-2.5">
                        <Check className="mt-0.5 h-4 w-4 shrink-0 text-nebula-cyan" />
                        <span className="leading-5">{feature}</span>
                      </li>
                    ))}
                  </ul>

                  {isCurrentPlan ? (
                    <span className="mt-8 rounded-xl border border-white/10 px-4 py-3 text-center text-sm text-white/50">
                      Your current plan
                    </span>
                  ) : custom ? (
                    <a
                      href="mailto:hello@datanebula.ai"
                      className={`mt-8 rounded-xl px-4 py-3 text-center text-sm ${
                        highlighted ? "btn-primary" : "btn-secondary"
                      }`}
                    >
                      Contact Sales
                    </a>
                  ) : !user ? (
                    <Link
                      href="/register"
                      className={`mt-8 rounded-xl px-4 py-3 text-center text-sm ${
                        highlighted ? "btn-primary" : "btn-secondary"
                      }`}
                    >
                      Get Started
                    </Link>
                  ) : (
                    // Billing isn't wired to a payment provider yet — plan
                    // changes for signed-in users go through an admin today
                    // (see /admin), so this stays an honest note rather than
                    // a button that pretends to self-serve upgrade.
                    <p className="mt-8 text-center text-xs text-white/30">Contact an admin to switch plans.</p>
                  )}
                </motion.div>
              );
            })}
          </div>
        )}

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
