from fastapi import APIRouter, Depends, HTTPException, File, UploadFile
import json
import csv
import io
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

@router.post("/upload", response_model=DatasetOut)
async def upload_dataset(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    if not file.filename.endswith((".json", ".csv")):
        raise HTTPException(status_code=400, detail="Only .csv and .json files are supported")
        
    content = await file.read()
    items = []
    
    if file.filename.endswith(".csv"):
        text = content.decode("utf-8")
        reader = csv.DictReader(io.StringIO(text))
        for row in reader:
            prompt = row.get("prompt")
            expected_output = row.get("expected_output") or row.get("expected")
            
            if prompt and expected_output:
                items.append(DatasetItem(
                    prompt=prompt.strip(),
                    expected_output=expected_output.strip(),
                    evaluation_type=row.get("evaluation_type", "question_answering"),
                    difficulty=row.get("difficulty", "medium")
                ))
    elif file.filename.endswith(".json"):
        try:
            data = json.loads(content)
            if not isinstance(data, list):
                raise HTTPException(status_code=400, detail="JSON must be a list of objects")
                
            for row in data:
                prompt = row.get("prompt")
                expected_output = row.get("expected_output") or row.get("expected")
                if prompt and expected_output:
                    items.append(DatasetItem(
                        prompt=prompt.strip(),
                        expected_output=expected_output.strip(),
                        evaluation_type=row.get("evaluation_type", "question_answering"),
                        difficulty=row.get("difficulty", "medium")
                    ))
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid JSON file format")
            
    if not items:
        raise HTTPException(status_code=400, detail="No valid items found. Must contain 'prompt' and 'expected_output' fields.")
        
    ds_name = file.filename.split(".")[0].replace("_", " ").title()
    dataset = EvaluationDataset(
        name=ds_name,
        description=f"Uploaded from {file.filename}"
    )
    db.add(dataset)
    db.commit()
    db.refresh(dataset)
    
    for item in items:
        item.dataset_id = dataset.id
        db.add(item)
        
    db.commit()
    
    return DatasetOut(
        id=dataset.id,
        name=dataset.name,
        description=dataset.description,
        created_at=dataset.created_at,
        item_count=len(items)
    )
