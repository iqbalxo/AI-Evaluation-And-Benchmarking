from sqlalchemy import Column, Integer, String, Float, Boolean, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from database import Base


class AISystem(Base):
    __tablename__ = "ai_systems"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    model_type = Column(String(100), nullable=False)
    api_endpoint = Column(String(500), nullable=True)
    config_json = Column(Text, default="{}")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    evaluation_runs = relationship("EvaluationRun", back_populates="system")


class EvaluationDataset(Base):
    __tablename__ = "evaluation_datasets"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, default="")
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

    dataset = relationship("EvaluationDataset", back_populates="items")
    results = relationship("EvaluationResult", back_populates="item")


class EvaluationRun(Base):
    __tablename__ = "evaluation_runs"

    id = Column(Integer, primary_key=True, index=True)
    system_id = Column(Integer, ForeignKey("ai_systems.id"), nullable=False)
    dataset_id = Column(Integer, ForeignKey("evaluation_datasets.id"), nullable=False)
    status = Column(String(50), default="pending")  # pending, running, completed, failed
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    avg_accuracy = Column(Float, nullable=True)
    avg_latency_ms = Column(Float, nullable=True)
    hallucination_rate = Column(Float, nullable=True)
    avg_relevance = Column(Float, nullable=True)
    total_cost = Column(Float, nullable=True)
    total_items = Column(Integer, default=0)

    system = relationship("AISystem", back_populates="evaluation_runs")
    dataset = relationship("EvaluationDataset", back_populates="evaluation_runs")
    results = relationship("EvaluationResult", back_populates="run", cascade="all, delete-orphan")


class EvaluationResult(Base):
    __tablename__ = "evaluation_results"

    id = Column(Integer, primary_key=True, index=True)
    run_id = Column(Integer, ForeignKey("evaluation_runs.id"), nullable=False)
    item_id = Column(Integer, ForeignKey("dataset_items.id"), nullable=False)
    response = Column(Text, default="")
    accuracy_score = Column(Float, default=0.0)
    hallucination_flag = Column(Boolean, default=False)
    reasoning_quality = Column(String(50), default="fair")
    relevance_score = Column(Float, default=0.0)
    latency_ms = Column(Float, default=0.0)
    token_cost = Column(Float, default=0.0)

    run = relationship("EvaluationRun", back_populates="results")
    item = relationship("DatasetItem", back_populates="results")


class Experiment(Base):
    __tablename__ = "experiments"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, default="")
    run_ids_json = Column(Text, default="[]")  # JSON array of run IDs
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
