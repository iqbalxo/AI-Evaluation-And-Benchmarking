from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List

from database import get_db, SessionLocal
from models import EvaluationRun, AISystem, EvaluationDataset
from schemas import EvaluationRunCreate, EvaluationRunOut, EvaluationRunDetail, EvaluationResultOut
from services.evaluation_engine import run_evaluation

router = APIRouter(prefix="/api/evaluations", tags=["Evaluations"])


def _run_eval_background(run_id: int):
    """Background task wrapper — uses its own DB session."""
    db = SessionLocal()
    try:
        run = db.query(EvaluationRun).filter(EvaluationRun.id == run_id).first()
        if run:
            run_evaluation(db, run)
    finally:
        db.close()


@router.post("/run", response_model=EvaluationRunOut)
def trigger_evaluation(payload: EvaluationRunCreate, background: BackgroundTasks, db: Session = Depends(get_db)):
    # Validate system exists
    system = db.query(AISystem).filter(AISystem.id == payload.system_id).first()
    if not system:
        raise HTTPException(status_code=404, detail="AI System not found")

    # Validate dataset exists
    dataset = db.query(EvaluationDataset).filter(EvaluationDataset.id == payload.dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")

    run = EvaluationRun(
        system_id=payload.system_id, 
        dataset_id=payload.dataset_id, 
        system_name=system.name,
        provider=system.provider,
        tier=system.tier,
        status="pending"
    )
    db.add(run)
    db.commit()
    db.refresh(run)

    # Trigger evaluation in background
    background.add_task(run_evaluation, run.id, db)
    
    kwargs = {c.name: getattr(run, c.name) for c in run.__table__.columns}
    kwargs["system_name"] = kwargs.get("system_name") or (run.system.name if run.system else None)
    kwargs["provider"] = kwargs.get("provider") or (run.system.provider if run.system else None)
    kwargs["tier"] = kwargs.get("tier") or (run.system.tier if run.system else None)
    kwargs["dataset_name"] = run.dataset.name if run.dataset else None
    
    return EvaluationRunOut(**kwargs)


@router.get("/runs", response_model=List[EvaluationRunOut])
def list_runs(db: Session = Depends(get_db)):
    runs = db.query(EvaluationRun).order_by(EvaluationRun.id.desc()).all()
    out = []
    for r in runs:
        kwargs = {c.name: getattr(r, c.name) for c in r.__table__.columns}
        kwargs["system_name"] = kwargs.get("system_name") or (r.system.name if r.system else None)
        kwargs["provider"] = kwargs.get("provider") or (r.system.provider if r.system else None)
        kwargs["tier"] = kwargs.get("tier") or (r.system.tier if r.system else None)
        kwargs["dataset_name"] = r.dataset.name if r.dataset else None
        out.append(EvaluationRunOut(**kwargs))
    return out


@router.get("/runs/{run_id}", response_model=EvaluationRunDetail)
def get_run(run_id: int, db: Session = Depends(get_db)):
    r = db.query(EvaluationRun).filter(EvaluationRun.id == run_id).first()
    if not r:
        raise HTTPException(status_code=404, detail="Run not found")
    kwargs = {c.name: getattr(r, c.name) for c in r.__table__.columns}
    kwargs["system_name"] = kwargs.get("system_name") or (r.system.name if r.system else None)
    kwargs["provider"] = kwargs.get("provider") or (r.system.provider if r.system else None)
    kwargs["tier"] = kwargs.get("tier") or (r.system.tier if r.system else None)
    kwargs["dataset_name"] = r.dataset.name if r.dataset else None
    
    return EvaluationRunDetail(
        **kwargs,
        results=[EvaluationResultOut.model_validate(res) for res in r.results],
    )


@router.get("/stats")
def get_stats(db: Session = Depends(get_db)):
    """Dashboard aggregate stats."""
    total_systems = db.query(AISystem).count()
    total_datasets = db.query(EvaluationDataset).count()
    total_runs = db.query(EvaluationRun).count()

    completed_runs = db.query(EvaluationRun).filter(EvaluationRun.status == "completed").all()
    avg_accuracy = 0.0
    if completed_runs:
        scores = [r.avg_accuracy for r in completed_runs if r.avg_accuracy is not None]
        avg_accuracy = round(sum(scores) / len(scores), 2) if scores else 0.0

    # Recent runs for trend
    recent = db.query(EvaluationRun).filter(
        EvaluationRun.status == "completed"
    ).order_by(EvaluationRun.completed_at.desc()).limit(20).all()

    trend = []
    for r in reversed(recent):
        trend.append({
            "run_id": r.id,
            "accuracy": r.avg_accuracy,
            "latency": r.avg_latency_ms,
            "hallucination_rate": r.hallucination_rate,
            "system_name": r.system.name if r.system else "Unknown",
            "completed_at": r.completed_at.isoformat() if r.completed_at else None,
        })

    return {
        "total_systems": total_systems,
        "total_datasets": total_datasets,
        "total_runs": total_runs,
        "avg_accuracy": avg_accuracy,
        "trend": trend,
    }
