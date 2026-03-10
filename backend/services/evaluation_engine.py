"""
Evaluation Execution Engine.

Orchestrates the full evaluation pipeline:
  1. Load dataset items
  2. Send each prompt to the AI system (simulated)
  3. Score responses via LLM judge
  4. Compute & persist metrics
"""
import random
import time
import os
import httpx
import logging
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from models import EvaluationRun, EvaluationResult, DatasetItem
from services.llm_judge import judge_response
from services.metrics import compute_run_summary
from pricing import calculate_cost

logger = logging.getLogger(__name__)


# ── Simulated AI System Response Generator ───────────────
_TEMPLATES = [
    "Based on my analysis, {expected}",
    "The answer is: {expected}",
    "{expected} This is derived from the available information.",
    "After careful consideration, I believe {expected}",
    "According to my knowledge, {expected}",
]


def _simulate_ai_response(prompt: str, expected_output: str) -> tuple[str, float]:
    """
    Simulate an AI system response. Returns (response_text, latency_ms).
    In production, this would make an HTTP call to the registered API endpoint.
    """
    # Add some randomness: sometimes accurate, sometimes not
    roll = random.random()
    if roll > 0.15:
        # Mostly give a reasonably correct response
        template = random.choice(_TEMPLATES)
        response = template.format(expected=expected_output)
        # Add minor perturbation
        if random.random() > 0.6:
            words = response.split()
            if len(words) > 3:
                idx = random.randint(1, len(words) - 2)
                words[idx] = random.choice(["potentially", "approximately", "roughly", "essentially"])
                response = " ".join(words)
    else:
        # Occasionally produce a hallucinated / off-topic response
        response = f"I think the answer involves quantum computing and neural networks applied to {prompt[:30]}..."

    latency_ms = round(random.uniform(50, 800), 1)
    prompt_tokens = len(prompt.split()) * 1.3
    comp_tokens = len(response.split()) * 1.3
    token_usage = int(prompt_tokens + comp_tokens)
    return response, latency_ms, token_usage


def _get_openrouter_response(prompt: str, model_id: str) -> tuple[str, float]:
    """
    Call OpenRouter API to get a real response.
    Returns (response_text, latency_ms).
    """
    api_key = os.getenv("OPENROUTER_API_KEY", "")
    if not api_key:
        print("OPENROUTER_API_KEY not set", flush=True)
        raise ValueError("OPENROUTER_API_KEY not set")

    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost:8000",
        "X-Title": "AI Evaluation Platform"
    }

    payload = {
        "model": model_id,
        "messages": [
            {"role": "user", "content": prompt}
        ]
    }

    start_time = time.time()
    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
            latency_ms = (time.time() - start_time) * 1000

            print(f"\n[LIVE EVAL] Status Code: {response.status_code}", flush=True)
            print(f"[LIVE EVAL] Latency: {latency_ms:.2f}ms", flush=True)
            print(f"[LIVE EVAL] Headers: {dict(response.headers)}", flush=True)

            if "choices" in data and len(data["choices"]) > 0:
                text = data["choices"][0].get("message", {}).get("content", "")
                usage = data.get("usage", {}).get("total_tokens", 0)
                print(f"[LIVE EVAL] OpenRouter [{model_id}] text: {text}", flush=True)
                print(f"[LIVE EVAL] Usage: {usage} tokens", flush=True)
                
                # Check for rate limiting or other provider hints in the usage details
                if "provider_response" in data:
                    print(f"[LIVE EVAL] Provider Response context: {data['provider_response']}", flush=True)
                    
                return text, latency_ms, usage
            print(f"[LIVE EVAL] Empty response from OpenRouter: {data}", flush=True)
            raise ValueError("Empty response from OpenRouter")
    except httpx.HTTPStatusError as e:
        print(f"HTTPStatusError calling OpenRouter: {e.response.status_code} - {e.response.text}", flush=True)
        raise
    except Exception as e:
        print(f"Error calling OpenRouter: {str(e)}", flush=True)
        import traceback
        traceback.print_exc()
        raise



def run_evaluation(db: Session, run: EvaluationRun):
    """Execute the full evaluation pipeline for a run."""
    run.status = "running"
    run.started_at = datetime.now(timezone.utc)
    db.commit()

    try:
        items = db.query(DatasetItem).filter(DatasetItem.dataset_id == run.dataset_id).all()
        if not items:
            run.status = "failed"
            db.commit()
            return

        results = []
        for item in items:
            trace_data = {
                "run_id": run.id,
                "item_id": item.id,
                "prompt": item.prompt,
                "expected_output": item.expected_output,
                "model_name": run.system.api_endpoint or run.system.name,
                "provider_name": run.system.model_type,
                "response": "",
                "judge_prompt": None,
                "judge_response": None,
                "accuracy_score": None,
                "hallucination_flag": None,
                "reasoning_quality": None,
                "relevance_score": None,
                "latency_ms": None,
                "token_usage": None,
                "token_cost": None,
                "status": "success",
                "error_message": None
            }
            
            try:
                # Step 1: Get AI response
                if run.system.model_type == "openrouter":
                    model_id = run.system.api_endpoint or run.system.name
                    response_text, latency, usage = _get_openrouter_response(item.prompt, model_id)
                else:
                    response_text, latency, usage = _simulate_ai_response(item.prompt, item.expected_output)

                trace_data["response"] = response_text
                trace_data["latency_ms"] = latency
                trace_data["token_usage"] = usage

                # Step 2: Judge the response
                scores = judge_response(item.prompt, response_text, item.expected_output)
                trace_data["accuracy_score"] = scores.get("accuracy_score", 0.0)
                trace_data["hallucination_flag"] = scores.get("hallucination_detected", False)
                trace_data["reasoning_quality"] = scores.get("reasoning_quality", "poor")
                trace_data["relevance_score"] = scores.get("relevance_score", 0.0)
                trace_data["judge_prompt"] = scores.get("judge_prompt")
                trace_data["judge_response"] = scores.get("raw_judge_response")

                # Step 3: Token cost (Calculate exact via pricing mapping)
                trace_data["token_cost"] = calculate_cost(trace_data["model_name"], usage)

            except Exception as item_expr:
                trace_data["status"] = "failed"
                trace_data["error_message"] = str(item_expr)
                logger.error(f"Failed evaluating item {item.id}: {item_expr}")

            # Step 4: Create result record
            result = EvaluationResult(**trace_data)
            db.add(result)
            results.append(result)

        db.flush()

        # Step 5: Compute summary metrics
        summary = compute_run_summary(results)
        run.avg_accuracy = summary["avg_accuracy"]
        run.avg_latency_ms = summary["avg_latency_ms"]
        run.hallucination_rate = summary["hallucination_rate"]
        run.avg_relevance = summary["avg_relevance"]
        run.avg_token_usage = summary["avg_token_usage"]
        run.successful_runs = summary["successful_runs"]
        run.failed_runs = summary["failed_runs"]
        run.total_cost = summary["total_cost"]
        run.total_items = summary["total_items"]
        run.status = "completed"
        run.completed_at = datetime.now(timezone.utc)
        db.commit()

    except Exception as e:
        run.status = "failed"
        db.commit()
        raise e
