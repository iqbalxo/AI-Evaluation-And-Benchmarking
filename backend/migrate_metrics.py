import sqlite3

def migrate():
    conn = sqlite3.connect('eval_platform.db')
    c = conn.cursor()
    
    try:
        c.execute("ALTER TABLE evaluation_runs ADD COLUMN avg_token_usage FLOAT;")
        print("Added avg_token_usage")
    except sqlite3.OperationalError:
        print("avg_token_usage already exists")
        
    try:
        c.execute("ALTER TABLE evaluation_runs ADD COLUMN successful_runs INTEGER DEFAULT 0;")
        print("Added successful_runs")
    except sqlite3.OperationalError:
        print("successful_runs already exists")
        
    try:
        c.execute("ALTER TABLE evaluation_runs ADD COLUMN failed_runs INTEGER DEFAULT 0;")
        print("Added failed_runs")
    except sqlite3.OperationalError:
        print("failed_runs already exists")
        
    conn.commit()
    conn.close()
    print("Migration complete")

if __name__ == "__main__":
    migrate()
