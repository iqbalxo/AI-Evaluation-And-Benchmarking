"""
Metrics aggregation engine.

Computes summary metrics from a list of individual EvaluationResult rows.
"""
from typing import List


def calc_avg_accuracy(results: list) -> float:
    if not results:
        return 0.0
    return round(sum(r.accuracy_score for r in results) / len(results), 2)


def calc_hallucination_rate(results: list) -> float:
    if not results:
        return 0.0
    flagged = sum(1 for r in results if r.hallucination_flag)
    return round(flagged / len(results) * 100, 2)


def calc_avg_latency(results: list) -> float:
    if not results:
        return 0.0
    return round(sum(r.latency_ms for r in results) / len(results), 2)


def calc_total_cost(results: list) -> float:
    if not results:
        return 0.0
    return round(sum(r.token_cost for r in results), 4)


def calc_avg_relevance(results: list) -> float:
    if not results:
        return 0.0
    return round(sum(r.relevance_score for r in results) / len(results), 2)


def compute_run_summary(results: list) -> dict:
    """Compute all summary metrics for an evaluation run."""
    return {
        "avg_accuracy": calc_avg_accuracy(results),
        "hallucination_rate": calc_hallucination_rate(results),
        "avg_latency_ms": calc_avg_latency(results),
        "total_cost": calc_total_cost(results),
        "avg_relevance": calc_avg_relevance(results),
        "total_items": len(results),
    }
