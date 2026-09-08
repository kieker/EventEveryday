import { csrfHeaders, extractApiError, PUBLIC_API_URL } from "@/lib/api";

export type Customer = {
  id: number;
  email: string;
  full_name: string;
  is_staff: boolean;
};

async function authPost(path: string, payload?: Record<string, string>) {
  const response = await fetch(`${PUBLIC_API_URL}${path}`, {
    method: "POST",
    credentials: "include",
    headers: {
      ...(await csrfHeaders()),
      ...(payload ? { "Content-Type": "application/json" } : {}),
    },
    body: payload ? JSON.stringify(payload) : undefined,
  });
  const body = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(extractApiError(body, "We could not complete that request."));
  return body as Customer;
}

export async function getCurrentCustomer() {
  const response = await fetch(`${PUBLIC_API_URL}/auth/me/`, {
    credentials: "include",
    cache: "no-store",
  });
  if (response.status === 401 || response.status === 403) return null;
  if (!response.ok) throw new Error("We could not load your account.");
  return response.json() as Promise<Customer>;
}

export function registerCustomer(payload: { full_name: string; email: string; password: string }) {
  return authPost("/auth/register/", payload);
}

export function loginCustomer(payload: { email: string; password: string }) {
  return authPost("/auth/login/", payload);
}

export async function logoutCustomer() {
  await authPost("/auth/logout/");
}
