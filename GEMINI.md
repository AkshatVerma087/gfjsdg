# GEMINI.md — Wind Forecast Monitor Project Instructions & Rules

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

The project documentation in `docs/implementation/` (and mirrored in the root directory) represents the single source of truth for the project.

### The 4 Core Documentation Files:
1. `docs/implementation/TASKS.md` (and `TASKS.md`)
2. `docs/implementation/DESIGN_DECISIONS.md` (and `DESIGN_DECISIONS.md`)
3. `docs/implementation/FOLDER_STRUCTURE.md` (and `FOLDER_STRUCTURE.md`)
4. `docs/implementation/PROJECT_STANDARDS.md` (and `PROJECT_STANDARDS.md`)

### Rules to Always Follow:

1. **Always Read Before Working**:
   - Before implementing any feature or modifying code, inspect the corresponding task in `TASKS.md`, the architectural boundary in `FOLDER_STRUCTURE.md`, the coding/security standard in `PROJECT_STANDARDS.md`, and any related decisions in `DESIGN_DECISIONS.md`.
   - Never guess or diverge from established project standards.

2. **Always Update `TASKS.md`**:
   - Update task status (`NOT_STARTED` → `IN_PROGRESS` → `DONE`) and checkboxes (`[ ]` → `[x]`).
   - Mark a task `DONE` **only** after its verification command/step passes.
   - Always update the progress summary count table at the top of `TASKS.md` when tasks change state.
   - Never renumber tasks. If an optional task is dropped, mark `DONE (dropped: reason)`.

3. **Always Update `DESIGN_DECISIONS.md`**:
   - Whenever an open decision (D01–D13) is made or changed, update the Decision Register and the decision record section.
   - When API spikes or research yield new facts, update the Verified Facts table (replacing UNVERIFIED rows U1–U6).

4. **Always Update `FOLDER_STRUCTURE.md` & `PROJECT_STANDARDS.md`**:
   - Keep directory trees, file responsibility tables, and standard checklists synchronized with any changes to the codebase.

5. **Maintain Sync Between `docs/implementation/` and Root**:
   - Whenever any of the 4 documentation files is modified, ensure both `docs/implementation/<FILE>.md` and the root `<FILE>.md` are updated and kept identical.

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
