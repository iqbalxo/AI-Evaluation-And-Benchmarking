import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(BASE_DIR, 'eval_platform.db')

def migrate():
    print(f"Migrating database at {db_path}...")
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    # We will use PRAGMA table_info to check if columns exist before adding them
    c.execute("PRAGMA table_info(evaluation_results)")
    columns = [row[1] for row in c.fetchall()]
    
    new_columns = [
        ("prompt", "TEXT"),
        ("expected_output", "TEXT"),
        ("model_name", "VARCHAR(255)"),
        ("provider_name", "VARCHAR(255)"),
        ("judge_prompt", "TEXT"),
        ("judge_response", "TEXT"),
        ("token_usage", "INTEGER DEFAULT 0"),
        ("status", "VARCHAR(50) DEFAULT 'success'"),
        ("error_message", "TEXT"),
        ("created_at", "DATETIME DEFAULT CURRENT_TIMESTAMP")
    ]
    
    for col_name, col_type in new_columns:
        if col_name not in columns:
            print(f"Adding column {col_name} to evaluation_results...")
            try:
                c.execute(f"ALTER TABLE evaluation_results ADD COLUMN {col_name} {col_type}")
            except sqlite3.OperationalError as e:
                print(f"Error adding {col_name}: {e}")
        else:
            print(f"Column {col_name} already exists.")
            
    conn.commit()
    conn.close()
    print("Migration finished successfully.")

if __name__ == "__main__":
    migrate()
