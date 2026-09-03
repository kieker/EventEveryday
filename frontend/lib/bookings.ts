import type { EventSummary } from "@/lib/events";

const PUBLIC_API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api";

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
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const body = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(extractApiError(body));
  return body as BookingCreated;
}

export async function getBooking(reference: string, token: string) {
  try {
    const response = await fetch(
      `${PUBLIC_API_URL}/bookings/${encodeURIComponent(reference)}/`,
      { headers: { "X-Booking-Token": token }, cache: "no-store" },
    );
    if (!response.ok) return null;
    return response.json() as Promise<Booking>;
  } catch {
    return null;
  }
}

export async function createPayFastCheckout(reference: string, token: string) {
  const response = await fetch(
    `${PUBLIC_API_URL}/payments/payfast/checkout/${encodeURIComponent(reference)}/`,
    { method: "POST", headers: { "X-Booking-Token": token } },
  );
  const body = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(extractApiError(body));
  return body as PayFastCheckout;
}

function extractApiError(value: unknown): string {
  if (!value || typeof value !== "object") return "We could not create this booking.";
  for (const message of Object.values(value as Record<string, unknown>)) {
    if (typeof message === "string") return message;
    if (Array.isArray(message) && message.length) {
      const first = message[0];
      if (typeof first === "string") return first;
      if (first && typeof first === "object") return extractApiError(first);
    }
  }
  return "We could not create this booking.";
}
