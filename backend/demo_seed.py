import json
from datetime import datetime, timezone

from database import Base, engine, SessionLocal
from models import AISystem, EvaluationDataset, DatasetItem
from services.benchmark_suites import get_benchmark_suite
from services.migrations import run_migrations


def main() -> None:
    Base.metadata.create_all(bind=engine)
    run_migrations(engine)
    db = SessionLocal()
    try:
        suite = get_benchmark_suite("reasoning_smoke")
        if not suite:
            raise RuntimeError("reasoning_smoke benchmark suite is missing")

        dataset = EvaluationDataset(
            name="Demo Reasoning Benchmark",
            description="Seeded benchmark for portfolio demos.",
            tags=json.dumps(["demo", "reasoning"]),
            schema_version=1,
            benchmark_suite=suite["id"],
        )
        db.add(dataset)
        db.commit()
        db.refresh(dataset)

        for item in suite["items"]:
            db.add(DatasetItem(dataset_id=dataset.id, **item))

        systems = [
            AISystem(
                name="GPT-4o Mini Demo",
                model_type="openrouter",
                provider="OpenAI",
                tier="Balanced",
                api_endpoint="openai/gpt-4o-mini",
                config_json='{"temperature":0,"max_tokens":128}',
            ),
            AISystem(
                name="Gemini Flash Demo",
                model_type="openrouter",
                provider="Google",
                tier="Balanced",
                api_endpoint="google/gemini-1.5-flash",
                config_json='{"temperature":0,"max_tokens":128}',
            ),
        ]
        for system in systems:
            db.add(system)
        db.commit()
        print(f"Seeded demo dataset {dataset.id} and {len(systems)} systems at {datetime.now(timezone.utc).isoformat()}.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
