import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(BASE_DIR, 'eval_platform.db')

def migrate_tiers():
    print(f"Migrating database tiers at {db_path}...")
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    # AI Systems table
    c.execute("PRAGMA table_info(ai_systems)")
    columns_sys = [row[1] for row in c.fetchall()]
    sys_cols = [
        ("provider", "VARCHAR(100)"),
        ("tier", "VARCHAR(50)")
    ]
    for col_name, col_type in sys_cols:
        if col_name not in columns_sys:
            print(f"Adding column {col_name} to ai_systems...")
            try:
                c.execute(f"ALTER TABLE ai_systems ADD COLUMN {col_name} {col_type}")
            except sqlite3.OperationalError as e:
                print(f"Error adding {col_name} to ai_systems: {e}")

    # Evaluation Runs table
    c.execute("PRAGMA table_info(evaluation_runs)")
    columns_run = [row[1] for row in c.fetchall()]
    run_cols = [
        ("system_name", "VARCHAR(255)"),
        ("provider", "VARCHAR(100)"),
        ("tier", "VARCHAR(50)")
    ]
    for col_name, col_type in run_cols:
        if col_name not in columns_run:
            print(f"Adding column {col_name} to evaluation_runs...")
            try:
                c.execute(f"ALTER TABLE evaluation_runs ADD COLUMN {col_name} {col_type}")
            except sqlite3.OperationalError as e:
                print(f"Error adding {col_name} to evaluation_runs: {e}")
                
    conn.commit()
    conn.close()
    print("Tier migration finished successfully.")

if __name__ == "__main__":
    migrate_tiers()
