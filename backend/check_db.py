import sqlite3

def check_results():
    conn = sqlite3.connect('eval_platform.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    print("=== LATEST RUNS ===")
    c.execute("SELECT id, status, started_at, completed_at, avg_accuracy, hallucination_rate, avg_latency_ms FROM evaluation_runs ORDER BY id DESC LIMIT 2")
    for r in c.fetchall():
        print(dict(r))

    print("\n=== LATEST TRACES ===")
    c.execute("SELECT id, run_id, prompt, expected_output, response, latency_ms, token_usage, token_cost, accuracy_score, hallucination_flag, status, error_message FROM evaluation_results ORDER BY id DESC LIMIT 5")
    for r in c.fetchall():
        print(dict(r))

if __name__ == '__main__':
    check_results()
