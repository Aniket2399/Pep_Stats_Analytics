# PepStats — Football Analytics

A football analytics dashboard covering a **historic La Liga season** (StatsBomb
open data) and the **World Cup 2026** (live speed layer), built on a
Lambda-architecture backend and a React frontend that reproduces a dark,
FIFA-style UI.

![PepStats — Historic Overview](docs/screenshots/historic-overview.png)

## What's inside

**Historic (La Liga 2015/16 · StatsBomb)**
- **Overview** — club hero, form guide, 6-KPI strip, possession & shot-outcome donuts, top scorers
- **Standings** — full league table with European/relegation zone bars
- **Squad** — sortable per-player table with a position filter (follows the club selector)
- **Trends** — per-matchweek line chart (goals / xG / possession / points / shots)
- **Set Pieces** — shot funnel, goal-types donut, goals-by-interval bars
- **Compare** — two-team overlaid radar + head-to-head stat rows
- **Players** — pitch **heatmap / path / points** view, movement KPIs, zone occupation (follows the club selector)

**World Cup 2026 (dynamic / live)**
- **Overview** — tournament KPIs, xG attack-vs-defense scatter, goals-by-group, latest results
- **Team Metrics** — per-team ratings derived from live standings
- **Insights** — points-vs-GD scatter, results-split donut, goal-difference leaders
- **Bracket** — built from all real knockout matches; winners auto-advance round by round
- **Groups** — the 12 live group tables

An **Update scores** button triggers a live refresh of the World Cup data.

## Screenshots

**Historic — Players (movement heatmap)**
![Historic Players heatmap](docs/screenshots/historic-players.png)

**World Cup — Bracket** (real knockout matches, winners auto-advancing)
![World Cup Bracket](docs/screenshots/wc-bracket.png)

**World Cup — Insights**
![World Cup Insights](docs/screenshots/wc-insights.png)

## Architecture

```
Batch layer   StatsBomb open data ─► parquet ─┐
Speed layer   ScraperFC / Sofascore ─► JSON ──┤─► apex.duckdb (serving store)
                                              ▼
Serving API   FastAPI (read-only over duckdb) ── /api/... 
                                              ▼
Frontend      Vite + React + TypeScript ─────── real data → wireframe UI
                                              └► bundled fallback if the API is down
```

- **`apex/`** — Python: ingest/clean (batch), live speed layer, and the FastAPI serving API.
- **`frontend/`** — the React dashboard (`src/data/adapter.ts` maps the API into the UI's shape; charts are hand-rolled SVG/canvas).
- **`data/`** — local serving store & raw data (git-ignored; ~1.3 GB).

## Running it

**1. Backend — serving API** (from the repo root)

```bash
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
uvicorn apex.api.app:app --port 8000
# → http://localhost:8000  (try /health)
```

**2. Frontend — dashboard**

```bash
cd frontend
npm install
npm run dev
# → http://localhost:5173
```

The frontend reads `VITE_API_URL` (defaults to `http://localhost:8000`). With the
API running you get real data; if it's unreachable, the historic tabs fall back
to bundled cached data.

## Data sources

- **Historic:** [StatsBomb open data](https://github.com/statsbomb/open-data) (La Liga), via `statsbombpy`.
- **World Cup live:** scraped through `ScraperFC` / a Sofascore snapshot, normalized into the serving store.

## Tests

```bash
cd frontend && npm test     # Vitest (adapter, charts, tabs)
pytest                      # backend
```

## Deploy

The repo ships everything needed to deploy both halves — the API's 3.3 MB
serving DB (`data/serving/apex.duckdb`) is committed, so the backend is
self-contained.

### API → Render (Docker)

1. In [Render](https://render.com): **New → Blueprint**, pick this repo — it
   reads [`render.yaml`](render.yaml) and builds the [`Dockerfile`](Dockerfile)
   (a slim image: `apex/` + the serving DB, via `requirements-api.txt`).
2. Deploy → you get `https://pepstats-api.onrender.com` (health check: `/health`).

The service is read-only and CORS-open. (Any Docker host works — Railway,
Fly.io, etc. — `docker build -t pepstats-api . && docker run -p 8000:8000 pepstats-api`.)

### Frontend → Vercel

1. In [Vercel](https://vercel.com): **Add New → Project**, import this repo.
2. Set **Root Directory → `frontend`** (the app lives in a subfolder; this also
   stops Vercel building the Python backend). Framework auto-detects as **Vite**
   (see [`frontend/vercel.json`](frontend/vercel.json)).
3. Add an env var **`VITE_API_URL`** = your Render API URL, then **Deploy**.

> Vite bakes env vars at build time, so change `VITE_API_URL` → redeploy. If you
> skip it, the Historic tabs still work from bundled cached data, but the World
> Cup tabs need the API.

## CI

Every push / PR to `main` runs the frontend test suite and a production build
via GitHub Actions (`.github/workflows/ci.yml`).

## Tech

TypeScript · React · Vite · Vitest · Python · FastAPI · DuckDB · pandas · StatsBomb · ScraperFC
