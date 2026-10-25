---
trigger: always_on
description: Mandatory rule to read and update project documentation files in docs/implementation/ and root
---

# Project Documentation Maintenance Rule

You are working on the **Wind Forecast Monitor** project for a UK energy utility day-ahead power purchasing team.

## Documentation Files
The project documentation files live in `docs/implementation/`:
1. `docs/implementation/TASKS.md`
2. `docs/implementation/DESIGN_DECISIONS.md`
3. `docs/implementation/FOLDER_STRUCTURE.md`
4. `docs/implementation/PROJECT_STANDARDS.md`

## Mandatory Directives
1. **Always Read Context**: Before working on any task or feature, check the corresponding tasks in `docs/implementation/TASKS.md`, architecture in `docs/implementation/FOLDER_STRUCTURE.md`, standards in `docs/implementation/PROJECT_STANDARDS.md`, and decisions in `docs/implementation/DESIGN_DECISIONS.md`.
2. **Always Update `docs/implementation/TASKS.md`**: When starting a task, set status to `IN_PROGRESS`. When completing a task, verify the acceptance criteria, check the box `[x]`, set status to `DONE`, and update the progress summary counts table at the top.
3. **Always Update `docs/implementation/DESIGN_DECISIONS.md`**: Whenever a technical or product decision is settled, update the Decision Register and the specific decision record. When facts are discovered/verified, update the facts table.
4. **Always Update `docs/implementation/FOLDER_STRUCTURE.md` & `docs/implementation/PROJECT_STANDARDS.md`**: Keep directory structures, file responsibilities, and standards in sync with code evolution.
5. **Never Commit or Push Challenge Brief**: Ensure `REint Full Stack SWE challenge v4 Shared.docx` / `*.docx` remains strictly gitignored and is never committed or pushed.
