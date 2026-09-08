import { BookingStatus } from "@/components/booking-status";
import { SiteHeader } from "@/components/site-header";

type BookingPageProps = { params: Promise<{ reference: string }> };

export default async function BookingPage({ params }: BookingPageProps) {
  const { reference } = await params;
  return (
    <main>
      <SiteHeader />
      <BookingStatus reference={reference} />
    </main>
  );
}
