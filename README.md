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

When all three `DEV_ADMIN_*` values are present in the local `.env`, startup creates or updates that development administrator automatically. The seed is idempotent and the credentials are intentionally excluded from version control.

Startup also seeds three published development events when their slugs are not already present. Manage events at `/admin/events/event/`, list published events at `/api/events/`, and open public event details at `/events/{slug}`.

Administrators may upload an event image directly or provide an external image URL. An uploaded image takes precedence. Development uploads are stored under `backend/media/`; production deployments should configure durable object storage.

Guest checkout creates a 15-minute pending reservation with one named attendee per ticket. Booking status is protected by a one-time returned access token whose hash is stored by the backend. Administrators can manage bookings and attendees or export selected bookings from Django Admin.

Create the first administrator in a separate terminal:

```bash
docker compose exec backend python manage.py createsuperuser
```

Stop the services with `docker compose down`. The PostgreSQL database remains in its named Docker volume.

## Checks

```bash
docker compose run --rm backend python manage.py test
docker compose run --rm frontend npm run lint
docker compose run --rm frontend npm run typecheck
docker compose config --quiet
```

Without Docker, the backend test can be run from the repository root with:

```powershell
.\.venv\Scripts\python.exe backend\manage.py test core
```

## Repository layout

- `backend/`: Django API and administration application.
- `frontend/`: Next.js customer-facing application.
- `compose.yaml`: reproducible local stack.
- `SPEC.md`: living product and technical specification.
