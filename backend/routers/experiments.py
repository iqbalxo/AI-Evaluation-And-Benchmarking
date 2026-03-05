import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from database import get_db
from models import Experiment, EvaluationRun
from schemas import ExperimentCreate, ExperimentOut, ExperimentCompareOut, EvaluationRunOut

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


@router.delete("/{experiment_id}")
def delete_experiment(experiment_id: int, db: Session = Depends(get_db)):
    exp = db.query(Experiment).filter(Experiment.id == experiment_id).first()
    if not exp:
        raise HTTPException(status_code=404, detail="Experiment not found")
    db.delete(exp)
    db.commit()
    return {"detail": "Experiment deleted"}
