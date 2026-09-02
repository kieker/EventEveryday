import Link from "next/link";

import { BookingStatus } from "@/components/booking-status";

type BookingPageProps = { params: Promise<{ reference: string }> };

export default async function BookingPage({ params }: BookingPageProps) {
  const { reference } = await params;
  return (
    <main>
      <nav>
        <Link className="brand" href="/">EventEveryday</Link>
        <Link href="/#events">All events</Link>
      </nav>
      <BookingStatus reference={reference} />
    </main>
  );
}

