# Stormwater-AI research track

This folder contains a reproducible **synthetic-data baseline** for the [Stormwater ASTANA OPS](../README.md) product prototype. The metrics demonstrate the pipeline and do not measure real flood prediction performance.

## Research question

Can weather, terrain, land-cover and drainage-network features predict an urban flood-risk event 6–24 hours in advance?

## Baseline protocol

`train_baseline.py` creates a deterministic synthetic dataset with the target schema, performs a chronological 75/25 split, fits a regularized logistic regression with gradient descent, and writes metrics plus model weights to `research/results/`.

The synthetic data is scaffolding only. Before reporting field performance, replace it with verified Astana events and document the source, label policy, missing-data handling and spatial leakage controls.

```bash
python research/train_baseline.py
```

The intended next step is a comparison against XGBoost and a spatiotemporal/graph model, with AUROC, F1, Brier score, calibration, false-alarm rate and lead time reported on a temporal holdout.

## Data contract

Each row represents an asset-area and observation window:

`timestamp, asset_id, latitude, longitude, rainfall_6h_mm, rainfall_24h_mm, impervious_pct, drain_distance_m, elevation_delta_m, prior_incidents, flooded`

Potential production sources include Open-Meteo, verified municipal incident records, Astana drainage asset GIS, DEM/elevation data, land-cover data and geotagged citizen reports. Keep personally identifiable data out of training tables.
