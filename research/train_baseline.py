"""Train a small, dependency-free temporal baseline for Stormwater-AI.

The generated records are synthetic scaffolding. They make the experiment
reproducible until verified Astana flood events are available.
"""

from __future__ import annotations

import csv
import json
import math
import random
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parent
DATA_PATH = ROOT / "data" / "sample_flood_events.csv"
RESULTS_PATH = ROOT / "results" / "baseline_results.json"
SEED = 20261011


@dataclass(frozen=True)
class Record:
    timestamp: str
    asset_id: str
    latitude: float
    longitude: float
    features: tuple[float, ...]
    flooded: int


def sigmoid(value: float) -> float:
    """Convert a logit to a numerically stable probability."""
    if value < -35:
        return 0.0
    if value > 35:
        return 1.0
    return 1.0 / (1.0 + math.exp(-value))


def generate_records(count: int = 160) -> list[Record]:
    """Create deterministic synthetic records with a realistic class balance."""
    rng = random.Random(SEED)
    start = datetime(2021, 1, 1, tzinfo=timezone.utc)
    records: list[Record] = []
    for index in range(count):
        timestamp = start + timedelta(days=index * 14)
        rainfall_6h = max(0.0, rng.gauss(4.0, 5.5))
        rainfall_24h = rainfall_6h + max(0.0, rng.gauss(8.0, 8.0))
        impervious_pct = rng.uniform(25.0, 95.0)
        drain_distance = rng.uniform(10.0, 420.0)
        elevation_delta = rng.uniform(0.2, 8.0)
        prior_incidents = rng.randint(0, 5)
        logit = (
            -2.65
            + rainfall_6h * 0.12
            + rainfall_24h * 0.055
            + impervious_pct * 0.018
            - drain_distance * 0.003
            - elevation_delta * 0.16
            + prior_incidents * 0.42
        )
        probability = sigmoid(logit)
        flooded = int(probability + rng.gauss(0.0, 0.055) >= 0.5)
        records.append(
            Record(
                timestamp=timestamp.isoformat(),
                asset_id=f"AST-{index % 32 + 1:03d}",
                latitude=51.05 + rng.random() * 0.22,
                longitude=71.35 + rng.random() * 0.24,
                features=(rainfall_6h, rainfall_24h, impervious_pct, drain_distance, elevation_delta, float(prior_incidents)),
                flooded=flooded,
            )
        )
    return records


def standardize(rows: list[Record]) -> tuple[list[list[float]], list[float], list[float]]:
    """Return standardized features plus means and scales from training rows."""
    columns = list(zip(*(record.features for record in rows)))
    means = [sum(column) / len(column) for column in columns]
    scales = [max(math.sqrt(sum((value - mean) ** 2 for value in column) / len(column)), 1e-9) for column, mean in zip(columns, means)]
    matrix = [[(value - mean) / scale for value, mean, scale in zip(record.features, means, scales)] for record in rows]
    return matrix, means, scales


def fit_logistic(rows: list[Record], epochs: int = 1_600, learning_rate: float = 0.08, regularization: float = 0.01) -> tuple[float, list[float], list[float], list[float]]:
    """Fit regularized logistic regression using full-batch gradient descent."""
    matrix, means, scales = standardize(rows)
    weights = [0.0] * len(matrix[0])
    bias = 0.0
    for _ in range(epochs):
        gradients = [0.0] * len(weights)
        bias_gradient = 0.0
        for values, row in zip(matrix, rows):
            probability = sigmoid(bias + sum(weight * value for weight, value in zip(weights, values)))
            error = probability - row.flooded
            bias_gradient += error
            for index, value in enumerate(values):
                gradients[index] += error * value
        scale = 1.0 / len(rows)
        bias -= learning_rate * bias_gradient * scale
        weights = [weight - learning_rate * (gradient * scale + regularization * weight) for weight, gradient in zip(weights, gradients)]
    return bias, weights, means, scales


def predict(row: Record, bias: float, weights: list[float], means: list[float], scales: list[float]) -> float:
    """Predict the probability of a flood event for one record."""
    values = [(value - mean) / scale for value, mean, scale in zip(row.features, means, scales)]
    return sigmoid(bias + sum(weight * value for weight, value in zip(weights, values)))


def metrics(rows: list[Record], probabilities: list[float]) -> dict[str, float]:
    """Calculate threshold and probabilistic metrics for the holdout set."""
    labels = [row.flooded for row in rows]
    predictions = [int(probability >= 0.5) for probability in probabilities]
    true_positive = sum(label == prediction == 1 for label, prediction in zip(labels, predictions))
    false_positive = sum(label == 0 and prediction == 1 for label, prediction in zip(labels, predictions))
    false_negative = sum(label == 1 and prediction == 0 for label, prediction in zip(labels, predictions))
    precision = true_positive / max(true_positive + false_positive, 1)
    recall = true_positive / max(true_positive + false_negative, 1)
    f1 = 2 * precision * recall / max(precision + recall, 1e-9)
    brier = sum((probability - label) ** 2 for probability, label in zip(probabilities, labels)) / len(labels)
    positives = [probability for probability, label in zip(probabilities, labels) if label == 1]
    negatives = [probability for probability, label in zip(probabilities, labels) if label == 0]
    concordant = sum(positive > negative for positive in positives for negative in negatives)
    ties = sum(positive == negative for positive in positives for negative in negatives)
    auroc = (concordant + 0.5 * ties) / max(len(positives) * len(negatives), 1)
    return {"auroc": round(auroc, 4), "f1": round(f1, 4), "brier": round(brier, 4), "precision": round(precision, 4), "recall": round(recall, 4)}


def write_dataset(records: list[Record]) -> None:
    """Persist the generated data using the documented data contract."""
    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    with DATA_PATH.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["timestamp", "asset_id", "latitude", "longitude", "rainfall_6h_mm", "rainfall_24h_mm", "impervious_pct", "drain_distance_m", "elevation_delta_m", "prior_incidents", "flooded"])
        for record in records:
            writer.writerow([record.timestamp, record.asset_id, f"{record.latitude:.5f}", f"{record.longitude:.5f}", *[f"{value:.4f}" for value in record.features], record.flooded])


def main() -> None:
    records = generate_records()
    split_index = int(len(records) * 0.75)
    train_rows, test_rows = records[:split_index], records[split_index:]
    bias, weights, means, scales = fit_logistic(train_rows)
    probabilities = [predict(row, bias, weights, means, scales) for row in test_rows]
    result = {"task": "urban_flood_risk_classification", "seed": SEED, "split": "chronological 75/25", "train_rows": len(train_rows), "test_rows": len(test_rows), "features": ["rainfall_6h_mm", "rainfall_24h_mm", "impervious_pct", "drain_distance_m", "elevation_delta_m", "prior_incidents"], "metrics": metrics(test_rows, probabilities), "model": {"type": "regularized_logistic_regression", "bias": round(bias, 6), "weights": [round(weight, 6) for weight in weights], "means": [round(value, 6) for value in means], "scales": [round(value, 6) for value in scales]}, "data_status": "synthetic_scaffolding_replace_with_verified_astana_events"}
    write_dataset(records)
    RESULTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULTS_PATH.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result["metrics"], indent=2))


if __name__ == "__main__":
    main()
