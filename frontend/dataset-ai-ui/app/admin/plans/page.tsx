"use client";

import { useCallback, useEffect, useState, type FormEvent } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { motion } from "framer-motion";
import { ArrowLeft, Pencil, Plus, Trash2, X } from "lucide-react";
import GalaxyBackground from "@/components/GalaxyBackground";
import Navbar from "@/components/Navbar";
import { AuthButton, AuthError, AuthInput } from "@/components/AuthCard";
import { useAuth } from "@/contexts/AuthContext";
import {
  ApiError,
  createPlan,
  deletePlan,
  getAdminPlans,
  updatePlan,
  type Plan,
  type PlanInput,
  type PlanUpdateInput,
} from "@/services/api";

interface PlanFormState {
  name: string;
  display_name: string;
  price_label: string;
  period: string;
  description: string;
  featuresText: string; // one feature per line in the UI, split to an array on save
  limitText: string; // "" = unlimited
}

const EMPTY_FORM: PlanFormState = {
  name: "",
  display_name: "",
  price_label: "",
  period: "",
  description: "",
  featuresText: "",
  limitText: "",
};

function toFormState(plan: Plan): PlanFormState {
  return {
    name: plan.name,
    display_name: plan.display_name,
    price_label: plan.price_label,
    period: plan.period ?? "",
    description: plan.description,
    featuresText: plan.features.join("\n"),
    limitText: plan.daily_search_limit === null ? "" : String(plan.daily_search_limit),
  };
}

export default function PlansAdminPage() {
  const { user, loading: authLoading } = useAuth();
  const router = useRouter();

  const [plans, setPlans] = useState<Plan[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  // "new" = the add form is open; a plan id = editing that row; null = no form open.
  const [editingId, setEditingId] = useState<string | "new" | null>(null);
  const [form, setForm] = useState<PlanFormState>(EMPTY_FORM);
  const [saving, setSaving] = useState(false);
  const [deletingId, setDeletingId] = useState<string | null>(null);

  const loadPlans = useCallback(() => {
    setError(null);
    return getAdminPlans()
      .then(setPlans)
      .catch((err) => {
        setError(err instanceof ApiError ? err.message : "Could not load plans.");
      });
  }, []);

  useEffect(() => {
    if (authLoading) return;
    if (!user || !user.is_admin) {
      router.push("/");
      return;
    }
    void Promise.resolve().then(() => loadPlans());
  }, [authLoading, user, router, loadPlans]);

  function startCreate() {
    setForm(EMPTY_FORM);
    setEditingId("new");
  }

  function startEdit(plan: Plan) {
    setForm(toFormState(plan));
    setEditingId(plan.id);
  }

  function cancelForm() {
    setEditingId(null);
    setForm(EMPTY_FORM);
  }

  function parseFeatures(text: string): string[] {
    return text
      .split("\n")
      .map((line) => line.trim())
      .filter(Boolean);
  }

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setSaving(true);
    setError(null);
    const limit = form.limitText.trim() ? Number(form.limitText.trim()) : null;
    try {
      if (editingId === "new") {
        const payload: PlanInput = {
          name: form.name.trim(),
          display_name: form.display_name.trim(),
          price_label: form.price_label.trim(),
          period: form.period.trim() || null,
          description: form.description.trim(),
          features: parseFeatures(form.featuresText),
          daily_search_limit: limit,
        };
        await createPlan(payload);
      } else if (editingId) {
        const updates: PlanUpdateInput = {
          display_name: form.display_name.trim(),
          price_label: form.price_label.trim(),
          period: form.period.trim() || null,
          description: form.description.trim(),
          features: parseFeatures(form.featuresText),
        };
        // Empty box means "unlimited" — since PATCH can't distinguish "leave
        // it alone" from "set to null" for an optional int, that's the
        // dedicated clear flag rather than daily_search_limit: null.
        if (limit === null) updates.clear_search_limit = true;
        else updates.daily_search_limit = limit;
        await updatePlan(editingId, updates);
      }
      cancelForm();
      await loadPlans();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not save the plan.");
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete(plan: Plan) {
    if (!window.confirm(`Delete the "${plan.display_name}" plan? This can't be undone.`)) return;
    setDeletingId(plan.id);
    setError(null);
    try {
      await deletePlan(plan.id);
      await loadPlans();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not delete the plan.");
    } finally {
      setDeletingId(null);
    }
  }

  if (authLoading || !user?.is_admin || !plans) {
    return (
      <div className="relative flex min-h-screen flex-col">
        <GalaxyBackground />
        <Navbar />
        <main className="flex flex-1 items-center justify-center text-sm text-white/40">
          {error ? <AuthError message={error} /> : "Loading..."}
        </main>
      </div>
    );
  }

  return (
    <div className="relative flex min-h-screen flex-col">
      <GalaxyBackground />
      <Navbar />
      <main className="mx-auto flex w-full max-w-3xl flex-1 flex-col gap-6 px-6 py-10">
        <div className="flex items-center justify-between">
          <div>
            <Link href="/admin" className="flex items-center gap-1 text-xs text-white/40 hover:text-white/70">
              <ArrowLeft className="h-3 w-3" />
              Admin
            </Link>
            <h1 className="mt-1 text-xl font-semibold">Plans</h1>
            <p className="mt-1 text-xs text-white/40">
              These rows drive the public pricing page and the daily search limit actually enforced on{" "}
              <code className="text-white/60">/discover</code> — not just labels.
            </p>
          </div>
          {editingId === null && (
            <button onClick={startCreate} className="btn-primary flex items-center gap-1.5 rounded-xl px-4 py-2 text-sm">
              <Plus className="h-4 w-4" />
              Add plan
            </button>
          )}
        </div>

        <AuthError message={error} />

        {editingId !== null && (
          <motion.form
            initial={{ opacity: 0, y: -8 }}
            animate={{ opacity: 1, y: 0 }}
            onSubmit={handleSubmit}
            className="glass flex flex-col gap-4 p-5"
          >
            <div className="flex items-center justify-between">
              <h2 className="text-sm font-semibold text-white/80">{editingId === "new" ? "New plan" : "Edit plan"}</h2>
              <button type="button" onClick={cancelForm} className="text-white/40 hover:text-white">
                <X className="h-4 w-4" />
              </button>
            </div>

            {editingId === "new" ? (
              <AuthInput
                label="Key (used internally, e.g. on User.plan — not shown to users)"
                required
                value={form.name}
                onChange={(e) => setForm({ ...form, name: e.target.value })}
                placeholder="e.g. student"
              />
            ) : (
              <label className="flex flex-col gap-1.5 text-sm">
                <span className="text-white/60">Key</span>
                <input
                  disabled
                  value={form.name}
                  className="cursor-not-allowed rounded-xl border border-white/10 bg-white/5 px-4 py-2.5 text-white/40"
                />
                <span className="text-[11px] text-white/30">
                  Not editable — it&apos;s the stable value stored on each user&apos;s account.
                </span>
              </label>
            )}

            <AuthInput
              label="Display name"
              required
              value={form.display_name}
              onChange={(e) => setForm({ ...form, display_name: e.target.value })}
              placeholder="e.g. Student"
            />

            <div className="grid grid-cols-2 gap-4">
              <AuthInput
                label="Price label"
                required
                value={form.price_label}
                onChange={(e) => setForm({ ...form, price_label: e.target.value })}
                placeholder="e.g. $9 or Custom"
              />
              <AuthInput
                label="Period (optional)"
                value={form.period}
                onChange={(e) => setForm({ ...form, period: e.target.value })}
                placeholder="e.g. /month"
              />
            </div>

            <label className="flex flex-col gap-1.5 text-sm">
              <span className="text-white/60">Description</span>
              <textarea
                required
                rows={2}
                value={form.description}
                onChange={(e) => setForm({ ...form, description: e.target.value })}
                className="rounded-xl border border-white/10 bg-white/5 px-4 py-2.5 text-white placeholder:text-white/30 focus:border-nebula-cyan/50 focus:outline-none"
              />
            </label>

            <label className="flex flex-col gap-1.5 text-sm">
              <span className="text-white/60">Features (one per line)</span>
              <textarea
                rows={4}
                value={form.featuresText}
                onChange={(e) => setForm({ ...form, featuresText: e.target.value })}
                placeholder={"Unlimited searches\nPriority support"}
                className="rounded-xl border border-white/10 bg-white/5 px-4 py-2.5 text-white placeholder:text-white/30 focus:border-nebula-cyan/50 focus:outline-none"
              />
            </label>

            <label className="flex flex-col gap-1.5 text-sm">
              <span className="text-white/60">Daily search limit (leave blank for unlimited)</span>
              <input
                type="number"
                min={1}
                value={form.limitText}
                onChange={(e) => setForm({ ...form, limitText: e.target.value })}
                placeholder="e.g. 10"
                className="rounded-xl border border-white/10 bg-white/5 px-4 py-2.5 text-white placeholder:text-white/30 focus:border-nebula-cyan/50 focus:outline-none"
              />
              <span className="text-[11px] text-white/30">
                Enforced server-side before every search — actually blocks requests over the limit, not cosmetic.
              </span>
            </label>

            <AuthButton type="submit" loading={saving} className="self-start">
              {editingId === "new" ? "Create plan" : "Save changes"}
            </AuthButton>
          </motion.form>
        )}

        <div className="glass flex flex-col divide-y divide-white/5 p-2">
          {plans.length === 0 && <p className="p-4 text-center text-sm text-white/40">No plans yet.</p>}
          {plans.map((plan) => (
            <div key={plan.id} className="flex items-start justify-between gap-4 p-4">
              <div className="min-w-0 flex-1">
                <div className="flex items-center gap-2">
                  <h3 className="text-sm font-medium text-white">{plan.display_name}</h3>
                  <span className="rounded-full border border-white/10 px-2 py-0.5 text-[10px] text-white/40">
                    {plan.name}
                  </span>
                </div>
                <p className="mt-1 text-xs text-white/40">
                  {plan.price_label}
                  {plan.period && <span className="text-white/30">{plan.period}</span>} ·{" "}
                  {plan.daily_search_limit === null ? "Unlimited searches/day" : `${plan.daily_search_limit} searches/day`}
                </p>
                <p className="mt-1 line-clamp-2 text-xs text-white/40">{plan.description}</p>
              </div>
              <div className="flex shrink-0 gap-2">
                <button
                  onClick={() => startEdit(plan)}
                  className="btn-secondary rounded-lg p-2"
                  aria-label={`Edit ${plan.display_name}`}
                >
                  <Pencil className="h-3.5 w-3.5" />
                </button>
                <button
                  onClick={() => handleDelete(plan)}
                  disabled={deletingId === plan.id}
                  className="rounded-lg border border-red-400/30 p-2 text-red-300 transition-colors hover:bg-red-400/10 disabled:opacity-40"
                  aria-label={`Delete ${plan.display_name}`}
                >
                  <Trash2 className="h-3.5 w-3.5" />
                </button>
              </div>
            </div>
          ))}
        </div>
      </main>
    </div>
  );
}
