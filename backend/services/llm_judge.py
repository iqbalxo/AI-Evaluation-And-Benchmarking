"""
LLM-Based Judge – Simulated scoring engine.

Uses heuristic text similarity and keyword analysis to produce evaluation scores.
Can be swapped with a real LLM API (OpenAI / Anthropic) later.
"""
import os
import re
import json
import httpx

def judge_response(prompt: str, response: str, expected_output: str) -> dict:
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

    print("\n" + "="*40, flush=True)
    print(f"--- JUDGING PROMPT ---", flush=True)
    print(f"Prompt: {prompt}", flush=True)
    print(f"Expected Answer: {expected_output}", flush=True)
    print(f"Model Response: {response}", flush=True)
    print(f"Exact Judge Prompt:\n{judge_prompt}\n", flush=True)

    api_key = os.getenv("OPENROUTER_API_KEY", "")
    if not api_key:
        print("OPENROUTER_API_KEY not set for Judge.", flush=True)
        return _fallback_judge(response, expected_output)

    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # Using google/gemma-2-9b-it:free or openrouter/free for the judge
    payload = {
        "model": "openrouter/free", 
        "messages": [
            {"role": "user", "content": judge_prompt}
        ]
    }

    try:
        with httpx.Client(timeout=45.0) as client:
            res = client.post(url, headers=headers, json=payload)
            res.raise_for_status()
            data = res.json()
            raw_judge_text = data["choices"][0]["message"]["content"]
            print(f"--- RAW JUDGE RESPONSE ---\n{raw_judge_text}\n", flush=True)
            
            # Extract JSON block if surrounded by markdown or extra text
            clean_text = raw_judge_text.strip()
            match = re.search(r'\{.*\}', clean_text, re.DOTALL)
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
            }
            print(f"--- PARSED SCORES ---\n{final_scores}\n" + "="*40 + "\n", flush=True)
            return final_scores

    except Exception as e:
        print(f"--- JUDGE ERROR ---\nFailed to call or parse judge LLM: {e}\n" + "="*40 + "\n", flush=True)
        return _fallback_judge(response, expected_output)


def _fallback_judge(response: str, expected_output: str) -> dict:
    from difflib import SequenceMatcher
    a_clean = re.sub(r'\s+', ' ', response.strip().lower())
    b_clean = re.sub(r'\s+', ' ', expected_output.strip().lower())
    similarity = SequenceMatcher(None, a_clean, b_clean).ratio()
    
    score = round(similarity * 10, 1)
    return {
        "accuracy_score": score,
        "hallucination_detected": score < 3.0,
        "reasoning_quality": "good" if score > 5.0 else "poor",
        "relevance_score": score
    }
