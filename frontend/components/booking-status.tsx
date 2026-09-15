"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { Booking, createPayFastCheckout, getBooking } from "@/lib/bookings";
import { BookingEditor } from "@/components/booking-editor";
import { formatEventDate, formatPrice } from "@/lib/events";

export function BookingStatus({ reference }: { reference: string }) {
  const [booking, setBooking] = useState<Booking | null>(null);
  const [loading, setLoading] = useState(true);
  const [paymentError, setPaymentError] = useState("");
  const [redirecting, setRedirecting] = useState(false);

  useEffect(() => {
    let active = true;
    async function loadBooking() {
      await Promise.resolve();
      const token = sessionStorage.getItem(`booking-token:${reference}`);
      let result = await getBooking(reference, token);
      if (active) {
        setBooking(result);
        setLoading(false);
      }
      const returnedFromPayFast = new URLSearchParams(window.location.search).get("payment") === "returned";
      for (let attempt = 0; active && returnedFromPayFast && result && !result.payment_received && result.status !== "confirmed" && attempt < 10; attempt += 1) {
        await new Promise((resolve) => window.setTimeout(resolve, 2000));
        result = await getBooking(reference, token);
        if (active) setBooking(result);
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
        <p>Sign in with the account that made this booking, or open it in the browser session where it was created.</p>
        <Link className="primary" href="/#events">Browse events</Link>
      </div>
    );
  }

  async function continueToPayFast() {
    const token = sessionStorage.getItem(`booking-token:${reference}`);
    setPaymentError("");
    setRedirecting(true);
    try {
      const checkout = await createPayFastCheckout(reference, token);
      const form = document.createElement("form");
      form.method = "POST";
      form.action = checkout.action_url;
      for (const [name, value] of Object.entries(checkout.fields)) {
        const input = document.createElement("input");
        input.type = "hidden";
        input.name = name;
        input.value = value;
        form.appendChild(input);
      }
      document.body.appendChild(form);
      form.submit();
    } catch (caught) {
      setPaymentError(caught instanceof Error ? caught.message : "PayFast checkout is unavailable.");
      setRedirecting(false);
    }
  }

  const statusLabel = booking.reconciliation_required ? "Payment received · reconciliation required" : booking.status.replaceAll("_", " ");
  return (
    <article className="booking-confirmation">
      <header>
        <div>
          <p className="eyebrow">Reservation created</p>
          <h1>{booking.event.title}</h1>
          <p className="intro">{booking.reconciliation_required
            ? "We received your payment, but your reservation was no longer active. Your tickets are not confirmed. Please contact the event organiser with your booking reference for payment reconciliation or a refund."
            : booking.status === "confirmed" ? "Your tickets are confirmed."
            : booking.status === "pending_payment" ? "Your tickets are held while payment is pending."
            : "Your reservation is no longer active and your tickets are not confirmed."}</p>
        </div>
        <div className={`booking-status booking-status-${booking.reconciliation_required ? "reconciliation" : booking.status}`} role="status">
          <svg className="booking-status-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
            <circle cx="12" cy="12" r="9" />
            {booking.reconciliation_required || booking.status === "payment_failed" ? (
              <path d="M12 7v6m0 4h.01" />
            ) : booking.status === "confirmed" ? (
              <path d="m8 12 3 3 5-6" />
            ) : booking.status === "cancelled" ? (
              <path d="m9 9 6 6m0-6-6 6" />
            ) : (
              <path d="M12 7v5l3 2" />
            )}
          </svg>
          <div>
            <span>Status</span>
            <strong>{statusLabel}</strong>
          </div>
        </div>
      </header>
      {booking.status === "pending_payment" && (
        <div className="payment-next-step">
          <div>
            <strong>Complete payment securely</strong>
            <p>You’ll be redirected to PayFast. EventEveryday never receives your card details.</p>
            {paymentError && <p className="payment-error" role="alert">{paymentError}</p>}
          </div>
          <button disabled={redirecting} onClick={continueToPayFast} type="button">
            {redirecting ? "Opening PayFast…" : "Continue to PayFast"}
          </button>
        </div>
      )}
      <div className="booking-reference">
        <span>Booking reference</span>
        <strong>{booking.reference}</strong>
      </div>
      <div className="booking-summary-grid">
        {booking.status === "pending_payment" ? (
          <BookingEditor booking={booking} onUpdated={setBooking} />
        ) : (
          <section>
            <h2>Attendees</h2>
            <ol>{booking.attendees.map((attendee) => <li key={attendee.full_name}>{attendee.full_name}</li>)}</ol>
          </section>
        )}
        <dl>
          <div><dt>Date</dt><dd>{formatEventDate(booking.event.start_at)}</dd></div>
          <div><dt>Venue</dt><dd>{booking.event.venue_name}</dd></div>
          {booking.status !== "pending_payment" && <div><dt>Contact</dt><dd>{booking.contact_name}<br />{booking.contact_email}{booking.contact_phone && <><br />{booking.contact_phone}</>}</dd></div>}
          <div className="booking-summary-total"><dt>Total</dt><dd>{formatPrice(booking.total)}</dd></div>
        </dl>
      </div>
    </article>
  );
}
