# Codex Session Memory

Last updated: 2026-02-16 (UTC)

## Current Repository State
- Branch: `main`
- Latest commit: `986873d` (`feat: add full-stack UX smoke automation and CI reporting`)
- Working tree: clean at save time
- Remote: `origin` uses SSH
  - `git@github.com:MosslandOpenDevs/null.git`

## What Was Implemented
1. pgvector startup fallback for local environments without vector extension.
   - `backend/src/null_engine/config.py`
   - `backend/src/null_engine/db.py`
   - `backend/src/null_engine/services/convergence.py`
   - `backend/src/null_engine/services/semantic_indexer.py`
   - `backend/src/null_engine/services/taxonomy_builder.py`
2. Loadtest live webhook reporting.
   - `.github/workflows/loadtest-live.yml`
3. Full-stack UX smoke automation.
   - `scripts/ux_smoke.py`
   - `Makefile` (`ux-smoke`)
   - `package.json` (`test:ux-smoke`)
4. CI integration for UX smoke with service containers + reporting.
   - `.github/workflows/ci.yml`
   - Adds:
     - `ux-smoke` job (Postgres + Redis)
     - `ux-smoke-report` artifact
     - Job summary table with fail highlights
     - PR comment upsert (`UX Smoke (CI)`)
5. Documentation updates.
   - `backend/README.md`
   - `docs/REBUILD_PLAN.ko.md`
   - `.gitignore` (`.pnpm-store/`, ux smoke local artifacts)

## Verified Commands
- `pnpm run lint:frontend`
- `pnpm run typecheck:frontend`
- `pnpm run lint:backend`
- `pnpm run test:backend`
- `pnpm run test:ux-smoke`

## Resume Checklist (Next Codex Run)
1. Open this file first: `docs/guides/CODEX_MEMORY.md`
2. Confirm base state:
   - `git status -sb`
   - `git log -1 --oneline`
3. If asked to continue CI/UX work, start from:
   - `.github/workflows/ci.yml`
   - `scripts/ux_smoke.py`
4. Candidate next tasks:
   - Highlight only newly introduced failing steps in PR comment.
   - Include UX smoke snapshot in external webhook reporting path.
