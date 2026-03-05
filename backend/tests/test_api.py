"""
API integration tests for the AI Evaluation & Benchmarking Platform.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


# ── AI Systems ─────────────────────────────────────────
def test_create_system():
    resp = client.post("/api/systems/", json={
        "name": "GPT-4 Test",
        "model_type": "gpt-4",
        "api_endpoint": "https://api.openai.com/v1/chat/completions",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "GPT-4 Test"
    assert data["id"] is not None


def test_list_systems():
    resp = client.get("/api/systems/")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


# ── Datasets ──────────────────────────────────────────
def test_create_dataset():
    resp = client.post("/api/datasets/", json={
        "name": "QA Benchmark",
        "description": "Question answering benchmark",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "QA Benchmark"


def test_add_dataset_items_batch():
    # Create a dataset first
    ds = client.post("/api/datasets/", json={"name": "Batch Test"}).json()
    items = [
        {"prompt": "What is 2+2?", "expected_output": "4"},
        {"prompt": "Capital of France?", "expected_output": "Paris"},
        {"prompt": "Who wrote Hamlet?", "expected_output": "William Shakespeare"},
    ]
    resp = client.post(f"/api/datasets/{ds['id']}/items/batch", json=items)
    assert resp.status_code == 200
    assert len(resp.json()) == 3


# ── Evaluations ───────────────────────────────────────
def test_trigger_evaluation():
    # Setup
    sys_resp = client.post("/api/systems/", json={
        "name": "Eval Test System", "model_type": "claude-3",
    })
    system_id = sys_resp.json()["id"]

    ds_resp = client.post("/api/datasets/", json={"name": "Eval Dataset"})
    dataset_id = ds_resp.json()["id"]

    # Add items
    client.post(f"/api/datasets/{dataset_id}/items/batch", json=[
        {"prompt": "What is AI?", "expected_output": "Artificial Intelligence"},
        {"prompt": "Define ML", "expected_output": "Machine Learning is a subset of AI"},
    ])

    # Trigger run
    resp = client.post("/api/evaluations/run", json={
        "system_id": system_id,
        "dataset_id": dataset_id,
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] in ["pending", "running", "completed"]


def test_list_runs():
    resp = client.get("/api/evaluations/runs")
    assert resp.status_code == 200


def test_get_stats():
    resp = client.get("/api/evaluations/stats")
    assert resp.status_code == 200
    data = resp.json()
    assert "total_systems" in data
    assert "total_datasets" in data


# ── Experiments ───────────────────────────────────────
def test_create_experiment():
    # We need at least one run to exist
    runs = client.get("/api/evaluations/runs").json()
    if runs:
        resp = client.post("/api/experiments/", json={
            "name": "Model Comparison v1",
            "description": "Comparing GPT-4 vs Claude",
            "run_ids": [runs[0]["id"]],
        })
        assert resp.status_code == 200
        assert resp.json()["name"] == "Model Comparison v1"


def test_list_experiments():
    resp = client.get("/api/experiments/")
    assert resp.status_code == 200
