export const PUBLIC_API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api";

export async function csrfHeaders(): Promise<Record<string, string>> {
  const response = await fetch(`${PUBLIC_API_URL}/auth/csrf/`, {
    credentials: "include",
  });
  if (!response.ok) throw new Error("We could not start a secure session.");
  const body = await response.json() as { csrf_token: string };
  return { "X-CSRFToken": body.csrf_token };
}

export function extractApiError(value: unknown, fallback: string): string {
  if (!value || typeof value !== "object") return fallback;
  for (const message of Object.values(value as Record<string, unknown>)) {
    if (typeof message === "string") return message;
    if (Array.isArray(message) && message.length) {
      const first = message[0];
      if (typeof first === "string") return first;
      if (first && typeof first === "object") return extractApiError(first, fallback);
    }
  }
  return fallback;
}
