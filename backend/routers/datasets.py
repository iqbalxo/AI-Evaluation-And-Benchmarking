from fastapi import APIRouter, Depends, HTTPException, File, UploadFile
import json
import csv
import io
from sqlalchemy.orm import Session
from typing import List

from database import get_db
from models import EvaluationDataset, DatasetItem
from schemas import DatasetCreate, DatasetOut, DatasetItemCreate, DatasetItemOut, BenchmarkSuiteOut, UploadPreviewOut
from services.benchmark_suites import get_benchmark_suite, list_benchmark_suites

router = APIRouter(prefix="/api/datasets", tags=["Datasets"])


@router.post("/", response_model=DatasetOut)
def create_dataset(payload: DatasetCreate, db: Session = Depends(get_db)):
    dataset = EvaluationDataset(
        name=payload.name,
        description=payload.description,
        tags=payload.tags,
        schema_version=payload.schema_version,
        benchmark_suite=payload.benchmark_suite,
    )
    db.add(dataset)
    db.commit()
    db.refresh(dataset)
    return DatasetOut(
        id=dataset.id,
        name=dataset.name,
        description=dataset.description,
        created_at=dataset.created_at,
        item_count=0,
        tags=dataset.tags,
        schema_version=dataset.schema_version,
        benchmark_suite=dataset.benchmark_suite,
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
            tags=d.tags,
            schema_version=d.schema_version,
            benchmark_suite=d.benchmark_suite,
        ))
    return out


@router.get("/benchmark-suites", response_model=List[BenchmarkSuiteOut])
def get_suites():
    return list_benchmark_suites()


@router.post("/benchmark-suites/{suite_id}/create", response_model=DatasetOut)
def create_benchmark_suite_dataset(suite_id: str, db: Session = Depends(get_db)):
    suite = get_benchmark_suite(suite_id)
    if not suite:
        raise HTTPException(status_code=404, detail="Benchmark suite not found")

    dataset = EvaluationDataset(
        name=suite["name"],
        description=suite["description"],
        tags=json.dumps(suite["tags"]),
        benchmark_suite=suite["id"],
        schema_version=1,
    )
    db.add(dataset)
    db.commit()
    db.refresh(dataset)

    for payload in suite["items"]:
        db.add(DatasetItem(dataset_id=dataset.id, **payload))
    db.commit()
    return DatasetOut(
        id=dataset.id,
        name=dataset.name,
        description=dataset.description,
        created_at=dataset.created_at,
        item_count=len(suite["items"]),
        tags=dataset.tags,
        schema_version=dataset.schema_version,
        benchmark_suite=dataset.benchmark_suite,
    )


@router.post("/preview-upload", response_model=UploadPreviewOut)
async def preview_dataset_upload(file: UploadFile = File(...)):
    rows, errors = await _parse_upload_rows(file)
    prompts = [row["prompt"] for row in rows if row.get("prompt")]
    duplicate_count = len(prompts) - len(set(prompts))
    return UploadPreviewOut(
        valid_rows=len(rows),
        invalid_rows=len(errors),
        duplicate_prompts=duplicate_count,
        errors=errors[:25],
        sample=rows[:5],
    )


@router.get("/{dataset_id:int}", response_model=DatasetOut)
def get_dataset(dataset_id: int, db: Session = Depends(get_db)):
    d = db.query(EvaluationDataset).filter(EvaluationDataset.id == dataset_id).first()
    if not d:
        raise HTTPException(status_code=404, detail="Dataset not found")
    return DatasetOut(
        id=d.id, name=d.name, description=d.description,
        created_at=d.created_at, item_count=len(d.items), tags=d.tags,
        schema_version=d.schema_version, benchmark_suite=d.benchmark_suite,
    )


@router.delete("/{dataset_id:int}")
def delete_dataset(dataset_id: int, db: Session = Depends(get_db)):
    d = db.query(EvaluationDataset).filter(EvaluationDataset.id == dataset_id).first()
    if not d:
        raise HTTPException(status_code=404, detail="Dataset not found")
    db.delete(d)
    db.commit()
    return {"detail": "Dataset deleted"}


# ── Dataset Items ──────────────────────────────────────
@router.post("/{dataset_id:int}/items", response_model=DatasetItemOut)
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
        matcher_type=payload.matcher_type,
        matcher_config=payload.matcher_config,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.post("/{dataset_id:int}/items/batch", response_model=List[DatasetItemOut])
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
            matcher_type=payload.matcher_type,
            matcher_config=payload.matcher_config,
        )
        db.add(item)
        created.append(item)
    db.commit()
    for item in created:
        db.refresh(item)
    return created


@router.get("/{dataset_id:int}/items", response_model=List[DatasetItemOut])
def list_items(dataset_id: int, db: Session = Depends(get_db)):
    return db.query(DatasetItem).filter(DatasetItem.dataset_id == dataset_id).all()

@router.post("/upload", response_model=DatasetOut)
async def upload_dataset(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    rows, errors = await _parse_upload_rows(file)
    if not rows:
        raise HTTPException(status_code=400, detail="No valid items found. Must contain 'prompt' and 'expected_output' fields.")
        
    ds_name = file.filename.split(".")[0].replace("_", " ").title()
    dataset = EvaluationDataset(
        name=ds_name,
        description=f"Uploaded from {file.filename}. Invalid rows skipped: {len(errors)}",
        tags=json.dumps(["uploaded"]),
        schema_version=1,
    )
    db.add(dataset)
    db.commit()
    db.refresh(dataset)
    
    for row in rows:
        db.add(DatasetItem(dataset_id=dataset.id, **row))
        
    db.commit()
    
    return DatasetOut(
        id=dataset.id,
        name=dataset.name,
        description=dataset.description,
        created_at=dataset.created_at,
        item_count=len(rows),
        tags=dataset.tags,
        schema_version=dataset.schema_version,
        benchmark_suite=dataset.benchmark_suite,
    )


async def _parse_upload_rows(file: UploadFile) -> tuple[list[dict], list[str]]:
    if not file.filename.endswith((".json", ".csv")):
        raise HTTPException(status_code=400, detail="Only .csv and .json files are supported")

    content = await file.read()
    rows: list[dict] = []
    errors: list[str] = []

    if file.filename.endswith(".csv"):
        text = content.decode("utf-8")
        source_rows = list(csv.DictReader(io.StringIO(text)))
    else:
        try:
            source_rows = json.loads(content)
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid JSON file format")
        if not isinstance(source_rows, list):
            raise HTTPException(status_code=400, detail="JSON must be a list of objects")

    seen_prompts = set()
    for idx, row in enumerate(source_rows, start=1):
        prompt = (row.get("prompt") or "").strip()
        expected_output = (row.get("expected_output") or row.get("expected") or "").strip()
        if not prompt or not expected_output:
            errors.append(f"Row {idx}: missing prompt or expected_output")
            continue
        if prompt in seen_prompts:
            errors.append(f"Row {idx}: duplicate prompt")
        seen_prompts.add(prompt)
        rows.append({
            "prompt": prompt,
            "expected_output": expected_output,
            "evaluation_type": row.get("evaluation_type", "question_answering"),
            "difficulty": row.get("difficulty", "medium"),
            "matcher_type": row.get("matcher_type", "judge"),
            "matcher_config": row.get("matcher_config", "{}"),
        })

    return rows, errors
