"use client";

import { Suspense, useState, type FormEvent } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import AuthCard, { AuthButton, AuthError, AuthInput, AuthLink } from "@/components/AuthCard";
import { ApiError, resetPassword } from "@/services/api";

function ResetPasswordForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const token = searchParams.get("token") ?? "";

  const [newPassword, setNewPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [done, setDone] = useState(false);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);

    if (newPassword.length < 8) {
      setError("Password must be at least 8 characters.");
      return;
    }

    setLoading(true);
    try {
      await resetPassword(token, newPassword);
      setDone(true);
      setTimeout(() => router.push("/login"), 2000);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not reset password.");
    } finally {
      setLoading(false);
    }
  }

  if (!token) {
    return <AuthError message="Missing or invalid reset link. Request a new one from Forgot Password." />;
  }

  if (done) {
    return <p className="text-center text-sm text-white/70">Password updated. Redirecting to sign in...</p>;
  }

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-4">
      <AuthInput
        label="New password"
        type="password"
        required
        minLength={8}
        value={newPassword}
        onChange={(e) => setNewPassword(e.target.value)}
        autoComplete="new-password"
      />
      <AuthError message={error} />
      <AuthButton type="submit" loading={loading}>
        Reset Password
      </AuthButton>
    </form>
  );
}

export default function ResetPasswordPage() {
  return (
    <AuthCard
      title="Reset password"
      subtitle="Choose a new password"
      footer={
        <>
          Back to <AuthLink href="/login">Sign in</AuthLink>
        </>
      }
    >
      <Suspense fallback={<p className="text-center text-sm text-white/50">Loading...</p>}>
        <ResetPasswordForm />
      </Suspense>
    </AuthCard>
  );
}
