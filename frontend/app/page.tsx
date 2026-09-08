import { EventCard } from "@/components/event-card";
import { HomeActions } from "@/components/home-actions";
import { SiteHeader } from "@/components/site-header";
import { getEvents } from "@/lib/events";

export default async function Home() {
  const events = await getEvents();

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
        {events.length ? (
          <div className="event-grid">
            {events.map((event) => <EventCard event={event} key={event.slug} />)}
          </div>
        ) : (
          <div className="empty-state">
            <p>There are no published events yet.</p>
            <span>Administrators can publish the first event from the dashboard.</span>
          </div>
        )}
      </section>

      <footer><span>EventEveryday</span><span>Make a day of it.</span></footer>
    </main>
  );
}
