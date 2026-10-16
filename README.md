# Stormwater ASTANA OPS

**A browser-based situation center for exploring stormwater incidents in Astana.** It connects map context, risk signals, resident reports, and response work in one demo workflow.

[Run locally](#run) · [Research baseline](research/README.md) · [Data sources](work/stormwater-mvp/DATA-SOURCES.md)

## Product idea

The prototype connects three views of the same incident:

- an infrastructure map and asset passport;
- rainfall context and a risk assessment;
- a resident report that can be routed to a response team and tracked through an SLA.

It also demonstrates photo evidence, GeoJSON/CSV import, event history, and report export. The UI is designed as a situation center rather than a static dashboard: an operator can move from a map signal to a work item and then to a documented result.

## Current scope

This is a frontend MVP. Reports and demo state are stored in the browser. The weather and operational integrations are demonstration-level; a pilot would connect a dispatch API, PostgreSQL/PostGIS, authenticated users, and object storage for photos.

## Run

Requirements: Node.js 18+ and Python.

```bash
npm run build
python -m http.server 4174 --directory dist
```

Open <http://127.0.0.1:4174>.

## Research baseline

The [`research/`](research/) directory contains a small synthetic flood-event dataset and a baseline training script. It is intentionally separate from the interface so the operational workflow and the modelling experiment can be evaluated independently.

## Repository map

- `work/stormwater-mvp/` — browser MVP source.
- `build.mjs` — build script.
- `research/` — sample data and baseline experiment.
- `work/stormwater-mvp/DATA-SOURCES.md` — data-source notes.
- `work/stormwater-mvp/DEPLOY.md` — deployment notes.
