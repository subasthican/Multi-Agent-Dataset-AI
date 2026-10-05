"use client";

import { useState, type FormEvent } from "react";
import AuthCard, { AuthButton, AuthError, AuthInput, AuthLink } from "@/components/AuthCard";
import { ApiError, forgotPassword } from "@/services/api";

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const result = await forgotPassword(email);
      setMessage(result.message);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Something went wrong. Is the backend running?");
    } finally {
      setLoading(false);
    }
  }

  return (
    <AuthCard
      title="Forgot password"
      subtitle="We'll help you get back in"
      footer={
        <>
          Remembered it? <AuthLink href="/login">Sign in</AuthLink>
        </>
      }
    >
      {message ? (
        <div className="flex flex-col gap-3 text-center text-sm text-white/70">
          <p>{message}</p>

        </div>
      ) : (
        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          <AuthInput
            label="Email"
            type="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            autoComplete="email"
          />
          <AuthError message={error} />
          <AuthButton type="submit" loading={loading}>
            Send Reset Link
          </AuthButton>
        </form>
      )}
    </AuthCard>
  );
}
