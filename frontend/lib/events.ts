const API_URL = process.env.INTERNAL_API_URL ?? "http://localhost:8000/api";
const PUBLIC_API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api";

export type EventSummary = {
  slug: string;
  title: string;
  summary: string;
  venue_name: string;
  timezone: string;
  start_at: string;
  end_at: string;
  capacity: number;
  available_capacity: number;
  price: string;
  currency: "ZAR";
  image_url: string;
};

export type EventDetail = EventSummary & {
  description: string;
  venue_address: string;
};

export async function getEvents(): Promise<EventSummary[]> {
  try {
    const response = await fetch(`${API_URL}/events/`, { cache: "no-store" });
    if (!response.ok) return [];
    return response.json();
  } catch {
    return [];
  }
}

export async function getEvent(slug: string): Promise<EventDetail | null> {
  try {
    const response = await fetch(`${API_URL}/events/${encodeURIComponent(slug)}/`, {
      cache: "no-store",
    });
    if (!response.ok) return null;
    return response.json();
  } catch {
    return null;
  }
}

export function formatEventDate(value: string) {
  return new Intl.DateTimeFormat("en-ZA", {
    weekday: "short",
    day: "numeric",
    month: "short",
    year: "numeric",
  }).format(new Date(value));
}

export function formatEventTime(value: string) {
  return new Intl.DateTimeFormat("en-ZA", {
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(value));
}

export function formatPrice(price: string) {
  return new Intl.NumberFormat("en-ZA", {
    style: "currency",
    currency: "ZAR",
    minimumFractionDigits: 0,
  }).format(Number(price));
}

export function resolveEventImageUrl(value: string) {
  if (!value || /^https?:\/\//i.test(value)) return value;
  const publicOrigin = new URL(PUBLIC_API_URL).origin;
  return new URL(value, publicOrigin).toString();
}
