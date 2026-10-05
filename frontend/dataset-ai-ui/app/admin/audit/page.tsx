"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { getAdminAudit, type AdminAuditEvent } from "@/services/api";

export default function AuditPage() {
  const [events, setEvents] = useState<AdminAuditEvent[] | null>(null);
  const [error, setError] = useState("");
  useEffect(() => {
    getAdminAudit().then(setEvents).catch((err: Error) => setError(err.message));
  }, []);
  return (
    <main className="min-h-screen bg-slate-950 p-6 text-white">
      <Link href="/admin" className="underline">Back to admin</Link>
      <h1 className="my-6 text-2xl font-semibold">Admin activity</h1>
      <p className="mb-6 text-slate-300">Latest 100 actions. Passwords and search text are excluded.</p>
      {error && <p role="alert">{error}</p>}
      {!events && !error && <p>Loading activity…</p>}
      {events?.length === 0 && <p>No activity recorded yet.</p>}
      {events && events.length > 0 && <div className="overflow-x-auto"><table className="w-full text-left">
        <thead><tr>{["Time", "Admin ID", "Action", "Target", "Changed fields"].map((label) => <th key={label} className="p-3">{label}</th>)}</tr></thead>
        <tbody>{events.map((event) => <tr key={event.id} className="border-t border-white/10">
          <td className="p-3">{new Date(event.created_at).toLocaleString()}</td>
          <td className="p-3">{event.actor_id}</td><td className="p-3">{event.action}</td>
          <td className="p-3">{event.target_type}: {event.target_id}</td>
          <td className="p-3">{event.changed_fields.join(", ") || "—"}</td>
        </tr>)}</tbody>
      </table></div>}
    </main>
  );
}
