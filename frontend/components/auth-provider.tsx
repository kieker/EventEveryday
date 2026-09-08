"use client";

import { createContext, ReactNode, useContext, useEffect, useState } from "react";

import { Customer, getCurrentCustomer } from "@/lib/auth";

type AuthContextValue = {
  customer: Customer | null;
  loading: boolean;
  refresh: () => Promise<void>;
};

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [customer, setCustomer] = useState<Customer | null>(null);
  const [loading, setLoading] = useState(true);

  async function refresh() {
    try {
      setCustomer(await getCurrentCustomer());
    } catch {
      setCustomer(null);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    getCurrentCustomer()
      .then(setCustomer)
      .catch(() => setCustomer(null))
      .finally(() => setLoading(false));
  }, []);

  return <AuthContext.Provider value={{ customer, loading, refresh }}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const value = useContext(AuthContext);
  if (!value) throw new Error("useAuth must be used inside AuthProvider.");
  return value;
}
