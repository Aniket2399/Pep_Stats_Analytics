# Snapshot scores: build-time ingest, not request-time refresh

**Date:** 2026-07-12
**Status:** approved

## Problem

The deployed app shows **1 World Cup match**. The live source has **99**. The
"Update scores" button that is supposed to fix this has never worked in
production, and cannot.

Three independent reasons it cannot work on Render:

1. **The deps aren't in the image.** `/api/live/refresh` shells out to
   `python -m apex.live.cli refresh`, which imports pandas. The API image
   installs only `requirements-api.txt` (fastapi/uvicorn/duckdb), so the
   subprocess dies at import with `ModuleNotFoundError: No module named 'pandas'`.
2. **The disk is ephemeral.** `serve()` writes `apex.duckdb` to local disk. On
   Render's free tier that write is lost on spin-down (~15 min idle).
3. **Auto-deploy re-bakes the DB.** The Dockerfile does
   `COPY data/serving/apex.duckdb`, so every push resets the data to the
   committed snapshot — even if 1 and 2 were solved.

Reason 3 is the important one: **the deploy pipeline actively overwrites any
runtime write.** Request-time refresh is fighting the delivery mechanism.

## Design: invert the model

Stop treating the DB as a cache the server refreshes. Treat it as a **build
artifact**, with git as the delivery channel.

Scrape where the deps and an unblocked IP already exist (a developer machine),
commit the resulting DB, and let auto-deploy ship it. The same mechanism that
was *erasing* scores becomes the one *delivering* them.

```
before:  browser --click--> API --subprocess--> scrape --write--> ephemeral disk  ✗
after:   dev machine --scrape--> apex.duckdb --commit--> auto-deploy --> API  ✓
```

## Changes

### 1. Stamp the snapshot time into the DB

`serve()` gains a one-row `live_meta` table: `updated_at` (UTC ISO-8601) and
`source` (`live` | `cache` | `unavailable`, already returned by `serve()`).

This is load-bearing, not decoration. `/api/meta` currently derives
`live_updated` from the mtime of `data/live/matches_raw.json` — a path in
`.dockerignore` that does not exist in the image. Production therefore returns
`{"historic_updated": null, "live_updated": null}`. The timestamp must live
*inside the DB* because the DB is the only artifact the Dockerfile copies.

`queries.meta()` reads `live_meta` when present and falls back to the current
mtime behaviour when it is not (local dev, older DBs).

### 2. Refresh the committed data

Run `python -m apex.live.cli refresh` locally. It `CREATE OR REPLACE`s the four
live tables (`live_matches`, `fixtures`, `standings`, `knockout`) plus the new
`live_meta`, leaving the historic StatsBomb tables (`player_season`,
`team_season`, `shots`) untouched. Commit `data/serving/apex.duckdb` (3.3 MB,
already tracked and deliberately un-gitignored).

### 3. Delete the button and the endpoint

Remove, as dead code that cannot succeed in the deployed image:

- the `POST /api/live/refresh` route (`apex/api/routers/live.py`)
- `refreshLive` and `RefreshResult` (`frontend/src/api/client.ts`)
- the "Update scores" button, its `updating`/`updateError` state, and the error
  banner (`frontend/src/App.tsx`)

In its place, the World Cup nav shows `SCORES AS OF <date>` sourced from
`/api/meta`. The app stops claiming to be live and states what it is: a snapshot.

> This supersedes part of PR #1, which made the refresh failure visible in the
> UI and in the host's log stream. That work is what surfaced the root cause; the
> banner is now redundant because the failing button is gone. The **server-side
> logging added to the route is removed along with the route**, but the logging
> pattern is retained in `apex/live/` for the CLI path.

### 4. Document the refresh ritual

README gains the one-liner:

```bash
python -m apex.live.cli refresh && git commit data/serving/apex.duckdb -m "data: refresh WC scores"
```

## Testing

| Change | Test |
|---|---|
| `live_meta` written | `tests/live/test_serve.py` — table exists, one row, `updated_at` matches the injected `now_ts` |
| `meta()` reads it | `tests/api/test_queries.py` — returns the stamped time; falls back when table absent |
| refresh route gone | `tests/api/test_live_routes.py` — `POST /api/live/refresh` returns 404 |
| button gone | `frontend/src/App.test.tsx` — no "Update scores" control; `SCORES AS OF` renders from meta |

Existing suites must stay green: 64 Python, 49 frontend.

## Explicitly not doing

- **Scheduled GitHub Action.** Deferred, not rejected. Scores go stale until the
  next manual refresh; with the final ~1 week out that is a handful of runs. If
  it starts to chafe, this design is the prerequisite for automating it — a
  scheduled job would do exactly what step 2 does, and `live_meta` is what would
  make its output verifiable.
- **Committing the DB on a schedule.** A 3.3 MB binary committed every few
  minutes would add gigabytes to the repo over a tournament. If scheduling
  happens, commit the small JSON snapshot and build the DB at image-build time,
  or publish the DB as a release asset.

## Risks

- **The scrape can break.** It is a third-party scrape with no contract.
  `serve()` already falls back to the last-good snapshot and refuses to write
  empty tables, so a failed refresh leaves the committed DB intact rather than
  blanking it.
- **Manual refresh gets forgotten.** Mitigated, not solved: `SCORES AS OF <date>`
  makes staleness visible in the UI instead of silent.
