"use client";

import { useEffect, useState, type FormEvent } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import Link from "next/link";
import GalaxyBackground from "@/components/GalaxyBackground";
import Navbar from "@/components/Navbar";
import { AuthButton, AuthError, AuthInput } from "@/components/AuthCard";
import { useAuth } from "@/contexts/AuthContext";
import { ApiError, changePassword, updateProfile } from "@/services/api";

export default function ProfilePage() {
  const { user, loading, refreshUser, logout } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!loading && !user) router.push("/login");
  }, [loading, user, router]);

  const [draftName, setDraftName] = useState<string | null>(null);
  const name = draftName ?? user?.name ?? "";

  const [profileSaving, setProfileSaving] = useState(false);
  const [profileMessage, setProfileMessage] = useState<string | null>(null);
  const [profileError, setProfileError] = useState<string | null>(null);

  async function handleProfileSave(event: FormEvent) {
    event.preventDefault();
    setProfileError(null);
    setProfileMessage(null);
    setProfileSaving(true);
    try {
      await updateProfile(name);
      await refreshUser();
      setProfileMessage("Profile updated.");
    } catch (err) {
      setProfileError(err instanceof ApiError ? err.message : "Could not update profile.");
    } finally {
      setProfileSaving(false);
    }
  }

  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [passwordSaving, setPasswordSaving] = useState(false);
  const [passwordMessage, setPasswordMessage] = useState<string | null>(null);
  const [passwordError, setPasswordError] = useState<string | null>(null);

  async function handlePasswordChange(event: FormEvent) {
    event.preventDefault();
    setPasswordError(null);
    setPasswordMessage(null);

    if (newPassword.length < 8) {
      setPasswordError("New password must be at least 8 characters.");
      return;
    }

    setPasswordSaving(true);
    try {
      await changePassword(currentPassword, newPassword);
      setPasswordMessage("Password changed.");
      setCurrentPassword("");
      setNewPassword("");
    } catch (err) {
      setPasswordError(err instanceof ApiError ? err.message : "Could not change password.");
    } finally {
      setPasswordSaving(false);
    }
  }

  if (loading || !user) {
    return (
      <div className="relative flex min-h-screen flex-col">
        <GalaxyBackground />
        <Navbar />
        <main className="flex flex-1 items-center justify-center text-sm text-white/40">Loading...</main>
      </div>
    );
  }

  return (
    <div className="relative flex min-h-screen flex-col">
      <GalaxyBackground />
      <Navbar />
      <main className="mx-auto flex w-full max-w-2xl flex-1 flex-col gap-6 px-6 py-10">
        <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} className="glass p-6">
          <div className="flex items-center justify-between">
            <h1 className="text-xl font-semibold">Your Profile</h1>
            <span
              className={`rounded-full px-3 py-1 text-xs uppercase tracking-wide ${
                user.plan === "pro" ? "bg-nebula-purple/20 text-nebula-purple" : "bg-white/10 text-white/50"
              }`}
            >
              {user.plan} plan
            </span>
          </div>
          {user.plan === "free" && (
            <p className="mt-2 text-xs text-white/40">
              <Link href="/pricing" className="text-nebula-cyan hover:underline">
                Upgrade to Pro
              </Link>{" "}
              for unlimited searches and saved history.
            </p>
          )}

          <form onSubmit={handleProfileSave} className="mt-6 flex flex-col gap-4">
            <AuthInput label="Name" required value={name} onChange={(e) => setDraftName(e.target.value)} />
            <AuthInput label="Email" value={user.email} disabled />
            {profileMessage && <p className="text-xs text-nebula-cyan">{profileMessage}</p>}
            <AuthError message={profileError} />
            <AuthButton type="submit" loading={profileSaving} className="self-start">
              Save Changes
            </AuthButton>
          </form>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.05 }}
          className="glass p-6"
        >
          <h2 className="text-lg font-semibold">Change Password</h2>
          <form onSubmit={handlePasswordChange} className="mt-4 flex flex-col gap-4">
            <AuthInput
              label="Current password"
              type="password"
              required
              value={currentPassword}
              onChange={(e) => setCurrentPassword(e.target.value)}
              autoComplete="current-password"
            />
            <AuthInput
              label="New password"
              type="password"
              required
              minLength={8}
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              autoComplete="new-password"
            />
            {passwordMessage && <p className="text-xs text-nebula-cyan">{passwordMessage}</p>}
            <AuthError message={passwordError} />
            <AuthButton type="submit" loading={passwordSaving} className="self-start">
              Update Password
            </AuthButton>
          </form>
        </motion.div>

        <button
          onClick={() => {
            logout();
            router.push("/");
          }}
          className="self-start rounded-xl border border-white/10 px-4 py-2 text-sm text-white/60 transition-colors hover:border-white/30 hover:text-white"
        >
          Sign out
        </button>
      </main>
    </div>
  );
}
