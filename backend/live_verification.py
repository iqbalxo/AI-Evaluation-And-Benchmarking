import os
import sys
import time
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

import models
import schemas
from services.evaluation_engine import run_evaluation

# Load env before anything else
load_dotenv()

# Setup test DB connection
SQLALCHEMY_DATABASE_URL = "sqlite:///./eval_platform.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def run_live_test():
    db = SessionLocal()
    try:
        print("====== STARTING STRICT LIVE VERIFICATION ======")
        print(f"Using OpenRouter Key: {'Yes' if os.environ.get('OPENROUTER_API_KEY') else 'No'}")
        
        # 1. Create a live test dataset
        print("\n[1] Creating Live Verification Dataset...")
        ds = models.EvaluationDataset(
            name="Live Verification Suite",
            description="Strict live verification dataset for end-to-end testing"
        )
        db.add(ds)
        db.commit()
        db.refresh(ds)
        print(f"  -> Created Dataset ID: {ds.id}")

        # Add 5 simple prompts
        prompts = [
            ("What is 2+2? Output only the number.", "4"),
            ("What is the capital of France?", "Paris"),
            ("Translate 'hello' to French.", "bonjour"),
            ("Who wrote Hamlet?", "William Shakespeare"),
            ("How many legs does a spider have? Output only the number.", "8")
        ]
        
        for p, exp in prompts:
            item = models.DatasetItem(
                dataset_id=ds.id,
                prompt=p,
                expected_output=exp,
                evaluation_type="qa",
                difficulty="easy"
            )
            db.add(item)
        db.commit()
        print("  -> Added 5 simple test items.")

        # 2. Register reliable model (GPT-4o-mini is fast and cheap)
        print("\n[2] Registering AI System...")
        sys_model = models.AISystem(
            name="GPT-4o Mini (Live Verif)",
            model_type="openrouter",
            provider="OpenAI",
            tier="Mid-tier",
            api_endpoint="openai/gpt-4o-mini",
            config_json="{}"
        )
        db.add(sys_model)
        db.commit()
        db.refresh(sys_model)
        print(f"  -> Created System ID: {sys_model.id} [{sys_model.api_endpoint}]")

        # 3. Create a Run
        print("\n[3] Triggering Real Evaluation Run...")
        run = models.EvaluationRun(
            dataset_id=ds.id,
            system_id=sys_model.id,
            status="pending"
        )
        db.add(run)
        db.commit()
        db.refresh(run)
        print(f"  -> Created Run ID: {run.id}, Status: {run.status}")

        # Execute
        print(f"  -> Executing run_evaluation() for Run {run.id}...\n")
        run_evaluation(db, run)

        db.refresh(run)
        print("\n[4] Run Completed!")
        print(f"  -> Final Status: {run.status}")
        print(f"  -> Accuracy: {run.avg_accuracy}")
        print(f"  -> Hallucination Rate: {run.hallucination_rate}")
        print(f"  -> Avg Latency: {run.avg_latency_ms}ms")

        # Fetch traces to prove they are in DB
        traces = db.query(models.EvaluationResult).filter(models.EvaluationResult.run_id == run.id).all()
        print(f"\n[5] Verifying Stored Traces ({len(traces)} found)")
        for t in traces:
            print("-" * 50)
            print(f"  Item {t.item_id} Prompt: '{t.prompt}'")
            print(f"  Expected: '{t.expected_output}'")
            print(f"  Status: {t.status}")
            print(f"  Raw Model Response: '{t.response}'")
            print(f"  Latency: {t.latency_ms:.1f} ms | Tokens usage: {t.token_usage}")
            print(f"  Cost: ${t.token_cost}")
            print(f"  Accuracy Score: {t.accuracy_score}/10")
            print(f"  Hallucinated: {t.hallucination_flag}")
            print(f"  Judge Response Saved: {bool(t.judge_response)}")

        print("\n====== VERIFICATION COMPLETE ======")
        
    finally:
        db.close()

if __name__ == "__main__":
    run_live_test()
