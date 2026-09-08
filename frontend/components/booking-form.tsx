"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";

import { createBooking } from "@/lib/bookings";
import { formatPrice } from "@/lib/events";
import { useAuth } from "@/components/auth-provider";

type BookingFormProps = {
  eventSlug: string;
  price: string;
  availableCapacity: number;
};

export function BookingForm({ eventSlug, price, availableCapacity }: BookingFormProps) {
  const router = useRouter();
  const { customer } = useAuth();
  const maximum = Math.min(availableCapacity, 10);
  const [quantity, setQuantity] = useState(maximum > 0 ? 1 : 0);
  const [attendees, setAttendees] = useState(maximum > 0 ? [""] : []);
  const [contactName, setContactName] = useState<string | null>(null);
  const [contactEmail, setContactEmail] = useState<string | null>(null);
  const [contactPhone, setContactPhone] = useState("");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  function changeQuantity(nextQuantity: number) {
    setQuantity(nextQuantity);
    setAttendees((current) =>
      Array.from({ length: nextQuantity }, (_, index) => current[index] ?? ""),
    );
  }

  function changeAttendee(index: number, value: string) {
    setAttendees((current) =>
      current.map((name, currentIndex) => (currentIndex === index ? value : name)),
    );
  }

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSubmitting(true);
    setError("");
    try {
      const booking = await createBooking({
        event_slug: eventSlug,
        contact_name: contactName ?? customer?.full_name ?? "",
        contact_email: contactEmail ?? customer?.email ?? "",
        contact_phone: contactPhone,
        attendees: attendees.map((full_name) => ({ full_name })),
      });
      sessionStorage.setItem(`booking-token:${booking.reference}`, booking.access_token);
      router.push(`/bookings/${booking.reference}`);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "We could not create this booking.");
      setSubmitting(false);
    }
  }

  if (maximum === 0) {
    return (
      <aside className="booking-panel booking-unavailable">
        <span>Tickets</span>
        <strong>Fully booked</strong>
        <p>No tickets are currently available for this event.</p>
      </aside>
    );
  }

  return (
    <aside className="booking-panel booking-form-panel">
      <div className="booking-price-line">
        <span>Tickets</span>
        <strong>{formatPrice(price)} each</strong>
      </div>
      <form onSubmit={submit}>
        <label>
          Number of tickets
          <select
            onChange={(event) => changeQuantity(Number(event.target.value))}
            value={quantity}
          >
            {Array.from({ length: maximum }, (_, index) => index + 1).map((value) => (
              <option key={value} value={value}>{value}</option>
            ))}
          </select>
        </label>

        <div className="booking-total">
          <span>Total</span>
          <strong>{formatPrice(String(Number(price) * quantity))}</strong>
        </div>

        <fieldset className="booking-attendees">
          <legend>Attendees</legend>
          {attendees.map((name, index) => (
            <label key={index}>
              Attendee {index + 1} full name
              <input required value={name} onChange={(event) => changeAttendee(index, event.target.value)} />
            </label>
          ))}
        </fieldset>

        <details className="booking-details" open>
          <summary>
            <span>Booking contact</span>
            <span className="booking-chevron" aria-hidden="true" />
          </summary>
          <div className="booking-details-content">
            {customer && <p className="signed-in-note">Booking as <strong>{customer.email}</strong>. This reservation will be saved to your account.</p>}
            <fieldset>
              <label>
                Full name
                <input required value={contactName ?? customer?.full_name ?? ""} onChange={(event) => setContactName(event.target.value)} />
              </label>
              <label>
                Email address
                <input required type="email" value={contactEmail ?? customer?.email ?? ""} onChange={(event) => setContactEmail(event.target.value)} />
              </label>
              <label>
                Phone <small>Optional</small>
                <input type="tel" value={contactPhone} onChange={(event) => setContactPhone(event.target.value)} />
              </label>
            </fieldset>

            {error && <p className="form-error" role="alert">{error}</p>}
            <button disabled={submitting} type="submit">
              {submitting ? "Reserving…" : "Reserve tickets"}
            </button>
            <small>Your reservation is held for 15 minutes before payment.</small>
          </div>
        </details>
      </form>
    </aside>
  );
}
