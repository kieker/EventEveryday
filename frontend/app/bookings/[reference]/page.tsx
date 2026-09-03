import Link from "next/link";

import { BookingStatus } from "@/components/booking-status";
import { SiteLogo } from "@/components/site-logo";

type BookingPageProps = { params: Promise<{ reference: string }> };

export default async function BookingPage({ params }: BookingPageProps) {
  const { reference } = await params;
  return (
    <main>
      <nav>
        <SiteLogo />
        <Link href="/#events">All events</Link>
      </nav>
      <BookingStatus reference={reference} />
    </main>
  );
}
