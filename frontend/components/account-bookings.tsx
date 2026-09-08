"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { useAuth } from "@/components/auth-provider";
import { Booking, getMyBookings } from "@/lib/bookings";
import { formatEventDate, formatPrice } from "@/lib/events";

export function AccountBookings() {
  const { customer, loading } = useAuth();
  const [bookings, setBookings] = useState<Booking[] | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    if (loading) return;
    if (!customer) return;
    getMyBookings()
      .then(setBookings)
      .catch((caught) => setError(caught instanceof Error ? caught.message : "We could not load your bookings."));
  }, [customer, loading]);

  if (loading || (customer && bookings === null)) return <section className="account-shell"><p>Loading your account…</p></section>;
  if (!customer) return (
    <section className="account-shell empty-account">
      <p className="eyebrow">Customer account</p><h1>Sign in to see your bookings.</h1>
      <Link className="primary account-action" href="/login?next=/account">Sign in</Link>
    </section>
  );

  return (
    <section className="account-shell">
      <header className="account-heading">
        <div><p className="eyebrow">Customer account</p><h1>{customer.full_name || "Your bookings"}</h1></div>
        <p>{customer.email}</p>
      </header>
      <div className="section-heading"><div><p className="eyebrow">Booking history</p><h2>Upcoming and past events</h2></div></div>
      {error ? <p className="form-error" role="alert">{error}</p> : bookings?.length ? (
        <div className="booking-history">
          {bookings.map((booking) => (
            <Link className="booking-history-card" href={`/bookings/${booking.reference}`} key={booking.reference}>
              <div><span>{formatEventDate(booking.event.start_at)}</span><h3>{booking.event.title}</h3><p>{booking.event.venue_name}</p></div>
              <div className="booking-history-meta"><span className={`history-status history-status-${booking.status}`}>{booking.status.replaceAll("_", " ")}</span><strong>{formatPrice(booking.total)}</strong><small>{booking.quantity} {booking.quantity === 1 ? "ticket" : "tickets"} · {booking.reference}</small></div>
            </Link>
          ))}
        </div>
      ) : <div className="empty-state"><p>No bookings yet.</p><span>Your account bookings will appear here.</span><br /><Link href="/#events">Explore events</Link></div>}
    </section>
  );
}
