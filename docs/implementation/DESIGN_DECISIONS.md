# DESIGN_DECISIONS.md — Wind Forecast Monitor

> Place in `docs/implementation/`. **The final decision on every item is yours.** My "recommendation" is advice only; nothing is `DECIDED` until you select it.
> Reply format: `D01=A, D02=A, D04=A, D05=B, D06=C` (blocking ones first). Non-blocking decisions have a **provisional default** I will use unless you change it.

---

## 0. Decision register

| ID | Topic | Blocking? | Status | Affected tasks |
|---|---|---|---|---|
| D01 | Backend API framework | **Yes** | **DECIDED — A (Django Ninja)** | P1-T02, P2-T03, P5-T01, P5-T02, P5-T03, P5-T04 |
| D02 | Database / persistence | **Yes** | **DECIDED — A (PostgreSQL)** | P1-T06, P2-T01, P3-T01, P4-T01, P8-T02 |
| D03 | Data acquisition trigger (how data gets in) | No | **DECIDED — A (Management command)** | P3-T03, P3-T05, P8-T03 |
| D04 | Deployment topology | **Yes** | **DECIDED — A (Single Docker container)** | P1-T05, P1-T06, P8-T01, P8-T02 |
| D05 | "Decision time" semantics (which forecast is "latest available") | **Yes** | **DECIDED — B (Selectable in UI, default 11:00 D-1)** | P0-T03, P4-T01, P4-T02, P4-T03, P5-T01, P5-T02, P6-T03 |
| D06 | Meaning/size of the "January 2026" window | **Yes** | **DECIDED — C (Ingest superset, default 2 Jan–1 Feb)** | P3-T01, P3-T03, P3-T05, P5-T01, P5-T02, P6-T03 |
| D07 | Configuration library (boilerplate pattern in Python) | No | **DECIDED — A (pydantic-settings)** | P1-T03, P2-T01 |
| D08 | Where accuracy metrics are computed | No | **DECIDED — B (Python with NumPy / pure metrics)** | P4-T02, P4-T03, P4-T05, P7-T03 |
| D09 | Frontend stack and chart library | No | **DECIDED — A (React + Vite + Recharts)** | P1-T04, P6-T03, P6-T04 |
| D10 | Which accuracy metrics to expose | No | **DECIDED — B (Count, Bias, MAE, RMSE, P50/90/95, WAPE, Over/Under)** | P4-T02, P4-T03, P4-T04, P4-T05, P5-T03, P6-T04 |
| D11 | Authentication | No | **DECIDED — A (None, public read-only throttled)** | P2-T01, P7-T02 |
| D12 | Caching | No | **DECIDED — A (None initially; HTTP Cache headers if needed)** | P5-T02, P5-T03, P7-T03 |
| D13 | Testing strategy and mock boundary | No | **DECIDED — A (pytest on real Postgres, mock external Elexon HTTP)** | P1-T07, P3-T02, P5-T04, P6-T05 |

**Already fixed by you (not decisions):** React frontend; Python **Django** backend; Docker; deploy to Vercel or Heroku; the Go boilerplate is a reference for the **configuration pattern only**.

---

## 1. Facts, sources and what is still unverified

Results verified directly against live Elexon BMRS API (`https://data.elexon.co.uk/bmrs/api/v1`) in spike (P0-T02):

| # | Fact | Status | Source |
|---|---|---|---|
| V1 | Base URL `https://data.elexon.co.uk/bmrs/api/v1`; endpoints do not require authorization | **Verified** | Live spike call return HTTP 200 without headers/keys |
| V2 | `FUELHH` and `WINDFOR` stream endpoints at `/datasets/<NAME>/stream` return compact JSON arrays | **Verified** | Live spike calls |
| V3 | Settlement periods are 30 min (1–48 per day); `generation` is in integer MW | **Verified** | Live spike payload inspect (`settlementPeriod`: 1..48, `generation`: int) |
| V4 | BMRS Data Licence terms require attribution in UI and docs | **Verified** | developer.data.elexon.co.uk terms |
| V5 | Zero negative values detected in January 2026 sample, but models must avoid strictly positive constraints | **Verified** | Zero negatives in 2026-01 sample; non-negative constraint omitted |
| V6 (was U1) | Stream query params: `FUELHH/stream` uses `settlementDateFrom` & `settlementDateTo` (YYYY-MM-DD); `WINDFOR/stream` uses `publishDateTimeFrom` & `publishDateTimeTo` (ISO-8601 UTC) | **Verified** | P0-T02 live spike |
| V7 (was U2) | Max date range: 30+ day ranges are accepted in single stream requests without 400/413 errors (e.g. 30 days FUELHH = 28,800 rows returned in ~3s) | **Verified** | P0-T02 live spike |
| V8 (was U3) | `WINDFOR` publishes ~8 times/day (~every 3 hours: 01:30, 04:30, 07:30, 10:30, 13:30, 16:30, 19:30, 22:30 UTC); forecast horizon extends from past target hours up to +66.5 hours | **Verified** | P0-T02 live spike |
| V9 (was U4) | `FUELHH` has exactly 48 half-hours per day when filtered for `fuelType == 'WIND'`; no duplicate start times for same fuelType | **Verified** | P0-T02 live spike (48 unique startTimes per day) |
| V10 (was U5) | Rate limits: fast response times (~200ms-1s), no 429 encountered during testing; resilient backoff recommended | **Verified** | P0-T02 live spike |
| V11 (was U6) | Ingestion row count: 22,192 `WINDFOR` rows and 1,728 `FUELHH` wind actuals for 36-day window (2025-12-30 to 2026-02-03, 100% complete half-hour coverage) | **Verified** | Ingested via `manage.py ingest_wind` and verified via `data_quality` |

### Domain notes (P0-T03)
In the Great Britain (GB) power wholesale market, day-ahead power purchasing decisions are governed by established auction gate closures on day D-1:
1. **EPEX SPOT GB Day-Ahead Auction**: Gate closure is **11:00 GMT/BST** on D-1. (Source: [EPEX SPOT Trading Rules & Day-Ahead GB Auction Specifications](https://www.epexspot.com/en/market-data/power/day-ahead/gb))
2. **Nord Pool N2EX Day-Ahead Auction**: Gate closure is **11:00 GMT/BST** on D-1. (Source: [Nord Pool GB Day-Ahead Auction Rules](https://www.nordpoolgroup.com/trading/Day-ahead-trading/))
3. **Utility Procurement Timing**: Power trading desks finalize day-ahead wind balancing positions between **10:00 and 11:00 GMT** to place bids prior to 11:00 auction gate closure.
4. **Default Cutoff Recommendation**: Default cutoff set to **11:00** on D-1, with interactive UI controls allowing buyers to test earlier (e.g., 09:00 morning desk briefing) or later (12:00 post-auction adjustment) cutoffs.

---

## 2. Blocking decisions

### D01 — Backend API framework

**Context.** The API is small: roughly 6 read-only JSON endpoints with typed query parameters (dates, cutoff time) and structured responses (time series, metrics). Needs: input validation, consistent errors, auto-generated OpenAPI for the contract (P5-T01).

| | **A. Django Ninja** | **B. Django REST Framework (DRF)** | **C. Plain Django views + Pydantic/manual validation** |
|---|---|---|---|
| Advantages | Typed params and schemas, automatic OpenAPI, little boilerplate; Pydantic aligns with `pydantic-settings` (D07) | Industry standard; huge ecosystem; many reviewers know it | No extra dependency; total control |
| Disadvantages | Smaller community than DRF; reviewer may be less familiar | More boilerplate (serializers, views, routers) for read-only endpoints | You hand-build validation, OpenAPI and error mapping |
| Ops complexity | Low | Low | Low |
| Dev / maintenance cost | Lowest of the three for this API | Medium | Highest (reinventing) |
| Testing | Django test client / pytest; schemas are plain classes | Same; serializers add test surface | Same, more custom code to test |
| Security / reliability | Validation by schema by default | Mature, widely audited | Validation gaps likelier |
| Fit for this product | **High** | High (safe, conventional choice) | Low |

**Recommendation:** **A** for speed and typed contracts in a 16-hour budget. Choose **B** if your tech lead expects DRF (open question Q6) — the structure barely changes.

**Decision record**
- Selected option: **A (Django Ninja)**
- Reason for choosing it: Strict type safety with Pydantic, automatic interactive OpenAPI docs (`/api/v1/docs`), minimal boilerplate for read-only analytical endpoints, and excellent performance matching modern typed Python standards.
- Consequences accepted: Reviewers less familiar with Ninja than DRF will see cleaner Pydantic schemas instead of DRF serializers.
- Decision date: 2026-10-25
- Related task IDs: P1-T02, P2-T03, P5-T01, P5-T02, P5-T03, P5-T04

**Implementation impact.** A: `wind/api.py` (router) + `wind/schemas.py`; handlers registered in `core/error_handlers.py`; `config/urls.py` mounts the API. B: `wind/views.py` + `wind/serializers.py`, DRF exception handler in `core/error_handlers.py`, `drf-spectacular` for OpenAPI. C: `wind/views.py` + validators in `wind/schemas.py`, hand-rolled OpenAPI (or none). Tests and folder tree change only in those files.

---

### D02 — Database / persistence

**Context.** Data = one month of half-hourly actuals (~1.5 k rows) plus forecasts with many publish times per target time (possibly hundreds of thousands of rows — U6). Key query: "latest publish ≤ cutoff per target time" (PostgreSQL has `DISTINCT ON`), plus percentile aggregations.

| | **A. PostgreSQL** (Compose locally, Heroku Postgres in prod) | **B. SQLite file, loaded at build and baked into the image** | **C. No database: immutable snapshot file (CSV/Parquet) loaded in memory** |
|---|---|---|---|
| Advantages | Same engine everywhere; `DISTINCT ON`, window functions, `percentile_cont`; real constraints | Zero external services, no DB cost | Fastest to start; no ORM/migrations |
| Disadvantages | Paid add-on on Heroku; one more service to run | No `DISTINCT ON`; dyno filesystem is ephemeral so data must be rebuilt/baked; weaker concurrency | Bypasses Django's strengths; memory use; harder to show "proper" engineering to a tech lead |
| Ops complexity | Medium | Low | Low |
| Dev / maintenance cost | Medium | Low–medium (query workarounds) | Low now, awkward later |
| Testing | Test against real Postgres (D13-A) | SQLite in tests differs from prod if prod is Postgres | Pure-Python tests, easy |
| Security / reliability | DB constraints enforce integrity | Integrity enforced less strictly | No constraints; relies on loader |
| Fit | **High** | Medium | Low–medium |

**Recommendation:** **A.** The as-of query and percentile maths are native in Postgres, and constraints protect data integrity. Only choose B/C if the Heroku add-on cost is a blocker (Q5).

**Decision record**
- Selected option: **A (PostgreSQL)**
- Reason for choosing it: Native support for `DISTINCT ON (start_time) ORDER BY start_time, publish_time DESC` enables high-speed as-of forecast selection with compound btree indexes. Strong integrity constraints prevent duplicated or corrupt intervals.
- Consequences accepted: Requires running Postgres service locally via Docker Compose and running migrations.
- Decision date: 2026-10-25
- Related task IDs: P1-T06, P2-T01, P3-T01, P4-T01, P8-T02

**Implementation impact.** A: `psycopg` driver, `db` service in `docker-compose.yml`, `DATABASE_URL` in config, constraints/indexes in `wind/models.py`, Postgres service in CI. B: `sqlite3`, ingestion in Docker build stage, as-of query rewritten with a correlated subquery or window function. C: no `models.py`/migrations; a loader module replaces ingestion; `selectors.py` works on dataframes.

---

### D04 — Deployment topology

**Context.** Brief: use Docker and deploy on Vercel **or** Heroku. Vercel cannot run an arbitrary Docker image; Heroku can via the container stack. Heroku's free dynos were retired in 2022 — expect a small paid plan (verify current pricing; Q5).

| | **A. Single Heroku container** (Django serves API + built React app) | **B. Frontend on Vercel + backend on Heroku container** | **C. Everything on Vercel** (Python serverless functions) |
|---|---|---|---|
| Advantages | One URL, no CORS, same image as local Docker | Vercel's CDN and preview deploys for the UI | One platform, free tier likely enough |
| Disadvantages | Heroku cost; dyno wake-up on cheap plans | Two deploys, CORS config, two sets of env vars | Django on serverless is awkward; DB must be external; Docker not used in production, weakening "use Docker" |
| Ops complexity | **Low** | Medium | Medium–high |
| Dev / maintenance cost | Low | Medium | Medium–high |
| Testing | Same image tested in CI | Needs cross-origin tests | Different runtime from local |
| Security / reliability | Fewer moving parts; one TLS endpoint | CORS must be strict | Cold starts, execution time limits |
| Fit | **High** | Medium | Low |

**Recommendation:** **A.**

**Decision record**
- Selected option: **A (Single Docker container / Heroku container stack)**
- Reason for choosing it: Zero CORS overhead, single unified deployment, same multi-stage Dockerfile works locally and in production with WhiteNoise serving static React assets with client-side SPA routing fallback.
- Consequences accepted: Production container runs both static file serving and Django API.
- Decision date: 2026-10-25
- Related task IDs: P1-T05, P1-T06, P8-T01, P8-T02

**Implementation impact.** A: multi-stage `Dockerfile` (SPA build → Django image), WhiteNoise, SPA fallback in `core/spa.py`, `heroku.yml`; `VITE_API_BASE_URL` empty (same origin). B: add `django-cors-headers` and an exact-origin allow-list in config, `vercel.json` in `frontend/`, API base URL env var set. C: Django adapted to Vercel's Python runtime, external Postgres, no `heroku.yml`.

---

### D05 — "Decision time": which forecast is the "latest available"?

**Context.** The brief says purchases are decided **one day before delivery** but does **not** give a time of day. For each delivery half-hour there may be dozens of forecasts (different `publishTime`). "Latest forecast available when they need to decide" therefore needs a cutoff (assumption A1/A2). This choice changes every number in the app, so it is a product decision, not a technical detail. P0-T03 supplies domain evidence.

| | **A. One configured cutoff** (e.g. `09:00` on D-1, in config; not user-facing) | **B. Cutoff selectable in the UI**, default from config, applied as "D-1 at HH:MM" | **C. Fixed lead-time rule**: latest forecast published at least N hours before each half-hour |
|---|---|---|---|
| Advantages | Simplest API and UI | Lets the client match their real gate; strong demo ("what if we decide earlier?") | Uniform lead time per point; clean for accuracy-vs-lead-time |
| Disadvantages | Hides a key assumption; wrong if client's time differs | Slightly more API/UI/test work | Doesn't match how a buyer sees a whole day at one moment; same-day points have different information ages |
| Ops complexity | Low | Low | Low |
| Dev / maintenance cost | Lowest | Low–medium | Medium |
| Testing | Fewer cases | Boundary cases around the cutoff (≤ inclusive) | Different boundary logic |
| Security / reliability | n/a (validate range) | Validate time format and range | n/a |
| Fit | Medium | **High** | Medium (good as a *secondary* analysis; that role is already covered by P4-T05) |

**Recommendation:** **B**, with the default value taken from P0-T03's sourced research, and the horizon analysis (P4-T05) covering what C offers.

**Decision record**
- Selected option: **B (Cutoff selectable in UI, default 11:00 D-1)**
- Default cutoff time (if A/B), with source: **11:00 GMT**, sourced from EPEX SPOT GB Day-Ahead Auction and Nord Pool N2EX Day-Ahead Auction gate closure rules.
- Reason for choosing it: Empowers power buyers to evaluate forecast accuracy at exact auction gate closures (11:00) while also testing morning pre-bidding snapshots (e.g. 09:00) or afternoon re-optimizations.
- Consequences accepted: API and UI need to accept and validate cutoff times; backend tests cover boundary conditions (<= inclusive).
- Decision date: 2026-10-25
- Related task IDs: P0-T03, P4-T01, P4-T02, P4-T03, P5-T01, P5-T02, P6-T03

**Implementation impact.** `wind/selectors.py` takes `(delivery_date, cutoff)`; `wind/schemas.py` has a `cutoff` param (B) or none (A); `GET /meta` returns the default; `DecisionControls.tsx` exists only for B; `config/env.py` holds `DEFAULT_CUTOFF_TIME`. For C the selector filters on `start_time - publish_time >= N h` and `cutoff` is replaced by `lead_hours`.

---

### D06 — Meaning and size of the "January 2026" window

**Context.** "Data relevant only for purchase decisions to be made in January 2026." Decisions are made a day ahead, so this can mean delivery days **2 Jan – 1 Feb** (decisions made on 1–31 Jan) or delivery days **1–31 Jan**. January is GMT, so no clock-change complications in either case (A7).

| | **A. Decision dates 1–31 Jan → delivery days 2 Jan–1 Feb** | **B. Delivery days 1–31 Jan** (decisions 31 Dec–30 Jan) | **C. Ingest a superset (≈30 Dec–3 Feb), default window = A, configurable** |
|---|---|---|---|
| Advantages | Literal reading of the brief | Easy to explain ("all of January") | Either reading can be shown without reloading; low risk |
| Disadvantages | Slightly unusual window | Includes a decision made in December | Slightly more data; UI must say which window is the default |
| Ops complexity | Low | Low | Low |
| Dev / maintenance cost | Low | Low | Low (window is config) |
| Testing | Boundary days tested | Boundary days tested | Tests for both boundaries |
| Security / reliability | Clamp API params to window | Same | Clamp to ingested superset |
| Fit | High | Medium | **High** |

**Recommendation:** **C** (default shown = A). It also removes the need to answer Q2 before coding.

**Decision record**
- Selected option: **C (Ingest superset 2025-12-30 to 2026-02-03, default UI delivery window 2026-01-02 to 2026-02-01)**
- Reason for choosing it: Gracefully satisfies both interpretations of "decisions made in January 2026" without data reloading; covers the day-ahead decisions made between 1 Jan and 31 Jan (delivering 2 Jan to 1 Feb) as primary default, while allowing exploration across full calendar January.
- Consequences accepted: Ingests ~35 days of data (~22k rows total, well within PostgreSQL and memory limits).
- Decision date: 2026-10-25
- Related task IDs: P3-T01, P3-T03, P3-T05, P5-T01, P6-T03

**Implementation impact.** `config/env.py` gets `DATA_WINDOW_START/END` (ingest superset) and `DEFAULT_WINDOW_START/END` (UI/API default); `ingest_wind` reads them; `GET /meta` reports both; date pickers in `DecisionControls.tsx` are bounded by `/meta`.

---

## 3. Non-blocking decisions (provisional defaults — change any time)

### D03 — Data acquisition trigger — *provisional default: A*

**Context.** The window is historical (A5). **Options:** **A.** `ingest_wind` management command run on demand / once in production (simple, reproducible). **B.** Scheduled periodic refresh (Heroku Scheduler/cron). **C.** Call Elexon live per user request.
**Trade-offs:** A — simplest, deterministic demo, no runtime dependency on Elexon; stale by design. B — adds scheduler, retry/alerting and failure handling, not needed for a closed window. C — every page load depends on Elexon's uptime/latency/rate limits; hard to test and slow.
**Recommendation:** A now; B `LATER` if the client wants rolling data. **Decision record:** Selected option: ____ · Reason: ____ · Consequences: ____ · Date: ____ · Tasks: P3-T03, P3-T05, P8-T03.
**Impact:** A — `ingestion.py`, `ingest_wind.py`, one-off dyno run. B — adds scheduler config and monitoring. C — no models/ingestion; `client.py` called from the API with timeouts and fallbacks.

### D07 — Configuration library — *provisional default: A*

**Context.** Your boilerplate's pattern (inferred from its dependencies; I could not read the `backend/` source): `.env` loaded → environment variables override → one typed config object → fail on invalid config at startup. **Options:** **A.** `pydantic-settings` (typed class, validation, secret types). **B.** `django-environ` (Django-idiomatic `env()` calls). **C.** `python-decouple` + hand-written validation.
**Trade-offs:** A — closest to typed-struct-plus-validation, pairs with Ninja/Pydantic; adds a dependency. B — very common in Django, but typing/validation is weaker. C — minimal, but you write the validation yourself.
**Recommendation:** A. **Decision record:** Selected option: ____ · Reason: ____ · Consequences: ____ · Date: ____ · Tasks: P1-T03, P2-T01.
**Impact:** A — `config/env.py` defines `Settings(BaseSettings)`; `settings.py` reads only from it. B — `env = environ.Env(...)` calls in `settings.py`; `env.py` disappears. C — `env.py` wraps `decouple.config` + validators.

### D08 — Where metrics are computed — *provisional default: B*

**Context.** As-of path ≈ 1.5 k pairs; horizon path may be ~10⁵–10⁶ pairs (U6). **Options:** **A.** SQL aggregates (`AVG`, `percentile_cont`). **B.** Python with NumPy (no pandas), SQL only selects/joins. **C.** Hybrid (SQL for horizon, Python for as-of).
**Trade-offs:** A — fast on big data, but metric logic lives in SQL strings and is harder to unit-test; B — one implementation, pure-function tests, memory-bounded if rows are fetched as arrays; may be slow if row count is very large; C — two implementations can diverge.
**Recommendation:** B, revisit after P0-T02/P3-T05 row counts (switch the horizon path to A only if too slow). **Decision record:** Selected option: ____ · Reason: ____ · Consequences: ____ · Date: ____ · Tasks: P4-T02, P4-T03, P4-T05, P7-T03.
**Impact:** B — `metrics.py` (NumPy), `accuracy.py` fetches arrays via `values_list`. A — raw SQL/ORM aggregates in `accuracy.py`; `metrics.py` shrinks to percentile-free helpers. C — both.

### D09 — Frontend stack and chart library — *provisional default: A*

**Context.** Two views, time-series charts of ~48–1,500 points, bar-style charts of metrics. **Fixed regardless:** Vite, TypeScript strict, React Query for server state, React Router, `zod` for config. **Chart options:** **A.** Recharts. **B.** Apache ECharts. **C.** Plotly.js.
**Trade-offs:** A — simple React API, small; interactions (zoom/brush) more manual; B — strong zoom/tooltips/large series, imperative-style config; C — rich but very large bundle.
**Recommendation:** A. **Decision record:** Selected option: ____ · Reason: ____ · Consequences: ____ · Date: ____ · Tasks: P1-T04, P6-T03, P6-T04.
**Impact:** chart components in `features/*/` only; swapping libraries touches `ForecastChart.tsx`, `HorizonChart.tsx`, `DailyErrorChart.tsx` and `package.json`.

### D10 — Accuracy metrics to expose — *provisional default: B*

**Context.** Convention A4: `error = forecast − actual`. No capacity data is allowed (A9), and wind actuals can be near zero, so MAPE is unsafe. **Options:** **A.** Count, bias, MAE, RMSE, P50/P90/P95 of |error|. **B.** A + WAPE (Σ|e| / Σactual) + over- vs under-forecast split. **C.** B + full error quantile curve/histogram.
**Trade-offs:** A — compact; B — adds scale-free % and the direction that matters for buyers, modest extra UI; C — richest, most UI work.
**Recommendation:** B. **Decision record:** Selected option: ____ · Reason: ____ · Consequences: ____ · Date: ____ · Tasks: P4-T02..T05, P5-T03, P6-T04.
**Impact:** fields in `schemas.py`, functions in `metrics.py`, cards in `MetricCards.tsx`; C adds a histogram component and endpoint payload.

### D11 — Authentication — *DEFERRED, default: A (none)*

**Context.** The brief mentions no users or login; the data is public Elexon data; reviewers must open the URL easily. **Options:** **A.** None (public, read-only). **B.** Shared HTTP basic auth. **C.** Full user accounts.
**Trade-offs:** A — zero friction, minimal attack surface (read-only endpoints, throttled); B — protects the demo but adds friction for reviewers and a secret to manage; C — large scope, not requested.
**Recommendation:** A, with throttling and strict input bounds (PROJECT_STANDARDS §C). **Decision record:** Selected option: ____ · Reason: ____ · Consequences: ____ · Date: ____ · Tasks: P2-T01, P7-T02.
**Impact:** A — none. B — middleware + config secret. C — user model, sessions/tokens, permissions, frontend login (not planned).

### D12 — Caching — *DEFERRED, default: A (none)*

**Context.** Data is immutable once loaded and the dataset is small. **Options:** **A.** None. **B.** HTTP `Cache-Control`/ETag on historical endpoints. **C.** Redis.
**Recommendation:** A, then B only if P7-T03 shows a measured need; C is not justified for one month of data. **Decision record:** Selected option: ____ · Reason: ____ · Consequences: ____ · Date: ____ · Tasks: P5-T02, P5-T03, P7-T03.
**Impact:** B — header set in `api.py` / middleware; C — new service, config, failure handling.

### D13 — Testing strategy and mock boundary — *provisional default: A*

**Context.** Logic-heavy parts: as-of selection, metrics, ingestion; external dependency: Elexon HTTP. **Options:** **A.** pytest + pytest-django on real Postgres; mock **only** Elexon HTTP (e.g. with `respx`); Vitest + Testing Library with a mocked API on the frontend. **B.** SQLite in tests. **C.** Mock repositories/ORM.
**Trade-offs:** A — tests exercise real SQL (`DISTINCT ON`, constraints), needs a Postgres service in CI; B — faster setup but diverges from production behaviour; C — fast but proves little about the queries that matter.
**Recommendation:** A. **Decision record:** Selected option: ____ · Reason: ____ · Consequences: ____ · Date: ____ · Tasks: P1-T07, P3-T02, P5-T04, P6-T05.
**Impact:** `conftest.py`, CI Postgres service, `respx` dev dependency, fixture JSON files.

---

## 4. Provisional defaults that are not real decisions

Fixed unless you object: Python/Django current LTS (pin versions in P1-T02), `gunicorn` + WhiteNoise, `uv` or pip for dependency install, `ruff` for lint/format, `Makefile` for dev commands, stdlib JSON logging (no logging framework), custom bounded-retry helper (no retry library), UTC storage with `Europe/London` display, times in API as ISO-8601 UTC.

## 5. How your choices change the other files

| Choice | Files updated |
|---|---|
| D01=B or C | FOLDER_STRUCTURE (`api.py`/`schemas.py` → `views.py`/`serializers.py`), TASKS P5-*, PROJECT_STANDARDS §B/§C |
| D02=B or C | FOLDER_STRUCTURE (models/migrations/compose), TASKS Phase 3, STANDARDS §F |
| D04=B or C | FOLDER_STRUCTURE (`vercel.json`, CORS config), TASKS P8-*, STANDARDS §N |
| D05=A or C | TASKS P4-T01, P5-T02, P6-T03; FOLDER_STRUCTURE (`DecisionControls.tsx` removed/changed) |
| D06 | TASKS P3-T03/P3-T05; `.env.example` keys |
