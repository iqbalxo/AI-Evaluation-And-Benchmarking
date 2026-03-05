from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


# ── AI System ──────────────────────────────────────────
class AISystemCreate(BaseModel):
    name: str
    model_type: str
    api_endpoint: Optional[str] = None
    config_json: Optional[str] = "{}"


class AISystemOut(BaseModel):
    id: int
    name: str
    model_type: str
    api_endpoint: Optional[str]
    config_json: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


# ── Dataset ────────────────────────────────────────────
class DatasetItemCreate(BaseModel):
    prompt: str
    expected_output: str
    evaluation_type: Optional[str] = "question_answering"
    difficulty: Optional[str] = "medium"


class DatasetItemOut(BaseModel):
    id: int
    dataset_id: int
    prompt: str
    expected_output: str
    evaluation_type: str
    difficulty: str

    class Config:
        from_attributes = True


class DatasetCreate(BaseModel):
    name: str
    description: Optional[str] = ""


class DatasetOut(BaseModel):
    id: int
    name: str
    description: str
    created_at: datetime
    item_count: Optional[int] = 0

    class Config:
        from_attributes = True


# ── Evaluation ─────────────────────────────────────────
class EvaluationRunCreate(BaseModel):
    system_id: int
    dataset_id: int


class EvaluationResultOut(BaseModel):
    id: int
    run_id: int
    item_id: int
    response: str
    accuracy_score: float
    hallucination_flag: bool
    reasoning_quality: str
    relevance_score: float
    latency_ms: float
    token_cost: float

    class Config:
        from_attributes = True


class EvaluationRunOut(BaseModel):
    id: int
    system_id: int
    dataset_id: int
    status: str
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    avg_accuracy: Optional[float]
    avg_latency_ms: Optional[float]
    hallucination_rate: Optional[float]
    avg_relevance: Optional[float]
    total_cost: Optional[float]
    total_items: int
    system_name: Optional[str] = None
    dataset_name: Optional[str] = None

    class Config:
        from_attributes = True


class EvaluationRunDetail(EvaluationRunOut):
    results: List[EvaluationResultOut] = []


# ── Experiment ─────────────────────────────────────────
class ExperimentCreate(BaseModel):
    name: str
    description: Optional[str] = ""
    run_ids: List[int]


class ExperimentOut(BaseModel):
    id: int
    name: str
    description: str
    run_ids_json: str
    created_at: datetime

    class Config:
        from_attributes = True


class ExperimentCompareOut(BaseModel):
    experiment: ExperimentOut
    runs: List[EvaluationRunOut]
