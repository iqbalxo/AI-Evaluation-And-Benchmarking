import sqlite3
import pprint
import sys

def check_results():
    conn = sqlite3.connect('eval_platform.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    with open('db_output.txt', 'w', encoding='utf-8') as f:
        f.write("=== LATEST RUNS ===\n")
        c.execute("SELECT id, status, started_at, completed_at, avg_accuracy, hallucination_rate, avg_latency_ms FROM evaluation_runs ORDER BY id DESC LIMIT 2")
        for r in c.fetchall():
            f.write(pprint.pformat(dict(r)) + "\n")

        f.write("\n=== LATEST TRACES ===\n")
        c.execute("SELECT id, run_id, prompt, expected_output, response, latency_ms, token_usage, token_cost, accuracy_score, hallucination_flag, status, error_message FROM evaluation_results ORDER BY id DESC LIMIT 5")
        for r in c.fetchall():
            f.write(pprint.pformat(dict(r)) + "\n")

if __name__ == '__main__':
    check_results()
