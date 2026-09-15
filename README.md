# EventEveryday

EventEveryday is a production-shaped proof of concept for publishing events, accepting named guest or account bookings, taking PayFast payments in South African rand, and managing attendees.

The product and technical decisions are recorded in [SPEC.md](./SPEC.md).

## Stack

- Next.js 16 and React 19
- Django 5.2 LTS and Django REST Framework
- PostgreSQL 17
- Docker Compose

## Start the development environment

Requirements: Docker Desktop with Docker Compose.

1. Copy `.env.example` to `.env` and review the development values.
2. Start the services:

   ```bash
   docker compose up --build
   ```

3. Open the frontend at <http://localhost:3000>.
4. Open the API health endpoint at <http://localhost:8000/api/health/>.
5. Open Django Admin at <http://localhost:8000/admin/>.
6. Open the local Mailpit inbox at <http://localhost:8025/>.

When all three `DEV_ADMIN_*` values are present in the local `.env`, startup creates or updates that development administrator automatically. The seed is idempotent and the credentials are intentionally excluded from version control.

Startup also seeds three published development events when their slugs are not already present. Manage events at `/admin/events/event/`, list published events at `/api/events/`, and open public event details at `/events/{slug}`.

Administrators may upload an event image directly or provide an external image URL. An uploaded image takes precedence. Development uploads are stored under `backend/media/`; production deployments should configure durable object storage.

Guest checkout creates a 15-minute pending reservation with one named attendee per ticket. Booking status is protected by a one-time returned access token whose hash is stored by the backend. Administrators can manage bookings and attendees or export selected bookings from Django Admin.

Customers can create an account or sign in from the frontend. Authenticated bookings are attached to the customer automatically and appear under **My bookings**. Browser authentication uses Django's secure, HTTP-only session cookie, and state-changing requests include a CSRF token; guest checkout remains available without an account.

## Domain and HTTPS on an Oracle VM

The optional Caddy overlay routes `/api/`, `/admin/`, `/static/`, and `/media/` to Django, and other requests to Next.js. Caddy obtains and renews a certificate for `SITE_DOMAIN` automatically.

1. Point an `A` record for your domain to the VM's public IPv4 address. If an `AAAA` record exists, it must also point to this VM or be removed.
2. In OCI, allow inbound TCP ports 80 and 443 from `0.0.0.0/0` on the VNIC's NSG or subnet security list. Allow them in the VM firewall too, if one is active.
3. In the VM's git-ignored `.env`, set the real domain (without `https://`):

   ```env
   SITE_DOMAIN=eventeveryday.kiekerweb.co.za
   HOST_BIND_IP=127.0.0.1
   NEXT_PUBLIC_API_URL=https://eventeveryday.kiekerweb.co.za/api
   DJANGO_ALLOWED_HOSTS=eventeveryday.kiekerweb.co.za,localhost,127.0.0.1,backend
   DJANGO_CORS_ALLOWED_ORIGINS=https://eventeveryday.kiekerweb.co.za
   PUBLIC_FRONTEND_URL=https://eventeveryday.kiekerweb.co.za
   PUBLIC_BACKEND_URL=https://eventeveryday.kiekerweb.co.za
   PAYFAST_NOTIFY_URL=https://eventeveryday.kiekerweb.co.za/api/payments/payfast/notify/
   ```

4. Start the overlay from the project directory:

   ```bash
   docker compose -f compose.yaml -f compose.caddy.yaml up -d --build
   docker compose -f compose.yaml -f compose.caddy.yaml logs caddy --tail 50
   ```

5. Check `https://eventeveryday.kiekerweb.co.za/` and `https://eventeveryday.kiekerweb.co.za/api/health/`. After HTTPS works, remove the temporary OCI ingress rule for port 3000; do not open 8000 or 8025 publicly. With `HOST_BIND_IP=127.0.0.1`, those three host ports are reachable only from the VM.

This overlay puts HTTPS in front of the current development containers. Before accepting real bookings or payments, switch to production server processes, disable Django debug mode, configure production secrets and email, and provide durable storage for uploaded media.

## Calendars

Open `/calendar` for month and list views in South African time. Signed-in customers can select their confirmed bookings; staff with event viewing permission can select all events and open Django event management. The admin list view also links to attendees and the existing CSV export action. The API at `/api/events/calendar/?month=YYYY-MM&scope=public` supports `public`, `mine`, and `admin` scopes with server-side access checks.

## Email delivery

Development email is captured by Mailpit and never leaves the local machine. To use Resend in staging or production, verify a sending domain, create a domain-restricted sending API key, and set these secret environment values:

```env
EMAIL_PROVIDER=resend
RESEND_API_KEY=re_replace_with_your_secret_key
DEFAULT_FROM_EMAIL=EventEveryday <bookings@updates.example.com>
EMAIL_REPLY_TO=support@example.com
```

Never commit the API key. Keep `EMAIL_PROVIDER=smtp` locally unless you intentionally want to exercise real delivery.

## PayFast sandbox

The local `.env` contains the developer's git-ignored sandbox credentials. Public examples intentionally leave all PayFast credentials blank.

Checkout uses PayFast Custom Integration: EventEveryday creates a signed form and the browser posts it directly to the PayFast sandbox. PayFast confirms the outcome through an Instant Transaction Notification (ITN); the browser return URL is never trusted as proof of payment.

`PAYFAST_NOTIFY_URL` must be a public URL that routes to `/api/payments/payfast/notify/`. PayFast cannot reach `localhost`, so automatic confirmation during local development requires a public HTTPS tunnel. Set the tunnel URL in `.env`, for example:

```env
PAYFAST_NOTIFY_URL=https://your-public-tunnel.example/api/payments/payfast/notify/
```

Restart the backend after changing PayFast environment values. Before production, replace every sandbox credential and URL with its live equivalent and review proxy/IP handling for the selected host.

Create the first administrator in a separate terminal:

```bash
docker compose exec backend python manage.py createsuperuser
```

Stop the services with `docker compose down`. The PostgreSQL database remains in its named Docker volume.

## Checks

See [ACCEPTANCE.md](./ACCEPTANCE.md) for the latest fresh-start and real PayFast sandbox walkthrough evidence and retained follow-ups.

```bash
docker compose run --rm backend python manage.py test
docker compose run --rm frontend npm run lint
docker compose run --rm frontend npm run typecheck
docker compose config --quiet
```

The payment concurrency tests use separate database connections and require row locking (PostgreSQL in Docker). They are skipped on SQLite. They cover competing reservations, duplicate and out-of-order webhooks, and confirmation racing ticket resale.

A verified payment confirms tickets only while its reservation is still active. Payments received after expiry, cancellation, or failure are recorded as complete without confirming the booking, even if tickets remain available. Booking details and account history explain that payment was received and reconciliation or a refund is required; the API exposes `payment_received` and `reconciliation_required`. The accepted webhook record also contains a manual refund/reconciliation note in `rejection_reason`; staff must reconcile these payments manually. No automatic refund is issued. Duplicate notifications are acknowledged without sending another confirmation email. CSV confirmation time stays blank for unconfirmed bookings, including late payments. Customer edits lock and recheck the booking before changing contact or attendee details.


Without Docker, the backend test can be run from the repository root with:

```powershell
.\.venv\Scripts\python.exe backend\manage.py test core
```

## Repository layout

- `backend/`: Django API and administration application.
- `frontend/`: Next.js customer-facing application.
- `compose.yaml`: reproducible local stack.
- `SPEC.md`: living product and technical specification.

### Endpoint rate limits

Requests are limited per client IP, including signed-in clients. The API allows
120 requests/minute across endpoints. Additional limits are 10 login attempts per
5 minutes (shared with admin login), 5 registrations/hour, 20 booking writes per
5 minutes, and 10 checkout requests/minute. Failed attempts count too. Limits use
fixed windows, so bursts can occur across window boundaries. Configure counts and
window seconds in `RATE_LIMITS` in backend settings.

A rejected request returns JSON with HTTP 429 and `Retry-After` in seconds.
Health checks, OPTIONS, and PayFast notifications are exempt; payment callbacks
retain their existing validation. A counter-store outage returns HTTP 503 for
protected endpoints. Docker Compose provides private Redis shared by all workers;
rebuild the backend and start the updated stack with `docker compose up -d --build`.
Outside Compose, set `RATE_LIMIT_REDIS_URL` to a shared Redis instance for deployment.
Without this URL the local-memory fallback is for single-process development only.

Client addresses default to REMOTE_ADDR. Configure `RATE_LIMIT_TRUSTED_PROXIES`
with only the IPs/CIDRs of proxies you control that append or replace
X-Forwarded-For correctly. The middleware walks that chain from the trusted peer
and stops at the first untrusted address. Do not trust arbitrary public networks.
Application limits complement upstream traffic filtering and do not prevent DDoS.
