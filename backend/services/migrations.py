from sqlalchemy import inspect, text


MIGRATIONS = {
    "evaluation_datasets": {
        "tags": "TEXT DEFAULT '[]'",
        "schema_version": "INTEGER DEFAULT 1",
        "benchmark_suite": "VARCHAR(100)",
    },
    "dataset_items": {
        "matcher_type": "VARCHAR(50) DEFAULT 'judge'",
        "matcher_config": "TEXT DEFAULT '{}'",
    },
    "evaluation_runs": {
        "judge_model": "VARCHAR(255)",
        "judge_rubric": "VARCHAR(100) DEFAULT 'general_quality'",
        "model_config_json": "TEXT DEFAULT '{}'",
        "progress_current": "INTEGER DEFAULT 0",
        "progress_total": "INTEGER DEFAULT 0",
        "cancellation_requested": "BOOLEAN DEFAULT 0",
        "baseline_run_id": "INTEGER",
        "thresholds_json": "TEXT DEFAULT '{}'",
        "trace_id": "VARCHAR(64)",
    },
    "evaluation_results": {
        "judge_model": "VARCHAR(255)",
        "judge_rubric": "VARCHAR(100)",
        "judge_confidence": "FLOAT",
        "judge_explanation": "TEXT",
        "matcher_type": "VARCHAR(50)",
        "matcher_passed": "BOOLEAN",
        "matcher_score": "FLOAT",
        "matcher_reason": "TEXT",
        "failure_category": "VARCHAR(100)",
        "trace_id": "VARCHAR(64)",
        "model_temperature": "FLOAT",
        "model_timeout_ms": "FLOAT",
    },
}


def run_migrations(engine) -> None:
    inspector = inspect(engine)
    with engine.begin() as conn:
        for table_name, columns in MIGRATIONS.items():
            if not inspector.has_table(table_name):
                continue
            existing = {column["name"] for column in inspector.get_columns(table_name)}
            for column_name, ddl in columns.items():
                if column_name not in existing:
                    conn.execute(text(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {ddl}"))
