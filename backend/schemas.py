from pydantic import BaseModel, ConfigDict
from typing import Optional, List, Any
from datetime import datetime


class AppBaseModel(BaseModel):
    model_config = ConfigDict(from_attributes=True, protected_namespaces=())


# ── AI System ──────────────────────────────────────────
class AISystemCreate(AppBaseModel):
    name: str
    model_type: str
    provider: Optional[str] = None
    tier: Optional[str] = None
    api_endpoint: Optional[str] = None
    config_json: Optional[str] = "{}"


class AISystemOut(AppBaseModel):
    id: int
    name: str
    model_type: str
    provider: Optional[str] = None
    tier: Optional[str] = None
    api_endpoint: Optional[str]
    config_json: Optional[str]
    created_at: datetime

class ModelPresetOut(AppBaseModel):
    id: str
    name: str
    provider: str
    tier: str
    quality: str
    cost_profile: str
    recommended_for: str


# ── Dataset ────────────────────────────────────────────
class DatasetItemCreate(AppBaseModel):
    prompt: str
    expected_output: str
    evaluation_type: Optional[str] = "question_answering"
    difficulty: Optional[str] = "medium"
    matcher_type: Optional[str] = "judge"
    matcher_config: Optional[str] = "{}"


class DatasetItemOut(AppBaseModel):
    id: int
    dataset_id: int
    prompt: str
    expected_output: str
    evaluation_type: str
    difficulty: str
    matcher_type: Optional[str] = "judge"
    matcher_config: Optional[str] = "{}"

class DatasetCreate(AppBaseModel):
    name: str
    description: Optional[str] = ""
    tags: Optional[str] = "[]"
    schema_version: Optional[int] = 1
    benchmark_suite: Optional[str] = None


class DatasetOut(AppBaseModel):
    id: int
    name: str
    description: str
    created_at: datetime
    item_count: Optional[int] = 0
    tags: Optional[str] = "[]"
    schema_version: Optional[int] = 1
    benchmark_suite: Optional[str] = None

# ── Evaluation ─────────────────────────────────────────
class EvaluationRunCreate(AppBaseModel):
    system_id: int
    dataset_id: int
    judge_rubric: Optional[str] = "general_quality"
    judge_model: Optional[str] = None
    model_config_json: Optional[str] = "{}"
    baseline_run_id: Optional[int] = None
    thresholds_json: Optional[str] = "{}"


class EvaluationResultOut(AppBaseModel):
    id: int
    run_id: int
    item_id: int
    prompt: Optional[str] = None
    expected_output: Optional[str] = None
    model_name: Optional[str] = None
    provider_name: Optional[str] = None
    response: str
    judge_prompt: Optional[str] = None
    judge_response: Optional[str] = None
    judge_model: Optional[str] = None
    judge_rubric: Optional[str] = None
    judge_confidence: Optional[float] = None
    judge_explanation: Optional[str] = None
    matcher_type: Optional[str] = None
    matcher_passed: Optional[bool] = None
    matcher_score: Optional[float] = None
    matcher_reason: Optional[str] = None
    accuracy_score: Optional[float] = None
    hallucination_flag: Optional[bool] = None
    reasoning_quality: Optional[str] = None
    relevance_score: Optional[float] = None
    latency_ms: Optional[float] = None
    token_usage: Optional[int] = 0
    token_cost: Optional[float] = None
    status: Optional[str] = "success"
    error_message: Optional[str] = None
    failure_category: Optional[str] = None
    trace_id: Optional[str] = None
    model_temperature: Optional[float] = None
    model_timeout_ms: Optional[float] = None
    created_at: Optional[datetime] = None

class EvaluationRunOut(AppBaseModel):
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
    avg_token_usage: Optional[float] = None
    total_cost: Optional[float]
    total_items: int
    successful_runs: Optional[int] = 0
    failed_runs: Optional[int] = 0
    system_name: Optional[str] = None
    provider: Optional[str] = None
    tier: Optional[str] = None
    dataset_name: Optional[str] = None
    judge_model: Optional[str] = None
    judge_rubric: Optional[str] = None
    model_config_json: Optional[str] = "{}"
    progress_current: Optional[int] = 0
    progress_total: Optional[int] = 0
    cancellation_requested: Optional[bool] = False
    baseline_run_id: Optional[int] = None
    thresholds_json: Optional[str] = "{}"
    trace_id: Optional[str] = None

class EvaluationRunDetail(EvaluationRunOut):
    results: List[EvaluationResultOut] = []


# ── Experiment ─────────────────────────────────────────
class ExperimentCreate(AppBaseModel):
    name: str
    description: Optional[str] = ""
    run_ids: List[int]


class ExperimentOut(AppBaseModel):
    id: int
    name: str
    description: str
    run_ids_json: str
    created_at: datetime

class ExperimentCompareOut(AppBaseModel):
    experiment: ExperimentOut
    runs: List[EvaluationRunOut]


class RubricDimensionOut(AppBaseModel):
    name: str
    description: str
    scale: str


class RubricOut(AppBaseModel):
    id: str
    name: str
    description: str
    dimensions: List[RubricDimensionOut]


class BenchmarkSuiteOut(AppBaseModel):
    id: str
    name: str
    description: str
    tags: List[str]


class UploadPreviewOut(AppBaseModel):
    valid_rows: int
    invalid_rows: int
    duplicate_prompts: int
    errors: List[str]
    sample: List[dict[str, Any]]


class LeaderboardRowOut(AppBaseModel):
    system_name: str
    provider: Optional[str] = None
    tier: Optional[str] = None
    runs: int
    avg_accuracy: float
    avg_relevance: float
    avg_latency_ms: float
    total_cost: float
    cost_per_correct: Optional[float] = None
    pass_rate: float


class RegressionReportOut(AppBaseModel):
    baseline_run_id: int
    candidate_run_id: int
    accuracy_delta: float
    relevance_delta: float
    latency_delta_ms: float
    cost_delta: float
    status: str
    findings: List[str]


class PairwiseComparisonCreate(AppBaseModel):
    run_a_id: int
    run_b_id: int
    judge_rubric: Optional[str] = "general_quality"


class PairwiseComparisonOut(AppBaseModel):
    run_a_id: int
    run_b_id: int
    winner: str
    confidence: float
    explanation: str
    compared_items: int
