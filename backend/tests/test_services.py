from services.answer_matchers import evaluate_matcher
from services.metrics import compute_run_summary
from pricing import calculate_cost


class Result:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


def test_numeric_tolerance_matcher_passes():
    result = evaluate_matcher(
        "What is 20 + 22?",
        "42",
        "42",
        "numeric_tolerance",
        '{"tolerance":0}',
    )
    assert result.passed is True
    assert result.score == 1.0


def test_regex_matcher_fails_invalid_pattern():
    result = evaluate_matcher("Return JSON", "nope", "(", "regex", '{"pattern":"("}')
    assert result.passed is False
    assert "Invalid regex" in result.reason


def test_pricing_known_model():
    assert calculate_cost("openai/gpt-4o-mini", 1_000_000) == 0.3


def test_metrics_ignore_failed_runs():
    results = [
        Result(status="success", accuracy_score=9, hallucination_flag=False, latency_ms=100, token_cost=0.01, relevance_score=8, token_usage=20),
        Result(status="failed", accuracy_score=None, hallucination_flag=None, latency_ms=None, token_cost=None, relevance_score=None, token_usage=None),
    ]
    summary = compute_run_summary(results)
    assert summary["avg_accuracy"] == 9
    assert summary["successful_runs"] == 1
    assert summary["failed_runs"] == 1
    assert summary["pass_rate"] == 100
