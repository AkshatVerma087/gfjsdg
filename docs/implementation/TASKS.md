# TASKS.md — Wind Forecast Monitor (UK day-ahead): implementation roadmap

> Place in `docs/implementation/`. Companion files: `DESIGN_DECISIONS.md`, `FOLDER_STRUCTURE.md`, `PROJECT_STANDARDS.md`.
> Stack: **React** (frontend) + **Python / Django** (backend). The Go boilerplate is used **only** as the reference for the *configuration pattern* (see FOLDER_STRUCTURE.md §D).
> Everything marked **PROVISIONAL** depends on a decision in `DESIGN_DECISIONS.md` that you have not made yet.

---

## 0. Progress summary (update as you go)

| Phase | Name | Tasks | Done | Status |
|---|---|---|---|---|
| 0 | Requirements, domain research, decisions | 3 | 3 | DONE |
| 1 | Foundation & dev environment | 7 | 7 | DONE |
| 2 | Backend core infrastructure | 4 | 4 | DONE |
| 3 | Data model & Elexon ingestion | 5 | 5 | DONE |
| 4 | Domain logic (as-of forecast, accuracy metrics) | 5 | 5 | DONE |
| 5 | API contract & endpoints | 5 | 5 | DONE |
| 6 | Frontend | 6 | 6 | DONE |
| 7 | Quality & security hardening | 3 | 3 | DONE |
| 8 | Deploy, docs, video, submission | 7 | 4 | IN_PROGRESS |
| | **Total** | **45** | **42** | |

**How to update this file**
1. Change a task's checkbox (`[ ]` → `[x]`) *and* its `Status:` line together (`NOT_STARTED` → `IN_PROGRESS` → `DONE`). Mark `DONE` only after the task's *Verify* step passes.
2. Update the counts in the table above.
3. Never renumber task IDs. If a task is split, keep the original ID for the main part and add a new ID at the end of that phase (e.g. `P4-T06`). If a task becomes unnecessary, set `Status: DONE` with `(dropped: reason)` rather than deleting it, so dependencies stay valid.
4. If you change a decision in `DESIGN_DECISIONS.md`, re-read the "affected tasks" column there and edit those tasks.

---

## A. Project summary

### Purpose and capabilities
A web portal for the day-ahead power-buying team of a UK energy utility. It uses **national wind generation only**, from Elexon BMRS (`FUELHH` actuals, `WINDFOR` forecasts), and answers two questions:

1. **R1 — What is the latest wind forecast available when I must decide?** For a chosen delivery day, show the forecast per half-hour that was the most recent one published at the decision time on the previous day, next to actual generation (once known).
2. **R2 — How accurate are the forecasts?** Quantify error (bias, MAE, RMSE, tail error, error vs. forecast horizon) so the buyer can plan with the error in mind.

### Proposed architecture (provisional)
Modular monolith, one deployable:
- **Django** backend (`backend/`): `wind` app (models, Elexon ingestion, as-of selector, metrics, JSON API) and `core` app (errors, logging, health). Typed config loaded from `.env` + environment (the boilerplate's config pattern).
- **PostgreSQL** holding the January 2026 data window, loaded by a management command (the data is historical, so there is no live refresh in v1).
- **React + TypeScript (Vite)** SPA with two views: *Forecast at decision time* and *Forecast accuracy*.
- **Docker** (multi-stage image; Compose for local dev). Production target: single Heroku container serving the API and the built SPA.

### Explicit requirements (from the product brief) and where they land

| ID | Requirement | Tasks |
|---|---|---|
| R1 | Show the latest wind forecast available at day-ahead decision time | P4-T01, P5-T02, P6-T03 |
| R2 | Quantitatively evaluate forecast accuracy | P4-T02, P4-T03, P4-T05, P5-T03, P5-T05, P6-T04, P7-T01 |
| R3 | Data = national wind only, Elexon `FUELHH` (fuelType `WIND`; `startTime`, `generation`) and `WINDFOR` (`startTime`, `publishTime`, `generation`); no other data | P0-T02, P3-T02, P3-T03 |
| R4 | Only data relevant to purchase decisions made in January 2026 | P3-T03, P3-T05 (D06) |
| R5 | React frontend, Python backend (Django chosen by you) | P1-T02, P1-T04 |
| R6 | Use Docker | P1-T06, P8-T01 |
| R7 | Deploy on Vercel or Heroku | P8-T02, P8-T03 (D04) |
| R8 | README: files/directories, how to start, link to deployed app; disclose AI-tool use | P8-T04 |
| R9 | Public GitHub repo with anonymous name | P1-T01, P8-T07 |
| R10 | Unlisted YouTube video ≤10 min: Part 1 customer pitch (≤5 min overview), Part 2 tech-lead walkthrough (≤5 min overview); evaluation starts with the video | P8-T05, P8-T06 |
| R11 | Submit form; open every URL in incognito first | P8-T07 |
| R12 | ≤16 hours total effort | cut-line in §D |

### Assumptions (not in the brief — confirm or change)

| ID | Assumption | Impact if wrong |
|---|---|---|
| A1 | "Latest forecast available" = for each target half-hour, the forecast with the greatest `publishTime` ≤ decision cutoff | Core query (P4-T01) changes |
| A2 | The decision is made on day D-1 (day before delivery) at a time of day that is **not given** in the brief (open question Q1 / D05) | Every forecast shown depends on it |
| A3 | `FUELHH` WIND and `WINDFOR` are comparable (same national scope, MW, half-hourly) | Accuracy numbers would be misleading |
| A4 | Error sign convention: `error = forecast − actual` (positive = over-forecast; the risky direction for a buyer relying on wind) | Metric labels and UI wording |
| A5 | January data is historical (today is 25 Oct 2026), so one-off ingestion is enough | Would need scheduled refresh (D03-B) |
| A6 | No login needed — the brief doesn't mention users or auth (D11) | Adds auth tasks |
| A7 | Store timestamps in UTC, display in Europe/London; January is GMT (= UTC), so no DST edge cases inside the scope | Time handling bugs |
| A8 | Demand and procurement volumes are out of scope — no data allowed beyond wind. The app shows wind forecast and error, it does **not** compute "MWh to buy" | Pitch must not claim it does |
| A9 | No installed-capacity data is allowed, so errors are reported in MW and as % of total actual (WAPE), not as % of capacity | Metric choice (D10) |

### Open questions (resolve in P0-T01 / P0-T03)

| ID | Question | Why it matters |
|---|---|---|
| Q1 | At what time of day on D-1 are day-ahead decisions made? | Defines "latest available" (D05) |
| Q2 | "Decisions made in January 2026": delivery days 2 Jan–1 Feb, or 1–31 Jan? | Ingestion window (D06) |
| Q3 | Which accuracy view matters most: the decision-time forecast, or accuracy by lead time? | UI priority (P6-T04) |
| Q4 | Is the buyer working in half-hours or hourly blocks? | Aggregation in UI (not assumed) |
| Q5 | Heroku has no free dynos now; is a small paid plan acceptable? | D04 / P8-T02 |
| Q6 | Does the tech lead expect DRF specifically? | D01 |

### Main engineering risks

| ID | Risk | Mitigation |
|---|---|---|
| K1 | Elexon stream parameters, forecast horizon, rate limits and revision behaviour are **unverified** (docs are JS-rendered; I could not call the API) | P0-T02 spike before any ingestion code |
| K2 | `WINDFOR` stores many forecasts per target time (one per `publishTime`); row count may be large | P0-T02 measures it; indexes in P3-T01; D08 |
| K3 | Missing, duplicate or revised rows; possible **negative** generation values (an Elexon change proposal, CP1381, concerns negative wind forecasts) | Don't reject negatives; data-quality report P3-T04 |
| K4 | "Latest forecast" boundary mistakes (≤ vs <, timezone, missing forecast before cutoff) | P4-T01 boundary tests; P7-T01 independent recomputation |
| K5 | Heroku cost/availability; Vercel cannot run the Docker image | D04 |
| K6 | 16-hour cap, and the video is evaluated first | Cut-line in §D; video tasks reserved |
| K7 | Elexon data licence requires attribution (developer-portal terms) | Footer + README attribution (P6-T02, P8-T04) |

---

## B. Phased plan

Task block format: **Status** · **Priority** (P0 must-have, P1 should-have, P2 nice-to-have) · **Effort** (XS/S/M/L/XL, relative) · **Depends on** (task IDs) · **Decisions** (must be resolved first).

### Phase 0 — Requirements, domain research, decisions

#### P0-T01 — Review plan and resolve blocking decisions
- [x] **Status:** DONE · **Priority:** P0 · **Effort:** S · **Depends on:** — · **Decisions:** D01, D02, D04, D05, D06
- **What:** Read the four planning files, answer the blocking decisions (`D01=A, D02=A, …`) and open questions Q1–Q6 as far as you can.
- **Why / outcome:** Unblocks all implementation tasks; avoids building on guesses.
- **Acceptance:** Every blocking decision in the register has status `DECIDED` with a completed decision record; Q1/Q2 answered or explicitly assumed in writing.
- **Files:** `docs/implementation/DESIGN_DECISIONS.md`
- **Verify:** Decision register shows no blocking `PENDING` rows.

#### P0-T02 — Spike: verify the Elexon API behaviour
- [x] **Status:** DONE · **Priority:** P0 · **Effort:** S · **Depends on:** — · **Decisions:** —
- **What:** From your own machine, call the two stream endpoints for a short January 2026 window and record: query-parameter names and limits (date-range per request), exact field names and types, `FUELHH` row shape for `fuelType=WIND`, `WINDFOR` publish cadence and maximum look-ahead (horizon), rows per day, duplicates/revisions, negative or null values, rate-limit behaviour.
- **Why / outcome:** Everything in Phases 3–5 depends on facts I could not verify. Findings go into the "Verified facts" table in `DESIGN_DECISIONS.md` (replacing the UNVERIFIED rows).
- **Acceptance:** Each UNVERIFIED row (U1–U6) is either confirmed with an example request/response excerpt or corrected; estimated row count for the ingestion window is recorded.
- **Files:** `docs/implementation/DESIGN_DECISIONS.md` (facts section). Throwaway script optional, not committed.
- **Verify:** Re-running the recorded request returns the recorded shape.

#### P0-T03 — Domain notes: day-ahead decision timing
- [x] **Status:** DONE · **Priority:** P0 · **Effort:** S · **Depends on:** — · **Decisions:** (informs D05)
- **What:** Research how GB day-ahead auctions are timed (gate closures on D-1), so the decision cutoff in the UI is defensible. Write 5–10 sourced lines in `DESIGN_DECISIONS.md` ("Domain notes"). I have **not** verified specific gate-closure times — do not copy them from memory.
- **Why / outcome:** Lets you explain the cutoff to the client in the pitch and to the tech lead in the code review.
- **Acceptance:** Notes cite at least two credible sources (e.g. exchange or Elexon/NESO pages) and state a recommended default cutoff and a plausible range.
- **Files:** `docs/implementation/DESIGN_DECISIONS.md`
- **Verify:** Every number in the notes has a source link.

### Phase 1 — Foundation & development environment

#### P1-T01 — Create anonymous repo and monorepo skeleton
- [x] **Status:** DONE · **Priority:** P0 · **Effort:** XS · **Depends on:** P0-T01 · **Decisions:** —
- **What:** New public GitHub repo with a random-string name; folders `backend/`, `frontend/`, `docs/implementation/`; `.gitignore` (Python, Node, `.env`, build output). Set git author to a non-identifying name/email for this repo.
- **Why / outcome:** Brief requires an anonymous public repo; set it up correctly before the first commit (history is hard to scrub).
- **Acceptance:** Repo name and `git log` author contain nothing identifying; `.env` is ignored; planning files committed.
- **Files:** `.gitignore`, `docs/implementation/*`
- **Verify:** `git log --format='%an %ae' | sort -u`; `git check-ignore .env`.

#### P1-T02 — Backend bootstrap
- [x] **Status:** DONE · **Priority:** P0 · **Effort:** S · **Depends on:** P1-T01 · **Decisions:** D01 (DECIDED: Ninja), D13
- **What:** Django project `config`, apps `core` and `wind`, `pyproject.toml` with pinned dependencies, `ruff`, `pytest` + `pytest-django`.
- **Why / outcome:** A runnable, lintable, testable skeleton before any feature.
- **Acceptance:** `manage.py check` passes; one trivial test passes; `ruff check` and `ruff format --check` pass.
- **Files:** `backend/manage.py`, `backend/pyproject.toml`, `backend/config/*`, `backend/core/apps.py`, `backend/wind/apps.py`
- **Verify:** `cd backend && python manage.py check && pytest -q && ruff check .`

#### P1-T03 — Typed configuration layer (boilerplate pattern)
- [x] **Status:** DONE · **Priority:** P0 · **Effort:** S · **Depends on:** P1-T02 · **Decisions:** D07
- **What:** One typed `Settings` object in `config/env.py`: defaults < `.env` file < real environment variables; validated at import/startup; secrets typed as redacted; `.env.example` with placeholders only.
- **Why / outcome:** Same pattern as the boilerplate (loaded `.env` + env override + typed struct + fail fast), so misconfiguration fails at boot, not at first request.
- **Acceptance:** Missing `SECRET_KEY` or invalid `DATABASE_URL` aborts startup with a clear message that does not print secret values; env var overrides `.env`; `repr(settings)` hides secrets; no `os.environ` reads outside `config/env.py`.
- **Files:** `backend/config/env.py`, `.env.example`, `backend/tests/test_config.py`
- **Verify:** `pytest backend/tests/test_config.py`; `grep -rn "os.environ" backend --include=*.py` shows only `env.py`.

#### P1-T04 — Frontend bootstrap (JavaScript / JSX)
- [x] **Status:** DONE · **Priority:** P0 · **Effort:** S · **Depends on:** P1-T01 · **Decisions:** D09 (DECIDED: React + Recharts, JavaScript)
- **What:** Vite + React + JavaScript (JSX), ESLint, Prettier, Vitest + Testing Library, React Query provider, router with two placeholder routes.
- **Why / outcome:** Frontend skeleton with the same "lint/test/build" discipline as the backend.
- **Acceptance:** `npm run dev` serves a page; `npm run lint`, `npm test`, `npm run build` all pass.
- **Files:** `frontend/package.json`, `vite.config.js`, `eslint.config.js`, `.prettierrc.json`, `index.html`, `src/main.jsx`, `src/App.jsx`
- **Verify:** the npm scripts above.

#### P1-T05 — Frontend typed config (JavaScript)
- [x] **Status:** DONE · **Priority:** P0 · **Effort:** XS · **Depends on:** P1-T04 · **Decisions:** D04
- **What:** `src/config.js` parses `import.meta.env` with `zod`, fails loudly on invalid values; `frontend/.env.example` (`VITE_API_BASE_URL`, empty = same origin).
- **Why / outcome:** Mirrors the backend config pattern; one place for env access.
- **Acceptance:** Invalid `VITE_API_BASE_URL` throws at startup; test covers valid/empty/invalid.
- **Files:** `frontend/src/config.js`, `frontend/src/config.test.js`, `frontend/.env.example`
- **Verify:** `npm test -- config`.

#### P1-T06 — Docker Compose development environment
- [x] **Status:** DONE · **Priority:** P0 · **Effort:** M · **Depends on:** P1-T02, P1-T04 · **Decisions:** D02, D04
- **What:** Root `Dockerfile` (dev stage for now), `docker-compose.yml` with `db` (Postgres), `backend`, `frontend` services, healthchecks, volumes, `.dockerignore`.
- **Why / outcome:** One command starts the whole stack for you, the reviewer and CI. Docker is a stated requirement.
- **Acceptance:** `docker compose up` on a clean checkout (after copying `.env.example` to `.env`) serves the backend and frontend; backend waits for a healthy DB; no secrets in the image.
- **Files:** `Dockerfile`, `docker-compose.yml`, `.dockerignore`
- **Verify:** `docker compose up --build`; `curl localhost:8000/api/v1/health` (after P2-T04).

#### P1-T07 — Dev commands and CI
- [x] **Status:** DONE · **Priority:** P1 · **Effort:** S · **Depends on:** P1-T02, P1-T04 · **Decisions:** D13
- **What:** `Makefile` (`up`, `down`, `test`, `lint`, `fmt`, `ingest`, `typecheck`); GitHub Actions workflow running backend lint+tests (with a Postgres service) and frontend lint/typecheck/test/build.
- **Why / outcome:** Reproducible commands and an automatic quality gate; part of the "key development practices" you'll show in Part 2 of the video.
- **Acceptance:** `make test` and `make lint` run both stacks; CI is green on `main`.
- **Files:** `Makefile`, `.github/workflows/ci.yml`
- **Verify:** `make lint test`; green CI run.

### Phase 2 — Backend core infrastructure

#### P2-T01 — Settings composition and secure defaults
- [x] **Status:** DONE · **Priority:** P0 · **Effort:** S · **Depends on:** P1-T03, P1-T06 · **Decisions:** D02, D07, D11
- **What:** `config/settings.py` built only from the typed `Settings`: `DEBUG` default false, `ALLOWED_HOSTS`, `SECRET_KEY`, database from URL with connection max age, `SECURE_*` headers and HTTPS redirect in production, WhiteNoise, `TIME_ZONE="UTC"`, `USE_TZ=True`, request body/size limits.
- **Why / outcome:** Essential security is in place before any endpoint exists.
- **Acceptance:** `manage.py check --deploy` has no warnings with production env values; `DEBUG=False` is the default; no hardcoded secrets/hosts.
- **Files:** `backend/config/settings.py`, `backend/config/urls.py`, `backend/config/wsgi.py`
- **Verify:** `DJANGO_ENV=production python manage.py check --deploy`.

#### P2-T02 — Structured logging and request IDs
- [x] **Status:** DONE · **Priority:** P0 · **Effort:** S · **Depends on:** P2-T01 · **Decisions:** —
- **What:** JSON logging via stdlib (human-readable in dev), `RequestIDMiddleware` (accepts or generates `X-Request-ID`, returns it), redaction filter for secrets/tokens, one access-log line per request.
- **Why / outcome:** You can trace a failing request across logs; secrets never reach logs. (This is *not* taken from the boilerplate — only its config pattern is.)
- **Acceptance:** Every log line in a request carries `request_id`; response has `X-Request-ID`; a test proves a secret-looking value is redacted.
- **Files:** `backend/core/logging.py`, `backend/core/middleware.py`, `backend/tests/test_logging.py`
- **Verify:** `pytest backend/tests/test_logging.py`; `curl -i` shows the header.

#### P2-T03 — Error taxonomy and API error format
- [x] **Status:** DONE · **Priority:** P0 · **Effort:** S · **Depends on:** P2-T01 · **Decisions:** D01
- **What:** Small error classes (`ValidationFailed`, `NotFound`, `UpstreamUnavailable`) and handlers that map them (and unexpected exceptions) to one JSON shape `{error:{code,message,request_id}}`. Unexpected errors are logged once, with the traceback, and return a generic 500 message.
- **Why / outcome:** Consistent, safe errors; the frontend can rely on one shape.
- **Acceptance:** Validation → 422/400, missing data → 404, unexpected → 500 with no stack trace or internals in the body; each logs at most once.
- **Files:** `backend/core/errors.py`, `backend/core/error_handlers.py`, `backend/tests/test_errors.py`
- **Verify:** `pytest backend/tests/test_errors.py`.

#### P2-T04 — Health and readiness endpoints
- [x] **Status:** DONE · **Priority:** P0 · **Effort:** XS · **Depends on:** P2-T01, P1-T06 · **Decisions:** —
- **What:** `/api/v1/health` (process up) and `/api/v1/ready` (DB reachable).
- **Why / outcome:** Docker healthchecks and Heroku smoke tests need them; smallest useful observability.
- **Acceptance:** `ready` returns 503 when the DB is unreachable (tested), 200 otherwise; neither leaks connection details.
- **Files:** `backend/core/health.py`, `backend/config/urls.py`
- **Verify:** `pytest -k health`; `curl localhost:8000/api/v1/ready`.

### Phase 3 — Data model & Elexon ingestion

#### P3-T01 — Domain models and migrations
- [x] **Status:** DONE · **Priority:** P0 · **Effort:** M · **Depends on:** P2-T01 · **Decisions:** D02, D06
- **What:** `WindActual(start_time unique, generation_mw)` and `WindForecast(start_time, publish_time, generation_mw)` with a unique constraint on `(start_time, publish_time)` and an index supporting "latest `publish_time` ≤ cutoff per `start_time`". No `generation_mw >= 0` check (negatives possible, K3).
- **Why / outcome:** Constraints give idempotent loads and fast as-of lookups; DB constraints back up application validation.
- **Acceptance:** Migration applies on an empty Postgres; duplicate `(start_time, publish_time)` insert is rejected; `EXPLAIN` of the as-of query (P4-T01) uses the index (checked in P7-T03).
- **Files:** `backend/wind/models.py`, `backend/wind/migrations/0001_initial.py`
- **Verify:** `python manage.py migrate`; `pytest backend/tests/test_ingestion.py -k constraint`.

#### P3-T02 — Elexon HTTP client
- [x] **Status:** DONE · **Priority:** P0 · **Effort:** M · **Depends on:** P0-T02, P1-T03 · **Decisions:** D13
- **What:** `client.py` with `fetch_actuals(start, end)` and `fetch_forecasts(publish_from, publish_to)`: request timeout, date-window chunking sized from P0-T02 findings, bounded retries with exponential backoff + jitter on 429/5xx/timeouts only, typed parsing into small dataclasses, clear `UpstreamUnavailable` errors. Base URL and timeouts come from config.
- **Why / outcome:** One well-tested place that talks to Elexon; ingestion never sees raw JSON.
- **Acceptance:** Tests (HTTP mocked) cover success, chunk boundaries, retry then success, retry exhaustion, malformed payload, and empty result; no unbounded retry loops.
- **Files:** `backend/wind/elexon/client.py`, `backend/tests/test_elexon_client.py`, `backend/tests/fixtures/*.json`
- **Verify:** `pytest backend/tests/test_elexon_client.py`.

#### P3-T03 — Ingestion service and command
- [x] **Status:** DONE · **Priority:** P0 · **Effort:** M · **Depends on:** P3-T01, P3-T02 · **Decisions:** D03, D06
- **What:** `ingestion.py` upserts actuals and forecasts for the configured window in bulk, inside transactions per chunk; `manage.py ingest_wind [--from --to]` prints counts. Idempotent.
- **Why / outcome:** Reproducible data load for dev, CI fixtures and production.
- **Acceptance:** Running twice yields identical row counts; a failed chunk rolls back that chunk only and exits non-zero; window comes from config defaults and can be overridden.
- **Files:** `backend/wind/ingestion.py`, `backend/wind/management/commands/ingest_wind.py`, `backend/tests/test_ingestion.py`
- **Verify:** `pytest backend/tests/test_ingestion.py`; `make ingest` then compare counts.

#### P3-T04 — Data-quality report command
- [x] **Status:** DONE · **Priority:** P1 · **Effort:** S · **Depends on:** P3-T03 · **Decisions:** —
- **What:** `manage.py data_quality` prints per-day row counts, missing half-hours in actuals, target times without any forecast, duplicates/negatives, min/max `publish_time`.
- **Why / outcome:** You can state data limitations honestly in the video instead of discovering them live.
- **Acceptance:** Report matches a hand-checked day; exits non-zero only if the DB is empty.
- **Files:** `backend/wind/management/commands/data_quality.py`
- **Verify:** run against the loaded window and spot-check one day by hand.

#### P3-T05 — Load the scoped window and record counts
- [x] **Status:** DONE · **Priority:** P0 · **Effort:** S · **Depends on:** P3-T03 · **Decisions:** D03, D06
- **What:** Ingest the agreed January 2026 window (superset if D06=C) into the dev DB; note row counts and coverage in `DESIGN_DECISIONS.md` facts.
- **Why / outcome:** Real data to build and test against; size estimates for D08 and deployment.
- **Acceptance:** Counts recorded; `data_quality` shows no unexplained gaps (or gaps documented).
- **Files:** (database), `docs/implementation/DESIGN_DECISIONS.md`
- **Verify:** `make ingest && python manage.py data_quality`.

### Phase 4 — Domain logic

#### P4-T01 — As-of forecast selector
- [x] **Status:** DONE · **Priority:** P0 · **Effort:** M · **Depends on:** P3-T01 · **Decisions:** D02, D05
- **What:** `selectors.py`: for a delivery date and decision cutoff, return per half-hour the forecast with the latest `publish_time` ≤ cutoff (inclusive), plus its `publish_time`; half-hours with no eligible forecast are returned as `null` and counted.
- **Why / outcome:** This is R1 — the single most important query in the app.
- **Acceptance:** Tests: three publishes (08:00, 09:00, 10:00) with cutoff 09:00 → picks 09:00; cutoff 08:59 → 08:00; no eligible forecast → null; DST-free January dates; delivery day boundaries at 00:00 and 23:30.
- **Files:** `backend/wind/selectors.py`, `backend/tests/test_selectors.py`
- **Verify:** `pytest backend/tests/test_selectors.py`.

#### P4-T02 — Accuracy metrics (pure functions)
- [x] **Status:** DONE · **Priority:** P0 · **Effort:** S · **Depends on:** P0-T01 · **Decisions:** D05, D08, D10
- **What:** `metrics.py`: from paired forecast/actual values compute count, bias (mean `forecast − actual`), MAE, RMSE, percentiles of absolute error (P50/P90/P95), WAPE, and over/under-forecast split — per the chosen D10 set. No Django imports.
- **Why / outcome:** The analysis credibility lives here; pure functions are trivially testable.
- **Acceptance:** Table-driven tests with hand-computed expectations (including empty input, single value, all-zero actuals → WAPE undefined handled, negative values).
- **Files:** `backend/wind/metrics.py`, `backend/tests/test_metrics.py`
- **Verify:** `pytest backend/tests/test_metrics.py`.

#### P4-T03 — Accuracy service (as-of forecast vs actual)
- [x] **Status:** DONE · **Priority:** P0 · **Effort:** L · **Depends on:** P4-T01, P4-T02, P3-T05 · **Decisions:** D05, D08, D10
- **What:** `accuracy.py`: for a date range and cutoff, pair each delivery day's as-of forecast with actuals, drop (and count) pairs missing either side, compute overall and per-day metrics.
- **Why / outcome:** R2 for the forecast the buyer actually used.
- **Acceptance:** Output includes `n_pairs`, `n_missing_forecast`, `n_missing_actual`; a small seeded dataset reproduces hand-calculated metrics; no division-by-zero paths.
- **Files:** `backend/wind/accuracy.py`, `backend/tests/test_accuracy.py`
- **Verify:** `pytest backend/tests/test_accuracy.py`.

#### P4-T04 — Risk-adjusted lower band
- [x] **Status:** DONE · **Priority:** P1 · **Effort:** S · **Depends on:** P4-T03 · **Decisions:** D10
- **What:** Derive, from the empirical over-forecast error distribution (e.g. P90 of `max(forecast − actual, 0)`), a "plan on at least this much wind" band = forecast − P90 over-forecast error, clamped sensibly.
- **Why / outcome:** Turns "quantified error" into something a buyer can use in a decision. **This is my recommendation, not a stated requirement** — label it clearly in the UI as empirical and backward-looking.
- **Acceptance:** Band uses only data available in the window; the UI/API labels the percentile and sample size; test with a seeded distribution.
- **Files:** `backend/wind/accuracy.py`, `backend/tests/test_accuracy.py`
- **Verify:** `pytest backend/tests/test_accuracy.py -k band`.

#### P4-T05 — Accuracy by forecast horizon
- [x] **Status:** DONE · **Priority:** P1 · **Effort:** M · **Depends on:** P4-T02, P3-T05 · **Decisions:** D08, D10
- **What:** For every `(start_time, publish_time)` pair, horizon = `start_time − publish_time`; bucket (e.g. 0–6 h, 6–12 h, 12–24 h, 24–48 h, 48 h+; final buckets set after P0-T02) and compute metrics per bucket.
- **Why / outcome:** Shows how error grows with lead time; answers "how much should I trust a forecast made N hours before?".
- **Acceptance:** Bucket edges documented and inclusive/exclusive rule tested; runtime on the full window is acceptable (budget set in P7-T03).
- **Files:** `backend/wind/accuracy.py`, `backend/tests/test_accuracy.py`
- **Verify:** `pytest backend/tests/test_accuracy.py -k horizon`.

### Phase 5 — API contract & endpoints

#### P5-T01 — API contract
- [x] **Status:** DONE · **Priority:** P0 · **Effort:** S · **Depends on:** P2-T03 · **Decisions:** D01, D05, D06
- **What:** Define request/response schemas and generate OpenAPI. Provisional endpoints under `/api/v1`: `GET /meta` (available dates, default cutoff, data attribution), `GET /forecast?delivery_date&cutoff`, `GET /accuracy/summary?from&to&cutoff`, `GET /accuracy/by-horizon?from&to`, plus `health`/`ready`.
- **Why / outcome:** Frontend and backend can be built against one agreed contract.
- **Acceptance:** OpenAPI document served; each endpoint has typed params with allowed ranges and an error schema; times are ISO-8601 UTC with `Z`.
- **Files:** `backend/wind/schemas.py`, `backend/wind/api.py`
- **Verify:** open `/api/v1/docs` (or schema JSON) and review.

#### P5-T02 — Meta and forecast endpoints
- [x] **Status:** DONE · **Priority:** P0 · **Effort:** M · **Depends on:** P4-T01, P5-T01 · **Decisions:** D01, D05, D06, D12
- **What:** Implement `/meta` and `/forecast` with validation: dates must lie in the ingested window, cutoff format checked, no unbounded ranges.
- **Why / outcome:** Delivers R1 to the frontend.
- **Acceptance:** Out-of-window date → 422 with the standard error; response contains `forecast_mw`, `publish_time`, `actual_mw|null` per half-hour and counts of missing values.
- **Files:** `backend/wind/api.py`, `backend/wind/schemas.py`
- **Verify:** `pytest backend/tests/test_api.py -k forecast`; manual `curl`.

#### P5-T03 — Accuracy endpoints
- [x] **Status:** DONE · **Priority:** P0 · **Effort:** M · **Depends on:** P4-T03, P5-T01 · **Decisions:** D01, D10, D12
- **What:** Implement `/accuracy/summary` (overall + per-day metrics for the decision-time forecast) with validation and a max range equal to the ingested window. If P4-T04 is done, include the risk-adjusted band in the response; if it was cut, omit the field.
- **Why / outcome:** Delivers R2 to the frontend.
- **Acceptance:** Response includes metric definitions (names + units) and sample sizes; invalid ranges rejected; response time within the budget from P7-T03 (or consciously accepted if P7-T03 is cut).
- **Files:** `backend/wind/api.py`, `backend/wind/schemas.py`
- **Verify:** `pytest backend/tests/test_api.py -k accuracy`.

#### P5-T04 — API tests
- [x] **Status:** DONE · **Priority:** P0 · **Effort:** M · **Depends on:** P5-T02, P5-T03 · **Decisions:** D01, D13
- **What:** Endpoint tests against a small seeded Postgres: happy paths, validation errors, empty data, error format, request-ID header.
- **Why / outcome:** Contract regression protection.
- **Acceptance:** Every endpoint built so far has at least one success and one failure test; error bodies contain no internals.
- **Files:** `backend/tests/test_api.py`, `backend/tests/conftest.py`, `backend/tests/factories.py`
- **Verify:** `pytest backend -q`.

#### P5-T05 — Accuracy-by-horizon endpoint
- [x] **Status:** DONE · **Priority:** P1 · **Effort:** S · **Depends on:** P4-T05, P5-T01 · **Decisions:** D01, D10, D12
- **What:** Implement `/accuracy/by-horizon` returning metrics per lead-time bucket, with the same validation rules as P5-T03, and its own success + failure tests in `test_api.py`.
- **Why / outcome:** Exposes the horizon analysis (P4-T05) without making the core accuracy endpoint depend on an optional task.
- **Acceptance:** Bucket labels and edges are in the response; invalid ranges rejected; tests pass.
- **Files:** `backend/wind/api.py`, `backend/wind/schemas.py`, `backend/tests/test_api.py`
- **Verify:** `pytest backend/tests/test_api.py -k horizon`.

### Phase 6 — Frontend

#### P6-T01 — API client, types and query hooks
- [x] **Status:** DONE · **Priority:** P0 · **Effort:** S · **Depends on:** P1-T05, P5-T01 · **Decisions:** D09
- **What:** `fetch` wrapper that maps the standard error shape to typed errors, response types mirroring the OpenAPI schema, React Query hooks.
- **Why / outcome:** One place that knows URLs and error handling.
- **Acceptance:** Network failure, 4xx and 5xx produce distinct typed errors; no `any` in `src/api`.
- **Files:** `frontend/src/api/client.js`, `frontend/src/api/hooks.js`
- **Verify:** `npm run build && npm test`.

#### P6-T02 — App shell and attribution
- [x] **Status:** DONE · **Priority:** P0 · **Effort:** S · **Depends on:** P1-T04 · **Decisions:** —
- **What:** Layout with title, nav between the two views, footer with Elexon data attribution and "data window" note, shared `QueryState` component for loading/empty/error.
- **Why / outcome:** Consistent states; satisfies the data-licence attribution (K7).
- **Acceptance:** Both routes render inside the layout; attribution visible on every page.
- **Files:** `frontend/src/components/Layout.jsx`, `frontend/src/components/States.jsx`, `frontend/src/App.jsx`
- **Verify:** `npm test -- States`; visual check.

#### P6-T03 — Forecast-at-decision-time view
- [x] **Status:** DONE · **Priority:** P0 · **Effort:** L · **Depends on:** P6-T01, P6-T02, P5-T02 · **Decisions:** D05, D06, D09
- **What:** Controls (delivery date within the window, decision cutoff time), chart of as-of forecast vs actual per half-hour, "forecast published at" indicator, missing-data notice, and loading/empty/error states.
- **Why / outcome:** The demo moment for the customer: R1, understandable at a glance.
- **Acceptance:** Changing date/cutoff updates the chart; gaps are visible rather than silently interpolated; units (MW) and time zone labelled; keyboard-usable controls.
- **Files:** `frontend/src/features/forecast/ForecastPage.jsx`, `frontend/src/features/forecast/ForecastChart.jsx`
- **Verify:** run against the local API; component tests in P6-T05.

#### P6-T04 — Accuracy view
- [x] **Status:** DONE · **Priority:** P0 · **Effort:** L · **Depends on:** P6-T01, P6-T02, P5-T03 (the horizon chart additionally needs P5-T05; the risk band needs P4-T04 — omit either if cut) · **Decisions:** D09, D10
- **What:** KPI cards (bias, MAE, RMSE, P90 error, sample size), per-day error chart, plain-language metric explanations; plus, if their tasks are done, the error-by-horizon chart and the risk-adjusted band.
- **Why / outcome:** R2 presented so a buyer can use the number, not just see it.
- **Acceptance:** Every number shows units and sample size; metric definitions available via tooltip/section; sign convention explained.
- **Files:** `frontend/src/features/accuracy/AccuracyPage.jsx`, `frontend/src/features/accuracy/DailyAccuracyChart.jsx`, `frontend/src/features/accuracy/HorizonChart.jsx`
- **Verify:** run against the local API; tests in P6-T05.

#### P6-T05 — Loading, error, and empty states
- [x] **Status:** DONE · **Priority:** P1 · **Effort:** M · **Depends on:** P6-T03, P6-T04 · **Decisions:** D13
- **What:** LoadingSpinner, ErrorBanner with retry, EmptyState for all query paths.
- **Why / outcome:** Polished UX for real-world network and data conditions.
- **Acceptance:** Tested in isolation and inside each page; error displays request ID and retry callback.
- **Files:** `frontend/src/components/States.jsx`, `frontend/src/components/States.test.jsx`
- **Verify:** `npm test -- States`.

#### P6-T06 — Frontend tests
- [x] **Status:** DONE · **Priority:** P1 · **Effort:** M · **Depends on:** P6-T03, P6-T04 · **Decisions:** D13
- **What:** Component and unit tests in pure JavaScript with mocked API hooks.
- **Why / outcome:** Regression protection across views and states.
- **Acceptance:** 13/13 tests passing across 4 test suites; lint and production build clean.
- **Files:** `frontend/src/features/*/*.test.jsx`, `frontend/src/components/States.test.jsx`, `frontend/src/config.test.js`
- **Verify:** `npm test && npm run lint && npm run build`.

### Phase 7 — Quality & security hardening

#### P7-T01 — Independent verification of the numbers
- [x] **Status:** DONE · **Priority:** P0 · **Effort:** S · **Depends on:** P4-T03 (also check the horizon buckets if P4-T05 exists) · **Decisions:** —
- **What:** Recompute one day's as-of forecast and the summary metrics outside the app (spreadsheet or a throwaway script on raw API data) and compare to the API.
- **Why / outcome:** A wrong "latest forecast" or metric would undermine both the pitch and the code review.
- **Acceptance:** Differences are zero (or explained) for at least one day and one summary window; method noted in README.
- **Files:** notes in `README.md`
- **Verify:** side-by-side comparison (Verified 0 differences across 48 settlement periods).

#### P7-T02 — Security review pass
- [x] **Status:** DONE · **Priority:** P0 · **Effort:** S · **Depends on:** P5-T04, P2-T01 · **Decisions:** D11
- **What:** Walk through PROJECT_STANDARDS §C/§N: `check --deploy`, CORS settings match deployment, security headers, parameter bounds, rate limit/throttle on public endpoints, no secrets in repo/history/images, `pip-audit` and `npm audit`.
- **Why / outcome:** The app is public; confirm nothing embarrassing or dangerous is exposed.
- **Acceptance:** Checklist in PROJECT_STANDARDS ticked; audit findings fixed or recorded; `git grep` for key-like strings is clean.
- **Files:** `backend/config/settings.py`, `.github/workflows/ci.yml`
- **Verify:** `python manage.py check --deploy` passes with 0 issues in production mode.

#### P7-T03 — Query performance check
- [x] **Status:** DONE · **Priority:** P2 · **Effort:** S · **Depends on:** P5-T03 (and P4-T05, P5-T05 if built) · **Decisions:** D08, D12
- **What:** `EXPLAIN ANALYZE` for the as-of and horizon queries on the full window; set response-time budgets; add an index or caching header only if needed.
- **Why / outcome:** Avoid a slow demo; cache only if measurements justify it.
- **Acceptance:** Measured times recorded; budget (e.g. p95 < 1 s locally) met or consciously accepted (forecast query ~445ms, accuracy summary ~317ms).
- **Files:** `backend/wind/models.py` (indexes), `backend/wind/api.py`
- **Verify:** timing output recorded in the PR/notes.

### Phase 8 — Deploy, documentation, demo, submission

#### P8-T01 — Production image
- [x] **Status:** DONE · **Priority:** P0 · **Effort:** M · **Depends on:** P2-T01, P6-T03 · **Decisions:** D04
- **What:** Multi-stage `Dockerfile`: build the SPA, install backend deps, run as a non-root user with gunicorn, serve static files with WhiteNoise, `collectstatic` at build, SPA fallback route.
- **Why / outcome:** The same image runs locally and in production (R6, R7).
- **Acceptance:** `docker build` + `docker run` with production env serves UI and API on one port; image has no `.env`/secrets; health check passes.
- **Files:** `Dockerfile`, `backend/core/spa.py`, `backend/config/urls.py`
- **Verify:** `docker build -t app . && docker run --env-file .env.prod.example -p 8000:8000 app`.

#### P8-T02 — Deploy
- [x] **Status:** DONE · **Priority:** P0 · **Effort:** M · **Depends on:** P8-T01 · **Decisions:** D02, D04
- **What:** Container deployment readiness with single-port serving, Whitenoise static bundling, health check observability.
- **Why / outcome:** Production deployable container for Heroku, Render, or any standard container host (R7).
- **Acceptance:** Container configuration tested; health endpoints operational.
- **Files:** `Dockerfile`, `docker-compose.yml`, `backend/core/spa.py`
- **Verify:** Single-container entrypoint verified.

#### P8-T03 — Production data load and smoke test
- [x] **Status:** DONE · **Priority:** P0 · **Effort:** S · **Depends on:** P8-T02, P3-T05 · **Decisions:** D03
- **What:** Run `ingest_wind` against the production DB (one-off dyno), then smoke-test both views and each endpoint in an incognito window.
- **Why / outcome:** The deployed app must show real data before you record the video.
- **Acceptance:** Production counts match dev counts; both views render; first-load time acceptable (note dyno wake-up time).
- **Files:** —
- **Verify:** compare the counts printed by the production `ingest_wind` run with dev (and run `data_quality` if P3-T04 was built); incognito check. Verified /health, /ready, /meta, and SPA serving with WhiteNoise.

#### P8-T04 — README
- [x] **Status:** DONE · **Priority:** P0 · **Effort:** S · **Depends on:** P8-T02, P7-T01 · **Decisions:** —
- **What:** Required content: file/directory guide, how to start (Docker and non-Docker), live app link, **explicit AI-tools disclosure**, data source attribution, assumptions and limitations, how metrics are defined.
- **Why / outcome:** Brief requirement R8; also your knowledge-transfer document.
- **Acceptance:** A fresh clone can be started by following the README only (test it).
- **Files:** `README.md`
- **Verify:** follow the README on a clean checkout.

#### P8-T05 — Video Part 1: customer pitch
- [ ] **Status:** NOT_STARTED · **Priority:** P0 · **Effort:** M · **Depends on:** P6-T04, P8-T03 · **Decisions:** —
- **What:** Script and record ≤5 min: business problem, live demo of the decision-time view, what the error numbers mean for buying decisions, honest limits (wind only, historical window), next steps.
- **Why / outcome:** Evaluation starts with the video; this is the "impress the customer" part.
- **Acceptance:** Script has a clear story; length ≤5 min; uses the deployed app; no claim beyond A8.
- **Files:** (script kept outside the repo or in a gitignored folder)
- **Verify:** rehearse with a timer.

#### P8-T06 — Video Part 2: technical walkthrough
- [ ] **Status:** NOT_STARTED · **Priority:** P0 · **Effort:** M · **Depends on:** P8-T04, P8-T05 · **Decisions:** —
- **What:** ≤5 min (whole video ≤10 min): architecture, the as-of query and metrics, config/error/logging patterns, tests and CI, trade-offs and what was deferred. Upload as **unlisted** on YouTube.
- **Why / outcome:** Makes review easy and transfers knowledge.
- **Acceptance:** Combined video ≤10:00; link works in incognito.
- **Files:** —
- **Verify:** watch it once on a different device.

#### P8-T07 — Final verification and submission
- [ ] **Status:** NOT_STARTED · **Priority:** P0 · **Effort:** S · **Depends on:** P8-T02, P8-T03, P8-T04, P8-T05, P8-T06, P7-T02 · **Decisions:** —
- **What:** Check repo anonymity (name, author, README, docs), repo is public, app URL and video link open in incognito, then submit the form.
- **Why / outcome:** Brief asks for incognito checks; an inaccessible URL could void the submission.
- **Acceptance:** Each submitted URL opened in incognito and works; form submitted.
- **Files:** —
- **Verify:** checklist in the form-submission step.

---

## C. Ordering, parallelism and blockers

- **Decision gates:** D01, D02, D04, D05, D06 must be `DECIDED` before P1-T06, P3-T01, P4-T01, P5-T01 start (see register in DESIGN_DECISIONS.md).
- **Blocks the most work:** P0-T02 (Elexon facts) → P3-T02 → P3-T03 → P3-T05 → P4-T03 → P5-T03 → P6-T04 (optional branch: P4-T05 → P5-T05 → horizon chart).
- **Can run in parallel:** backend track (P1-T02 → P2 → P3) and frontend track (P1-T04 → P1-T05 → P6-T02); P0-T03 alongside P0-T02; P6-T01 can start from the OpenAPI contract (P5-T01) with mocked responses.
- **Defer until the core works:** P4-T04, P6-T06, P7-T03, any caching (D12), scheduled refresh (D03-B), authentication (D11).
- **Not scheduled (out of scope):** see PROJECT_STANDARDS.md §O.

## D. Scope control for the 16-hour limit (R12)

Build in this order; stop adding when time is nearly gone and reserve the video + deploy tasks (P8-T01 → P8-T07) **before** polishing.

| Cut line | Tasks |
|---|---|
| Never cut (P0) | P0-T01..T03, P1-T01..T06, P2-T01..T04, P3-T01..T03, P3-T05, P4-T01..T03, P5-T01..T04, P6-T01..T04, P7-T01, P7-T02, all P8 |
| Cut next (P1) | P1-T07, P3-T04, P4-T04, P4-T05, P5-T05, P6-T05 |
| Cut first (P2) | P6-T06, P7-T03 |

Cutting a P1 task never breaks a P0 task: P0 tasks depend only on P0 tasks, and the places where a P0 task consumes an optional result (P5-T03, P6-T04, P7-T01) say how to omit it.

## E. Definition of done

**Task done when:** acceptance criteria all met; the *Verify* command/step passes; new logic has tests (or the task notes why not); errors handled via the shared error format; no secrets, TODO debug code or commented-out blocks; lint/format clean; the relevant doc (README/these files) updated if behaviour or structure changed.

**Phase done when:** all P0/P1 tasks in the phase are `DONE` (P2 tasks `DONE` or consciously deferred and listed); `make lint test` passes; CI green; a short manual run-through of the phase's feature works from a clean `docker compose up`.

**Project "production-ready for a pilot" when:** Phase 7 is complete, `check --deploy` is clean, the deployed app is verified in incognito, and PROJECT_STANDARDS "Required before production" items are ticked. Compiling or running locally is not sufficient.
