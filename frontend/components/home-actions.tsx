"use client";

import Link from "next/link";

import { useAuth } from "@/components/auth-provider";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api";
const ADMIN_URL = `${API_URL.replace(/\/api\/?$/, "")}/admin/`;

export function HomeActions() {
  const { customer, loading } = useAuth();

  return (
    <div className="actions">
      <a className="primary" href="#events">Browse events</a>
      {!loading && customer?.is_staff && (
        <Link className="secondary" href={ADMIN_URL}>Admin dashboard</Link>
      )}
    </div>
  );
}
