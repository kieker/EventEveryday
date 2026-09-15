import type { EventSummary } from "@/lib/events";
import { csrfHeaders, extractApiError, PUBLIC_API_URL } from "@/lib/api";

export type Booking = {
  reference: string;
  event: EventSummary;
  contact_name: string;
  contact_email: string;
  contact_phone: string;
  quantity: number;
  unit_price: string;
  total: string;
  currency: "ZAR";
  status: "pending_payment" | "confirmed" | "payment_failed" | "expired" | "cancelled";
  expires_at: string;
  payment_received: boolean;
  reconciliation_required: boolean;
  created_at: string;
  attendees: { full_name: string }[];
};

export type BookingCreated = Booking & { access_token: string };

export type PayFastCheckout = {
  action_url: string;
  fields: Record<string, string>;
};

export async function createBooking(payload: {
  event_slug: string;
  contact_name: string;
  contact_email: string;
  contact_phone: string;
  attendees: { full_name: string }[];
}) {
  const response = await fetch(`${PUBLIC_API_URL}/bookings/`, {
    method: "POST",
    credentials: "include",
    headers: { "Content-Type": "application/json", ...(await csrfHeaders()) },
    body: JSON.stringify(payload),
  });
  const body = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(extractApiError(body, "We could not create this booking."));
  return body as BookingCreated;
}

export async function getBooking(reference: string, token?: string | null) {
  try {
    const response = await fetch(
      `${PUBLIC_API_URL}/bookings/${encodeURIComponent(reference)}/`,
      { credentials: "include", headers: token ? { "X-Booking-Token": token } : {}, cache: "no-store" },
    );
    if (!response.ok) return null;
    return response.json() as Promise<Booking>;
  } catch {
    return null;
  }
}

export async function updateBooking(
  reference: string,
  token: string | null,
  payload: Pick<Booking, "contact_name" | "contact_email" | "contact_phone" | "attendees">,
) {
  const response = await fetch(`${PUBLIC_API_URL}/bookings/${encodeURIComponent(reference)}/`, {
    method: "PATCH",
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      ...(token ? { "X-Booking-Token": token } : {}),
      ...(await csrfHeaders()),
    },
    body: JSON.stringify(payload),
  });
  const body = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(extractApiError(body, "We could not update this booking."));
  return body as Booking;
}

export async function createPayFastCheckout(reference: string, token?: string | null) {
  const response = await fetch(
    `${PUBLIC_API_URL}/payments/payfast/checkout/${encodeURIComponent(reference)}/`,
    { method: "POST", credentials: "include", headers: { ...(token ? { "X-Booking-Token": token } : {}), ...(await csrfHeaders()) } },
  );
  const body = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(extractApiError(body, "PayFast checkout is unavailable."));
  return body as PayFastCheckout;
}

export async function getMyBookings() {
  const response = await fetch(`${PUBLIC_API_URL}/me/bookings/`, { credentials: "include", cache: "no-store" });
  const body = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(extractApiError(body, "We could not load your bookings."));
  return body as Booking[];
}
