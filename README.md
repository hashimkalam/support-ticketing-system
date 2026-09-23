# Support Ticketing System

A production-angled MVP for a shared support ticket queue: agents pick up tickets from a common
backlog, and only one of them can ever win a given ticket — even when a dozen of them click **Claim**
at the same instant.

The interesting work here isn't the CRUD; it's the concurrency guarantee on assignment, the
pagination contract on a table that will hold thousands of rows, and a ticket lifecycle that the
database itself refuses to break.

**Stack:** Python 3.12 · FastAPI · SQLAlchemy 2.0 · Pydantic v2 · PostgreSQL 16 · React 19 · Vite 8 ·
TypeScript 6 · Tailwind CSS 4 · Docker Compose

---

## Table of contents

- [Quick start](#quick-start)
- [Running the tests](#running-the-tests)
- [Configuration](#configuration)
- [What you get](#what-you-get)
- [Repository layout](#repository-layout)
- [API reference](#api-reference)
- [Data model](#data-model)
- [Architectural Decisions & Edge Cases Handled](#architectural-decisions--edge-cases-handled)
  - [1. The implicit requirement: a `status` lifecycle](#1-the-implicit-requirement-a-status-lifecycle)
  - [2. Pagination for the list view](#2-pagination-for-the-list-view)
  - [3. Concurrency: claiming without races](#3-concurrency-claiming-without-races)
  - [4. Idempotency for same-agent retries](#4-idempotency-for-same-agent-retries)
  - [5. Enum storage: VARCHAR + CHECK, not native enums](#5-enum-storage-varchar--check-not-native-enums)
  - [6. Indexes chosen from real query shapes](#6-indexes-chosen-from-real-query-shapes)
  - [7. Integrity the database enforces, not the application](#7-integrity-the-database-enforces-not-the-application)
  - [8. Connection pooling and session lifecycle](#8-connection-pooling-and-session-lifecycle)
  - [9. Error semantics the frontend can branch on](#9-error-semantics-the-frontend-can-branch-on)
  - [10. Schema creation: create_all for the MVP](#10-schema-creation-create_all-for-the-mvp)
  - [11. Frontend state: a discriminated union, not a thrown conflict](#11-frontend-state-a-discriminated-union-not-a-thrown-conflict)
  - [12. Local evaluation ergonomics: idempotent demo seeding](#12-local-evaluation-ergonomics-idempotent-demo-seeding)
- [Local development without Docker](#local-development-without-docker)
- [Resetting the database](#resetting-the-database)
- [Known limitations](#known-limitations)

---

## Quick start

### Prerequisites

| Tool | Version | Notes |
| --- | --- | --- |
| Docker | 24+ | With Docker Desktop or a running daemon; Compose v2 (`docker compose`, not `docker-compose`) |

Nothing else needs to be installed. Python, Node, and PostgreSQL all live inside the containers.

### 1. Create your environment file

```bash
cp .env.example .env
```

The defaults in `.env.example` work as-is for local development. If you skip this step, Compose falls
back to the same values through `${VAR:-default}` interpolation — but the file documents what is
configurable.

### 2. Build and start the whole stack

```bash
docker compose up --build
```

First run builds both images and installs dependencies, so allow a couple of minutes. Later runs are
near-instant; drop `--build` unless you changed `backend/requirements.txt` or `frontend/package.json`.

Prefer background mode? `docker compose up --build -d`, then `docker compose logs -f`.

**No migration step is required.** The API creates its tables on startup (see
[§10](#10-schema-creation-create_all-for-the-mvp)), and it waits for PostgreSQL to report healthy
before it starts.

### 3. Verify it's up

```bash
curl -s http://localhost:8000/health
# {"status":"ok","version":"0.1.0"}

curl -s http://localhost:8000/health/db
# {"status":"ok","database":"reachable"}
```

Optional — confirm the table and its indexes exist:

```bash
docker compose exec db psql -U tickets -d tickets -c '\d tickets'
```

### 4. Open the apps

| Service | URL |
| --- | --- |
| Ticket UI | http://localhost:5173 |
| API docs (Swagger) | http://localhost:8000/docs |
| ReDoc | http://localhost:8000/redoc |
| PostgreSQL | `localhost:5432` (`tickets` / `tickets` / `tickets`) |

Type your email into the **Working as** field in the header — that field is the current user for
claiming (authentication is explicitly out of scope). It persists in `localStorage`.

Stop everything with `Ctrl+C`, or `docker compose down`.

### 5. Run the test suite (optional)

```bash
docker compose --profile test run --rm tests
```

See [Running the tests](#running-the-tests) for what it covers.

---

## Running the tests

```bash
docker compose --profile test run --rm tests
```

```
....................                                                     [100%]
20 passed in 1.37s
```

The suite runs against its own database (`tickets_test`) on the same Postgres container, and
`conftest.py` **refuses to start** if the database name does not end in `_test` — a truncation bug in
a test can never cost you development data. A run creates the database and the schema itself, and
truncates the table between tests.

It is declared as a compose service behind the `test` profile, so a plain `docker compose up` never
runs it, and the runtime image stays free of test dependencies (`INSTALL_DEV=true` installs
`requirements-dev.txt` into the test image only).

| File | Covers |
| --- | --- |
| `tests/test_tickets_api.py` | Create defaults, tag normalisation, validation rejections, fetch-by-id, pagination windows and ordering, paging bounds |
| `tests/test_claim_api.py` | Successful claim, `409` against the owner, idempotent replays, case-insensitive match, resolved tickets, `404`, malformed input |
| `tests/test_claim_concurrency.py` | The race itself: 16 simultaneous claims, and 16 simultaneous retries by one agent |

The concurrency test is the one that matters. It is not a smoke test that would pass regardless: the
assertions are written so that **replacing the atomic `UPDATE` with a read-then-write implementation
makes it fail**, which is how it was validated — that mutation produced 15 "winners" for a single
ticket:

```
E  AssertionError: expected exactly one winner, got ['agent0@example.com', 'agent2@example.com',
   'agent12@example.com', 'agent7@example.com', ... 15 total']
```

---

## Configuration

Everything is read from the environment (or `.env`), and every value has a working default.

| Variable | Default | Purpose |
| --- | --- | --- |
| `POSTGRES_USER` / `POSTGRES_PASSWORD` / `POSTGRES_DB` | `tickets` | Postgres credentials and the database Compose creates |
| `DATABASE_URL` | `postgresql+psycopg2://tickets:tickets@db:5432/tickets` | Set by Compose; point it elsewhere to use another server |
| `CORS_ORIGINS` | `["http://localhost:5173","http://127.0.0.1:5173"]` | JSON list of browser origins allowed to call the API |
| `SEED_DEMO_DATA` | `true` in Compose, `false` in the app | Insert 16 demo tickets when the table is empty ([§12](#12-local-evaluation-ergonomics-idempotent-demo-seeding)) |
| `DEBUG` | `false` | Verbose framework behaviour. With `true`, unhandled errors return a **traceback to the client** instead of the JSON envelope |
| `VITE_API_BASE_URL` | `http://localhost:8000/api/v1` | The API base URL the **browser** calls |

`CORS_ORIGINS` must be valid JSON when overridden, because it is parsed as a list.

---

## What you get

**Backend**
- `POST /api/v1/tickets` — create a ticket (validated, tags normalised)
- `GET /api/v1/tickets` — paginated directory with `total_count` for navigation controls
- `GET /api/v1/tickets/{id}` — fetch a single ticket
- `POST /api/v1/tickets/{id}/claim` — atomically assign a ticket to an agent
- `GET /health`, `GET /health/db` — split liveness/readiness probes
- CORS, connection pooling, dependency-injected sessions, typed settings from the environment
- A global error handler that returns a stable JSON envelope instead of leaking tracebacks
- 20 pytest tests, including a 16-thread regression test for the claim race

**Frontend**
- Persistent "current agent" email in React context, surfaced through a header input
- Ticket list with priority/status badges, server-driven Previous/Next pagination
- Inline expandable detail view (description, tags, status, assignee, timestamps)
- Claim action that switches on a discriminated union and surfaces conflicts as an alert
- Tailwind CSS 4, no config file needed, Vite HMR inside Docker

### Requirements traceability

| Requirement | Implementation | Verification |
| --- | --- | --- |
| Ticket creation | `POST /api/v1/tickets` → `routers/tickets.py` | `tests/test_tickets_api.py` |
| Ticket retrieval over a large table | `GET /api/v1/tickets` with `skip`/`limit` + `total_count` ([§2](#2-pagination-for-the-list-view)) | Pagination and ordering tests |
| Assignment, once only, first agent wins | Conditional `UPDATE ... WHERE assigned_to IS NULL` ([§3](#3-concurrency-claiming-without-races)) | `tests/test_claim_concurrency.py` |
| Email input for the "current user" | `Header.tsx` + `AgentProvider` (persisted in `localStorage`) | Live UI |
| List view with navigation controls | `TicketList.tsx` + `Pagination.tsx` driving server-side paging | Live UI, 16 seeded rows |
| Detail view (description, tags) | Inline expansion via `TicketDetail.tsx` | Live UI |
| Claim an unassigned ticket | Claim button → `claimTicket()` → union outcome | Live UI + API tests |
| README with database init and startup | This file, steps 1–4 | Executed end to end |
| `docker-compose.yml` for local evaluation | `db` + `api` + `web`, plus a `tests` profile | `docker compose config` |
| Process visible in Git history | Six commits, one per increment | `git log --oneline` |
| Production-grade hygiene (implicit) | Error envelope, logging, pooling, constraints, indexes, tests ([§7](#7-integrity-the-database-enforces-not-the-application)–[§12](#12-local-evaluation-ergonomics-idempotent-demo-seeding)) | Suite + live checks |

---

## Repository layout

```
.
├── docker-compose.yml          # db + api + web, wired with healthchecks
├── .env.example                # every configurable value, documented
├── backend/
│   ├── Dockerfile              # python:3.12-slim, non-root user
│   ├── requirements.txt
│   └── app/
│       ├── config.py           # typed settings (pydantic-settings)
│       ├── database.py         # engine, pool tuning, session factory, get_db
│       ├── models.py           # Ticket, Priority, Status + constraints/indexes
│       ├── schemas.py          # request/response contracts
│       ├── main.py             # app factory, CORS, lifespan, health
│       └── routers/
│           └── tickets.py      # create / list / claim
└── frontend/
    ├── Dockerfile              # node:22-alpine, Vite dev server
    └── src/
        ├── api/                # client.ts (transport) + tickets.ts (endpoints)
        ├── components/         # Header, TicketList, TicketRow, TicketDetail, Pagination, …
        ├── constants/          # page sizes, storage keys, labels
        ├── context/            # agent identity (context + provider)
        ├── hooks/              # useTickets: pagination + fetch lifecycle
        └── types/              # domain models and component contracts
```

---

## API reference

All ticket endpoints are served under `/api/v1`.

| Method | Path | Description |
| --- | --- | --- |
| `POST` | `/api/v1/tickets` | Create a ticket. Always starts `open` and unassigned. |
| `GET` | `/api/v1/tickets?skip=0&limit=20` | Paginated list, newest first. `limit` is capped at 100. |
| `GET` | `/api/v1/tickets/{id}` | Fetch a single ticket. `404` when it does not exist. |
| `POST` | `/api/v1/tickets/{id}/claim` | Assign an agent. Returns the updated ticket. |

### Create a ticket

```bash
curl -s -X POST http://localhost:8000/api/v1/tickets \
  -H 'Content-Type: application/json' \
  -d '{
        "title": "Printer on fire",
        "description": "Sparks and smoke from the paper tray. Floor 3 is evacuated.",
        "priority": "urgent",
        "tags": ["Hardware", "hardware", "facilities"]
      }'
```

```json
{
  "title": "Printer on fire",
  "description": "Sparks and smoke from the paper tray. Floor 3 is evacuated.",
  "priority": "urgent",
  "tags": ["hardware", "facilities"],
  "id": "8e7be486-1f0e-4bac-bbe0-d0d993ce8ab1",
  "status": "open",
  "assigned_to": null,
  "created_at": "2026-09-23T10:51:25.123456Z",
  "updated_at": "2026-09-23T10:51:25.123456Z"
}
```

Note the tag normalisation: `["Hardware", "hardware", "facilities"]` becomes
`["hardware", "facilities"]` — lowercased and de-duplicated so tag filters stay predictable.

### List tickets

```bash
curl -s 'http://localhost:8000/api/v1/tickets?skip=0&limit=10'
```

```json
{
  "items": [ /* up to 10 tickets, newest first */ ],
  "total_count": 14,
  "skip": 0,
  "limit": 10
}
```

`total_count` is the count of **all** tickets, not the page — that is what the UI needs to render
"Showing 1–10 of 14" and to know when to disable **Next**.

### Fetch a single ticket

```bash
curl -s http://localhost:8000/api/v1/tickets/8e7be486-1f0e-4bac-bbe0-d0d993ce8ab1
```

Unknown IDs return `404 {"detail": "Ticket not found"}`.

### Claim a ticket

```bash
curl -s -X POST http://localhost:8000/api/v1/tickets/8e7be486-1f0e-4bac-bbe0-d0d993ce8ab1/claim \
  -H 'Content-Type: application/json' \
  -d '{"assigned_to": "alice@example.com"}'
```

A successful claim returns **200** with the ticket now `in_progress` and assigned to that agent. The
ticket transitions are described in [§4](#4-idempotency-for-same-agent-retries).

### Error responses

| Status | When it happens |
| --- | --- |
| `422` | Payload fails validation — title shorter than 3 characters, unknown `priority`, empty description, non-email `assigned_to`, `status` sent on create, `limit` above 100, `skip` negative |
| `404` | Claiming a ticket ID that does not exist |
| `409` | Claiming a ticket that another agent already owns |
| `500` | Unhandled server error — always `{"detail": "Internal server error."}`; the traceback goes to the logs, never to the client |

---

## Data model

A single `tickets` table:

| Column | Type | Notes |
| --- | --- | --- |
| `id` | `uuid` | Primary key, `gen_random_uuid()` default |
| `title` | `varchar(200)` | Not null |
| `description` | `text` | Not null |
| `priority` | `varchar(20)` | Not null, CHECK `low`/`medium`/`high`/`urgent`, default `medium` |
| `status` | `varchar(20)` | Not null, CHECK `open`/`in_progress`/`resolved`, default `open` |
| `tags` | `varchar(50)[]` | Not null, default `{}`, GIN-indexed |
| `assigned_to` | `varchar(255)` | Nullable — null means unclaimed |
| `created_at` | `timestamptz` | Not null, `now()` |
| `updated_at` | `timestamptz` | Not null, `now()`, bumped on write |

```
Indexes:  tickets_pkey (id), ix_tickets_status, ix_tickets_priority,
          ix_tickets_assigned_to, ix_tickets_created_at, ix_tickets_tags_gin (gin)
Checks:   ticket_status   CHECK (status IN ('open','in_progress','resolved'))
          ticket_priority CHECK (priority IN ('low','medium','high','urgent'))
          ck_tickets_status_requires_assignee CHECK (status = 'open' OR assigned_to IS NOT NULL)
```

---

## Architectural Decisions & Edge Cases Handled

### 1. The implicit requirement: a `status` lifecycle

The original field list was `Title`, `Description`, `Priority`, `Tags`, and `Assigned User`. That
list is *almost* sufficient — but `assigned_to IS NULL` can only ever express two states: taken and
untaken. It cannot express the difference between a ticket an agent is actively working and one they
have **finished**.

That gap becomes a bug the moment anyone asks "what's still outstanding?", and — more urgently — it
becomes a migration on a table that already holds production rows. So `status` was added up front
with three values:

```
open  ──claim──▶  in_progress  ──resolve──▶  resolved
```

Two properties make this production-grade rather than decorative:

1. **`status` is never accepted from the client on create.** `TicketCreate` sets
   `extra="forbid"`, so a caller sending `{"status": "resolved"}` gets a **422**, not a silently
   ignored field. Without that, a client would believe it had filed something already closed while
   the server quietly stored `open`. New tickets are always `open`; only the claim endpoint moves
   them.
2. **"In progress" cannot exist without an owner.** A table-level constraint encodes the lifecycle
   invariant the enum implies:

   ```sql
   CHECK (status = 'open' OR assigned_to IS NOT NULL)
   ```

   The enum alone would still allow `status = 'in_progress'` with `assigned_to = NULL` — a ticket
   being worked by nobody. A bug (or a half-applied update) could produce exactly that state, and it
   is invisible until someone reports a ticket stuck in limbo. The database now rejects it outright.
   This is also why the claim endpoint writes `assigned_to` and `status` in the *same* statement:
   splitting them into two updates would momentarily violate the constraint, and any interleaving
   between them would leave the row inconsistent.

### 2. Pagination for the list view

The list endpoint never returns the whole table. It takes `skip` and `limit` and returns them
alongside `total_count` so the client can render real navigation controls rather than a
never-ending scroll:

```python
skip: int = Query(0, ge=0)
limit: int = Query(20, ge=1, le=100)

total_count = db.scalar(select(func.count()).select_from(Ticket)) or 0

stmt = (
    select(Ticket)
    .order_by(Ticket.created_at.desc(), Ticket.id.desc())
    .offset(skip)
    .limit(limit)
)
```

Four decisions are load-bearing here:

- **`limit` is capped at 100 and floored at 1.** A cap protects the database from a self-inflicted
  DoS (`?limit=1000000`), and validation (`ge=1`) makes `?limit=0` an explicit `422` instead of a
  confusing empty page.
- **The `ORDER BY` is not cosmetic — it is a correctness requirement.** SQL does not guarantee row
  order without an explicit sort, so offset pagination over an unsorted query can return the same
  row on two consecutive pages and silently omit another. The `id` tiebreaker handles the case where
  several tickets share a `created_at` timestamp, which genuinely happens under concurrent inserts.
- **`total_count` is the full count, computed separately from the page.** It is one extra cheap
  aggregate query that saves the client from inferring "is there more?" from a short page.
- **Offset pagination is a deliberate choice for this scale.** It is simple, it supports random
  access ("page 7"), and it is exactly what `skip`/`limit` semantics were requested to do. It has two
  known costs that are worth naming rather than hiding: `COUNT(*)` degrades to a sequential scan on
  large tables, and deep offsets (`OFFSET 50000`) require scanning and discarding the preceding rows.
  Both are sub-millisecond at MVP volumes; the escape hatch when they stop being acceptable is keyset
  pagination (`WHERE (created_at, id) < (:last_created_at, :last_id)`), which trades random access
  for constant-time page fetches. The `ix_tickets_created_at` index already supports that migration.

### 3. Concurrency: claiming without races

This is the heart of the system, and the requirement it satisfies is blunt: **during peak hours,
several agents will click Claim on the same urgent ticket at the same moment, and exactly one of
them must win.**

A naive implementation reads first, checks in Python, then writes:

```python
ticket = db.get(Ticket, ticket_id)        # ← both agents read assigned_to = None here
if ticket.assigned_to is None:            # ← both agents pass this check
    ticket.assigned_to = email            # ← both agents write
    db.commit()                           # ← last writer wins; the first agent's claim vanishes
```

Both requests read `NULL`, both pass the guard, and both commit. One agent is told they own a ticket
they don't. The window between the read and the write is small, which makes this class of bug
particularly nasty: it will not show up in manual testing, only under real concurrent load, and by
then it has already assigned two people to one customer.

The fix is to make the check and the write **one atomic statement**, so the decision is made by the
database under a row lock rather than by application code in a gap:

```python
stmt = (
    update(Ticket)
    .where(Ticket.id == ticket_id, Ticket.assigned_to.is_(None))
    .values(
        assigned_to=payload.assigned_to,
        status=Status.IN_PROGRESS,
        updated_at=func.now(),
    )
    .returning(Ticket)
    .execution_options(synchronize_session=False)
)

ticket = db.execute(stmt).scalar_one_or_none()
```

**Why this is race-free.** Under PostgreSQL's default `READ COMMITTED` isolation, when two `UPDATE`
statements target the same row:

1. The first transaction acquires the row lock and updates it.
2. The second blocks on that lock rather than proceeding.
3. When the first commits, PostgreSQL does **not** blindly apply the second update. It re-evaluates
   the `WHERE` predicate against the *new* row version (EvalPlanQual). `assigned_to IS NULL` is now
   false, so the row no longer matches.
4. The second statement therefore affects **zero rows** — and returns `0` to the caller.

There is no read-then-write gap for a competitor to slip into, because the predicate and the write
are evaluated by the same statement inside the same lock. The database's own concurrency control is
the only participant; there is no advisory lock, no `SELECT ... FOR UPDATE` round trip, and no
application-level mutex that would fail the moment you run more than one API worker.

An alternative was considered and rejected: `SELECT ... FOR UPDATE` followed by an update. It is also
correct, but it costs an extra round trip, holds the lock across two statements, and is easier to get
wrong later (forgetting `.with_for_update()`, or extending the transaction with unrelated work while
holding a lock on a hot row). The conditional `UPDATE` is one statement, one lock, one decision.

**Lost races are explained, not just rejected.** When the statement affects zero rows, the handler
distinguishes the two possible causes instead of returning a blanket conflict:

```python
ticket = db.execute(stmt).scalar_one_or_none()
if ticket is not None:
    db.commit()
    return ticket

db.rollback()
existing = db.get(Ticket, ticket_id)
if existing is None:
    raise HTTPException(404, "Ticket not found")          # never existed
if existing.assigned_to and existing.assigned_to.lower() == payload.assigned_to.lower():
    return existing                                        # same agent: a retry, not a conflict
raise HTTPException(409, f"Ticket already assigned to {existing.assigned_to}")
```

A nonexistent ticket ID also produces zero affected rows, and reporting `409 Conflict` for it would
be a lie the frontend cannot recover from — "someone beat you to it" and "this link is broken" demand
different UI. Hence the existence check *after* the atomic attempt, on the failure path only, where
an extra query costs nothing.

**Verified under real contention**, not just reasoned about. 16 simultaneous claims against one
ticket, released from a shared thread barrier so they hit the API together:

```
status codes:        {200: 1, 409: 15}
winning assignee:    agent14@example.com
database row:        in_progress | agent14@example.com   ← matches the single winner
```

One winner, fifteen clean conflicts, and the persisted row agrees with the response.

That check is now a permanent regression test rather than a one-off script —
`backend/tests/test_claim_concurrency.py`, runnable with `docker compose --profile test run --rm
tests`. It was validated by mutation: against a read-then-write implementation it fails with 15
winners, so it genuinely detects the race instead of passing by construction.

### 4. Idempotency for same-agent retries

The atomic claim solves mutual exclusion, but it introduces a user-facing edge case. Because the
`WHERE` clause matches only `assigned_to IS NULL`, an agent who clicks Claim twice — an impatient
double-click, a retried request after a dropped connection — gets `0` rows back and, naively, a
`409`. The UI would then show a red "someone else claimed it first" alert to the agent who in fact
owns the ticket. That is a false alarm on the happy path, which is worse than a cosmetic bug.

So a lost race is only a conflict if the winner is *somebody else*:

- **Same agent → `200 OK`.** The row is returned untouched.
- **Different agent → `409 Conflict`.** The response names the current owner so the UI can say
  something useful, and the client refetches.

Two details matter:

- **The retry is a genuine no-op.** The idempotent path returns the row it read — it does not write
  to it. Verified by inspecting `updated_at`: a repeat claim leaves the timestamp byte-identical, so
  retries do not inflate the audit trail or fire the `onupdate` default.
- **The comparison is case-insensitive.** Email local-parts are technically case-sensitive, but no
  real provider treats them that way, so a strict `==` would hand `Alice@example.com` a
  `409` reading "already assigned to alice@example.com" — which, to the person reading it, looks like
  a bug in their own tooling. `existing.assigned_to.lower() == payload.assigned_to.lower()` keeps the
  retry behaviour consistent. (Note this normalises the *comparison* only; the stored value keeps the
  casing the caller sent.)

The 409 branch is reached only after the winner has committed and released its row lock, so the read
that follows is guaranteed to see committed state — there is no window in which a retry could
misread a rival claim as its own.

Verified: 16 concurrent retries by the same agent → `{200: 16}`, all reporting the same assignee,
with the underlying row written exactly once. Both properties are covered by
`tests/test_claim_api.py` and `tests/test_claim_concurrency.py`.

### 5. Enum storage: VARCHAR + CHECK, not native enums

`priority` and `status` are stored as `varchar(20)` with a `CHECK` constraint rather than as
PostgreSQL `ENUM` types (`native_enum=False`, `create_constraint=True`):

```python
Enum(Status, name="ticket_status", native_enum=False, length=20,
     values_callable=lambda enum_cls: [member.value for member in enum_cls],
     create_constraint=True, validate_strings=True)
```

Adding a fourth priority — `critical`, say — becomes a constraint swap. With a native `ENUM` it
requires `ALTER TYPE`, which in older PostgreSQL versions cannot run inside a transaction and cannot
drop values at all.

`values_callable` is doing real work here: SQLAlchemy persists enum **member names** by default
(`MEDIUM`), which would have put the CHECK constraint and the `server_default='medium'` in direct
conflict — the column's own default would have violated the column's own constraint. Persisting
`.value` keeps the stored values, the CHECK, the default, and the JSON API in one casing.
`validate_strings=True` rejects invalid values at the Python boundary too.

### 6. Indexes chosen from real query shapes

Every index corresponds to a query the application actually issues — an unused index is a write-time
tax with no reader:

| Index | Serves |
| --- | --- |
| `tickets_pkey (id)` | Claim by ID; primary key |
| `ix_tickets_status` | "Show me the open queue" — the hottest filter |
| `ix_tickets_priority` | Triaging by urgency |
| `ix_tickets_assigned_to` | "My tickets" |
| `ix_tickets_created_at` | The list endpoint's `ORDER BY created_at DESC` |
| `ix_tickets_tags_gin` | Tag containment (`tags @> ARRAY['billing']`) |

`tags` is a PostgreSQL array rather than JSONB. For a flat, ordered set of labels with no per-tag
attributes, arrays give containment (`@>`) and overlap (`&&`) operators that index cleanly with GIN;
JSONB would force `jsonb_array_elements` gymnastics or a bulkier index for no benefit. The GIN index
is confirmed in use rather than assumed:

```
Bitmap Heap Scan on tickets
  Recheck Cond: (tags @> '{it}'::character varying[])
  ->  Bitmap Index Scan on ix_tickets_tags_gin
```

The ORM type is `sqlalchemy.dialects.postgresql.ARRAY`, not the generic `ARRAY` — the generic type
raises `NotImplementedError` for `.contains()`, a papercut that only shows up when you first write
the query.

Deliberately *not* added: composite indexes like `(status, created_at)`. Ticket tables are small at
this stage, the endpoint shapes are still settling, and a redundant index costs write throughput.
Adding the right one later — once the filter combinations are known — beats guessing now.

### 7. Integrity the database enforces, not the application

The rule of thumb applied here: if a state is contradictory, the database should make it impossible
to store, not merely unlikely to be written.

- **`ck_tickets_status_requires_assignee`** — a ticket cannot be `in_progress` without an owner
  (see [§1](#1-the-implicit-requirement-a-status-lifecycle)).
- **`CHECK` constraints on both enums** — invalid priorities and statuses are rejected even by raw
  SQL, so a manual `INSERT` from `psql` cannot poison the table.
- **UUID primary keys with a `gen_random_uuid()` server default** — IDs are non-enumerable in the
  public API, which is the right default for anything a customer might see or share. The server-side
  default means non-ORM inserts (scripts, `psql`, future services) work without supplying an ID; the
  Python-side `default=uuid.uuid4` means ORM inserts do not need a database round trip to learn it.

Verified directly, including the failures:

```sql
INSERT INTO tickets (title, description) VALUES ('raw sql', 'x');
-- ✓ status defaults to 'open', tags default to '{}', id generated

INSERT INTO tickets (title, description, status) VALUES ('orphan', 'x', 'in_progress');
-- ✗ violates check constraint "ck_tickets_status_requires_assignee"

INSERT INTO tickets (title, description, status) VALUES ('bad', 'x', 'closed');
-- ✗ violates check constraint "ticket_status"
```

### 8. Connection pooling and session lifecycle

`database.py` tunes the pool for a long-lived API process rather than accepting SQLAlchemy's
defaults:

- `pool_pre_ping=True` — validates a pooled connection before handing it out. Without it, a database
  restart or a failover surfaces as a stale-socket `OperationalError` on a random request instead of
  a transparent reconnect.
- `pool_recycle=1800` — recycles connections below typical idle timeouts imposed by proxies and
  managed Postgres, so the pool never hands out a connection something already closed.
- `pool_size=5`, `max_overflow=10` — bounded per worker. Pool sizing is a *per-process* budget, so
  this multiplies by worker count; the defaults are deliberately modest.
- `expire_on_commit=False` — objects stay usable after a commit, so a handler can return the row it
  just wrote without triggering a refresh query.

Sessions are injected via a FastAPI dependency (`get_db`), which closes the session in a `finally`
block — so a session cannot leak even when a handler raises, including from the 404/409 paths above.
The engine is disposed on application shutdown, releasing pooled connections cleanly on reload.

### 9. Error semantics the frontend can branch on

- **Nothing internal ever reaches the client.** A global `Exception` handler returns
  `500 {"detail": "Internal server error."}` and logs the traceback server-side with
  `logger.exception`. This matters more than it looks: with `DEBUG=true`, Starlette installs its own
  debug response *ahead of* any registered handler and returns a full stack trace — table names,
  file paths, the lot — so the default is `DEBUG=false` and the handler is the only path out.
- **`404` before `409`, always.** A missing ticket and a taken ticket both mean "zero rows updated",
  but they are different worlds to the client (see [§3](#3-concurrency-claiming-without-races)).
- **Validation errors are `422` with field-level detail.** Pydantic constraints (title ≥ 3 chars,
  valid email for `assigned_to`, ≤ 20 tags, `priority` from the enum) reject bad input before it
  reaches the database.
- **`extra="forbid"` on the create schema.** Unknown fields are a `422` rather than silently
  dropped, so a client cannot believe it set something it didn't.
- **Failed *fakes* are distinguished from failures.** `fetch` in the frontend rejects only on
  network/CORS failure, never on HTTP error codes. That distinction is captured in one place
  (`ApiError` with `status: 0` for "cannot reach the API"), so a backend that isn't running doesn't
  present itself as an HTTP error.
- **CORS is explicit, not `*`.** Origins come from the `CORS_ORIGINS` environment variable (JSON when
  overridden), which keeps credentials-allowed and wildcard-origin from ever coexisting.

### 10. Schema creation: `create_all` for the MVP

The API creates tables on startup via `Base.metadata.create_all()`, scheduled in the FastAPI
`lifespan` handler:

```python
@asynccontextmanager
async def lifespan(_: FastAPI):
    # MVP only: swap for Alembic once the schema starts evolving.
    create_tables()
    yield
    engine.dispose()
```

This keeps the quick start genuinely one command. Its **limitation is deliberate and important to
know**: `create_all` creates missing tables, and never alters existing ones. Change a column on a
table that already exists and the change will not appear until the volume is reset. That is
acceptable now — the schema is fresh — and it is the first thing to replace: Alembic migrations
should land before the first real schema change, not after.

### 11. Frontend state: a discriminated union, not a thrown conflict

The API layer converts the `409` into a **value** rather than an exception, because a lost race is an
expected outcome under load, not an error:

```ts
export type ClaimResult =
  | { outcome: 'claimed'; ticket: Ticket }
  | { outcome: 'conflict'; message: string }
```

Consumers `switch` on `outcome`, and the compiler enforces both branches — so the "someone beat you
to it" case cannot be forgotten the way a `catch` block can. Everything else (`404`, `422`, network)
still throws, because those are bugs or infrastructure faults rather than normal flow.

The two branches then do genuinely different things:

- **Win:** the list is patched in place from the response body. The API already returned the updated
  row, so no refetch is needed and the row flips instantly.
- **Loss:** the client's whole snapshot is stale by definition, so it refetches — but the alert is
  rendered immediately and the refetch is fire-and-forget, because making an error message wait on a
  network round trip is how you get a UI that feels broken.

One more edge case worth naming: `useTickets` guards against **out-of-order responses**. Pagination
fires a request per page change, and responses can resolve in the wrong order — click Next twice
quickly and the slower first page can overwrite the newer one. Each request takes a monotonically
increasing id and only commits its result if it is still the newest:

```ts
const requestId = ++latestRequest.current
const response = await fetchTickets({ skip, limit })
if (requestId !== latestRequest.current) return  // a newer request already won
```

The same instinct as the atomic claim, in a different layer: make the stale writer detectable rather
than hoping it doesn't happen.

### 12. Local evaluation ergonomics: idempotent demo seeding

Opening this stack against an empty database shows an empty list — and the list, detail, and claim
flows are the entire point of the exercise. So the app can seed 16 realistic tickets on startup:

```python
@asynccontextmanager
async def lifespan(_: FastAPI):
    create_tables()
    if settings.seed_demo_data:
        logger.info("Seeded %d demo tickets.", seed_demo_tickets())
    yield
    engine.dispose()
```

Three properties keep it from becoming a liability:

1. **Idempotent.** `seed_demo_tickets()` counts the rows first and returns `0` if the table is not
   empty, so restarts and reloads never duplicate data. It can also be run directly:
   `docker compose exec api python -m app.seed`.
2. **Off in the application, on in the Compose stack.** `Settings.seed_demo_data` defaults to
   `false`, and only `.env.example` / `docker-compose.yml` opt in. A real deployment pointed at this
   image gets an empty database unless someone explicitly asks for demo rows.
3. **The demo rows are a hazard test, not filler.** They include two `resolved` tickets owned by
   other agents, which is how a reviewer sees all three status badges and the "already owned"
   rendering without needing a resolve endpoint first. They also give the queue enough rows to make
   the pagination controls non-trivial: 16 tickets with a page size of 10, so page two exists.

---

## Local development without Docker

Docker Compose is the supported path, but if you want a tighter loop:

**Backend** (needs a reachable PostgreSQL):

```bash
cd backend
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
export DATABASE_URL='postgresql+psycopg2://tickets:tickets@localhost:5432/tickets'
uvicorn app.main:app --reload
```

**Frontend:**

```bash
cd frontend
npm install
npm run dev        # http://localhost:5173
npm run build      # typecheck (tsc -b) + production build
npm run lint       # oxlint
```

The frontend reads `VITE_API_BASE_URL` (default `http://localhost:8000/api/v1`). Because the `fetch`
calls execute in the **browser**, that URL must be reachable from the host — `http://api:8000` would
resolve only inside the Compose network.

---

## Resetting the database

The schema is created automatically, so a clean slate means dropping the volume:

```bash
docker compose down -v      # -v also removes the postgres_data volume
docker compose up --build
```

To clear rows but keep the volume — and therefore the indexes and constraints — use:

```bash
docker compose exec db psql -U tickets -d tickets -c 'DELETE FROM tickets;'
```

---

## Known limitations

Honest scope boundaries, in rough priority order:

- **No API UI for creating tickets.** The frontend lists, expands, and claims; ticket creation is
  available through the API and `/docs`. The create form is the natural next increment.
- **No resolve/reopen endpoint yet.** The `status` lifecycle and the `TicketStatusUpdate` schema exist
  and are enforced at the database level, but only the claim transition is exposed over HTTP, so
  `in_progress` is currently terminal from the client's perspective.
- **No authentication or authorization.** The header email is self-declared identity — deliberately
  out of scope for this MVP. Anyone can claim a ticket as anyone until an auth layer lands, and the
  `assigned_to` field is trusted as-is.
- **The Compose stack seeds demo rows by default.** Intentional for evaluation, controlled by
  `SEED_DEMO_DATA=false` ([§12](#12-local-evaluation-ergonomics-idempotent-demo-seeding)).
- **No auto-refresh.** The list does not poll. If another agent claims a ticket you're looking at, you
  learn about it when you click Claim and receive the `409` — and the conflict path is exactly the
  recovery for that.
- **`create_all` instead of migrations** — see [§10](#10-schema-creation-create_all-for-the-mvp).
- **Offset pagination and `COUNT(*)`** — correct and fast at MVP scale, with the keyset migration path
  documented in [§2](#2-pagination-for-the-list-view).

---

Built with FastAPI, SQLAlchemy, React, and PostgreSQL. The two behaviours to trust are the atomic
claim and the deterministic pagination order; both are verified under concurrent load rather than
assumed.
