"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { useAuth } from "@/components/auth-provider";
import { ProfileEditor } from "@/components/profile-editor";
import { Booking, getMyBookings } from "@/lib/bookings";
import { formatEventDate, formatPrice } from "@/lib/events";

export function AccountBookings() {
  const { customer, loading } = useAuth();
  const [bookings, setBookings] = useState<Booking[] | null>(null);
  const [error, setError] = useState("");
  const [editingProfile, setEditingProfile] = useState(false);

  useEffect(() => {
    if (loading) return;
    if (!customer) return;
    getMyBookings()
      .then(setBookings)
      .catch((caught) => setError(caught instanceof Error ? caught.message : "We could not load your bookings."));
  }, [customer, loading]);

  if (loading || (customer && bookings === null && !error)) return <section className="account-shell"><p>Loading your account…</p></section>;
  if (!customer) return (
    <section className="account-shell empty-account">
      <p className="eyebrow">Customer account</p><h1>Sign in to see your bookings.</h1>
      <Link className="primary account-action" href="/login?next=/account">Sign in</Link>
    </section>
  );

  return (
    <>
    <div className="account-profile-actions">
      <button className="booking-edit-button profile-edit-button" type="button" aria-expanded={editingProfile} aria-controls="profile-editor" onClick={() => setEditingProfile(true)}>
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
          <path d="m16 3 5 5M4 20l5-1L21 7a2.1 2.1 0 0 0-4-4L5 15l-1 5Z" />
        </svg>
        Edit profile
      </button>
    </div>
    <section className="account-shell">
      <header className="account-heading">
        <div><p className="eyebrow">Customer account</p><h1>{customer.full_name || "Your bookings"}</h1></div>
        <p>{customer.email}</p>
      </header>
      <ProfileEditor editing={editingProfile} onClose={() => setEditingProfile(false)} />
      <div className="section-heading"><div><p className="eyebrow">Booking history</p><h2>Upcoming and past events</h2></div></div>
      {error ? <p className="form-error" role="alert">{error}</p> : bookings?.length ? (
        <div className="booking-history">
          {bookings.map((booking) => (
            <Link className="booking-history-card" href={`/bookings/${booking.reference}`} key={booking.reference}>
              <div><span>{formatEventDate(booking.event.start_at)}</span><h3>{booking.event.title}</h3><p>{booking.event.venue_name}</p>{booking.reconciliation_required && <p>Payment received; tickets are not confirmed. Open this booking for reconciliation details.</p>}</div>
              <div className="booking-history-meta"><span className={`history-status history-status-${booking.status}`}>{booking.reconciliation_required ? "Payment received · reconciliation required" : booking.status.replaceAll("_", " ")}</span><strong>{formatPrice(booking.total)}</strong><small>{booking.quantity} {booking.quantity === 1 ? "ticket" : "tickets"} · {booking.reference}</small></div>
            </Link>
          ))}
        </div>
      ) : <div className="empty-state"><p>No bookings yet.</p><span>Your account bookings will appear here.</span><br /><Link href="/#events">Explore events</Link></div>}
    </section>
    </>
  );
}
