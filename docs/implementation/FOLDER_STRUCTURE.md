# FOLDER_STRUCTURE.md — Wind Forecast Monitor

> Place in `docs/implementation/`. **PROVISIONAL** where marked: it assumes my recommended options (D01=A Ninja, D02=A Postgres, D04=A single container, D05=B selectable cutoff). Files affected by an unmade decision carry a ⚠ tag naming it.
> Trivial package markers (`__init__.py`) are omitted from the tree and tables; they must stay empty.

---

## A. Proposed directory tree

```
<anonymous-repo-name>/
├── README.md                                   # P8-T04
├── Makefile                                    # P1-T07
├── Dockerfile                                  # P1-T06 (dev stage), P8-T01 (prod stages)
├── docker-compose.yml                          # P1-T06
├── heroku.yml                                  # P8-T02   ⚠ D04
├── .env.example                                # P1-T03
├── .gitignore                                  # P1-T01
├── .dockerignore                               # P1-T06
├── .github/
│   └── workflows/
│       └── ci.yml                              # P1-T07
├── docs/
│   └── implementation/
│       ├── TASKS.md
│       ├── DESIGN_DECISIONS.md
│       ├── FOLDER_STRUCTURE.md
│       └── PROJECT_STANDARDS.md
├── backend/
│   ├── manage.py                               # P1-T02
│   ├── pyproject.toml                          # P1-T02
│   ├── config/                                 # Django project package
│   │   ├── env.py                              # P1-T03  typed config (boilerplate pattern)
│   │   ├── settings.py                         # P2-T01
│   │   ├── urls.py                             # P2-T01 (+P2-T04, P5-T01, P8-T01)
│   │   └── wsgi.py                             # P2-T01
│   ├── core/                                   # cross-cutting, knows nothing about wind
│   │   ├── errors.py                           # P2-T03
│   │   ├── error_handlers.py                   # P2-T03  ⚠ D01
│   │   ├── logging.py                          # P2-T02
│   │   ├── middleware.py                       # P2-T02
│   │   ├── health.py                           # P2-T04
│   │   └── spa.py                              # P8-T01  ⚠ D04
│   ├── wind/                                   # the single domain module
│   │   ├── models.py                           # P3-T01  ⚠ D02
│   │   ├── migrations/
│   │   │   └── 0001_initial.py                 # P3-T01  ⚠ D02
│   │   ├── elexon/
│   │   │   └── client.py                       # P3-T02
│   │   ├── ingestion.py                        # P3-T03
│   │   ├── management/
│   │   │   └── commands/
│   │   │       ├── ingest_wind.py              # P3-T03
│   │   │       └── data_quality.py             # P3-T04
│   │   ├── selectors.py                        # P4-T01  ⚠ D05
│   │   ├── metrics.py                          # P4-T02  ⚠ D08, D10
│   │   ├── accuracy.py                         # P4-T03, P4-T04, P4-T05
│   │   ├── schemas.py                          # P5-T01  ⚠ D01
│   │   └── api.py                              # P5-T01..T03  ⚠ D01
│   └── tests/
│       ├── conftest.py                         # P1-T02 (minimal), P5-T04
│       ├── factories.py                        # P3-T03, P5-T04
│       ├── test_config.py                      # P1-T03
│       ├── test_logging.py                     # P2-T02
│       ├── test_errors.py                      # P2-T03
│       ├── test_elexon_client.py               # P3-T02
│       ├── test_ingestion.py                   # P3-T01, P3-T03
│       ├── test_selectors.py                   # P4-T01
│       ├── test_metrics.py                     # P4-T02
│       ├── test_accuracy.py                    # P4-T03..T05
│       ├── test_api.py                         # P2-T04, P5-T04
│       └── fixtures/
│           ├── elexon_windfor_sample.json      # P3-T02
│           └── elexon_fuelhh_sample.json       # P3-T02
└── frontend/
    ├── package.json                            # P1-T04
    ├── tsconfig.json                           # P1-T04
    ├── vite.config.ts                          # P1-T04 (dev proxy, Vitest config)
    ├── eslint.config.js                        # P1-T04
    ├── .prettierrc.json                        # P1-T04
    ├── index.html                              # P1-T04
    ├── .env.example                            # P1-T05
    └── src/
        ├── main.tsx                            # P1-T04
        ├── App.tsx                             # P1-T04, P6-T02
        ├── config.ts                           # P1-T05
        ├── config.test.ts                      # P1-T05
        ├── api/
        │   ├── client.ts                       # P6-T01
        │   ├── client.test.ts                  # P6-T01
        │   ├── types.ts                        # P6-T01
        │   └── hooks.ts                        # P6-T01
        ├── components/
        │   ├── Layout.tsx                      # P6-T02
        │   ├── Layout.test.tsx                 # P6-T02
        │   └── QueryState.tsx                  # P6-T02
        ├── features/
        │   ├── forecast/
        │   │   ├── ForecastPage.tsx            # P6-T03
        │   │   ├── ForecastPage.test.tsx       # P6-T05
        │   │   ├── DecisionControls.tsx        # P6-T03  ⚠ D05
        │   │   └── ForecastChart.tsx           # P6-T03  ⚠ D09
        │   └── accuracy/
        │       ├── AccuracyPage.tsx            # P6-T04
        │       ├── AccuracyPage.test.tsx       # P6-T05
        │       ├── MetricCards.tsx             # P6-T04  ⚠ D10
        │       ├── HorizonChart.tsx            # P6-T04  ⚠ D09
        │       └── DailyErrorChart.tsx         # P6-T04  ⚠ D09
        ├── lib/
        │   ├── format.ts                       # P6-T03
        │   └── format.test.ts                  # P6-T05
        └── test/
            └── setup.ts                        # P1-T04, P6-T05
```

Why one Django domain app (`wind`) and one cross-cutting app (`core`): the product has a single bounded context (wind forecast vs. actual). More apps would add files without adding clarity. If a second energy source is ever added, split `wind` then.

---

## B. Every file explained

Columns: **Responsibility / why** · **Belongs** · **Must NOT contain** · **Depends on** · **Used by** · **Tasks**.

### B1. Repository root

| Path | Responsibility / why | Belongs | Must NOT contain | Depends on | Used by | Tasks |
|---|---|---|---|---|---|---|
| `README.md` | Required deliverable and knowledge-transfer entry point | Directory guide, start instructions (Docker and local), live URL, AI-tools disclosure, data attribution, metric definitions, assumptions | Secrets, personal identifiers, stale commands | everything it documents | Reviewers, you | P8-T04 |
| `Makefile` | Reproducible dev commands | `up`, `down`, `test`, `lint`, `fmt`, `ingest`, `typecheck` wrappers | Business logic, long scripts | Docker, npm, pytest | You, CI | P1-T07 |
| `Dockerfile` | One multi-stage build: `dev`, `frontend-build`, `prod` | Build steps, non-root user, gunicorn entrypoint | Secrets, `.env`, dev tooling in `prod` | `backend/pyproject.toml`, `frontend/package.json` | Compose, Heroku | P1-T06, P8-T01 |
| `docker-compose.yml` | Local stack: `db`, `backend`, `frontend` | Services, healthchecks, volumes, env wiring | Real credentials | `Dockerfile`, `.env` | You, CI | P1-T06 |
| `heroku.yml` ⚠D04 | Tells Heroku to build the container and run migrations on release | `build`, `release`, `run` blocks | App config values | `Dockerfile` | Heroku | P8-T02 |
| `.env.example` | Documents every backend setting with safe placeholders | Variable names, comments, dummy values | Real secrets | `backend/config/env.py` (must stay in sync) | You, README | P1-T03 (extended P2-T01, P3-T02, D06 window keys) |
| `.gitignore` | Keep secrets and build output out of git | `.env`, `node_modules`, `dist`, `__pycache__`, `*.sqlite3` | Anything that should be tracked | — | git | P1-T01 |
| `.dockerignore` | Smaller, safer build context | `.git`, `.env`, `node_modules`, tests output | — | — | Docker | P1-T06 |
| `.github/workflows/ci.yml` | Automated lint + tests | Backend job (Postgres service), frontend job | Deploy steps with secrets, long logic | `Makefile`/commands | GitHub | P1-T07 |
| `docs/implementation/*.md` | The four planning files | Plans, decisions, standards | Application code | — | You | P1-T01 |

### B2. Backend — `config/`

| Path | Responsibility / why | Belongs | Must NOT contain | Depends on | Used by | Tasks |
|---|---|---|---|---|---|---|
| `backend/manage.py` | Django CLI entry point | Standard Django stub | Custom logic | `config.settings` | You, Docker, Heroku | P1-T02 |
| `backend/pyproject.toml` | Dependencies and tool config | Pinned deps, `ruff`, `pytest`, `mypy` sections | Secrets | — | Docker, CI | P1-T02 (+deps in P1-T03, P3-T02) |
| `backend/config/env.py` | **The single typed configuration object** (boilerplate pattern: defaults < `.env` < environment; validated at startup; secrets redacted). ⚠D07 | `Settings` class: `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS`, `DATABASE_URL`, `ELEXON_BASE_URL`, timeouts/retries, `DATA_WINDOW_*`, `DEFAULT_*`, `DEFAULT_CUTOFF_TIME`, `LOG_LEVEL`, `DJANGO_ENV` | Django imports, business logic, any other `os.environ` reads | `pydantic-settings` | `settings.py`, tests | P1-T03 |
| `backend/config/settings.py` | Django settings assembled **only** from `env.Settings` | Installed apps, middleware order, DB, static, security flags, logging hookup | Hardcoded secrets/hosts, `os.environ` | `env.py`, `core.logging` | Django | P2-T01 |
| `backend/config/urls.py` | **Wiring point** for routes | Mount API router, health routes, SPA fallback (last) | Business logic | `wind.api`, `core.health`, `core.spa` | Django | P2-T01, P2-T04, P5-T01, P8-T01 |
| `backend/config/wsgi.py` | WSGI entry for gunicorn | Standard stub | Anything else | `settings.py` | gunicorn | P2-T01 |

### B3. Backend — `core/` (cross-cutting; must not import from `wind`)

| Path | Responsibility / why | Belongs | Must NOT contain | Depends on | Used by | Tasks |
|---|---|---|---|---|---|---|
| `backend/core/errors.py` | Small error taxonomy shared by all layers | `ValidationFailed`, `NotFound`, `UpstreamUnavailable`, base `AppError` with a stable `code` | HTTP/JSON concerns | stdlib | `wind.*`, `error_handlers.py` | P2-T03 |
| `backend/core/error_handlers.py` ⚠D01 | Maps errors → one JSON shape and status; logs unexpected errors once | Handlers for `AppError`, validation errors, catch-all 500 | Domain decisions, stack traces in responses | `errors.py`, `logging.py` | API framework | P2-T03 |
| `backend/core/logging.py` | Logging config: JSON in prod, readable in dev; redaction filter | `LOGGING` dict, formatter, filter that masks secret-like fields | Request handling | `config.env` | `settings.py` | P2-T02 |
| `backend/core/middleware.py` | Request-ID middleware + access log line | Generate/propagate `X-Request-ID`, put it in log context | Auth, business logic | `logging.py` | `settings.py` | P2-T02 |
| `backend/core/health.py` | `/health` (liveness) and `/ready` (DB check) | Two tiny views | Anything that reveals config or DB details | Django DB | `config/urls.py`, Docker/Heroku checks | P2-T04 |
| `backend/core/spa.py` ⚠D04 | Serves the built React `index.html` for non-API routes | One view returning the built file | API logic | Built frontend files | `config/urls.py` | P8-T01 |

### B4. Backend — `wind/` (domain)

| Path | Responsibility / why | Belongs | Must NOT contain | Depends on | Used by | Tasks |
|---|---|---|---|---|---|---|
| `backend/wind/models.py` ⚠D02 | Persistence schema | `WindActual`, `WindForecast`, constraints, indexes | Query logic beyond simple managers, metrics | Django ORM | `selectors.py`, `ingestion.py`, `accuracy.py` | P3-T01 |
| `backend/wind/migrations/0001_initial.py` ⚠D02 | Versioned schema | Auto-generated migration (reviewed) | Hand-edits unrelated to schema | `models.py` | `migrate` | P3-T01 |
| `backend/wind/elexon/client.py` | The **only** code that talks to Elexon | HTTP calls, window chunking, bounded retry/backoff, parsing to dataclasses, upstream-error mapping | DB access, Django models | `httpx`, `core.errors`, `config.env` | `ingestion.py` | P3-T02 |
| `backend/wind/ingestion.py` | Orchestrates fetch → validate → bulk upsert, idempotent | Chunk loop, transactions, counts | HTTP details, CLI parsing | `elexon.client`, `models.py` | `ingest_wind.py`, tests | P3-T03 |
| `backend/wind/management/commands/ingest_wind.py` | CLI entry for ingestion | Argument parsing, printing counts, exit codes | Fetch/upsert logic | `ingestion.py`, `config.env` | You, `make ingest`, one-off Heroku dyno | P3-T03 |
| `backend/wind/management/commands/data_quality.py` | Data-coverage report | Gaps, duplicates, negatives, per-day counts | Mutations | `models.py` | You | P3-T04 |
| `backend/wind/selectors.py` ⚠D05 | **R1 query:** latest forecast ≤ cutoff per half-hour | One or two read-only query functions returning plain data | Metrics, HTTP, schema classes | `models.py` | `accuracy.py`, `api.py` | P4-T01 |
| `backend/wind/metrics.py` ⚠D08/D10 | **Pure** metric functions (bias, MAE, RMSE, percentiles, WAPE, split) | Functions on arrays/lists | Django/ORM/IO imports | NumPy | `accuracy.py`, tests | P4-T02 |
| `backend/wind/accuracy.py` | Use-case layer: pair forecast with actual, compute per-window, per-day, per-horizon metrics, risk band | Service functions combining selectors + metrics | HTTP/serialization, SQL string building scattered around | `selectors.py`, `metrics.py`, `models.py` | `api.py` | P4-T03, P4-T04, P4-T05 |
| `backend/wind/schemas.py` ⚠D01 | API request/response contract | Typed param and response classes, validation rules | ORM calls, business rules | framework | `api.py`, OpenAPI | P5-T01 |
| `backend/wind/api.py` ⚠D01 | HTTP endpoints, thin | Route functions: validate → call `selectors`/`accuracy` → return schema | Business logic, SQL | `schemas.py`, `accuracy.py`, `selectors.py`, `core.errors` | `config/urls.py` | P5-T01, P5-T02, P5-T03 |

### B5. Backend — `tests/`

| Path | Responsibility / why | Belongs | Must NOT contain | Depends on | Used by | Tasks |
|---|---|---|---|---|---|---|
| `tests/conftest.py` | Shared fixtures (DB, API client) | Fixtures only | Test cases | pytest-django | all tests | P1-T02, P5-T04 |
| `tests/factories.py` | Build `WindActual`/`WindForecast` rows tersely | Helper builders | Assertions | `models.py` | tests | P3-T03, P5-T04 |
| `tests/test_config.py` | Config precedence, fail-fast, redaction | Table-driven env cases | Network | `config.env` | CI | P1-T03 |
| `tests/test_logging.py` | Request ID present, secrets redacted | Log capture tests | — | `core.logging`, `core.middleware` | CI | P2-T02 |
| `tests/test_errors.py` | Error → status/shape mapping, no leakage | Handler tests | — | `core.error_handlers` | CI | P2-T03 |
| `tests/test_elexon_client.py` | Client behaviour with mocked HTTP | Success, chunking, retries, bad payloads | Real network calls | `wind.elexon.client`, fixtures | CI | P3-T02 |
| `tests/test_ingestion.py` | Idempotency, constraints, rollback | DB tests | Real network calls | `ingestion.py`, `models.py` | CI | P3-T01, P3-T03 |
| `tests/test_selectors.py` | Boundary tests for "latest ≤ cutoff" | Inclusive boundary, no-forecast cases | — | `selectors.py` | CI | P4-T01 |
| `tests/test_metrics.py` | Hand-calculated metric cases | Table-driven numerics | DB | `metrics.py` | CI | P4-T02 |
| `tests/test_accuracy.py` | End-to-end accuracy service on seeded data | Pairing, missing counts, band, horizon buckets | — | `accuracy.py` | CI | P4-T03, P4-T04, P4-T05 |
| `tests/test_api.py` | Endpoint contract, validation, health | Success + failure per endpoint | — | whole backend | CI | P2-T04, P5-T04 |
| `tests/fixtures/elexon_windfor_sample.json` | Recorded sample payload (shape confirmed in P0-T02) | Small real excerpt | Large dumps, secrets | — | client tests | P3-T02 |
| `tests/fixtures/elexon_fuelhh_sample.json` | Same for actuals (WIND rows) | Small real excerpt | — | — | client tests | P3-T02 |

### B6. Frontend

| Path | Responsibility / why | Belongs | Must NOT contain | Depends on | Used by | Tasks |
|---|---|---|---|---|---|---|
| `frontend/package.json` | Dependencies and scripts (`dev`, `build`, `lint`, `typecheck`, `test`) | Scripts, pinned deps | Secrets | — | CI, Docker | P1-T04 |
| `frontend/tsconfig.json` | Strict TypeScript | `strict: true` | Loosening flags without reason | — | tools | P1-T04 |
| `frontend/vite.config.ts` | Build, dev proxy to backend, Vitest config | Proxy `/api` → backend | Env secrets | — | dev server | P1-T04 |
| `frontend/eslint.config.js` | Lint rules | React/TS rules | — | — | CI | P1-T04 |
| `frontend/.prettierrc.json` | Formatting | Style options | — | — | editor/CI | P1-T04 |
| `frontend/index.html` | HTML shell | Root div, title | Inline secrets | — | Vite | P1-T04 |
| `frontend/.env.example` | Documents `VITE_API_BASE_URL` | Placeholder values | Real URLs with credentials | `src/config.ts` | You | P1-T05 |
| `src/main.tsx` | Mount React, providers (Query client, router) | Bootstrapping | Feature code | `App.tsx` | Vite | P1-T04 |
| `src/App.tsx` | Route table | Two routes inside `Layout` | Data fetching | `Layout`, feature pages | `main.tsx` | P1-T04, P6-T02 |
| `src/config.ts` | Typed, validated env access (mirrors backend config pattern) | `zod` schema over `import.meta.env` | Reads of `import.meta.env` elsewhere | `zod` | `api/client.ts` | P1-T05 |
| `src/config.test.ts` | Config validation tests | Valid/empty/invalid | — | `config.ts` | CI | P1-T05 |
| `src/api/client.ts` | `fetch` wrapper, error mapping | Base URL, timeouts, typed errors | UI code | `config.ts`, `types.ts` | `hooks.ts` | P6-T01 |
| `src/api/client.test.ts` | Error-mapping tests | Network/4xx/5xx cases | — | `client.ts` | CI | P6-T01 |
| `src/api/types.ts` | Response types matching the OpenAPI contract | Type definitions | Logic | — | `client.ts`, features | P6-T01 |
| `src/api/hooks.ts` | React Query hooks per endpoint | `useForecast`, `useAccuracySummary`, `useHorizonAccuracy`, `useMeta` | Rendering | `client.ts` | features | P6-T01 |
| `src/components/Layout.tsx` | Header, nav, attribution footer | Page chrome | Data fetching | router | `App.tsx` | P6-T02 |
| `src/components/Layout.test.tsx` | Attribution/nav render test | — | — | `Layout.tsx` | CI | P6-T02 |
| `src/components/QueryState.tsx` | Shared loading/empty/error rendering | One small component | Feature-specific copy | — | both pages | P6-T02 |
| `src/features/forecast/ForecastPage.tsx` | Page for R1 | Compose controls + chart, own state for date/cutoff | Chart internals | `hooks.ts`, `DecisionControls`, `ForecastChart` | `App.tsx` | P6-T03 |
| `src/features/forecast/DecisionControls.tsx` ⚠D05 | Delivery-date and cutoff inputs | Bounded inputs from `/meta` | Fetching | `types.ts` | `ForecastPage` | P6-T03 |
| `src/features/forecast/ForecastChart.tsx` ⚠D09 | Forecast vs actual line chart | Chart config, gaps shown as gaps | Fetching | chart lib, `format.ts` | `ForecastPage` | P6-T03 |
| `src/features/forecast/ForecastPage.test.tsx` | Page tests with mocked API | Success/empty/error | — | page | CI | P6-T05 |
| `src/features/accuracy/AccuracyPage.tsx` | Page for R2 | Date range + cutoff state, compose cards/charts | Chart internals | `hooks.ts` | `App.tsx` | P6-T04 |
| `src/features/accuracy/MetricCards.tsx` ⚠D10 | KPI cards with definitions | Labels, units, sample size | Fetching | `types.ts`, `format.ts` | `AccuracyPage` | P6-T04 |
| `src/features/accuracy/HorizonChart.tsx` ⚠D09 | Error by lead-time bucket | Chart config | Fetching | chart lib | `AccuracyPage` | P6-T04 |
| `src/features/accuracy/DailyErrorChart.tsx` ⚠D09 | Error per delivery day | Chart config | Fetching | chart lib | `AccuracyPage` | P6-T04 |
| `src/features/accuracy/AccuracyPage.test.tsx` | Page tests with mocked API | Success/error | — | page | CI | P6-T05 |
| `src/lib/format.ts` | Number/date/unit formatting (UTC → Europe/London) | Pure helpers | Components | — | features | P6-T03 |
| `src/lib/format.test.ts` | Table-driven formatting tests | — | — | `format.ts` | CI | P6-T05 |
| `src/test/setup.ts` | Vitest/Testing Library setup | Matchers, API mock setup | Test cases | — | Vitest | P1-T04, P6-T05 |

---

## C. Dependency direction

```
config/env.py ──► config/settings.py ──► (Django)
                         │
core/*  (errors, logging, middleware, health, spa)   ← no imports from wind

config/urls.py  (wiring)
   ├──► core.health, core.spa
   └──► wind.api ──► wind.schemas
                └──► wind.accuracy ──► wind.selectors ──► wind.models
                │                └──► wind.metrics   (pure)
                └──► wind.selectors

wind.management.commands.* ──► wind.ingestion ──► wind.elexon.client
                                          └────► wind.models
```

Rules:
1. **Business logic** lives in `wind/selectors.py`, `wind/metrics.py` and `wind/accuracy.py`. `api.py` is a thin adapter.
2. **`metrics.py` is pure** (no Django, no I/O). It is the most-tested file.
3. **`core` never imports `wind`.** `wind` may import `core.errors`.
4. **Interfaces:** Python's duck typing makes extra interface classes unnecessary here. The one external boundary (Elexon) is isolated in `client.py`; tests mock HTTP, not the client. No repository layer: only two models and two query modules, so the ORM is called directly in `selectors.py`/`ingestion.py`/`accuracy.py`. Add a repository abstraction only if a second storage backend is ever required.
5. **Wiring** happens in `config/urls.py` (routes) and `config/settings.py` (middleware, logging). No dependency-injection framework.
6. **Avoiding circular imports:** dependencies only flow downward in the diagram; if you need to import "upward", move the shared piece to `core/` or a lower module.
7. **Transport vs domain:** query functions return plain data (tuples/dataclasses), not request/response schema objects, so DB and HTTP concerns don't leak into each other.
8. **Frontend:** `features/*` import from `api/`, `components/`, `lib/`; `api/` imports only `config.ts` and types; `lib/` imports nothing from the app.

---

## D. Mapping from the existing boilerplate (configuration pattern only)

**What I could and could not inspect.** Readable: repo root listing (`backend/`, `.gitignore`, `README.md` — empty, `bun.lock`, `go.mod`, `package.json`, `turbo.json`), `go.mod` and `turbo.json`. **Blocked:** the `backend/` folder contents (GitHub refused automated access), so I have **not** seen the actual config structs or loader. The mapping below is inferred from dependencies and is provisional. If you paste your `backend` config files (or `tree backend`), I will align names and precedence exactly.

| Boilerplate evidence | Pattern carried over | Python/Django equivalent here |
|---|---|---|
| `github.com/joho/godotenv` | Load a `.env` file for local development | `pydantic-settings` `env_file` (D07-A) |
| `github.com/knadh/koanf/v2` + env provider | Layered config: defaults < file < environment variables | `Settings` defaults < `.env` < real env vars |
| Typed struct (koanf unmarshal) + `go-playground/validator` (indirect dep) | One typed object, validated | `Settings(BaseSettings)` with field validators |
| (inferred) fail-fast on bad config | App refuses to start | Settings instantiated at import in `config/env.py` |
| `zerolog` | **Not carried** (you asked for config only) | stdlib JSON logging in `core/logging.py`, designed independently |
| `turbo.json` + `bun` | **Not carried** | `Makefile` + Docker Compose |
| `go.mod`/`go.sum` | n/a | `pyproject.toml` |

- **Files to reuse:** none directly (different language) — reuse the *pattern* and the `.env.example` convention.
- **Files to add:** everything in §A.
- **Existing abstractions that may be unnecessary:** cannot be judged without reading `backend/`.
- **Migration steps:** none; this is a new repository. Do **not** fork the boilerplate repo (it carries Go files and an identifiable owner name — the submission repo must be anonymous).

---

## E. Guarding against over-engineering

- No repository/service/factory layers beyond what the table shows; `accuracy.py` is the only "service".
- No generic base classes, serializers frameworks, DI container, or event system.
- A new endpoint should touch at most: `schemas.py`, `api.py`, `accuracy.py` or `selectors.py`, `api/types.ts`, `api/hooks.ts`, a feature component, plus tests.
- Split a file only when it exceeds ~300 lines or mixes two responsibilities from the table.
- Do not create `utils.py`, `helpers.py`, or `common/` — name the module for its job.
