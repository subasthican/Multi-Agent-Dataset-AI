"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { motion } from "framer-motion";
import { Activity, ChartBar, Crown, Database, Shield, Sliders, Trash2, Users } from "lucide-react";
import GalaxyBackground from "@/components/GalaxyBackground";
import Navbar from "@/components/Navbar";
import { AuthError } from "@/components/AuthCard";
import { useAuth } from "@/contexts/AuthContext";
import {
  ApiError,
  deleteAdminUser,
  getAdminStats,
  getAdminUsers,
  getPlans,
  updateAdminUser,
  type AdminStats,
  type AdminUser,
  type Plan,
} from "@/services/api";

function StatCard({ icon: Icon, label, value }: { icon: typeof Users; label: string; value: number | string }) {
  return (
    <div className="glass flex items-center gap-4 p-5">
      <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-nebula-purple/15 text-nebula-purple">
        <Icon className="h-5 w-5" />
      </div>
      <div>
        <div className="text-2xl font-semibold text-white">{value}</div>
        <div className="text-xs text-white/40">{label}</div>
      </div>
    </div>
  );
}

export default function AdminPage() {
  const { user, loading: authLoading } = useAuth();
  const router = useRouter();

  const [users, setUsers] = useState<AdminUser[] | null>(null);
  const [stats, setStats] = useState<AdminStats | null>(null);
  const [plans, setPlans] = useState<Plan[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [busyUserId, setBusyUserId] = useState<string | null>(null);

  const loadData = useCallback(async () => {
    setError(null);
    try {
      // getPlans() is public and only used here to populate the plan
      // dropdown below — GET /admin/plans (admin-only, with full CRUD) is
      // what the dedicated /admin/plans page uses.
      const [usersData, statsData, plansData] = await Promise.all([getAdminUsers(), getAdminStats(), getPlans()]);
      setUsers(usersData);
      setStats(statsData);
      setPlans(plansData);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not load admin data.");
    }
  }, []);

  useEffect(() => {
    if (authLoading) return;
    if (!user || !user.is_admin) {
      router.push("/");
      return;
    }
    // loadData's own body sets state synchronously at its top (setError),
    // so calling it directly here would itself be a synchronous setState-
    // in-effect. Deferring to a microtask keeps the effect body itself free
    // of any direct state write — the same fix used in RecommendedForYou.
    void Promise.resolve().then(() => loadData());
  }, [authLoading, user, router, loadData]);

  async function handlePlanChange(target: AdminUser, plan: string) {
    setBusyUserId(target.id);
    setError(null);
    try {
      await updateAdminUser(target.id, { plan });
      await loadData();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not update plan.");
    } finally {
      setBusyUserId(null);
    }
  }

  async function handleAdminToggle(target: AdminUser) {
    setBusyUserId(target.id);
    setError(null);
    try {
      await updateAdminUser(target.id, { is_admin: !target.is_admin });
      await loadData();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not update admin access.");
    } finally {
      setBusyUserId(null);
    }
  }

  async function handleDelete(target: AdminUser) {
    if (!window.confirm(`Delete ${target.email}? This also removes their search history. This can't be undone.`)) {
      return;
    }
    setBusyUserId(target.id);
    setError(null);
    try {
      await deleteAdminUser(target.id);
      await loadData();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not delete user.");
    } finally {
      setBusyUserId(null);
    }
  }

  if (authLoading || !user?.is_admin || !users || !stats) {
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
      <main className="mx-auto flex w-full max-w-5xl flex-1 flex-col gap-6 px-6 py-10">
        <div className="flex items-center justify-between">
          <h1 className="text-xl font-semibold">Admin</h1>
          <div className="flex gap-2">
            <Link href="/admin/catalog" className="btn-secondary flex items-center gap-1.5 rounded-xl px-4 py-2 text-sm">
              <Database className="h-4 w-4" />
              Manage catalog
            </Link>
            <Link href="/admin/plans" className="btn-secondary flex items-center gap-1.5 rounded-xl px-4 py-2 text-sm">
              <Sliders className="h-4 w-4" />
              Manage plans
            </Link>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-7">
          <StatCard icon={Users} label="Total users" value={stats.total_users} />
          <StatCard icon={Crown} label="Pro users" value={stats.pro_users} />
          <StatCard icon={Shield} label="Admins" value={stats.admin_users} />
          <StatCard icon={Database} label="Catalog size" value={stats.catalog_size} />
          <StatCard icon={Activity} label="Total searches" value={stats.total_searches} />
          <StatCard icon={ChartBar} label="Via Gemini" value={stats.searches_via_llm} />
          <StatCard icon={ChartBar} label="Via fallback" value={stats.searches_via_rule_based} />
        </div>

        <AuthError message={error} />

        <div className="glass overflow-x-auto p-5">
          <table className="w-full min-w-[640px] text-left text-sm">
            <thead>
              <tr className="text-xs uppercase tracking-wide text-white/40">
                <th className="pb-3 pr-4 font-medium">Name</th>
                <th className="pb-3 pr-4 font-medium">Email</th>
                <th className="pb-3 pr-4 font-medium">Plan</th>
                <th className="pb-3 pr-4 font-medium">Admin</th>
                <th className="pb-3 pr-4 font-medium">Searches</th>
                <th className="pb-3 font-medium">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5">
              {users.map((u) => {
                const isSelf = u.id === user.id;
                const busy = busyUserId === u.id;
                return (
                  <motion.tr key={u.id} initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="text-white/80">
                    <td className="py-3 pr-4">{u.name}</td>
                    <td className="py-3 pr-4 text-white/50">{u.email}</td>
                    <td className="py-3 pr-4">
                      <span
                        className={`rounded-full px-2 py-0.5 text-[10px] uppercase tracking-wide ${
                          u.plan === "pro" ? "bg-nebula-purple/20 text-nebula-purple" : "bg-white/10 text-white/50"
                        }`}
                      >
                        {u.plan}
                      </span>
                    </td>
                    <td className="py-3 pr-4">{u.is_admin ? <Shield className="h-4 w-4 text-nebula-cyan" /> : null}</td>
                    <td className="py-3 pr-4">{u.search_count}</td>
                    <td className="py-3">
                      <div className="flex flex-wrap items-center gap-2">
                        <select
                          disabled={busy}
                          value={u.plan}
                          onChange={(e) => handlePlanChange(u, e.target.value)}
                          className="rounded-lg border border-white/10 bg-white/5 px-2 py-1 text-xs text-white disabled:opacity-40"
                        >
                          {/* Falls back to the user's current plan name even if it's
                              since been deleted, so the select never silently shows
                              the wrong value. */}
                          {!plans.some((p) => p.name === u.plan) && <option value={u.plan}>{u.plan}</option>}
                          {plans.map((p) => (
                            <option key={p.id} value={p.name}>
                              {p.display_name}
                            </option>
                          ))}
                        </select>
                        <button
                          disabled={busy || isSelf}
                          title={isSelf ? "Can't change your own admin access" : undefined}
                          onClick={() => handleAdminToggle(u)}
                          className="btn-secondary rounded-lg px-2.5 py-1 text-xs disabled:opacity-40"
                        >
                          {u.is_admin ? "Revoke admin" : "Make admin"}
                        </button>
                        <button
                          disabled={busy || isSelf}
                          title={isSelf ? "Can't delete your own account here" : undefined}
                          onClick={() => handleDelete(u)}
                          className="flex items-center gap-1 rounded-lg border border-red-400/30 px-2.5 py-1 text-xs text-red-300 transition-colors hover:bg-red-400/10 disabled:opacity-40"
                        >
                          <Trash2 className="h-3 w-3" />
                        </button>
                      </div>
                    </td>
                  </motion.tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </main>
    </div>
  );
}
