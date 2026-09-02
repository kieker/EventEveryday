# EventEveryday — Product and Technical Specification

Status: Initial draft  
Date: 2026-09-01

## 1. Product summary

EventEveryday is a web platform where organizers publish events and customers reserve and pay for attendance. Administrators manage events and attendee lists from a protected backend. Customers discover events, complete bookings on the frontend, and view relevant events in a calendar.

The initial market uses South African rand (`ZAR`) and PayFast. Checkout supports both registered customers and guests. Every ticket must be associated with an attendee name so that attendance records can support certificates in phase two.

The platform must never store raw card or bank-account details. Payments are processed by an external payment provider. EventEveryday stores only the provider name, a non-sensitive transaction reference, payment status, amount, currency, and timestamps needed to reconcile a booking.

## 2. Goals

- Let administrators create, update, publish, cancel, and inspect events.
- Let customers browse event details and book available tickets.
- Take payment through a hosted or tokenized provider flow without handling payment credentials.
- Give administrators an attendee list for each event and allow CSV export.
- Show events in a calendar, with customer-specific booking context when signed in.
- Run the complete development environment reproducibly with Docker.

## 3. Non-goals for the proof of concept

- A marketplace with multiple independent organizer accounts.
- Reserved seating or interactive seat maps.
- Discount codes, subscriptions, refunds, transfers, or ticket resale.
- Native mobile applications.
- Sophisticated tax, invoicing, accounting, or payout workflows.
- Production-scale email delivery, analytics, or fraud detection.

These may be added later, but they should not shape the first implementation unnecessarily.

## 4. Users and roles

### Visitor

- Browse and search published upcoming events.
- View event details and ticket availability.
- Start sign-up or sign-in, or continue as a guest at checkout.

### Customer

- Maintain a basic profile.
- Create a booking and complete payment.
- View their upcoming and past bookings.
- View booked events in a personal calendar.

### Guest customer

- Book without creating an account.
- Provide a contact email and the full name of each attendee covered by the booking.
- Receive a booking reference that can later be used to locate and claim eligible certificates.
- Optionally create an account later and claim matching bookings/certificates after verification.

### Administrator

- Use a protected administration dashboard.
- Manage events, ticket price, capacity, publication status, and schedule.
- View booking and payment status.
- View and export event attendee lists.
- View all events in an operational calendar.

For the proof of concept, administrators are internal staff. A future organizer role can introduce tenant-level access controls if the product becomes multi-organizer.

## 5. Core workflows

### Event publishing

1. An administrator creates a draft event with title, description, venue, timezone, start/end time, capacity, price, currency, and optional image.
2. The system validates that the end is after the start and that price and capacity are valid.
3. The administrator publishes the event.
4. The event becomes visible on the public event list and calendar.

### Booking and payment

1. A registered customer or guest selects a published event and ticket quantity.
2. The customer supplies contact details and one attendee name per ticket.
3. The backend validates availability and creates a time-limited pending booking.
4. The backend creates a PayFast payment request in South African rand.
5. The frontend redirects the customer to PayFast's secure payment UI.
6. PayFast sends a server-to-server payment notification to the backend.
7. The backend validates the notification and amount, records the PayFast transaction reference, and confirms the booking idempotently.
8. The frontend success page retrieves status from the backend; a browser redirect alone never confirms payment.

If payment fails or the reservation expires, held capacity is released. Duplicate webhook deliveries must not create duplicate payments or bookings.

### Attendee management

1. An administrator opens an event from the dashboard or admin calendar.
2. The attendee view lists confirmed bookings and customer details needed for admission.
3. The administrator exports a CSV generated on demand.

## 6. Functional requirements

### Events

- Event fields: ID, slug, title, summary/description, venue name/address, timezone, start/end, capacity, price, currency, image, status, and audit timestamps.
- Statuses: `draft`, `published`, `cancelled`, `completed`.
- Public APIs return only published events unless the caller is an administrator.
- Times are stored in UTC and rendered in the event's timezone.
- The administration home page provides an event overview using the available dashboard space rather than requiring administrators to navigate through the model list first.
- The overview shows event thumbnails, title and summary, publication status, schedule, venue, price, and capacity, with direct edit and remove links subject to Django permissions.
- Dashboard summary figures show total, published, upcoming, and draft event counts.
- On wide screens, the dashboard presents Administration, Events, and Recent actions side by side in that order, with Events receiving the widest working area. The panels stack responsively on smaller screens.
- The wide-screen dashboard must use the available viewport width and must not inherit Django's narrow default dashboard content constraint.
- Administrative headings and status indicators must meet readable contrast expectations in both light and dark themes.
- The administration interface uses the full content width without Django's collapsible navigation sidebar or its show/hide toggle.
- Header actions such as “View site” and “Log out” are visually distinct, high-contrast controls rather than low-emphasis text links.

### Bookings

- A booking belongs to one event and either a registered customer or a guest contact.
- Booking fields include a human-friendly booking reference, quantity, unit price snapshot, total, currency, status, and timestamps.
- A booking contains exactly one attendee record per ticket quantity, including the attendee's full name.
- Guest bookings require a contact email. A guest email does not automatically create a user account.
- Statuses: `pending_payment`, `confirmed`, `payment_failed`, `expired`, `cancelled`.
- Capacity is checked and reserved atomically to prevent overselling.
- Price and event details needed for historical accuracy are snapshotted on the booking.
- Guest reservations hold capacity for 15 minutes while payment is pending.
- Booking creation is transactional and locks the event capacity calculation so simultaneous requests cannot intentionally allocate the same remaining tickets.
- A guest receives a high-entropy access token when the booking is created. Only its hash is stored; subsequent status requests provide the token in a request header so contact and attendee details are not public by booking reference alone.
- The first frontend implementation retains this access token in browser session storage. Email-based recovery and cross-device access are deferred until the notification stage.

### Payments

- Payment fields include booking, provider, provider transaction/session reference, expected and received amount, currency, status, and timestamps.
- No primary account number, CVV, bank credential, or other raw payment credential is persisted or logged.
- Webhook events are signature-verified, recorded sufficiently for audit, and processed idempotently.
- Secrets exist only in environment variables or a deployment secret manager.
- Logs redact authorization headers, cookies, payment payload secrets, and personal data where practical.
- The initial provider is PayFast and the initial/only proof-of-concept currency is `ZAR`.

### Calendar

- Public calendar: published events.
- Customer calendar: events attached to the signed-in customer's confirmed bookings.
- Admin calendar: all events, with status and a link to event/attendee management.
- Month and list views are sufficient for the proof of concept.
- A later release may add downloadable/subscribable ICS feeds.

### Export

- CSV export is restricted to administrators.
- Initial columns: event, booking reference, attendee/customer name, email, quantity, booking status, payment reference, and confirmation time.
- Export actions should be auditable in a production release.

## 7. Proposed architecture

### Frontend

- Next.js with TypeScript and the App Router.
- Server-rendered public event pages where useful for discovery and sharing.
- Authenticated account, checkout-status, and calendar screens.
- A calendar component that consumes the backend event API.

### Backend

- Django with Django REST Framework.
- Django Admin as the initial administration dashboard.
- PostgreSQL for transactional data.
- OpenAPI schema generated from the API for typed frontend integration if desired.
- A background worker is optional for the proof of concept; email and cleanup can initially use simple management commands or synchronous development behavior. Production should use a queue for notifications and scheduled expiry.

### Infrastructure

- Docker Compose services: `frontend`, `backend`, and `db`.
- Optional later services: `worker`, `scheduler`, and `redis`.
- Health checks, migrations, seeded development data, and `.env.example` are included.
- Uploaded media uses a Docker volume during development and object storage in production.

### Payment integration

The initial provider is PayFast, using its sandbox environment for the proof of concept and South African rand for all prices and payments. The backend will expose a small payment-provider interface so PayFast-specific request and notification logic does not leak into booking rules. A mock provider remains useful for fast, deterministic automated tests.

## 8. Initial data model

- `User`: Django user identity plus name and role/profile metadata.
- `Event`: event content, schedule, venue, status, capacity, price, and currency.
- `Booking`: optional registered customer, guest/contact details, event, quantity, price snapshot, reference, status, and expiry.
- `Attendee`: booking, full name, and future certificate/attendance associations.
- `Payment`: booking, provider references, monetary values, and status.
- `PaymentWebhookEvent`: provider event ID, processing state, timestamps, and a safely retained/redacted audit payload where appropriate.

One booking may contain multiple general-admission tickets, but each ticket has a named attendee from the beginning. Ticket types may be introduced later without changing the payment boundary.

## 9. API outline

Public/customer endpoints:

- `GET /api/events`
- `GET /api/events/{slug}`
- `POST /api/bookings`
- `GET /api/bookings/{reference}` using authenticated ownership or the `X-Booking-Token` guest credential
- `GET /api/me/bookings`
- `POST /api/bookings/{reference}/payment-session`
- `POST /api/payments/payfast/notify` (provider-authenticated)

Administration may initially use Django Admin. Explicit admin APIs can be added when a custom dashboard is justified.

## 10. Security and privacy baseline

- HTTPS is mandatory outside local development.
- Use secure, HTTP-only cookies for browser authentication; protect state-changing requests against CSRF.
- Enforce authorization in the backend, not only in the UI.
- Apply rate limiting to authentication, booking, and webhook endpoints.
- Validate uploaded files and restrict their type and size.
- Collect only personal information necessary for booking and attendance.
- Do not expose a public attendee directory. Certificate discovery must limit enumeration and require proof of control before revealing or attaching personal records.
- Define data retention and deletion rules before production launch.
- Do not claim PCI compliance solely because payment data is not stored; use the provider's hosted/tokenized flow and confirm the applicable compliance obligations before launch.

## 11. Proof of concept

### Scope

A short proof of concept should demonstrate one complete vertical slice:

1. Start the stack with Docker Compose.
2. Sign in as an administrator and create/publish an event in Django Admin.
3. Browse the event in Next.js.
4. Continue as a guest, provide a contact email and attendee names, and reserve one or more tickets.
5. Complete a PayFast sandbox payment in `ZAR` and confirm it through a validated server notification.
6. Sign in and complete the same booking path as a registered customer, then see the event in the customer's booking list/calendar.
7. Open the event in the admin calendar and export confirmed attendees as CSV.

### Acceptance criteria

- A clean checkout can run locally from documented commands.
- Database migrations and seed data run without host-specific setup.
- Concurrent booking logic cannot confirm more tickets than event capacity in covered tests.
- Replaying the same payment webhook has no additional effect.
- The booking stores a transaction reference but no raw payment credential.
- Guest checkout records one attendee name per ticket without creating an account.
- Non-admin users cannot access attendee lists or exports.
- Core backend tests and frontend lint/type checks pass in containers or documented local tooling.

## 12. Suggested delivery stages

### Stage 1 — Foundation

Docker Compose, Django/DRF, Next.js, PostgreSQL, authentication, migrations, and development documentation.

### Stage 2 — Event and booking slice

Event administration, public listing/details, availability, pending bookings, and account booking list.

### Stage 3 — Payment and confirmation

Provider sandbox, secure webhook processing, expiry behavior, and success/failure UI.

### Stage 4 — Calendars and export

Customer/admin calendar views, attendee management links, CSV export, and end-to-end verification.

## 13. Open decisions

- Whether events have one price or multiple ticket types.
- Whether “admins” are one internal team or separate organizers who must not see each other's data.
- Whether calendar integration means an in-app calendar only, or also Google/Apple/Outlook subscriptions.
- Whether certificate eligibility is based on a confirmed booking, recorded attendance, or manual administrator approval.
- What proof a guest must provide to retrieve or claim a certificate: booking reference plus email verification is recommended.
- Required cancellation and refund policy.
- Hosting platform, expected traffic, privacy jurisdiction, and retention requirements.

## 14. Recommendation

Proceed with Django/DRF, Next.js, PostgreSQL, and Docker Compose. Django Admin is the strongest fit for a fast, reliable first backend. Keep the first release to a single organizer, named general-admission tickets, registered and guest checkout, `ZAR`, and PayFast sandbox payments. This validates the risky parts—capacity, payment confirmation, authorization, guest identity, and export—before investing in a custom administration interface.

## 15. Phase two — attendance certificates

- Administrators can mark attendees as attended or otherwise certificate-eligible.
- The system generates a certificate for an eligible attendee using the exact attendee name captured at booking, with an administrator correction workflow for genuine errors.
- Signed-in users see certificates associated with their verified bookings on their profile.
- Guests can search for a certificate using their attendee name, but name matching alone must not reveal or download a certificate.
- A matching guest completes an additional verification step, recommended as booking reference plus a one-time code sent to the booking contact email.
- After verification, a guest may download the certificate directly or create/sign in to an account and claim the booking and certificate.
- Search responses are rate-limited and avoid confirming unnecessary personal details. Matching should account for case, spacing, and common punctuation differences without silently merging different people.
- Generated certificates should carry a non-guessable public verification identifier so a recipient can prove authenticity without exposing booking or payment data.
