import { EventCard } from "@/components/event-card";
import { HomeActions } from "@/components/home-actions";
import { SiteHeader } from "@/components/site-header";
import { getEvents } from "@/lib/events";
import Link from "next/link";

export default async function Home({ searchParams }: { searchParams: Promise<{ q?: string }> }) {
  const params = await searchParams;
  const query = typeof params.q === "string" ? params.q.trim().slice(0, 200) : "";
  const events = await getEvents(query);

  return (
    <main>
      <SiteHeader showEvents={false} />

      <section className="hero">
        <p className="eyebrow">Events worth showing up for</p>
        <h1>Find your next memorable event.</h1>
        <p className="intro">
          Event discovery, secure PayFast booking, attendee management, and calendars—built for South Africa.
        </p>
        <HomeActions />
      </section>

      <section className="events-section" id="events">
        <div className="section-heading">
          <div>
            <p className="eyebrow">Coming up</p>
            <h2>Events to look forward to.</h2>
          </div>
          <p>{events.length ? `${events.length} events available` : "New events coming soon"}</p>
        </div>
        <form action="/#events" className="event-search" role="search">
          <label htmlFor="event-search">Find an event</label>
          <div><input id="event-search" type="search" name="q" defaultValue={query} placeholder="Search events, venues or cities" maxLength={200} /><button type="submit">Search</button>{query && <Link href="/#events">Clear</Link>}</div>
        </form>
        {events.length ? (
          <div className="event-grid">
            {events.map((event) => <EventCard event={event} key={event.slug} />)}
          </div>
        ) : (
          <div className="empty-state">
            <p>{query ? `No events match “${query}”.` : "New events coming soon."}</p>
            <span>{query ? "Try another event, venue or city." : "Check back soon for upcoming events."}</span>
          </div>
        )}
      </section>

      <footer><span>EventEveryday</span><span>Make a day of it.</span></footer>
    </main>
  );
}
