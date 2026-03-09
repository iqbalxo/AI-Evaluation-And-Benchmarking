"""
Metrics aggregation engine.

Computes summary metrics from a list of individual EvaluationResult rows.
"""
from typing import List


def _get_valid(results: list, attr: str):
    return [getattr(r, attr) for r in results if r.status == "success" and getattr(r, attr) is not None]

def calc_avg_accuracy(results: list) -> float:
    valid = _get_valid(results, "accuracy_score")
    if not valid:
        return 0.0
    return round(sum(valid) / len(valid), 2)


def calc_hallucination_rate(results: list) -> float:
    valid = _get_valid(results, "hallucination_flag")
    if not valid:
        return 0.0
    flagged = sum(1 for flag in valid if flag)
    return round(flagged / len(valid) * 100, 2)


def calc_avg_latency(results: list) -> float:
    valid = _get_valid(results, "latency_ms")
    if not valid:
        return 0.0
    return round(sum(valid) / len(valid), 2)


def calc_total_cost(results: list) -> float:
    valid = _get_valid(results, "token_cost")
    if not valid:
        return 0.0
    return round(sum(valid), 4)


def calc_avg_relevance(results: list) -> float:
    valid = _get_valid(results, "relevance_score")
    if not valid:
        return 0.0
    return round(sum(valid) / len(valid), 2)


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
