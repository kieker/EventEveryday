# Acceptance verification — 9 September 2026

## Scope and automated checks

Implemented customer-visible late-payment reconciliation status, unconfirmed CSV timestamp suppression, and locked booking edits with a status/expiry recheck. Added explicit denial tests for anonymous customers, signed-in non-staff customers, and staff without model permissions accessing attendee lists or CSV export, plus an authorized-admin positive case.

- Full PostgreSQL backend suite: **59 tests passed**, on both the development stack and the fresh acceptance stack.
- Explicit regression-module run: **26 tests passed**, including actual PostgreSQL row-lock contention between booking edits and payment confirmation.
- Frontend lint and TypeScript checks: passed after the final frontend changes.
- Migration drift check: no changes detected.
- The CORS preflight test now declares its allowed origin, so alternate acceptance ports do not change its assumptions.

## Fresh startup

Built an isolated source snapshot using tracked and non-ignored untracked files, excluding local secrets, dependencies, databases, uploaded media, and build output. This includes the current uncommitted work; it is **not verification of a committed Git revision**.

Used `.env.example`, fresh PostgreSQL and frontend volumes, a separate Compose project (`ee-acceptance-06d47bd3`), and host ports 13000/18000/18025 to avoid the existing stack. Ran `docker compose up --build -d --wait`. Backend migrations and demo seeding completed, and all services started successfully.

Verified HTTP 200 from the frontend, API health endpoint, and published-events API. Ran the full backend suite in this stack. The temporary stack was stopped after verification; its source snapshot and named volumes were retained for inspection.

## Real PayFast sandbox walkthrough

Used the browser and PayFast's sandbox wallet, with R33.80 test tickets. These were simulated payments, not live charges. No payment callback was forged or mocked for these walkthroughs.

| Flow | Booking | Verified result |
| --- | --- | --- |
| Guest reservation and payment | `EVT-5754DD7157` | Signed checkout accepted by sandbox; real ITN confirmed booking; browser returned to confirmed status. |
| New customer account and payment | `EVT-EBD5E3B448` | Registered synthetic customer; booking linked to account; real ITN confirmed booking; return page displayed confirmed-ticket copy; booking appeared in account history. |
| Payment after hold expiry | `EVT-6B322CF49C` | Created a new test hold and opened checkout, then deliberately expired only that hold before completing sandbox payment. Real ITN recorded complete payment while booking remained expired. API returned `payment_received=true` and `reconciliation_required=true`. Return page and account history explained reconciliation. CSV confirmation time was empty while payment reference remained present. |

All three real callbacks passed signature, source-IP, amount, and PayFast server-confirmation checks. The late-payment callback recorded the manual refund/reconciliation note. No automatic refund is implemented or claimed.

The existing development database initially lacked the already-written booking snapshot migration; applied it to resolve a booking-creation HTTP 500. Refreshed the backend and frontend to use current sources and dependencies, including Redis.

The existing ngrok tunnel was stopped before testing. Restarted it with approval for callback verification, then stopped it again. Email was temporarily routed to Mailpit after discovering the existing stack used Resend; restored the configured provider afterward. Synthetic acceptance records were retained in the development database. The first guest reservation was created before the provider switch; later application emails used Mailpit.

## Tracked follow-ups

Per the user's scope decision, event search, profile editing, upcoming-only discovery, consistent South African date formatting, and production security configuration remain follow-ups. Production deployment acceptance is not established by these development/sandbox checks. Webhook rate limiting remains explicitly excluded.
