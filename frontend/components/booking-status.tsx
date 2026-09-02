"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { Booking, getBooking } from "@/lib/bookings";
import { formatEventDate, formatPrice } from "@/lib/events";

export function BookingStatus({ reference }: { reference: string }) {
  const [booking, setBooking] = useState<Booking | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let active = true;
    async function loadBooking() {
      await Promise.resolve();
      const token = sessionStorage.getItem(`booking-token:${reference}`);
      const result = token ? await getBooking(reference, token) : null;
      if (active) {
        setBooking(result);
        setLoading(false);
      }
    }
    void loadBooking();
    return () => {
      active = false;
    };
  }, [reference]);

  if (loading) return <div className="booking-message">Loading your booking…</div>;
  if (!booking) {
    return (
      <div className="booking-message">
        <p className="eyebrow">Booking unavailable</p>
        <h1>We can’t open this booking.</h1>
        <p>This browser does not have the secure access token created with the reservation.</p>
        <Link className="primary" href="/#events">Browse events</Link>
      </div>
    );
  }

  const statusLabel = booking.status.replaceAll("_", " ");
  return (
    <article className="booking-confirmation">
      <header>
        <div>
          <p className="eyebrow">Reservation created</p>
          <h1>{booking.event.title}</h1>
          <p className="intro">Your tickets are held while payment is pending.</p>
        </div>
        <div className={`booking-status booking-status-${booking.status}`}>
          <span>Status</span>
          <strong>{statusLabel}</strong>
        </div>
      </header>
      <div className="booking-reference">
        <span>Booking reference</span>
        <strong>{booking.reference}</strong>
      </div>
      <div className="booking-summary-grid">
        <section>
          <h2>Attendees</h2>
          <ol>{booking.attendees.map((attendee) => <li key={attendee.full_name}>{attendee.full_name}</li>)}</ol>
        </section>
        <dl>
          <div><dt>Date</dt><dd>{formatEventDate(booking.event.start_at)}</dd></div>
          <div><dt>Venue</dt><dd>{booking.event.venue_name}</dd></div>
          <div><dt>Contact</dt><dd>{booking.contact_name}<br />{booking.contact_email}</dd></div>
          <div><dt>Total</dt><dd>{formatPrice(booking.total)}</dd></div>
        </dl>
      </div>
      {booking.status === "pending_payment" && (
        <div className="payment-next-step">
          <div><strong>Payment comes next</strong><p>PayFast checkout will be connected in the next implementation stage.</p></div>
          <button disabled type="button">Continue to PayFast</button>
        </div>
      )}
    </article>
  );
}
