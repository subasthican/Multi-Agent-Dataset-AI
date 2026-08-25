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
  createCatalogDataset,
  deleteCatalogDataset,
  getAdminCatalog,
  updateCatalogDataset,
  type CatalogDataset,
  type CatalogDatasetInput,
} from "@/services/api";

const EMPTY_FORM: CatalogDatasetInput = { name: "", description: "", domain: "", task: "" };

export default function CatalogAdminPage() {
  const { user, loading: authLoading } = useAuth();
  const router = useRouter();

  const [datasets, setDatasets] = useState<CatalogDataset[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  // "new" = the add form is open; a dataset id = editing that row; null = no form open.
  const [editingId, setEditingId] = useState<string | "new" | null>(null);
  const [form, setForm] = useState<CatalogDatasetInput>(EMPTY_FORM);
  const [saving, setSaving] = useState(false);
  const [deletingId, setDeletingId] = useState<string | null>(null);

  const loadCatalog = useCallback(() => {
    setError(null);
    return getAdminCatalog()
      .then(setDatasets)
      .catch((err) => {
        setError(err instanceof ApiError ? err.message : "Could not load the catalog.");
      });
  }, []);

  useEffect(() => {
    if (authLoading) return;
    if (!user || !user.is_admin) {
      router.push("/");
      return;
    }
    void Promise.resolve().then(() => loadCatalog());
  }, [authLoading, user, router, loadCatalog]);

  function startCreate() {
    setForm(EMPTY_FORM);
    setEditingId("new");
  }

  function startEdit(dataset: CatalogDataset) {
    setForm({
      name: dataset.name,
      description: dataset.description,
      domain: dataset.domain,
      task: dataset.task,
    });
    setEditingId(dataset.id);
  }

  function cancelForm() {
    setEditingId(null);
    setForm(EMPTY_FORM);
  }

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setSaving(true);
    setError(null);
    try {
      if (editingId === "new") {
        await createCatalogDataset(form);
      } else if (editingId) {
        await updateCatalogDataset(editingId, form);
      }
      cancelForm();
      await loadCatalog();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not save the dataset.");
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete(dataset: CatalogDataset) {
    if (!window.confirm(`Delete "${dataset.name}" from the catalog? This can't be undone.`)) return;
    setDeletingId(dataset.id);
    setError(null);
    try {
      await deleteCatalogDataset(dataset.id);
      await loadCatalog();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not delete the dataset.");
    } finally {
      setDeletingId(null);
    }
  }

  if (authLoading || !user?.is_admin || !datasets) {
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
            <h1 className="mt-1 text-xl font-semibold">Dataset Catalog</h1>
            <p className="mt-1 text-xs text-white/40">
              Changes here take effect immediately in live search — no restart needed.
            </p>
          </div>
          {editingId === null && (
            <button onClick={startCreate} className="btn-primary flex items-center gap-1.5 rounded-xl px-4 py-2 text-sm">
              <Plus className="h-4 w-4" />
              Add dataset
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
              <h2 className="text-sm font-semibold text-white/80">
                {editingId === "new" ? "New dataset" : "Edit dataset"}
              </h2>
              <button type="button" onClick={cancelForm} className="text-white/40 hover:text-white">
                <X className="h-4 w-4" />
              </button>
            </div>
            <AuthInput
              label="Name"
              required
              value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
            />
            <label className="flex flex-col gap-1.5 text-sm">
              <span className="text-white/60">Description</span>
              <textarea
                required
                rows={3}
                value={form.description}
                onChange={(e) => setForm({ ...form, description: e.target.value })}
                className="rounded-xl border border-white/10 bg-white/5 px-4 py-2.5 text-white placeholder:text-white/30 focus:border-nebula-cyan/50 focus:outline-none"
              />
            </label>
            <div className="grid grid-cols-2 gap-4">
              <AuthInput
                label="Domain"
                required
                value={form.domain}
                onChange={(e) => setForm({ ...form, domain: e.target.value })}
                placeholder="e.g. healthcare"
              />
              <AuthInput
                label="Task"
                required
                value={form.task}
                onChange={(e) => setForm({ ...form, task: e.target.value })}
                placeholder="e.g. classification"
              />
            </div>
            <AuthButton type="submit" loading={saving} className="self-start">
              {editingId === "new" ? "Add to catalog" : "Save changes"}
            </AuthButton>
          </motion.form>
        )}

        <div className="glass flex flex-col divide-y divide-white/5 p-2">
          {datasets.length === 0 && (
            <p className="p-4 text-center text-sm text-white/40">
              Catalog is empty — search will have no local matches until you add one.
            </p>
          )}
          {datasets.map((dataset) => (
            <div key={dataset.id} className="flex items-start justify-between gap-4 p-4">
              <div className="min-w-0 flex-1">
                <h3 className="text-sm font-medium text-white">{dataset.name}</h3>
                <p className="mt-1 line-clamp-2 text-xs text-white/40">{dataset.description}</p>
                <div className="mt-2 flex gap-2">
                  <span className="rounded-full border border-white/10 px-2 py-0.5 text-[10px] text-white/50">
                    {dataset.domain}
                  </span>
                  <span className="rounded-full border border-white/10 px-2 py-0.5 text-[10px] text-white/50">
                    {dataset.task}
                  </span>
                </div>
              </div>
              <div className="flex shrink-0 gap-2">
                <button
                  onClick={() => startEdit(dataset)}
                  className="btn-secondary rounded-lg p-2"
                  aria-label={`Edit ${dataset.name}`}
                >
                  <Pencil className="h-3.5 w-3.5" />
                </button>
                <button
                  onClick={() => handleDelete(dataset)}
                  disabled={deletingId === dataset.id}
                  className="rounded-lg border border-red-400/30 p-2 text-red-300 transition-colors hover:bg-red-400/10 disabled:opacity-40"
                  aria-label={`Delete ${dataset.name}`}
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
