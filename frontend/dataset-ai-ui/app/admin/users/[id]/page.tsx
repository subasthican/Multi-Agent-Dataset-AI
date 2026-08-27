"use client";

import { useCallback, useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { motion } from "framer-motion";
import { ArrowLeft, Ban, PlayCircle, Shield, Trash2 } from "lucide-react";
import GalaxyBackground from "@/components/GalaxyBackground";
import Navbar from "@/components/Navbar";
import { AuthError } from "@/components/AuthCard";
import { useAuth } from "@/contexts/AuthContext";
import {
  ApiError,
  deleteAdminUser,
  getAdminUser,
  getPlans,
  updateAdminUser,
  type AdminUserDetail,
  type Plan,
} from "@/services/api";

function formatDate(iso: string): string {
  return new Date(iso).toLocaleString();
}

export default function UserDetailPage() {
  const { id } = useParams<{ id: string }>();
  const { user: currentAdmin, loading: authLoading } = useAuth();
  const router = useRouter();

  const [detail, setDetail] = useState<AdminUserDetail | null>(null);
  const [plans, setPlans] = useState<Plan[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const load = useCallback(() => {
    setError(null);
    return Promise.all([getAdminUser(id), getPlans()])
      .then(([d, p]) => {
        setDetail(d);
        setPlans(p);
      })
      .catch((err) => setError(err instanceof ApiError ? err.message : "Could not load this user."));
  }, [id]);

  useEffect(() => {
    if (authLoading) return;
    if (!currentAdmin || !currentAdmin.is_admin) {
      router.push("/");
      return;
    }
    void Promise.resolve().then(() => load());
  }, [authLoading, currentAdmin, router, load]);

  async function handlePlanChange(plan: string) {
    setBusy(true);
    setError(null);
    try {
      await updateAdminUser(id, { plan });
      await load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not update plan.");
    } finally {
      setBusy(false);
    }
  }

  async function handleAdminToggle() {
    if (!detail) return;
    setBusy(true);
    setError(null);
    try {
      await updateAdminUser(id, { is_admin: !detail.is_admin });
      await load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not update admin access.");
    } finally {
      setBusy(false);
    }
  }

  async function handleActiveToggle() {
    if (!detail) return;
    setBusy(true);
    setError(null);
    try {
      await updateAdminUser(id, { is_active: !detail.is_active });
      await load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not update account status.");
    } finally {
      setBusy(false);
    }
  }

  async function handleDelete() {
    if (!detail) return;
    if (!window.confirm(`Delete ${detail.email}? This also removes their search history. This can't be undone.`)) {
      return;
    }
    setBusy(true);
    setError(null);
    try {
      await deleteAdminUser(id);
      router.push("/admin");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not delete user.");
      setBusy(false);
    }
  }

  if (authLoading || !currentAdmin?.is_admin || !detail) {
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

  const isSelf = detail.id === currentAdmin.id;

  return (
    <div className="relative flex min-h-screen flex-col">
      <GalaxyBackground />
      <Navbar />
      <main className="mx-auto flex w-full max-w-3xl flex-1 flex-col gap-6 px-6 py-10">
        <Link href="/admin" className="flex w-fit items-center gap-1 text-xs text-white/40 hover:text-white/70">
          <ArrowLeft className="h-3 w-3" />
          Admin
        </Link>

        <AuthError message={error} />

        <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} className="glass flex flex-col gap-5 p-6">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-xl font-semibold text-white">{detail.name}</h1>
                {detail.is_admin && <Shield className="h-4 w-4 text-nebula-cyan" aria-label="Admin" />}
                {!detail.is_active && (
                  <span className="rounded-full bg-red-400/15 px-2 py-0.5 text-[10px] uppercase tracking-wide text-red-300">
                    Suspended
                  </span>
                )}
              </div>
              <p className="mt-1 text-sm text-white/50">{detail.email}</p>
              <p className="mt-1 text-xs text-white/30">
                Joined {formatDate(detail.created_at)} · {detail.search_count} searches recorded
              </p>
            </div>

            <div className="flex flex-wrap gap-2">
              <button
                disabled={busy || isSelf}
                title={isSelf ? "Can't change your own admin access" : undefined}
                onClick={handleAdminToggle}
                className="btn-secondary rounded-lg px-3 py-1.5 text-xs disabled:opacity-40"
              >
                {detail.is_admin ? "Revoke admin" : "Make admin"}
              </button>
              <button
                disabled={busy || isSelf}
                title={isSelf ? "Can't suspend your own account" : undefined}
                onClick={handleActiveToggle}
                className="flex items-center gap-1 rounded-lg border border-amber-400/30 px-3 py-1.5 text-xs text-amber-300 transition-colors hover:bg-amber-400/10 disabled:opacity-40"
              >
                {detail.is_active ? (
                  <>
                    <Ban className="h-3 w-3" /> Suspend
                  </>
                ) : (
                  <>
                    <PlayCircle className="h-3 w-3" /> Reactivate
                  </>
                )}
              </button>
              <button
                disabled={busy || isSelf}
                title={isSelf ? "Can't delete your own account here" : undefined}
                onClick={handleDelete}
                className="flex items-center gap-1 rounded-lg border border-red-400/30 px-3 py-1.5 text-xs text-red-300 transition-colors hover:bg-red-400/10 disabled:opacity-40"
              >
                <Trash2 className="h-3 w-3" /> Delete
              </button>
            </div>
          </div>

          <label className="flex flex-col gap-1.5 text-sm">
            <span className="text-white/60">Plan</span>
            <select
              disabled={busy}
              value={detail.plan}
              onChange={(e) => handlePlanChange(e.target.value)}
              className="w-fit rounded-xl border border-white/10 bg-white/5 px-4 py-2 text-sm text-white disabled:opacity-40"
            >
              {!plans.some((p) => p.name === detail.plan) && <option value={detail.plan}>{detail.plan}</option>}
              {plans.map((p) => (
                <option key={p.id} value={p.name}>
                  {p.display_name}
                </option>
              ))}
            </select>
          </label>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.05 }}
          className="glass flex flex-col gap-3 p-6"
        >
          <h2 className="text-sm font-semibold text-white/80">Search history</h2>
          {detail.search_history.length === 0 ? (
            <p className="text-sm text-white/40">No searches recorded for this account yet.</p>
          ) : (
            <div className="flex flex-col divide-y divide-white/5">
              {detail.search_history.map((entry) => (
                <div key={entry.id} className="flex flex-wrap items-center justify-between gap-2 py-3">
                  <div className="min-w-0">
                    <p className="truncate text-sm text-white/90">{entry.query}</p>
                    <div className="mt-1 flex flex-wrap gap-1.5">
                      <span className="rounded-full border border-white/10 px-2 py-0.5 text-[10px] text-white/50">
                        {entry.domain}
                      </span>
                      <span className="rounded-full border border-white/10 px-2 py-0.5 text-[10px] text-white/50">
                        {entry.task}
                      </span>
                      <span
                        className={`rounded-full px-2 py-0.5 text-[10px] uppercase tracking-wide ${
                          entry.understanding_source === "llm"
                            ? "bg-nebula-purple/20 text-nebula-purple"
                            : "bg-white/10 text-white/50"
                        }`}
                      >
                        {entry.understanding_source === "llm" ? "Gemini" : "Fallback"}
                      </span>
                    </div>
                  </div>
                  <span className="shrink-0 text-xs text-white/30">{formatDate(entry.created_at)}</span>
                </div>
              ))}
            </div>
          )}
        </motion.div>
      </main>
    </div>
  );
}
