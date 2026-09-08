"use client";

import Link from "next/link";
import { FormEvent, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";

import { useAuth } from "@/components/auth-provider";
import { loginCustomer, registerCustomer } from "@/lib/auth";

export function AuthForm({ mode }: { mode: "login" | "register" }) {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { refresh } = useAuth();
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const registering = mode === "register";

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSubmitting(true);
    setError("");
    try {
      if (registering) await registerCustomer({ full_name: fullName, email, password });
      else await loginCustomer({ email, password });
      await refresh();
      const next = searchParams.get("next");
      router.push(next?.startsWith("/") && !next.startsWith("//") ? next : "/account");
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "We could not complete that request.");
      setSubmitting(false);
    }
  }

  return (
    <section className="auth-shell">
      <div className="auth-copy">
        <p className="eyebrow">{registering ? "Create your account" : "Welcome back"}</p>
        <h1>{registering ? "Keep every booking together." : "Your events are waiting."}</h1>
        <p className="intro">
          {registering
            ? "Book as a registered customer and return to your reservations from any device."
            : "Sign in to see your upcoming and past EventEveryday bookings."}
        </p>
      </div>
      <form className="auth-card" onSubmit={submit}>
        {registering && <label>Full name<input autoComplete="name" required value={fullName} onChange={(event) => setFullName(event.target.value)} /></label>}
        <label>Email address<input autoComplete="email" required type="email" value={email} onChange={(event) => setEmail(event.target.value)} /></label>
        <label>Password<input autoComplete={registering ? "new-password" : "current-password"} minLength={8} required type="password" value={password} onChange={(event) => setPassword(event.target.value)} /></label>
        {registering && <small>Use at least 8 characters and avoid common passwords.</small>}
        {error && <p className="form-error" role="alert">{error}</p>}
        <button disabled={submitting} type="submit">{submitting ? "Please wait…" : registering ? "Create account" : "Sign in"}</button>
        <p>{registering ? "Already registered?" : "New to EventEveryday?"} <Link href={registering ? "/login" : "/register"}>{registering ? "Sign in" : "Create an account"}</Link></p>
      </form>
    </section>
  );
}
