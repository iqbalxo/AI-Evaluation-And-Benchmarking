import json
import math
import re
from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class MatcherResult:
    matcher_type: str
    passed: bool | None
    score: float | None
    reason: str


def _normalize(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^\w\s.-]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _parse_config(config_json: str | None) -> dict:
    if not config_json:
        return {}
    try:
        parsed = json.loads(config_json)
        return parsed if isinstance(parsed, dict) else {}
    except json.JSONDecodeError:
        return {}


def _numeric_value(text: str) -> float | None:
    match = re.search(r"-?\d+(?:\.\d+)?", text)
    return float(match.group(0)) if match else None


def evaluate_matcher(prompt: str, response: str, expected_output: str,
                     matcher_type: str | None = None, matcher_config: str | None = None) -> MatcherResult:
    matcher = (matcher_type or "judge").strip().lower()
    config = _parse_config(matcher_config)
    response_norm = _normalize(response)
    expected_norm = _normalize(expected_output)

    if matcher == "judge":
        return MatcherResult(matcher, None, None, "Judge-only scoring selected.")

    if matcher == "exact":
        passed = response_norm == expected_norm
        return MatcherResult(matcher, passed, 1.0 if passed else 0.0, "Normalized exact match.")

    if matcher == "contains":
        passed = expected_norm in response_norm
        return MatcherResult(matcher, passed, 1.0 if passed else 0.0, "Expected output containment check.")

    if matcher == "regex":
        pattern = config.get("pattern") or expected_output
        try:
            passed = bool(re.search(pattern, response, re.IGNORECASE | re.MULTILINE))
            return MatcherResult(matcher, passed, 1.0 if passed else 0.0, f"Regex pattern: {pattern}")
        except re.error as exc:
            return MatcherResult(matcher, False, 0.0, f"Invalid regex pattern: {exc}")

    if matcher == "numeric_tolerance":
        tolerance = float(config.get("tolerance", 0.0))
        expected_value = _numeric_value(expected_output)
        response_value = _numeric_value(response)
        if expected_value is None or response_value is None:
            return MatcherResult(matcher, False, 0.0, "Could not parse numeric values.")
        delta = abs(expected_value - response_value)
        passed = delta <= tolerance
        score = 1.0 if passed else max(0.0, 1.0 - delta / max(abs(expected_value), 1.0))
        return MatcherResult(matcher, passed, round(score, 3), f"Delta {delta:g}, tolerance {tolerance:g}.")

    if matcher == "semantic_similarity":
        expected_tokens = set(expected_norm.split())
        response_tokens = set(response_norm.split())
        if not expected_tokens or not response_tokens:
            return MatcherResult(matcher, False, 0.0, "No comparable tokens.")
        overlap = len(expected_tokens & response_tokens) / math.sqrt(len(expected_tokens) * len(response_tokens))
        threshold = float(config.get("threshold", 0.6))
        passed = overlap >= threshold
        return MatcherResult(matcher, passed, round(overlap, 3), f"Token cosine similarity threshold {threshold}.")

    return MatcherResult(matcher, None, None, f"Unknown matcher '{matcher}'; falling back to judge-only scoring.")


def matcher_result_to_dict(result: MatcherResult) -> dict:
    return asdict(result)
