import Image from "next/image";
import Link from "next/link";

import {
  EventSummary,
  formatEventDate,
  formatPrice,
  resolveEventImageUrl,
} from "@/lib/events";

export function EventCard({ event }: { event: EventSummary }) {
  return (
    <article className="event-card">
      <Link className="event-image" href={`/events/${event.slug}`}>
        {event.image_url ? (
          <Image
            alt=""
            fill
            unoptimized
            sizes="(max-width: 720px) 100vw, 33vw"
            src={resolveEventImageUrl(event.image_url)}
          />
        ) : (
          <span className="event-image-placeholder" />
        )}
      </Link>
      <div className="event-card-copy">
        <p className="event-meta">
          {formatEventDate(event.start_at)} · {event.venue_name}
        </p>
        <h3><Link href={`/events/${event.slug}`}>{event.title}</Link></h3>
        <p>{event.summary}</p>
        <div className="event-card-footer">
          <strong>{formatPrice(event.price)}</strong>
          <Link href={`/events/${event.slug}`}>View event <span aria-hidden="true">→</span></Link>
        </div>
      </div>
    </article>
  );
}
