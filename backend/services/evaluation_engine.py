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
import json
import logging
import uuid
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from models import EvaluationRun, EvaluationResult, DatasetItem
from services.llm_judge import judge_response
from services.metrics import compute_run_summary
from services.answer_matchers import evaluate_matcher
from services.provider_client import ModelRequest, OpenRouterClient
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


def _load_system_config(config_json: str | None) -> dict:
    if not config_json:
        return {}

    try:
        parsed = json.loads(config_json)
    except json.JSONDecodeError as exc:
        raise ValueError("System config_json must be valid JSON") from exc

    if not isinstance(parsed, dict):
        raise ValueError("System config_json must be a JSON object")

    return parsed


def _get_openrouter_response(prompt: str, model_id: str, config: dict | None = None) -> tuple[str, float, int]:
    """
    Call OpenRouter API to get a real response.
    Returns (response_text, latency_ms, token_usage).
    """
    if not model_id:
        raise ValueError("OpenRouter model id is required")

    config = config or {}
    request = ModelRequest(
        prompt=prompt,
        model_id=model_id,
        temperature=config.get("temperature"),
        max_tokens=config.get("max_tokens"),
        top_p=config.get("top_p"),
        seed=config.get("seed"),
        timeout_seconds=float(config.get("timeout_seconds", 30.0)),
    )
    response = OpenRouterClient().complete(request)
    print(f"[LIVE EVAL] OpenRouter [{model_id}] text: {response.text}", flush=True)
    print(f"[LIVE EVAL] Usage: {response.token_usage} tokens", flush=True)
    return response.text, response.latency_ms, response.token_usage



def run_evaluation(db: Session, run: EvaluationRun):
    """Execute the full evaluation pipeline for a run."""
    run.status = "running"
    run.started_at = datetime.now(timezone.utc)
    run.trace_id = run.trace_id or str(uuid.uuid4())
    db.commit()

    try:
        items = db.query(DatasetItem).filter(DatasetItem.dataset_id == run.dataset_id).all()
        if not items:
            run.status = "failed"
            db.commit()
            return
        run.progress_total = len(items)
        run.progress_current = 0
        db.commit()

        results = []
        for item in items:
            if run.cancellation_requested:
                run.status = "cancelled"
                db.commit()
                break

            config = _load_system_config(run.model_config_json or run.system.config_json)
            item_trace_id = str(uuid.uuid4())
            trace_data = {
                "run_id": run.id,
                "item_id": item.id,
                "trace_id": item_trace_id,
                "prompt": item.prompt,
                "expected_output": item.expected_output,
                "model_name": run.system.api_endpoint or run.system.name,
                "provider_name": run.system.provider or run.system.model_type,
                "response": "",
                "judge_prompt": None,
                "judge_response": None,
                "judge_model": run.judge_model,
                "judge_rubric": run.judge_rubric,
                "judge_confidence": None,
                "judge_explanation": None,
                "matcher_type": item.matcher_type,
                "matcher_passed": None,
                "matcher_score": None,
                "matcher_reason": None,
                "accuracy_score": None,
                "hallucination_flag": None,
                "reasoning_quality": None,
                "relevance_score": None,
                "latency_ms": None,
                "token_usage": None,
                "token_cost": None,
                "status": "success",
                "error_message": None,
                "failure_category": None,
                "model_temperature": config.get("temperature"),
                "model_timeout_ms": float(config.get("timeout_seconds", 30.0)) * 1000,
            }

            try:
                # Step 1: Get AI response
                if run.system.model_type == "openrouter":
                    model_id = run.system.api_endpoint or run.system.name
                    response_text, latency, usage = _get_openrouter_response(item.prompt, model_id, config)
                else:
                    response_text, latency, usage = _simulate_ai_response(item.prompt, item.expected_output)

                trace_data["response"] = response_text
                trace_data["latency_ms"] = latency
                trace_data["token_usage"] = usage

                # Step 2: Apply deterministic matcher and judge the response
                matcher = evaluate_matcher(
                    item.prompt,
                    response_text,
                    item.expected_output,
                    item.matcher_type,
                    item.matcher_config,
                )
                trace_data["matcher_type"] = matcher.matcher_type
                trace_data["matcher_passed"] = matcher.passed
                trace_data["matcher_score"] = matcher.score
                trace_data["matcher_reason"] = matcher.reason

                scores = judge_response(
                    item.prompt,
                    response_text,
                    item.expected_output,
                    rubric_id=run.judge_rubric,
                    judge_model=run.judge_model,
                )
                trace_data["accuracy_score"] = scores.get("accuracy_score", 0.0)
                trace_data["hallucination_flag"] = scores.get("hallucination_detected", False)
                trace_data["reasoning_quality"] = scores.get("reasoning_quality", "poor")
                trace_data["relevance_score"] = scores.get("relevance_score", 0.0)
                trace_data["judge_confidence"] = scores.get("confidence")
                trace_data["judge_explanation"] = scores.get("explanation")
                trace_data["judge_prompt"] = scores.get("judge_prompt")
                trace_data["judge_response"] = scores.get("raw_judge_response")
                trace_data["judge_model"] = scores.get("judge_model")
                trace_data["judge_rubric"] = scores.get("judge_rubric")

                # Step 3: Token cost (Calculate exact via pricing mapping)
                trace_data["token_cost"] = calculate_cost(trace_data["model_name"], usage)

            except Exception as item_expr:
                trace_data["status"] = "failed"
                trace_data["error_message"] = str(item_expr)
                trace_data["failure_category"] = _classify_failure(str(item_expr))
                logger.error(f"Failed evaluating item {item.id}: {item_expr}")

            # Step 4: Create result record
            result = EvaluationResult(**trace_data)
            db.add(result)
            results.append(result)
            run.progress_current += 1
            db.flush()

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
        if run.status != "cancelled":
            run.status = "completed"
        run.completed_at = datetime.now(timezone.utc)
        db.commit()

    except Exception as e:
        run.status = "failed"
        db.commit()
        raise e


def _classify_failure(message: str) -> str:
    lowered = message.lower()
    if "rate" in lowered or "429" in lowered:
        return "rate_limit"
    if "timeout" in lowered:
        return "timeout"
    if "api_key" in lowered or "authorization" in lowered:
        return "auth"
    if "json" in lowered:
        return "configuration"
    return "provider_error"
