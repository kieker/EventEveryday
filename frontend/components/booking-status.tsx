"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { Booking, createPayFastCheckout, getBooking } from "@/lib/bookings";
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
      let result = token ? await getBooking(reference, token) : null;
      if (active) {
        setBooking(result);
        setLoading(false);
      }
      const returnedFromPayFast = new URLSearchParams(window.location.search).get("payment") === "returned";
      for (let attempt = 0; active && token && returnedFromPayFast && result?.status === "pending_payment" && attempt < 10; attempt += 1) {
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
        <p>This browser does not have the secure access token created with the reservation.</p>
        <Link className="primary" href="/#events">Browse events</Link>
      </div>
    );
  }

  async function continueToPayFast() {
    const token = sessionStorage.getItem(`booking-token:${reference}`);
    if (!token) {
      setPaymentError("The secure booking token is no longer available in this browser.");
      return;
    }
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
    </article>
  );
}
