# AGENTS.md

This file provides guidance to Codex (Codex.ai/code) when working with code in this repository.

## Project state

Past the skeleton stage — see `docs/roadmap.md` for exactly what's built vs. not. Working docs live in `docs/` (gitignored, local only): `docs/DESIGN.md` is the frozen pre-code design from the original "grilling" session, `docs/architecture.md` is the as-built reference (kept current as the code changes), `docs/architecture-essentials.md` is a short version of that for fast orientation, `docs/roadmap.md` tracks build-order status. Read `architecture-essentials.md` first in a new session. If a change contradicts `docs/DESIGN.md`, raise it rather than silently diverging.

This is a **portfolio project** (final project for a scaling course, L1–L8). The value is not just working code — it's the growth story mapping each design decision to a scaling lesson (`docs/architecture.md` §7). Preserve that mapping.

## What it is

Multi-tenant virtual queue mini-SaaS. Businesses open virtual lines; clients join by email + OTP (no password, no saved accounts), see their position via polling, get one web-push alert when their turn is near. Staff call next person, mark done/no-show.

## Architecture (as built — full detail in `docs/architecture.md`)

Layer-based FastAPI app, **async SQLAlchemy**, service layer holds all logic:

```
app/main.py
app/core/     config.py db.py exceptions.py logging.py
app/models/   SQLAlchemy tables
app/schemas/  Pydantic request/response
app/routers/  thin routes — call services, return schemas
app/services/ real logic (queue_service so far; otp_service, notify_service, business_service not built yet)
app/workers/  Celery tasks (not built yet — folder exists, empty)
tests/
```

**Hard rule:** routers never touch the DB directly. Router → service function → models → plain data → router wraps in schema. The atomic-position logic lives in exactly one place (`queue_service.py`), callable from a route today and a retry job later.

## Critical correctness point (the L8 lesson — do not get wrong)

Position assignment on join **must be atomic**. Two clients joining the same second must never get the same position. Use a single-statement update, no read-then-write:

```sql
UPDATE queues SET next_position = next_position + 1
WHERE id = :queue_id RETURNING next_position;
```

Position *assignment* = strongly consistent. Position *display* while polling = eventual consistency is fine (few seconds lag harmless).

## Data model (full detail in `docs/architecture.md` §2)

`businesses → services → counters` and `services → queues (one per day) → queue_entries`. `queue_entries.counter_id` set only once called. `queue_events` = append-only audit log, one row per state change — table is migrated but nothing writes to it yet (see `docs/roadmap.md` step 4). One model class per box in the class diagram. All primary keys are UUID.

## Scope discipline (decided, not forgotten)

v1 excludes: client accounts/history, SMS, reports/dashboards on the log, payments, WebSockets (polling every 10–15s instead), caching, read replicas, load balancer. These are the documented growth path — add only when real load asks. Don't build them in early.

## Build order and status

See `docs/roadmap.md` for the 8-step build order with real status per step (checked against the code, not assumed) — update it there, not here, so it doesn't go stale twice.

The atomic-position test in `tests/test_queue_service.py` comes first among tests.

## Stack notes

FastAPI + async SQLAlchemy + PostgreSQL + Celery/Redis. Env-var config via `app/core/config.py`. Dev venv: Python 3.12 via `uv` (matches CI). Commands (venv, docker db, migrations, seed, tests, run): `docs/architecture-essentials.md`.

## Git rules (hard rules, do not deviate)

- Never run `git commit` or `git push` without the user explicitly saying "go ahead" in that moment. Asking "want me to commit?" is fine; running it on assumed consent is not, even if approved earlier in the session.
- Commit messages: subject line only, no body/description, unless the user explicitly asks for one.
- Never add Codex/Anthropic as co-author or contributor. No `Co-Authored-By` trailer. The user is the sole author — this overrides the default commit template.
- Be extra cautious with destructive/dangerous git commands (`reset --hard`, force push, discarding checkouts, etc.) — confirm before running, beyond the usual default caution.
