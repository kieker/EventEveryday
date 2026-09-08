"use client";

import { FormEvent, useState } from "react";

import { Booking, updateBooking } from "@/lib/bookings";

export function BookingEditor({ booking, onUpdated }: { booking: Booking; onUpdated: (booking: Booking) => void }) {
  const [editing, setEditing] = useState(false);
  const [contactName, setContactName] = useState(booking.contact_name);
  const [contactEmail, setContactEmail] = useState(booking.contact_email);
  const [contactPhone, setContactPhone] = useState(booking.contact_phone);
  const [attendees, setAttendees] = useState(booking.attendees.map(({ full_name }) => full_name));
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  function cancel() {
    setContactName(booking.contact_name);
    setContactEmail(booking.contact_email);
    setContactPhone(booking.contact_phone);
    setAttendees(booking.attendees.map(({ full_name }) => full_name));
    setError("");
    setEditing(false);
  }

  async function save(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSaving(true);
    setError("");
    try {
      const token = sessionStorage.getItem(`booking-token:${booking.reference}`);
      const updated = await updateBooking(booking.reference, token, {
        contact_name: contactName,
        contact_email: contactEmail,
        contact_phone: contactPhone,
        attendees: attendees.map((full_name) => ({ full_name })),
      });
      onUpdated(updated);
      setEditing(false);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "We could not update this booking.");
    } finally {
      setSaving(false);
    }
  }

  if (!editing) {
    return (
      <div className="booking-edit-summary">
        <section>
          <h2>Attendees</h2>
          <ol>{booking.attendees.map((attendee, index) => <li key={`${index}-${attendee.full_name}`}>{attendee.full_name}</li>)}</ol>
        </section>
        <section>
          <h2>Booking contact</h2>
          <p>{booking.contact_name}<br />{booking.contact_email}{booking.contact_phone && <><br />{booking.contact_phone}</>}</p>
          <button className="booking-edit-button" onClick={() => setEditing(true)} type="button">Edit details</button>
        </section>
      </div>
    );
  }

  return (
    <form className="booking-edit-form" onSubmit={save}>
      <div>
        <h2>Attendees</h2>
        {attendees.map((name, index) => (
          <label key={index}>Attendee {index + 1} full name
            <input required value={name} onChange={(event) => setAttendees((current) => current.map((value, currentIndex) => currentIndex === index ? event.target.value : value))} />
          </label>
        ))}
      </div>
      <div>
        <h2>Booking contact</h2>
        <label>Full name<input required value={contactName} onChange={(event) => setContactName(event.target.value)} /></label>
        <label>Email address<input required type="email" value={contactEmail} onChange={(event) => setContactEmail(event.target.value)} /></label>
        <label>Phone <small>Optional</small><input type="tel" value={contactPhone} onChange={(event) => setContactPhone(event.target.value)} /></label>
        {error && <p className="form-error" role="alert">{error}</p>}
        <div className="booking-edit-actions">
          <button disabled={saving} type="submit">{saving ? "Saving…" : "Save changes"}</button>
          <button disabled={saving} onClick={cancel} type="button">Cancel</button>
        </div>
      </div>
    </form>
  );
}
