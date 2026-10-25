# AGENTS.md — Wind Forecast Monitor Project Instructions & Rules

You are working on the **Wind Forecast Monitor** project for a UK energy utility day-ahead power purchasing team.

---

## 1. Project Context & Objectives

- **Client Goal**: Day-ahead power buyers need to know how much thermal/additional power to procure beyond renewable generation.
- **Key Capabilities**:
  1. **R1 (Decision-time forecast)**: Show the latest national wind forecast available at the decision cutoff on D-1 for each delivery half-hour, plotted against actual generation.
  2. **R2 (Forecast accuracy)**: Quantify error (bias, MAE, RMSE, P50/P90/P95 of |error|, WAPE, over/under-forecast split, error vs. forecast horizon) to support risk-adjusted procurement decisions.
- **Data Scope**: Elexon BMRS data only (`FUELHH` actuals where `fuelType=WIND`, `WINDFOR` forecasts). Decisions made in January 2026.
- **Tech Stack**: Python/Django backend (`backend/`), React + TypeScript Vite frontend (`frontend/`), Docker (multi-stage image), PostgreSQL persistence.

---

## 2. Mandatory Rules for Project Documentation

The project documentation lives in `docs/implementation/` and represents the single source of truth for the project:
1. `docs/implementation/TASKS.md`
2. `docs/implementation/DESIGN_DECISIONS.md`
3. `docs/implementation/FOLDER_STRUCTURE.md`
4. `docs/implementation/PROJECT_STANDARDS.md`

### Rules to Always Follow:

1. **Always Read Before Working**:
   - Before implementing any feature or modifying code, inspect the corresponding task in `docs/implementation/TASKS.md`, the architectural boundary in `docs/implementation/FOLDER_STRUCTURE.md`, the coding/security standard in `docs/implementation/PROJECT_STANDARDS.md`, and any related decisions in `docs/implementation/DESIGN_DECISIONS.md`.
   - Never guess or diverge from established project standards.

2. **Always Update `docs/implementation/TASKS.md`**:
   - Update task status (`NOT_STARTED` → `IN_PROGRESS` → `DONE`) and checkboxes (`[ ]` → `[x]`).
   - Mark a task `DONE` **only** after its verification command/step passes.
   - Always update the progress summary count table at the top of `TASKS.md` when tasks change state.
   - Never renumber tasks. If an optional task is dropped, mark `DONE (dropped: reason)`.

3. **Always Update `docs/implementation/DESIGN_DECISIONS.md`**:
   - Whenever an open decision (D01–D13) is made or changed, update the Decision Register and the decision record section.
   - When API spikes or research yield new facts, update the Verified Facts table (replacing UNVERIFIED rows U1–U6).

4. **Always Update `docs/implementation/FOLDER_STRUCTURE.md` & `docs/implementation/PROJECT_STANDARDS.md`**:
   - Keep directory trees, file responsibility tables, and standard checklists synchronized with any changes to the codebase.

5. **Never Commit or Push Challenge Brief**:
   - The challenge brief document (`REint Full Stack SWE challenge v4 Shared.docx` / `*.docx`) must NEVER be tracked, committed, or pushed to preserve full repository anonymity and prevent prompt leakage.

---

## 3. Key Architecture & Engineering Standards

- **Domain Boundaries**:
  - `core/` contains cross-cutting infrastructure (errors, logging, middleware, health). `core/` must **never** import from `wind/`.
  - `wind/` contains domain logic, models, ingestion, selectors, metrics, and API adapters.
  - `wind/metrics.py` must remain **pure** (arrays/floats in, metrics out; no Django, no ORM, no I/O).
- **Configuration**:
  - One typed `Settings` object in `config/env.py` (`pydantic-settings`). Defaults < `.env` < real environment variables. Fail-fast at boot; secrets typed as redacted.
- **Error Handling**:
  - Shared taxonomy (`core/errors.py`) mapped to unified JSON `{error: {code, message, request_id}}`. Never leak stack traces, SQL, or internal configuration to clients.
- **Testing**:
  - Table-driven unit tests for `metrics.py` with hand-calculated values.
  - Boundary tests for `selectors.py` (inclusive cutoff, empty/missing forecast, day edges).
  - Real PostgreSQL for tests exercising SQL (`DISTINCT ON`, constraints); mock only external Elexon HTTP.
