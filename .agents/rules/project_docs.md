---
trigger: always_on
description: Mandatory rule to read and update project documentation files in docs/implementation/ and root
---

# Project Documentation Maintenance Rule

You are working on the **Wind Forecast Monitor** project for a UK energy utility day-ahead power purchasing team.

## Documentation Files
The project documentation files are:
1. `docs/implementation/TASKS.md` (and `TASKS.md`)
2. `docs/implementation/DESIGN_DECISIONS.md` (and `DESIGN_DECISIONS.md`)
3. `docs/implementation/FOLDER_STRUCTURE.md` (and `FOLDER_STRUCTURE.md`)
4. `docs/implementation/PROJECT_STANDARDS.md` (and `PROJECT_STANDARDS.md`)

## Mandatory Directives
1. **Always Read Context**: Before working on any task or feature, check the corresponding tasks in `TASKS.md`, architecture in `FOLDER_STRUCTURE.md`, standards in `PROJECT_STANDARDS.md`, and decisions in `DESIGN_DECISIONS.md`.
2. **Always Update `TASKS.md`**: When starting a task, set status to `IN_PROGRESS`. When completing a task, verify the acceptance criteria, check the box `[x]`, set status to `DONE`, and update the progress summary counts table at the top.
3. **Always Update `DESIGN_DECISIONS.md`**: Whenever a technical or product decision is settled, update the Decision Register and the specific decision record. When facts are discovered/verified, update the facts table.
4. **Always Update `FOLDER_STRUCTURE.md` & `PROJECT_STANDARDS.md`**: Keep directory structures, file responsibilities, and standards in sync with code evolution.
5. **Keep Copies Synchronized**: Whenever you edit any of the documentation files, update both `docs/implementation/<FILE>.md` and the root `<FILE>.md` so they stay synchronized.
