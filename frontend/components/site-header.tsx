"use client";

import Link from "next/link";

import { SiteLogo } from "@/components/site-logo";
import { logoutCustomer } from "@/lib/auth";
import { useAuth } from "@/components/auth-provider";

export function SiteHeader({ showEvents = true }: { showEvents?: boolean }) {
  const { customer, loading, refresh } = useAuth();

  async function signOut() {
    await logoutCustomer();
    await refresh();
  }

  return (
    <nav>
      <SiteLogo />
      <div className="site-nav-links">
        {showEvents && <Link href="/#events">Events</Link>}
        <Link href="/calendar">Calendar</Link>
        {!loading && customer ? (
          <>
            <Link href="/account">My bookings</Link>
            <button onClick={signOut} type="button">Sign out</button>
          </>
        ) : !loading ? <Link href="/login">Sign in</Link> : null}
      </div>
    </nav>
  );
}
