from sqlalchemy import Column, Integer, String, Float, Boolean, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from database import Base


class AISystem(Base):
    __tablename__ = "ai_systems"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    model_type = Column(String(100), nullable=False)
    provider = Column(String(100), nullable=True)
    tier = Column(String(50), nullable=True) # Premium, Mid-tier, Open Source
    api_endpoint = Column(String(500), nullable=True)
    config_json = Column(Text, default="{}")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    evaluation_runs = relationship("EvaluationRun", back_populates="system")


class EvaluationDataset(Base):
    __tablename__ = "evaluation_datasets"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, default="")
    tags = Column(Text, default="[]")
    schema_version = Column(Integer, default=1)
    benchmark_suite = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    items = relationship("DatasetItem", back_populates="dataset", cascade="all, delete-orphan")
    evaluation_runs = relationship("EvaluationRun", back_populates="dataset")


class DatasetItem(Base):
    __tablename__ = "dataset_items"

    id = Column(Integer, primary_key=True, index=True)
    dataset_id = Column(Integer, ForeignKey("evaluation_datasets.id"), nullable=False)
    prompt = Column(Text, nullable=False)
    expected_output = Column(Text, nullable=False)
    evaluation_type = Column(String(100), default="question_answering")
    difficulty = Column(String(50), default="medium")
    matcher_type = Column(String(50), default="judge")
    matcher_config = Column(Text, default="{}")

    dataset = relationship("EvaluationDataset", back_populates="items")
    results = relationship("EvaluationResult", back_populates="item")


class EvaluationRun(Base):
    __tablename__ = "evaluation_runs"

    id = Column(Integer, primary_key=True, index=True)
    system_id = Column(Integer, ForeignKey("ai_systems.id"), nullable=False)
    dataset_id = Column(Integer, ForeignKey("evaluation_datasets.id"), nullable=False)

    system_name = Column(String(255), nullable=True)
    provider = Column(String(100), nullable=True)
    tier = Column(String(50), nullable=True)

    status = Column(String(50), default="pending")  # pending, running, completed, failed
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    avg_accuracy = Column(Float, nullable=True)
    avg_latency_ms = Column(Float, nullable=True)
    hallucination_rate = Column(Float, nullable=True)
    avg_relevance = Column(Float, nullable=True)
    avg_token_usage = Column(Float, nullable=True)
    total_cost = Column(Float, nullable=True)
    total_items = Column(Integer, default=0)
    successful_runs = Column(Integer, default=0)
    failed_runs = Column(Integer, default=0)
    judge_model = Column(String(255), nullable=True)
    judge_rubric = Column(String(100), default="general_quality")
    model_config_json = Column(Text, default="{}")
    progress_current = Column(Integer, default=0)
    progress_total = Column(Integer, default=0)
    cancellation_requested = Column(Boolean, default=False)
    baseline_run_id = Column(Integer, nullable=True)
    thresholds_json = Column(Text, default="{}")
    trace_id = Column(String(64), nullable=True)

    system = relationship("AISystem", back_populates="evaluation_runs")
    dataset = relationship("EvaluationDataset", back_populates="evaluation_runs")
    results = relationship("EvaluationResult", back_populates="run", cascade="all, delete-orphan")


class EvaluationResult(Base):
    __tablename__ = "evaluation_results"

    id = Column(Integer, primary_key=True, index=True)
    run_id = Column(Integer, ForeignKey("evaluation_runs.id"), nullable=False)
    item_id = Column(Integer, ForeignKey("dataset_items.id"), nullable=False)
    
    # Trace telemetry
    prompt = Column(Text, nullable=True)
    expected_output = Column(Text, nullable=True)
    model_name = Column(String(255), nullable=True)
    provider_name = Column(String(255), nullable=True)
    response = Column(Text, default="")
    judge_prompt = Column(Text, nullable=True)
    judge_response = Column(Text, nullable=True)
    judge_model = Column(String(255), nullable=True)
    judge_rubric = Column(String(100), nullable=True)
    judge_confidence = Column(Float, nullable=True)
    judge_explanation = Column(Text, nullable=True)
    matcher_type = Column(String(50), nullable=True)
    matcher_passed = Column(Boolean, nullable=True)
    matcher_score = Column(Float, nullable=True)
    matcher_reason = Column(Text, nullable=True)
    
    # Metrics
    accuracy_score = Column(Float, nullable=True)
    hallucination_flag = Column(Boolean, nullable=True)
    reasoning_quality = Column(String(50), nullable=True)
    relevance_score = Column(Float, nullable=True)
    latency_ms = Column(Float, nullable=True)
    token_usage = Column(Integer, nullable=True)
    token_cost = Column(Float, nullable=True)
    
    # Status
    status = Column(String(50), default="success")  # success, failed
    error_message = Column(Text, nullable=True)
    failure_category = Column(String(100), nullable=True)
    trace_id = Column(String(64), nullable=True)
    model_temperature = Column(Float, nullable=True)
    model_timeout_ms = Column(Float, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    run = relationship("EvaluationRun", back_populates="results")
    item = relationship("DatasetItem", back_populates="results")


class Experiment(Base):
    __tablename__ = "experiments"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, default="")
    run_ids_json = Column(Text, default="[]")  # JSON array of run IDs
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
