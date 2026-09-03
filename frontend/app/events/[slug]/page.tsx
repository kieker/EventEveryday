import type { Metadata } from "next";
import Image from "next/image";
import Link from "next/link";
import { notFound } from "next/navigation";

import { BookingForm } from "@/components/booking-form";
import { SiteLogo } from "@/components/site-logo";
import {
  formatEventDate,
  formatEventTime,
  getEvent,
  resolveEventImageUrl,
} from "@/lib/events";

type EventPageProps = {
  params: Promise<{ slug: string }>;
};

export async function generateMetadata({ params }: EventPageProps): Promise<Metadata> {
  const { slug } = await params;
  const event = await getEvent(slug);
  return event
    ? { title: `${event.title} | EventEveryday`, description: event.summary }
    : { title: "Event not found | EventEveryday" };
}

export default async function EventPage({ params }: EventPageProps) {
  const { slug } = await params;
  const event = await getEvent(slug);
  if (!event) notFound();

  return (
    <main>
      <nav>
        <SiteLogo />
        <Link href="/#events">All events</Link>
      </nav>

      <article className="event-detail">
        <header className="event-detail-header">
          <div>
            <p className="eyebrow">{formatEventDate(event.start_at)}</p>
            <h1>{event.title}</h1>
            <p className="intro">{event.summary}</p>
          </div>
          <BookingForm
            availableCapacity={event.available_capacity}
            eventSlug={event.slug}
            price={event.price}
          />
        </header>

        {event.image_url && (
          <div className="event-hero-image">
            <Image
              alt=""
              fill
              priority
              unoptimized
              sizes="100vw"
              src={resolveEventImageUrl(event.image_url)}
            />
          </div>
        )}

        <div className="event-detail-body">
          <section>
            <p className="eyebrow">About this event</p>
            <p className="event-description">{event.description}</p>
          </section>
          <dl>
            <div>
              <dt>Date</dt>
              <dd>{formatEventDate(event.start_at)}</dd>
            </div>
            <div>
              <dt>Time</dt>
              <dd>{formatEventTime(event.start_at)}–{formatEventTime(event.end_at)}</dd>
            </div>
            <div>
              <dt>Venue</dt>
              <dd>{event.venue_name}<br />{event.venue_address}</dd>
            </div>
            <div>
              <dt>Capacity</dt>
              <dd>{event.capacity} guests</dd>
            </div>
          </dl>
        </div>
      </article>
    </main>
  );
}
