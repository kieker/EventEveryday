"use client";
import { FormEvent, useState } from "react";
import { useAuth } from "@/components/auth-provider";
import { csrfHeaders, extractApiError, PUBLIC_API_URL } from "@/lib/api";

export function ProfileEditor({ editing, onClose }: { editing: boolean; onClose: () => void }) {
  const { customer, refresh } = useAuth();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [saved, setSaved] = useState(false);
  const [email, setEmail] = useState(customer?.email ?? "");
  if (!customer) return null;
  async function save(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const values = Object.fromEntries(new FormData(event.currentTarget));
    setBusy(true); setError(""); setSaved(false);
    try {
      const response = await fetch(`${PUBLIC_API_URL}/auth/me/`, {
        method: "PATCH", credentials: "include",
        headers: { ...(await csrfHeaders()), "Content-Type": "application/json" },
        body: JSON.stringify(values),
      });
      const body = await response.json();
      if (!response.ok) throw new Error(extractApiError(body, "Could not save your profile."));
      await refresh(); onClose(); setSaved(true);
    } catch (caught) { setError(caught instanceof Error ? caught.message : "Could not save your profile."); }
    finally { setBusy(false); }
  }
  return <section id="profile-editor" className="profile-editor" aria-label="Your profile" hidden={!editing && !saved}>
    {editing && <form className="booking-edit-form" onSubmit={save}>
      <h2>Edit profile</h2>
      <fieldset disabled={busy}>
        <label>Full name<input name="full_name" autoComplete="name" autoFocus defaultValue={customer.full_name} required maxLength={150} /></label>
        <label>Email address<input name="email" type="email" autoComplete="email" value={email} onChange={e => setEmail(e.target.value)} required maxLength={150} /></label>
        {email.trim().toLowerCase() !== customer.email.toLowerCase() && <label>Current password<input name="current_password" type="password" autoComplete="current-password" required /><small>Confirm your password to change your sign-in email.</small></label>}
        <div className="booking-edit-actions"><button type="submit">{busy ? "Saving…" : "Save changes"}</button><button type="button" onClick={() => { onClose(); setError(""); setSaved(false); setEmail(customer.email); }}>Cancel</button></div>
      </fieldset>
      {error && <p className="form-error" role="alert">{error}</p>}
    </form>}
    {saved && !editing && <p role="status">Profile updated.</p>}
  </section>;
}
