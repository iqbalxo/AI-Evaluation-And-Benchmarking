from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from database import get_db
from models import EvaluationDataset, DatasetItem
from schemas import DatasetCreate, DatasetOut, DatasetItemCreate, DatasetItemOut

router = APIRouter(prefix="/api/datasets", tags=["Datasets"])


@router.post("/", response_model=DatasetOut)
def create_dataset(payload: DatasetCreate, db: Session = Depends(get_db)):
    dataset = EvaluationDataset(name=payload.name, description=payload.description)
    db.add(dataset)
    db.commit()
    db.refresh(dataset)
    return DatasetOut(
        id=dataset.id,
        name=dataset.name,
        description=dataset.description,
        created_at=dataset.created_at,
        item_count=0,
    )


@router.get("/", response_model=List[DatasetOut])
def list_datasets(db: Session = Depends(get_db)):
    datasets = db.query(EvaluationDataset).order_by(EvaluationDataset.created_at.desc()).all()
    out = []
    for d in datasets:
        out.append(DatasetOut(
            id=d.id,
            name=d.name,
            description=d.description,
            created_at=d.created_at,
            item_count=len(d.items),
        ))
    return out


@router.get("/{dataset_id}", response_model=DatasetOut)
def get_dataset(dataset_id: int, db: Session = Depends(get_db)):
    d = db.query(EvaluationDataset).filter(EvaluationDataset.id == dataset_id).first()
    if not d:
        raise HTTPException(status_code=404, detail="Dataset not found")
    return DatasetOut(
        id=d.id, name=d.name, description=d.description,
        created_at=d.created_at, item_count=len(d.items),
    )


@router.delete("/{dataset_id}")
def delete_dataset(dataset_id: int, db: Session = Depends(get_db)):
    d = db.query(EvaluationDataset).filter(EvaluationDataset.id == dataset_id).first()
    if not d:
        raise HTTPException(status_code=404, detail="Dataset not found")
    db.delete(d)
    db.commit()
    return {"detail": "Dataset deleted"}


# ── Dataset Items ──────────────────────────────────────
@router.post("/{dataset_id}/items", response_model=DatasetItemOut)
def add_item(dataset_id: int, payload: DatasetItemCreate, db: Session = Depends(get_db)):
    d = db.query(EvaluationDataset).filter(EvaluationDataset.id == dataset_id).first()
    if not d:
        raise HTTPException(status_code=404, detail="Dataset not found")
    item = DatasetItem(
        dataset_id=dataset_id,
        prompt=payload.prompt,
        expected_output=payload.expected_output,
        evaluation_type=payload.evaluation_type,
        difficulty=payload.difficulty,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.post("/{dataset_id}/items/batch", response_model=List[DatasetItemOut])
def add_items_batch(dataset_id: int, items: List[DatasetItemCreate], db: Session = Depends(get_db)):
    d = db.query(EvaluationDataset).filter(EvaluationDataset.id == dataset_id).first()
    if not d:
        raise HTTPException(status_code=404, detail="Dataset not found")
    created = []
    for payload in items:
        item = DatasetItem(
            dataset_id=dataset_id,
            prompt=payload.prompt,
            expected_output=payload.expected_output,
            evaluation_type=payload.evaluation_type,
            difficulty=payload.difficulty,
        )
        db.add(item)
        created.append(item)
    db.commit()
    for item in created:
        db.refresh(item)
    return created


@router.get("/{dataset_id}/items", response_model=List[DatasetItemOut])
def list_items(dataset_id: int, db: Session = Depends(get_db)):
    return db.query(DatasetItem).filter(DatasetItem.dataset_id == dataset_id).all()
