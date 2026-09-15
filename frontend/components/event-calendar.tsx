"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useAuth } from "@/components/auth-provider";
import { PUBLIC_API_URL, extractApiError } from "@/lib/api";
import { formatEventDate, formatEventTime } from "@/lib/events";
import { CalendarSelect } from "@/components/calendar-select";

type CalendarEvent = {
  id: number; slug: string; title: string; venue_name: string;
  start_at: string; end_at: string; timezone: string; status: string;
};
const zone = "Africa/Johannesburg";
const dayKey = (date: Date) => new Intl.DateTimeFormat("en-CA", { timeZone: zone, year: "numeric", month: "2-digit", day: "2-digit" }).format(date);
const stamp = (value: string) => `${formatEventDate(value)} · ${formatEventTime(value)}`;

export function EventCalendar() {
  const { customer, loading: authLoading } = useAuth();
  const [month, setMonth] = useState(() => dayKey(new Date()).slice(0, 7));
  const [scope, setScope] = useState("public");
  const [view, setView] = useState("month");
  const [result, setResult] = useState<{ key: string; events: CalendarEvent[]; error: string } | null>(null);
  const activeScope = scope === "admin" && !customer?.is_staff || scope === "mine" && !customer ? "public" : scope;
  const requestKey = `${month}:${activeScope}:${customer?.id ?? "guest"}`;
  const ready = result?.key === requestKey;
  const events = ready ? result.events : [];
  const error = ready ? result.error : "";

  useEffect(() => {
    if (authLoading) return;
    const controller = new AbortController();
    fetch(`${PUBLIC_API_URL}/events/calendar/?month=${month}&scope=${activeScope}`, { credentials: "include", cache: "no-store", signal: controller.signal })
      .then(async response => {
        const body = await response.json();
        if (!response.ok) throw new Error(extractApiError(body, "Could not load the calendar."));
        setResult({ key: requestKey, events: body, error: "" });
      }).catch(error => {
        if (!controller.signal.aborted) setResult({ key: requestKey, events: [], error: error.message });
      });
    return () => controller.abort();
  }, [month, activeScope, requestKey, authLoading]);

  const [year, number] = month.split("-").map(Number);
  const first = new Date(Date.UTC(year, number - 1, 1));
  const days = new Date(Date.UTC(year, number, 0)).getUTCDate();
  const offset = (first.getUTCDay() + 6) % 7;
  const label = first.toLocaleDateString("en-ZA", { month: "long", year: "numeric", timeZone: "UTC" });
  function move(delta: number) {
    setMonth(new Date(Date.UTC(year, number - 1 + delta, 1)).toISOString().slice(0, 7));
  }
  function eventLink(event: CalendarEvent) {
    if (activeScope === "admin") return `${new URL(PUBLIC_API_URL).origin}/admin/events/event/${event.id}/change/`;
    return activeScope === "mine" ? "/account" : `/events/${event.slug}`;
  }
  return <section className="calendar-section">
    <p className="eyebrow">Make time for something good</p>
    <h1>Event calendar</h1>
    <p>Explore what’s on. All dates and times are shown in South African time (SAST).</p>
    <div className="calendar-toolbar">
      <div className="calendar-scope"><CalendarSelect label="Calendar" value={activeScope} onValueChange={setScope} options={[
        { value: "public", label: "Public events" },
        ...(customer ? [{ value: "mine", label: "My confirmed bookings" }] : []),
        ...(customer?.is_staff ? [{ value: "admin", label: "All events · Admin" }] : []),
      ]} /></div>
      <div className="calendar-controls" role="group" aria-label="Month navigation">
        <button type="button" onClick={() => move(-1)} aria-label="Previous month"><svg aria-hidden="true" viewBox="0 0 24 24"><path d="M19 12H5m6-6-6 6 6 6" /></svg></button>
        <h2 aria-live="polite" aria-atomic="true">{label}</h2>
        <button type="button" onClick={() => move(1)} aria-label="Next month"><svg aria-hidden="true" viewBox="0 0 24 24"><path d="M5 12h14m-6-6 6 6-6 6" /></svg></button>
        <button className="calendar-today-button" type="button" onClick={() => setMonth(dayKey(new Date()).slice(0, 7))}>Today</button>
      </div>
      <div className="calendar-view"><CalendarSelect label="View" value={view} onValueChange={setView} options={[{ value: "month", label: "Month" }, { value: "list", label: "List" }]} /></div>
    </div>
    {!ready || authLoading ? <p role="status">Loading calendar…</p> : error ? <p role="alert">{error}</p> : <>
      {!events.length && <p role="status">No {activeScope === "mine" ? "confirmed bookings" : "events"} this month.</p>}
      {view === "month" ? <div className="calendar-scroll"><div className="calendar-grid">
        {["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"].map(day => <div className="calendar-weekday" key={day}>{day}</div>)}
        {Array.from({ length: Math.ceil((offset + days) / 7) * 7 }, (_, index) => {
          const day = index - offset + 1;
          if (day < 1 || day > days) return <div className="calendar-day calendar-empty" key={index} />;
          const key = `${month}-${String(day).padStart(2, "0")}`;
          const matches = events.filter(event => dayKey(new Date(event.start_at)) <= key && dayKey(new Date(new Date(event.end_at).getTime() - 1)) >= key);
          return <div className="calendar-day" key={key}><time dateTime={key} className={key === dayKey(new Date()) ? "calendar-today" : ""}>{day}</time>{matches.map(event => <Link className="calendar-event" href={eventLink(event)} key={event.id}>{event.title}<small>{stamp(event.start_at)}{activeScope !== "public" ? ` · ${event.status}` : ""}</small></Link>)}</div>;
        })}
      </div></div> : <div className="calendar-list">{events.map(event => <article key={event.id}><h3><Link href={eventLink(event)}>{event.title}</Link></h3><p>{stamp(event.start_at)} – {stamp(event.end_at)}</p><p>{event.venue_name}{activeScope !== "public" ? ` · ${event.status}` : ""}</p>{activeScope === "admin" && <a href={`${new URL(PUBLIC_API_URL).origin}/admin/bookings/booking/?event__id__exact=${event.id}&status__exact=confirmed`}>Manage attendees and export CSV</a>}</article>)}</div>}
    </>}
    {!customer && !authLoading && <p><Link href="/login">Sign in</Link> to see your confirmed bookings.</p>}
  </section>;
}
