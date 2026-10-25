# PROJECT_STANDARDS.md — Wind Forecast Monitor

> Place in `docs/implementation/`. Classification key: `MUST_HAVE` (core app or security) · `SHOULD_HAVE` (before production / when need is established) · `LATER` (needs a concrete trigger) · `NOT_APPLICABLE` (with reason).
> Task IDs refer to `TASKS.md`; decision IDs to `DESIGN_DECISIONS.md`. Context: a small, read-only, public analytics portal over one month of public data — standards are sized accordingly.

---

## 0. Prioritisation table

| Required from the beginning | Required before production (the deployed pilot) | Implement only when justified | Explicitly out of scope |
|---|---|---|---|
| Typed, validated config; `.env.example` (P1-T03, P1-T05) | `check --deploy` clean, HTTPS-only, security headers (P2-T01, P7-T02) | Scheduled data refresh (D03-B) | User accounts / login (D11) |
| Secrets never in git/image (P1-T01, P1-T06) | Throttling on public endpoints (P7-T02) | HTTP caching headers (D12-B) | Redis / multi-level caching |
| Error taxonomy + one error format (P2-T03) | Dependency audit: `pip-audit`, `npm audit` (P7-T02) | Prometheus/Grafana metrics | Kubernetes, service mesh, microservices |
| Structured logs + request IDs (P2-T02) | Independent verification of numbers (P7-T01) | OpenTelemetry tracing | Distributed locks, event buses |
| Input validation on every endpoint (P5-T02, P5-T03) | CI green incl. image build (P1-T07, P8-T01) | Circuit breaker around Elexon | Dynamic config reload, plugin systems |
| DB constraints + migrations (P3-T01) | Non-root production image, health checks (P8-T01, P2-T04) | Rate-limit store beyond in-process | Demand / procurement modelling (A8) |
| Context-aware timeouts on outbound calls (P3-T02) | Smoke test in incognito on the deployed URL (P8-T03, P8-T07) | Idempotency keys (no write API exists) | Other renewables / other data sources |
| Metrics unit-tested with hand-calculated cases (P4-T02) | Backup/restore note (see §F) | OpenAPI-generated frontend client | Code generation, elaborate abstractions |

---

## A. Application foundation — `MUST_HAVE` (Phase 1–2)

- Modular monolith: `core` (cross-cutting) and `wind` (domain), dependency direction per FOLDER_STRUCTURE §C. Tasks: P1-T02, P2-T01.
- **No global mutable state.** The only module-level singleton is the validated `Settings` object (immutable). Tasks: P1-T03.
- **Context/timeouts:** every outbound HTTP call has an explicit timeout (P3-T02); DB statement timeout set in production settings (P2-T01); gunicorn worker timeout set (P8-T01).
- Separation: config (`config/env.py`) ≠ settings composition ≠ domain (`wind/*`) ≠ transport (`api.py`, `schemas.py`) ≠ infrastructure (`elexon/client.py`, ORM).
- Wiring is manual in `config/urls.py` and `settings.py` — no DI framework (LATER, only if wiring becomes unmanageable).

## B. Error handling — `MUST_HAVE` (P2-T03)

- **Shared design, not a global catch-all:** small error classes in `core/errors.py`; one handler module maps them to the response shape `{"error":{"code","message","request_id"}}`.
- Mapping: validation → 422/400; not found → 404; upstream/DB unavailable → 503; unexpected → 500 with a generic message. Auth codes (401/403) are `NOT_APPLICABLE` while D11 = none.
- Client messages are safe and stable; internal context (exception chain, parameters) goes to logs only. Never return stack traces, SQL, hostnames or settings.
- Wrap with context when raising (`raise UpstreamUnavailable(...) from exc`); check by type, not by message text.
- **Log once:** lower layers raise; only the boundary handler logs unexpected errors (with traceback and request ID).
- Panic/exception safety: Django's middleware stack plus the catch-all handler guarantees a JSON 500 rather than an HTML debug page (`DEBUG=False`).
- Tests: `tests/test_errors.py` asserts status, shape and absence of internals.

## C. Input validation and security — `MUST_HAVE` (P2-T01, P5-T02, P5-T03, P7-T02)

- Validate every query parameter at the API boundary via schemas: dates must lie within the ingested window (from `/meta`), cutoff must parse as `HH:MM`, ranges are bounded (no open-ended queries). Path/headers: no user-controlled paths or file uploads exist (`NOT_APPLICABLE`).
- Request size and timeouts: `DATA_UPLOAD_MAX_MEMORY_SIZE` small (API is GET-only); gunicorn timeout set; reject non-GET methods on data routes.
- DB constraints complement validation: unique `(start_time, publish_time)`, `NOT NULL`, no artificial `>= 0` check (negative values possible — K3).
- **SQL injection:** use the ORM or parameterised queries only; no f-string SQL. **IDOR / mass assignment / authorisation:** `NOT_APPLICABLE` (no per-user data, no write endpoints) — revisit if D11 changes.
- Sanitisation: not needed for storage; output encoding is handled by React's default escaping. Never use `dangerouslySetInnerHTML`.
- **Rate limiting / abuse:** `SHOULD_HAVE` — simple throttle (framework-level, in-process) on public endpoints before production; a shared store is `LATER`.
- Headers and transport: `SECURE_SSL_REDIRECT`, HSTS, `X-Content-Type-Options`, `Referrer-Policy`, `X-Frame-Options`, and a Content-Security-Policy compatible with the built SPA (`SHOULD_HAVE`). CORS: none when same origin (D04-A); exact-origin allow-list if D04-B. Never `*` with credentials.

## D. Serialization and deserialization — keep it simple (`MUST_HAVE` for the minimum)

- Use ordinary typed schema classes (D01) for **request parsing + validation** and **response shaping** at the API boundary only.
- Domain functions take/return plain values (floats, datetimes, small dataclasses) — **not** schema or ORM objects — so `metrics.py` stays pure.
- Elexon payloads are parsed once, in `elexon/client.py`, into small dataclasses; nothing downstream sees raw JSON. The ORM models are the persistence mapping; no separate persistence DTO layer.
- Times: UTC ISO-8601 with `Z` on the wire; MW as numbers (no strings). The frontend mirrors response shapes in `api/types.ts`.
- No generic serialization framework. `LATER`: generated TypeScript client from OpenAPI if the contract starts changing often.

## E. Authentication and authorization — `NOT_APPLICABLE` for v1 (D11 DEFERRED)

- The brief has no users, roles or login; data is public; reviewers must open the URL without friction. JWT is **not** warranted — it would add token signing/rotation/revocation scope with no requirement behind it.
- If this changes (client SSO, or access control for the pilot): prefer the client's identity provider (OIDC) or Django sessions over home-grown JWT; if JWT is used: pin the signing algorithm and verify it, validate `iss`/`aud`/`exp`, short-lived access tokens, refresh rotation with revocation, secrets from config only, no sensitive claims, tests for expired/malformed/revoked/wrongly-signed tokens, object-level checks. Trigger: a requirement for per-user or per-organisation data.

## F. Database and persistence — `MUST_HAVE` core; rest `SHOULD_HAVE`

- Schema and constraints: P3-T01; migrations are committed and applied via release phase (P8-T02). Never edit an applied migration.
- Transactions: ingestion upserts per chunk inside `transaction.atomic` (P3-T03); read endpoints need no explicit transactions.
- Connections: `CONN_MAX_AGE` set; production pool size sized to dyno count and Heroku Postgres limits (P2-T01).
- Query performance: index for the as-of query; `EXPLAIN ANALYZE` on the as-of and horizon queries (P7-T03). Pagination: `NOT_APPLICABLE` — responses are bounded by construction (≤ 48 points/day, ≤ window-size aggregates); enforce the date-range bound instead.
- Consistency / concurrent updates: data is append-only/upsert from one command; no concurrent-update scenarios. Make ingestion idempotent (P3-T03).
- Backup/recovery: the data is reproducible from Elexon; document "re-run `ingest_wind`" as the recovery procedure (README, P8-T04). Provider backups are `LATER`.

## G. Caching — `NOT_APPLICABLE` now (D12 DEFERRED)

Dataset is small and immutable; PostgreSQL answers within budget. Revisit only if P7-T03 shows a measured problem: first `Cache-Control`/ETag on historical endpoints, never Redis for one month of data. If ever added: key by `(endpoint, normalised params)`, long TTL (data immutable), no stampede concern at this size, and the app must work when cache is absent.

## H. Fault tolerance and external dependencies — `SHOULD_HAVE` (scoped)

- The only outbound dependency is Elexon, used **only by the ingestion command** (D03-A), so the user-facing app does not depend on Elexon being up.
- In `elexon/client.py` (P3-T02): timeouts on connect/read; **bounded** retries (e.g. 3) with exponential backoff and jitter on timeouts/429/5xx only; honour `Retry-After` if present; GET-only (safe to retry); fail with `UpstreamUnavailable` and a non-zero exit code.
- Partial failures: chunked ingestion commits per chunk and reports which chunk failed; re-running is idempotent.
- DB unavailable: `/ready` returns 503; API returns 503 through the shared handler.
- Circuit breaker, queues, background workers: `LATER` — no live dependency to protect.
- No unbounded loops/goroutine-equivalents: no background threads in v1.

## I. Configuration management — `MUST_HAVE` (P1-T03, P1-T05, P2-T01) — pattern from the boilerplate

- One typed `Settings` (D07-A) in `config/env.py`: defaults < `.env` < environment variables; validated at startup; missing/invalid values abort boot with a clear, secret-free message.
- `DJANGO_ENV` (`development` | `production`) selects defaults (e.g. `DEBUG`, log format); secrets have **no** defaults.
- Secrets typed as redacted (`SecretStr`); `repr`/logs never print them; `.env` git-ignored; `.env.example` committed with placeholders only; no production URLs or credentials in code (Elexon base URL is a setting).
- Production secrets live in Heroku config vars. Do not bake `.env` into images (`.dockerignore`).
- Frontend mirror: `src/config.ts` validates `VITE_*` values with `zod`. Remember `VITE_*` values are **public** in the bundle — never put secrets there.
- Config reload at runtime: `NOT_APPLICABLE`.

## J. Logging — `MUST_HAVE` basics (P2-T02); designed independently of the boilerplate

- stdlib `logging` with JSON lines in production, readable text in development; levels: `INFO` access/ingestion summaries, `WARNING` recoverable retries, `ERROR` unexpected failures.
- `X-Request-ID` accepted/generated per request and included in every log line and error body.
- One access-log line per request (method, path, status, duration) — no query strings containing anything sensitive (none exist, but keep the rule).
- Redaction filter masks keys like `secret`, `password`, `token`, `authorization`, `key`. Never log request bodies or full settings.
- Avoid duplicate logging (see §B) and per-row logging in ingestion (log per chunk).

## K. Observability — `SHOULD_HAVE` minimal; the rest `LATER`

- Logs (what happened): P2-T02. Health/readiness: P2-T04 (`MUST_HAVE`, used by Docker/Heroku).
- Request count/latency/error rate: **use Heroku's built-in metrics and router logs** before adding anything (`LATER`: Prometheus/Grafana).
- Tracing/OpenTelemetry: `NOT_APPLICABLE` (single process, one DB). Business metrics: not needed; the data-quality command (P3-T04) is the operational signal. Alerting: `LATER`.
- If metrics are added: no high-cardinality labels (never label by raw timestamp or request ID).

## L. Graceful shutdown and lifecycle — `SHOULD_HAVE` (P8-T01)

- gunicorn handles SIGTERM: stops accepting, finishes in-flight requests within `--graceful-timeout`; set it below Heroku's 30 s SIGTERM→SIGKILL window (e.g. 25 s) and document it.
- No background workers in v1; DB connections close with the worker. Ingestion command is a short-lived process and exits non-zero on failure.

## M. Testing and code quality — `MUST_HAVE` core (P1-T07, P4-*, P5-T04, P6-T05, P7-T01)

- **Priority order of tests:** (1) `metrics.py` table-driven with hand-computed values; (2) `selectors.py` boundary cases (≤ cutoff, no forecast, day edges); (3) ingestion idempotency and constraints; (4) API contract and error shape; (5) frontend pages with mocked API; (6) config precedence and fail-fast.
- Real PostgreSQL in tests (D13-A); mock only Elexon HTTP (`respx`). Do not mock the ORM.
- Race detector: `NOT_APPLICABLE` (no concurrency in v1).
- Static checks: `ruff check` + `ruff format --check` (`MUST_HAVE`); `mypy` on `wind/` and `core/` (`SHOULD_HAVE`); ESLint, Prettier, `tsc --noEmit` (`MUST_HAVE`).
- Reproducible commands: `make lint test`; CI runs the same (P1-T07).
- **Acceptance tests for critical requirements:** R1 → selector boundary tests + one API test returning the as-of forecast; R2 → one seeded dataset whose metrics are verified by hand and independently re-computed (P7-T01).
- End-to-end browser tests: `LATER`.

## N. API and operational standards

| Item | Class | When | Tasks |
|---|---|---|---|
| API versioning (`/api/v1`) | MUST_HAVE | From the first endpoint | P5-T01 |
| Consistent response/error contracts | MUST_HAVE | P2-T03, P5-T01 | P2-T03, P5-T01 |
| OpenAPI documentation | SHOULD_HAVE (free with D01-A/B) | P5-T01 | P5-T01 |
| Pagination | NOT_APPLICABLE (bounded responses) | — | — |
| Idempotency keys | NOT_APPLICABLE (no write endpoints) | — | — |
| CORS and security headers | MUST_HAVE (headers) / conditional (CORS, D04) | Before production | P2-T01, P7-T02 |
| Docker practices (multi-stage, non-root, pinned base images, no secrets) | MUST_HAVE | P1-T06, P8-T01 | P1-T06, P8-T01 |
| Migration procedure (release phase `migrate`) | MUST_HAVE | Deploy | P8-T02 |
| Dependency updates / vulnerability checks | SHOULD_HAVE (`pip-audit`, `npm audit`; Dependabot LATER) | Before production | P7-T02 |
| Rollback | SHOULD_HAVE: Heroku release rollback + backward-compatible migrations | Deploy | P8-T02 |

## O. Deferred features and their triggers

| Feature | Why not now | Trigger to introduce |
|---|---|---|
| Scheduled data refresh | Window is historical (A5) | Client wants rolling/live data |
| Authentication / roles | Not in the brief | Per-user data or client access policy |
| Caching (HTTP → Redis) | Small immutable data | Measured p95 above budget (P7-T03) |
| Prometheus/Grafana, alerting | Heroku metrics suffice for a pilot | Production traffic and an on-call owner |
| OpenTelemetry tracing | Single service, one DB | Multiple services or unexplained latency |
| Circuit breaker / queues / workers | No live dependency | Live Elexon calls in the request path |
| OpenAPI-generated frontend client | Only ~6 endpoints | Frequent contract changes |
| Browser E2E tests (Playwright) | Component tests cover v1 | Regressions slip through the UI |
| Kubernetes, service mesh, microservices | One small service | Several independently scaling services |
| Distributed locks, event buses | No concurrency problem | Multi-writer or async workflows |
| Dynamic config reload, plugin systems, code generation | No requirement | Concrete operational need |
| Demand / procurement optimisation | Out of data scope (A8) | Client provides demand data and scope |
