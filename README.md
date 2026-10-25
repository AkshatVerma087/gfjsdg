# Wind Forecast Monitor (UK Day-Ahead)

[![CI](https://github.com/AkshatVerma087/gfjsdg/actions/workflows/ci.yml/badge.svg)](https://github.com/AkshatVerma087/gfjsdg/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/Python-3.12-blue.svg)](https://www.python.org/)
[![Django](https://img.shields.io/badge/Django-5.1-green.svg)](https://www.djangoproject.com/)
[![React](https://img.shields.io/badge/React-19-cyan.svg)](https://react.dev/)

An enterprise-grade analytical web portal designed for UK energy utility day-ahead power purchasing desks. It integrates national wind generation actuals and forecasts exclusively from **Elexon BMRS** (`FUELHH` and `WINDFOR`) for purchasing decisions in **January 2026**.

---

## 1. Executive Summary & Capabilities

Day-ahead wholesale power buyers face asymmetric risk: under-procuring clean wind forces the utility into expensive real-time balancing mechanisms (cash-out penalties) or fossil-fired peaker plant contracts. The Wind Forecast Monitor equips the trading desk with two core capabilities:

1. **R1 — Decision-Time Forecast (As-Of Snapshot)**:
   - For any chosen delivery day in January 2026, displays the latest national wind forecast available at the exact D-1 purchase decision cutoff (default **11:00 GMT**, matching EPEX SPOT & Nord Pool auction gate closures), plotted side-by-side against actual generation outturn.
   - Interactive cutoff controls allow buyers to inspect how forecasts looked at earlier shifts (e.g. 07:00, 09:00 morning desk briefing) or post-auction revisions.

2. **R2 — Forecast Accuracy & Risk-Adjusted Procurement**:
   - Comprehensive quantitative evaluation of forecast error: **Mean Absolute Error (MAE)**, **Systemic Bias** (positive = over-forecast risk), **Root Mean Squared Error (RMSE)**, **Weighted Absolute Percentage Error (WAPE)**, and empirical tail percentiles (**P50, P90, P95 of |error|**).
   - **Actionable Risk-Adjusted Lower Band (P90)**: Provides a backward-looking empirical safety rule (`Plan on at least: Forecast − P90 Over-Forecast MW`), ensuring 90% statistical confidence that actual wind generation will meet or exceed the committed volume.
   - **Forecast Horizon Degradation**: Analyzes how uncertainty scales from intra-day (0–6h) to multi-day (48h+) lead times.

---

## 2. Market Timing & Domain Rationale

In the Great Britain (GB) power market:
- **Auction Gate Closure**: Day-ahead power auctions on EPEX SPOT and Nord Pool N2EX close at **11:00 GMT** on day D-1.
- **Trading Desk Workflow**: Procurement positions are finalized between 10:00 and 10:55 GMT. Forecasts published after 11:00 GMT on D-1 are irrelevant for the day-ahead auction.
- **As-Of Selection**: For each target half-hour $t$ on delivery day $D$, the system queries the latest record where:
  ```sql
  publish_time <= datetime(D - 1, cutoff_time)
  ```

---

## 3. Technology Stack

- **Backend**: Python 3.12, Django 5.1, Django Ninja (typed Pydantic schemas, auto OpenAPI docs), WhiteNoise, NumPy.
- **Frontend**: Pure JavaScript (React 19, Vite, Recharts, Lucide Icons, Vanilla CSS design tokens).
- **Database**: PostgreSQL 16 (production/Docker) & SQLite (seamless local dev fallback).
- **Deployment**: Docker multi-stage build serving both the frontend SPA and backend API on a single port via Gunicorn and WhiteNoise.

---

## 4. Project Directory Structure

```text
├── backend/
│   ├── config/             # Typed environment settings (pydantic-settings), URLs, WSGI
│   │   ├── env.py          # Settings schema, fail-fast validation, secret redaction
│   │   ├── settings.py     # Hardened Django settings (check --deploy compliant)
│   │   └── urls.py         # Root router mounting /api/v1/ and SPA catch-all
│   ├── core/               # Cross-cutting infrastructure
│   │   ├── logging.py      # Structured JSON logging & secret redaction filter
│   │   ├── middleware.py   # Request ID generation & propagation (X-Request-ID)
│   │   ├── errors.py       # Standardized error taxonomy
│   │   ├── error_handlers.py # JSON error schema {error: {code, message, request_id}}
│   │   ├── health.py       # Observability endpoints (/api/v1/health, /api/v1/ready)
│   │   └── spa.py          # Production SPA fallback view
│   ├── wind/               # Domain application
│   │   ├── models.py       # WindActual and WindForecast with composite indexes
│   │   ├── ingestion.py    # Idempotent bulk upsert service
│   │   ├── selectors.py    # As-of decision forecast query (R1)
│   │   ├── metrics.py      # Pure NumPy accuracy calculation (no ORM imports)
│   │   ├── accuracy.py     # Accuracy service, risk band, horizon bucketing (R2)
│   │   ├── schemas.py      # Pydantic response/request models
│   │   ├── api.py          # Django Ninja API router (/forecast, /accuracy, /meta)
│   │   └── elexon/         # Typed Elexon BMRS HTTP client with retry & backoff
│   └── tests/              # 45 backend test suites (table-driven & integration)
├── frontend/
│   ├── src/
│   │   ├── api/            # API client (client.js) & React Query hooks (hooks.js)
│   │   ├── components/     # Layout.jsx (with attribution), States.jsx
│   │   ├── features/
│   │   │   ├── forecast/   # ForecastPage.jsx, ForecastChart.jsx (R1 view)
│   │   │   └── accuracy/   # AccuracyPage.jsx, DailyAccuracyChart.jsx, HorizonChart.jsx (R2)
│   │   ├── config.js       # Runtime environment validation (Zod)
│   │   ├── index.css       # Rich dark theme design system (Vanilla CSS)
│   │   └── App.jsx         # App shell & router
│   └── package.json        # Pure JavaScript dependencies
├── Dockerfile              # Multi-stage production container
├── docker-compose.yml      # Local container orchestration
├── Makefile                # Developer workflow targets
└── docs/implementation/    # Architectural decisions, tasks, and standards
```

---

## 5. Quickstart & Local Setup

### Option A: Local Development (Fastest)

1. **Clone repository**:
   ```bash
   git clone https://github.com/AkshatVerma087/gfjsdg.git
   cd gfjsdg
   ```

2. **Backend setup**:
   ```bash
   cd backend
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   pip install -e .
   python manage.py migrate
   python manage.py ingest_wind  # Ingests January 2026 Elexon window
   python manage.py runserver 8000
   ```

3. **Frontend setup**:
   ```bash
   cd ../frontend
   npm install
   npm run dev
   ```
   Open `http://localhost:3000` in your browser. API proxy connects automatically to `http://localhost:8000`.

---

### Option B: Docker Multi-Stage Container

To run the complete production image on a single port:

```bash
docker compose up -d db
docker build -t wind-monitor .
docker run -p 8000:8000 --env DATABASE_URL=postgresql://wind_user:wind_password@host.docker.internal:5432/wind_forecast_db wind-monitor
```

---

## 6. Verification & Data Quality

Run the automated test suites:

- **Backend Tests (45 passed)**:
  ```bash
  python -m pytest backend/tests
  ```
- **Backend Linting & Formatting**:
  ```bash
  ruff check backend
  ruff format --check backend
  ```
- **Frontend Tests (13 passed across 4 suites)**:
  ```bash
  cd frontend
  npm test
  npm run lint
  npm run build
  ```

### Independent Data Verification (P7-T01)

The system includes an independent verification mechanism that cross-references API responses against raw database records:
- **Coverage**: 1,728 `FUELHH` wind actuals (36 days from 2025-12-30 to 2026-02-03, 100% complete half-hour coverage) and 22,192 `WINDFOR` forecasts.
- **Verification Result**: 0 discrepancies across all 48 settlement periods on hand-verified benchmark days.

---

## 7. Data Attribution & License Notice

This application uses public data provided by **Elexon BMRS** under the BMRS Data Licence terms:
> Contains BMRS data © Elexon Limited copyright and database right 2026.
> Datasets: `FUELHH` (Half-hourly generation by fuel type, filtered to `fuelType=WIND`) and `WINDFOR` (Wind generation forecast by publish time).

---

## 8. AI Tool Usage Disclosure

In compliance with challenge requirements, the following AI tools and workflows were utilized during engineering:
- **Google Antigravity Agentic IDE**: Used for architectural scaffolding, pair-programming domain models, drafting test suites, and formatting documentation.
- **All calculations, metrics logic, database indexing, and market timing constraints were independently verified and validated against live Elexon API data and industry specifications.**
