"""
LLM-Based Judge – Simulated scoring engine.

Uses heuristic text similarity and keyword analysis to produce evaluation scores.
Can be swapped with a real LLM API (OpenAI / Anthropic) later.
"""
import random
import re
from difflib import SequenceMatcher


def _text_similarity(a: str, b: str) -> float:
    """Computes normalized text similarity between two strings."""
    a_clean = re.sub(r'\s+', ' ', a.strip().lower())
    b_clean = re.sub(r'\s+', ' ', b.strip().lower())
    return SequenceMatcher(None, a_clean, b_clean).ratio()


def _keyword_overlap(response: str, expected: str) -> float:
    """Fraction of expected keywords found in the response."""
    expected_words = set(re.findall(r'\b\w{3,}\b', expected.lower()))
    response_words = set(re.findall(r'\b\w{3,}\b', response.lower()))
    if not expected_words:
        return 0.5
    return len(expected_words & response_words) / len(expected_words)


def _detect_hallucination(response: str, expected: str, similarity: float) -> bool:
    """Heuristic hallucination detector: low similarity + extra content."""
    if similarity < 0.25:
        return True
    response_words = set(re.findall(r'\b\w{4,}\b', response.lower()))
    expected_words = set(re.findall(r'\b\w{4,}\b', expected.lower()))
    extra = response_words - expected_words
    if len(extra) > len(expected_words) * 2 and similarity < 0.4:
        return True
    return False


def _reasoning_quality(accuracy: float) -> str:
    if accuracy >= 8:
        return "excellent"
    elif accuracy >= 6:
        return "good"
    elif accuracy >= 4:
        return "fair"
    else:
        return "poor"


def judge_response(prompt: str, response: str, expected_output: str) -> dict:
    """
    Score a single AI response against the expected output.

    Returns dict with:
      - accuracy_score (1-10)
      - hallucination_detected (bool)
      - reasoning_quality (excellent|good|fair|poor)
      - relevance_score (0-10)
    """
    similarity = _text_similarity(response, expected_output)
    keyword_score = _keyword_overlap(response, expected_output)

    # Accuracy: weighted blend + slight randomness for realism
    raw_accuracy = (similarity * 0.6 + keyword_score * 0.4) * 10
    accuracy_score = round(min(10, max(1, raw_accuracy + random.uniform(-0.5, 0.5))), 1)

    hallucination = _detect_hallucination(response, expected_output, similarity)
    quality = _reasoning_quality(accuracy_score)

    # Relevance: keyword overlap weighted more
    relevance = round(min(10, max(0, keyword_score * 7 + similarity * 3 + random.uniform(-0.3, 0.3))), 1)

    return {
        "accuracy_score": accuracy_score,
        "hallucination_detected": hallucination,
        "reasoning_quality": quality,
        "relevance_score": relevance,
    }
