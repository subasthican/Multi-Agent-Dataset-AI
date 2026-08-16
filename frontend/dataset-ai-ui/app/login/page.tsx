"use client";

import { useState, type FormEvent } from "react";
import { useRouter } from "next/navigation";
import AuthCard, { AuthButton, AuthError, AuthInput, AuthLink } from "@/components/AuthCard";
import { ApiError } from "@/services/api";
import { useAuth } from "@/contexts/AuthContext";

export default function LoginPage() {
  const { login } = useAuth();
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await login(email, password);
      router.push("/profile");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not sign in. Is the backend running?");
    } finally {
      setLoading(false);
    }
  }

  return (
    <AuthCard
      title="Welcome back"
      subtitle="Sign in to your DATA NEBULA AI account"
      footer={
        <>
          No account? <AuthLink href="/register">Create one</AuthLink>
        </>
      }
    >
      <form onSubmit={handleSubmit} className="flex flex-col gap-4">
        <AuthInput
          label="Email"
          type="email"
          required
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          autoComplete="email"
        />
        <AuthInput
          label="Password"
          type="password"
          required
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          autoComplete="current-password"
        />
        <div className="-mt-1 text-right text-xs">
          <AuthLink href="/forgot-password">Forgot password?</AuthLink>
        </div>
        <AuthError message={error} />
        <AuthButton type="submit" loading={loading}>
          Sign In
        </AuthButton>
      </form>
    </AuthCard>
  );
}
