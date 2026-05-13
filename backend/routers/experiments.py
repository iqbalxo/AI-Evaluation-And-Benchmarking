import json
import csv
import io
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse
from sqlalchemy.orm import Session
from typing import List

from database import get_db
from models import Experiment, EvaluationRun
from schemas import (
    ExperimentCreate,
    ExperimentOut,
    ExperimentCompareOut,
    EvaluationRunOut,
    LeaderboardRowOut,
    RegressionReportOut,
    PairwiseComparisonCreate,
    PairwiseComparisonOut,
)
from services.llm_judge import judge_pairwise

router = APIRouter(prefix="/api/experiments", tags=["Experiments"])


@router.post("/", response_model=ExperimentOut)
def create_experiment(payload: ExperimentCreate, db: Session = Depends(get_db)):
    # Validate that all run IDs exist
    for rid in payload.run_ids:
        if not db.query(EvaluationRun).filter(EvaluationRun.id == rid).first():
            raise HTTPException(status_code=404, detail=f"Run {rid} not found")

    exp = Experiment(
        name=payload.name,
        description=payload.description,
        run_ids_json=json.dumps(payload.run_ids),
    )
    db.add(exp)
    db.commit()
    db.refresh(exp)
    return exp


@router.get("/", response_model=List[ExperimentOut])
def list_experiments(db: Session = Depends(get_db)):
    return db.query(Experiment).order_by(Experiment.created_at.desc()).all()


@router.get("/{experiment_id}/compare", response_model=ExperimentCompareOut)
def compare_experiment(experiment_id: int, db: Session = Depends(get_db)):
    exp = db.query(Experiment).filter(Experiment.id == experiment_id).first()
    if not exp:
        raise HTTPException(status_code=404, detail="Experiment not found")

    run_ids = json.loads(exp.run_ids_json)
    runs = []
    for rid in run_ids:
        r = db.query(EvaluationRun).filter(EvaluationRun.id == rid).first()
        if r:
            runs.append(EvaluationRunOut(
                **{c.name: getattr(r, c.name) for c in r.__table__.columns},
                system_name=r.system.name if r.system else None,
                dataset_name=r.dataset.name if r.dataset else None,
            ))

    return ExperimentCompareOut(experiment=exp, runs=runs)


@router.get("/{experiment_id}/export")
def export_experiment(experiment_id: int, format: str = "json", db: Session = Depends(get_db)):
    exp = db.query(Experiment).filter(Experiment.id == experiment_id).first()
    if not exp:
        raise HTTPException(status_code=404, detail="Experiment not found")
    run_ids = json.loads(exp.run_ids_json)
    runs = [db.query(EvaluationRun).filter(EvaluationRun.id == rid).first() for rid in run_ids]
    rows = [_run_export_row(run) for run in runs if run]

    if format == "csv":
        stream = io.StringIO()
        writer = csv.DictWriter(stream, fieldnames=list(rows[0].keys()) if rows else ["experiment_id"])
        writer.writeheader()
        writer.writerows(rows)
        stream.seek(0)
        return StreamingResponse(
            iter([stream.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=experiment_{experiment_id}.csv"},
        )

    return JSONResponse({"experiment": ExperimentOut.model_validate(exp).model_dump(mode="json"), "runs": rows})


@router.get("/analytics/leaderboard", response_model=List[LeaderboardRowOut])
def leaderboard(db: Session = Depends(get_db)):
    completed_runs = db.query(EvaluationRun).filter(EvaluationRun.status == "completed").all()
    grouped: dict[str, list[EvaluationRun]] = {}
    for run in completed_runs:
        key = run.system_name or f"System {run.system_id}"
        grouped.setdefault(key, []).append(run)

    rows = []
    for system_name, runs in grouped.items():
        total_success = sum(run.successful_runs or 0 for run in runs)
        total_items = sum(run.total_items or 0 for run in runs)
        total_cost = sum(run.total_cost or 0.0 for run in runs)
        avg_accuracy = _avg([run.avg_accuracy for run in runs])
        cost_per_correct = None
        estimated_correct = sum(((run.avg_accuracy or 0) / 10) * (run.successful_runs or 0) for run in runs)
        if estimated_correct:
            cost_per_correct = round(total_cost / estimated_correct, 6)
        rows.append(LeaderboardRowOut(
            system_name=system_name,
            provider=runs[-1].provider,
            tier=runs[-1].tier,
            runs=len(runs),
            avg_accuracy=avg_accuracy,
            avg_relevance=_avg([run.avg_relevance for run in runs]),
            avg_latency_ms=_avg([run.avg_latency_ms for run in runs]),
            total_cost=round(total_cost, 6),
            cost_per_correct=cost_per_correct,
            pass_rate=round((total_success / total_items * 100), 2) if total_items else 0.0,
        ))

    return sorted(rows, key=lambda row: (row.avg_accuracy, -row.total_cost), reverse=True)


@router.get("/analytics/regression", response_model=RegressionReportOut)
def regression_report(baseline_run_id: int, candidate_run_id: int, db: Session = Depends(get_db)):
    baseline = db.query(EvaluationRun).filter(EvaluationRun.id == baseline_run_id).first()
    candidate = db.query(EvaluationRun).filter(EvaluationRun.id == candidate_run_id).first()
    if not baseline or not candidate:
        raise HTTPException(status_code=404, detail="Baseline or candidate run not found")

    accuracy_delta = round((candidate.avg_accuracy or 0) - (baseline.avg_accuracy or 0), 2)
    relevance_delta = round((candidate.avg_relevance or 0) - (baseline.avg_relevance or 0), 2)
    latency_delta = round((candidate.avg_latency_ms or 0) - (baseline.avg_latency_ms or 0), 2)
    cost_delta = round((candidate.total_cost or 0) - (baseline.total_cost or 0), 6)
    findings = []
    if accuracy_delta < -0.5:
        findings.append(f"Accuracy regressed by {abs(accuracy_delta):.2f} points.")
    if relevance_delta < -0.5:
        findings.append(f"Relevance regressed by {abs(relevance_delta):.2f} points.")
    if latency_delta > 1000:
        findings.append(f"Latency increased by {latency_delta:.0f} ms.")
    if cost_delta > 0.01:
        findings.append(f"Cost increased by ${cost_delta:.4f}.")
    status = "regression" if findings else "pass"
    if not findings:
        findings.append("No meaningful regression detected.")
    return RegressionReportOut(
        baseline_run_id=baseline_run_id,
        candidate_run_id=candidate_run_id,
        accuracy_delta=accuracy_delta,
        relevance_delta=relevance_delta,
        latency_delta_ms=latency_delta,
        cost_delta=cost_delta,
        status=status,
        findings=findings,
    )


@router.post("/pairwise", response_model=PairwiseComparisonOut)
def pairwise_compare(payload: PairwiseComparisonCreate, db: Session = Depends(get_db)):
    run_a = db.query(EvaluationRun).filter(EvaluationRun.id == payload.run_a_id).first()
    run_b = db.query(EvaluationRun).filter(EvaluationRun.id == payload.run_b_id).first()
    if not run_a or not run_b:
        raise HTTPException(status_code=404, detail="Run not found")

    by_item_b = {result.item_id: result for result in run_b.results if result.status == "success"}
    votes = {"a": 0, "b": 0, "tie": 0}
    explanations = []
    compared = 0
    confidence_total = 0.0
    for result_a in run_a.results:
        result_b = by_item_b.get(result_a.item_id)
        if not result_b or result_a.status != "success":
            continue
        compared += 1
        verdict = judge_pairwise(
            result_a.prompt or "",
            result_a.expected_output or "",
            result_a.response or "",
            result_b.response or "",
            rubric_id=payload.judge_rubric,
        )
        votes[verdict["winner"]] += 1
        confidence_total += verdict["confidence"]
        if verdict["explanation"]:
            explanations.append(verdict["explanation"])

    if compared == 0:
        raise HTTPException(status_code=400, detail="No matching successful items to compare")
    winner = max(votes, key=votes.get)
    return PairwiseComparisonOut(
        run_a_id=payload.run_a_id,
        run_b_id=payload.run_b_id,
        winner=winner,
        confidence=round(confidence_total / compared, 2),
        explanation=explanations[0] if explanations else "Pairwise comparison completed.",
        compared_items=compared,
    )


@router.delete("/{experiment_id}")
def delete_experiment(experiment_id: int, db: Session = Depends(get_db)):
    exp = db.query(Experiment).filter(Experiment.id == experiment_id).first()
    if not exp:
        raise HTTPException(status_code=404, detail="Experiment not found")
    db.delete(exp)
    db.commit()
    return {"detail": "Experiment deleted"}


def _avg(values: list[float | None]) -> float:
    valid = [value for value in values if value is not None]
    return round(sum(valid) / len(valid), 2) if valid else 0.0


def _run_export_row(run: EvaluationRun) -> dict:
    return {
        "run_id": run.id,
        "system_name": run.system_name,
        "provider": run.provider,
        "tier": run.tier,
        "dataset_id": run.dataset_id,
        "status": run.status,
        "avg_accuracy": run.avg_accuracy,
        "avg_relevance": run.avg_relevance,
        "hallucination_rate": run.hallucination_rate,
        "avg_latency_ms": run.avg_latency_ms,
        "avg_token_usage": run.avg_token_usage,
        "total_cost": run.total_cost,
        "successful_runs": run.successful_runs,
        "failed_runs": run.failed_runs,
        "judge_model": run.judge_model,
        "judge_rubric": run.judge_rubric,
    }
