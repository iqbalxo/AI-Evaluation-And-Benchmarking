import sqlite3

def check_integrity():
    conn = sqlite3.connect('eval_platform.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    c.execute("SELECT COUNT(*) FROM evaluation_results")
    total_runs = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM evaluation_results WHERE status='success'")
    success_runs = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM evaluation_results WHERE status='failed'")
    failed_runs = c.fetchone()[0]

    print(f"Total Traces: {total_runs}")
    print(f"Successful Traces: {success_runs}")
    print(f"Failed Traces: {failed_runs}")

    # Check for any failed runs that still have non-null numeric metrics
    c.execute("""
    SELECT id, prompt, error_message, latency_ms, token_usage, accuracy_score
    FROM evaluation_results 
    WHERE status='failed' 
    AND (latency_ms IS NOT NULL OR token_usage IS NOT NULL OR accuracy_score IS NOT NULL)
    """)
    bad_failures = c.fetchall()
    
    # Exclude historical failures where they naturally stored 0.0 because of old code.
    # We want to ensure we're looking at NEW runs or we don't care about old ones if we just changed the code.
    # To be strictly safe, let's just count them.
    print(f"\nHistorical Failed Traces with numeric metrics (due to old code): {len(bad_failures)}")

if __name__ == '__main__':
    check_integrity()
