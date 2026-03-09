"""
LLM-Based Judge — Scoring engine with retry and smart fallback.

Uses an LLM via OpenRouter for evaluation. Falls back to token-containment
heuristics when the API is unavailable.
"""
import os
import re
import json
import time
import httpx
import logging

logger = logging.getLogger(__name__)

# Patterns that strongly indicate fabricated / hallucinated content
_FABRICATION_PATTERNS = [
    r"secret(?:ly)?",
    r"alien[s]?",
    r"conspiracy",
    r"magic(?:al)?",
    r"supernatural",
    r"unicorn[s]?",
    r"dragon[s]?",
    r"invented (?:by|in) \d{4}",  # fabricated dates
    r"according to (?:ancient|secret|classified)",
    r"nobody knows",
    r"it is rumou?red",
]

_FABRICATION_RE = re.compile("|".join(_FABRICATION_PATTERNS), re.IGNORECASE)

# Max retry attempts for the judge LLM call
_MAX_RETRIES = 3
_RETRY_BACKOFF_SECS = 2


# Stopwords to strip (but NOT when the answer itself is very short)
_STOPWORDS = {"the", "a", "an", "is", "are", "was", "were", "it", "of",
              "to", "in", "for", "on", "and", "or", "that", "this"}


def _normalize(text: str, strip_stopwords: bool = True) -> str:
    """Lowercase, strip punctuation, optionally remove stopwords."""
    text = text.lower().strip()
    text = re.sub(r"[^\w\s]", " ", text)          # remove punctuation
    if strip_stopwords:
        words = text.split()
        words = [w for w in words if w not in _STOPWORDS]
        text = " ".join(words)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _tokenize(text: str, strip_stopwords: bool = True) -> set[str]:
    return set(_normalize(text, strip_stopwords).split())


def _fuzzy_token_overlap(expected_tokens: set[str], response_tokens: set[str]) -> float:
    """
    Count how many expected tokens are matched in the response,
    either exactly or by sharing a 4+ character prefix (stem match).
    Returns a ratio 0.0 – 1.0.
    """
    if not expected_tokens:
        return 0.0
    matched = 0
    for et in expected_tokens:
        if et in response_tokens:
            matched += 1
        elif len(et) >= 4:
            prefix = et[:4]
            if any(rt.startswith(prefix) for rt in response_tokens):
                matched += 0.8  # partial credit
    return matched / len(expected_tokens)


def judge_response(prompt: str, response: str, expected_output: str,
                   *, force_fallback: bool = False) -> dict:
    """
    Score a single AI response against the expected output using an LLM.

    Returns dict with:
      - accuracy_score (1-10)
      - hallucination_detected (bool)
      - reasoning_quality (excellent|good|fair|poor)
      - relevance_score (0-10)
    """
    judge_prompt = f"""You are an expert AI evaluator. 
Given a prompt, an expected correct answer, and an AI's actual response, evaluate the response.

Prompt: {prompt}
Expected Answer: {expected_output}
AI Response: {response}

Output ONLY a JSON object with the following schema:
{{
  "accuracy_score": <float 1-10>,
  "hallucination_detected": <boolean>,
  "reasoning_quality": "<excellent|good|fair|poor>",
  "relevance_score": <float 0-10>
}}

Rules:
- Accuracy (1-10): How factually correct is the AI response compared to the expected answer? 10 = perfect.
- Hallucination (bool): ONLY set to true if the AI introduces false, unfactual, or completely unfounded information. Do NOT set to true for harmless extra wording, elaborations, formatting, or correct additional context.
- Reasoning (string): Choose one of excellent, good, fair, poor.
- Relevance (0-10): How direct and relevant is the answer to the prompt?
"""

    print("\n" + "=" * 40, flush=True)
    print("--- JUDGING PROMPT ---", flush=True)
    print(f"Prompt: {prompt}", flush=True)
    print(f"Expected Answer: {expected_output}", flush=True)
    print(f"Model Response: {response}", flush=True)
    print(f"Exact Judge Prompt:\n{judge_prompt}\n", flush=True)

    # ── Short-circuit: force fallback for testing ─────────
    if force_fallback:
        print("--- FORCED FALLBACK MODE ---", flush=True)
        scores = _fallback_judge(prompt, response, expected_output)
        scores["judge_prompt"] = judge_prompt
        print(f"--- PARSED SCORES (fallback) ---\n{scores}\n" + "=" * 40 + "\n", flush=True)
        return scores

    api_key = os.getenv("OPENROUTER_API_KEY", "")
    if not api_key:
        print("OPENROUTER_API_KEY not set for Judge — using fallback.", flush=True)
        scores = _fallback_judge(prompt, response, expected_output)
        scores["judge_prompt"] = judge_prompt
        print(f"--- PARSED SCORES (fallback) ---\n{scores}\n" + "=" * 40 + "\n", flush=True)
        return scores

    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": "openrouter/free",
        "messages": [{"role": "user", "content": judge_prompt}],
    }

    # ── Retry loop ────────────────────────────────────────
    last_error = None
    for attempt in range(1, _MAX_RETRIES + 1):
        try:
            with httpx.Client(timeout=45.0) as client:
                res = client.post(url, headers=headers, json=payload)
                res.raise_for_status()
                data = res.json()
                raw_judge_text = data["choices"][0]["message"]["content"]
                print(f"--- RAW JUDGE RESPONSE (attempt {attempt}) ---\n{raw_judge_text}\n", flush=True)

                # Extract JSON block if surrounded by markdown or extra text
                clean_text = raw_judge_text.strip()
                match = re.search(r"\{.*\}", clean_text, re.DOTALL)
                if match:
                    clean_text = match.group(0)

                parsed = json.loads(clean_text)

                acc = float(parsed.get("accuracy_score", 1.0))
                hal = bool(parsed.get("hallucination_detected", False))
                rea = str(parsed.get("reasoning_quality", "poor")).lower()
                rel = float(parsed.get("relevance_score", 0.0))

                final_scores = {
                    "accuracy_score": acc,
                    "hallucination_detected": hal,
                    "reasoning_quality": rea,
                    "relevance_score": rel,
                    "judge_prompt": judge_prompt,
                    "raw_judge_response": raw_judge_text,
                }
                print(f"--- PARSED SCORES ---\n{final_scores}\n" + "=" * 40 + "\n", flush=True)
                return final_scores

        except Exception as e:
            last_error = e
            print(f"--- JUDGE ATTEMPT {attempt}/{_MAX_RETRIES} FAILED: {e} ---", flush=True)
            if attempt < _MAX_RETRIES:
                wait = _RETRY_BACKOFF_SECS * attempt
                print(f"    Retrying in {wait}s ...", flush=True)
                time.sleep(wait)

    # All retries exhausted — fall back to heuristics
    print(f"--- JUDGE ERROR (all {_MAX_RETRIES} retries failed) ---\n"
          f"Last error: {last_error}\nUsing fallback heuristic judge.\n" + "=" * 40 + "\n", flush=True)
    scores = _fallback_judge(prompt, response, expected_output)
    scores["judge_prompt"] = judge_prompt
    scores["raw_judge_response"] = f"API Error: {last_error}. Used fallback judge."
    print(f"--- PARSED SCORES (fallback) ---\n{scores}\n" + "=" * 40 + "\n", flush=True)
    return scores


# ── Fallback heuristic judge ─────────────────────────────
def _fallback_judge(prompt: str, response: str, expected_output: str) -> dict:
    """
    Score using token-containment and keyword matching.

    Strategy:
      1. Normalize & tokenise both expected and response.
      2. Check if all expected-answer tokens appear in the response (containment).
      3. Compute token-overlap ratio as a secondary signal.
      4. Detect hallucination via fabrication-pattern regex.
    """
    # For short expected answers (e.g. "No", "Yes", "4"), don't strip stopwords
    exp_word_count = len(expected_output.strip().split())
    strip_sw = exp_word_count > 3

    resp_norm = _normalize(response, strip_stopwords=True)
    exp_norm = _normalize(expected_output, strip_stopwords=strip_sw)

    resp_tokens = _tokenize(response, strip_stopwords=True)
    exp_tokens = _tokenize(expected_output, strip_stopwords=strip_sw)
    prompt_tokens = _tokenize(prompt)

    # Also keep a no-stopword-strip version for substring checks
    resp_norm_full = _normalize(response, strip_stopwords=False)
    exp_norm_full = _normalize(expected_output, strip_stopwords=False)

    # ── Accuracy ──────────────────────────────────────────
    if not exp_tokens:
        accuracy = 5.0  # can't evaluate without expected
    else:
        # Primary: does the response contain every expected-answer token?
        contained = exp_tokens.issubset(resp_tokens)
        # Also check plain substring containment (handles numbers like "4")
        substring_match = exp_norm in resp_norm or exp_norm_full in resp_norm_full

        if contained or substring_match:
            accuracy = 9.0
        else:
            # Fuzzy token overlap (handles stem matches like spheroid/spherical)
            fuzzy_ratio = _fuzzy_token_overlap(exp_tokens, resp_tokens)
            if fuzzy_ratio >= 0.4:
                accuracy = round(7.0 + fuzzy_ratio * 2, 1)  # 7-9
            else:
                accuracy = round(fuzzy_ratio * 8, 1)  # 0-8

    # ── Hallucination ─────────────────────────────────────
    # Only flag if the response has fabrication patterns AND misses the answer
    has_fabrication = bool(_FABRICATION_RE.search(response))
    answer_present = (exp_norm in resp_norm or exp_norm_full in resp_norm_full
                      or exp_tokens.issubset(resp_tokens))
    hallucination = has_fabrication and not answer_present

    # Even if the answer IS present, flag if there's strong fabrication language
    if has_fabrication and answer_present:
        # The answer is there but surrounded by fabricated nonsense
        hallucination = True
        accuracy = min(accuracy, 6.0)  # cap accuracy when mixed with fabrication

    # ── Relevance ─────────────────────────────────────────
    if not prompt_tokens:
        relevance = 5.0
    else:
        # How many prompt keywords appear in the response?
        prompt_overlap = len(prompt_tokens & resp_tokens) / len(prompt_tokens) if prompt_tokens else 0
        # Boost if the answer itself is relevant (using any matching method)
        if answer_present or accuracy >= 7.0:
            relevance = round(7.0 + prompt_overlap * 3, 1)  # 7-10
        else:
            relevance = round(prompt_overlap * 7, 1)  # 0-7

    relevance = min(relevance, 10.0)

    # ── Reasoning quality ─────────────────────────────────
    if accuracy >= 8.0 and not hallucination:
        reasoning = "excellent"
    elif accuracy >= 5.0:
        reasoning = "good"
    elif accuracy >= 3.0:
        reasoning = "fair"
    else:
        reasoning = "poor"

    return {
        "accuracy_score": accuracy,
        "hallucination_detected": hallucination,
        "reasoning_quality": reasoning,
        "relevance_score": relevance,
        "raw_judge_response": "Heuristic fallback judge executed."
    }
