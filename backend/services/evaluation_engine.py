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
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from models import EvaluationRun, EvaluationResult, DatasetItem
from services.llm_judge import judge_response
from services.metrics import compute_run_summary


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
    return response, latency_ms


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
            # Step 1: Get AI response (simulated)
            response_text, latency = _simulate_ai_response(item.prompt, item.expected_output)

            # Step 2: Judge the response
            scores = judge_response(item.prompt, response_text, item.expected_output)

            # Step 3: Simulate token cost
            token_cost = round(random.uniform(0.001, 0.05), 4)

            # Step 4: Create result record
            result = EvaluationResult(
                run_id=run.id,
                item_id=item.id,
                response=response_text,
                accuracy_score=scores["accuracy_score"],
                hallucination_flag=scores["hallucination_detected"],
                reasoning_quality=scores["reasoning_quality"],
                relevance_score=scores["relevance_score"],
                latency_ms=latency,
                token_cost=token_cost,
            )
            db.add(result)
            results.append(result)

        db.flush()

        # Step 5: Compute summary metrics
        summary = compute_run_summary(results)
        run.avg_accuracy = summary["avg_accuracy"]
        run.avg_latency_ms = summary["avg_latency_ms"]
        run.hallucination_rate = summary["hallucination_rate"]
        run.avg_relevance = summary["avg_relevance"]
        run.total_cost = summary["total_cost"]
        run.total_items = summary["total_items"]
        run.status = "completed"
        run.completed_at = datetime.now(timezone.utc)
        db.commit()

    except Exception as e:
        run.status = "failed"
        db.commit()
        raise e
