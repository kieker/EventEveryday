import { EventCard } from "@/components/event-card";
import { SiteLogo } from "@/components/site-logo";
import { getEvents } from "@/lib/events";

const API_URL = process.env.INTERNAL_API_URL ?? "http://localhost:8000/api";

type Health = {
  service: string;
  status: string;
};

async function getApiHealth(): Promise<Health | null> {
  try {
    const response = await fetch(`${API_URL}/health/`, { cache: "no-store" });
    if (!response.ok) return null;
    return response.json();
  } catch {
    return null;
  }
}

export default async function Home() {
  const health = await getApiHealth();
  const events = await getEvents();

  return (
    <main>
      <nav>
        <SiteLogo />
        <span>Proof of concept</span>
      </nav>

      <section className="hero">
        <p className="eyebrow">Events worth showing up for</p>
        <h1>Find your next memorable event.</h1>
        <p className="intro">
          Event discovery, secure PayFast booking, attendee management, and calendars—built for South Africa.
        </p>
        <div className="actions">
          <a className="primary" href="#foundation">Explore the foundation</a>
          <a className="secondary" href="http://localhost:8000/admin/">Admin dashboard</a>
        </div>
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

      <section className="foundation" id="foundation">
        <article>
          <p className="number">01</p>
          <h2>Publish</h2>
          <p>Administrators create and manage events from a focused dashboard.</p>
        </article>
        <article>
          <p className="number">02</p>
          <h2>Book</h2>
          <p>Guests and members reserve named tickets and pay securely in rand.</p>
        </article>
        <article>
          <p className="number">03</p>
          <h2>Attend</h2>
          <p>Organizers manage attendee lists, calendars, and future certificates.</p>
        </article>
      </section>

      <footer>
        <span>Foundation status</span>
        <span className={health ? "status healthy" : "status unavailable"}>
          {health ? "API connected" : "API unavailable"}
        </span>
      </footer>
    </main>
  );
}
