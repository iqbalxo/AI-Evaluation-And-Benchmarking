import asyncio
import httpx
import sqlite3
import json

DB_PATH = 'eval_platform.db'

async def verify():
    # TEST 1: dataset upload
    print("--- TEST 1: DATASET UPLOAD ---")
    csv_content = b"prompt,expected_output\nWhat is 2+2?,4\nCapital of France?,Paris\nWho wrote Hamlet?,Shakespeare\nWhat is 10*3?,30\nTranslate hello to French,bonjour\n"
    files = {"file": ("test_verify.csv", csv_content, "text/csv")}
    
    async with httpx.AsyncClient(base_url="http://localhost:8000") as client:
        try:
            resp = await client.post("/api/datasets/upload", files=files)
            if resp.status_code != 200:
                print("Failed to upload dataset:", resp.text)
                return
            dataset = resp.json()
            dataset_id = dataset["id"]
            print(f"Dataset stored correctly with ID: {dataset_id}")
            print(f"Dataset name: {dataset['name']}, items: {dataset['item_count']}")
            if dataset['item_count'] != 5:
                print("ERROR: Expected 5 items, got", dataset['item_count'])
                
            # Verify it appears in the list
            list_resp = await client.get("/api/datasets/")
            ds_names = [d["name"] for d in list_resp.json()]
            if dataset["name"] in ds_names:
                print(f"Dataset '{dataset['name']}' appears in dataset list.")
            else:
                print(f"ERROR: Dataset not found in list.")
                
        except Exception as e:
            print("Error connecting to server:", e)
            print("Please ensure the FastAPI server is running on port 8000!")
            return

    # TEST 2 & 3: Real Model Execution & Cost Tracking
    print("\n--- TEST 2 & 3: MODEL EXECUTION & COST TRACKING ---")
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    # Get models from DB
    c.execute("SELECT id, name, api_endpoint FROM ai_systems")
    systems = c.fetchall()
    
    target_models = ['gpt-4o-mini', 'claude-3-haiku', 'gemini-1.5-flash']
    run_ids = []
    
    async with httpx.AsyncClient(base_url="http://localhost:8000", timeout=60.0) as client:
        for m in target_models:
            sys_id = None
            for sys in systems:
                name = sys['name'].lower()
                if m in name or (sys['api_endpoint'] and m in sys['api_endpoint'].lower()):
                    sys_id = sys['id']
                    break
            
            if not sys_id:
                print(f"Model {m} not found in database. Trying to add it...")
                payload = {
                    "name": m.title(),
                    "model_type": "openrouter",
                    "provider": m.split('-')[0] if '-' in m else m,
                    "tier": "Premium",
                    "api_endpoint": f"openai/{m}" if m.startswith("gpt") else f"anthropic/{m}" if m.startswith("claude") else f"google/{m}"
                }
                res = await client.post("/api/systems/", json=payload)
                sys_id = res.json()["id"]
                print(f"Added {m} dynamically.")
                
            print(f"Triggering evaluation run for {m}...")
            run_payload = {
                "system_id": sys_id,
                "dataset_id": dataset_id
            }
            res = await client.post("/api/evaluations/run", json=run_payload)
            if res.status_code == 200:
                run_id = res.json()["id"]
                run_ids.append(run_id)
                print(f"Run {run_id} triggered. Waiting for completion...")
                while True:
                    await asyncio.sleep(2)
                    status_res = await client.get(f"/api/evaluations/runs/{run_id}")
                    if status_res.status_code != 200:
                        print("Error checking status:", status_res.text)
                        break
                    
                    if status_res.json().get("status") in ["completed", "failed"]:
                        run_data = status_res.json()
                        print(f"Run {run_id} ({m}) finished with status: {run_data['status']}")
                        print(f"  Avg Latency: {run_data.get('avg_latency_ms')} ms")
                        print(f"  Avg Token Usage: {run_data.get('avg_token_usage')}")
                        print(f"  Total Cost: ${run_data.get('total_cost')}")
                        break
            else:
                print(f"Failed to trigger run for {m}: {res.text}")

    print("\n--- TEST 4: DASHBOARD AGGREGATION ---")
    async with httpx.AsyncClient(base_url="http://localhost:8000") as client:
        if run_ids:
            exp_payload = {
                "name": "Production Features Verif",
                "description": "Integration tests",
                "run_ids": run_ids
            }
            res = await client.post("/api/experiments/", json=exp_payload)
            exp_id = res.json()["id"]
            
            comp_res = await client.get(f"/api/experiments/{exp_id}/compare")
            data = comp_res.json()
            for r in data["runs"]:
                print(f"Dashboard Aggregation for Run {r['id']}:")
                print(f"  System: {r['system_name']}")
                print(f"  Accuracy: {r['avg_accuracy']}")
                print(f"  Hallucination Rate: {r['hallucination_rate']}%")
                print(f"  Tokens: {r['avg_token_usage']}")
                print(f"  Success/Fail: {r['successful_runs']} / {r['failed_runs']}")
        else:
            print("No runs to aggregate.")

    print("\n--- TEST 5: DATABASE VALIDATION ---")
    if run_ids:
        r_ids = ",".join(map(str, run_ids))
        print("Runs Table Examples:")
        c.execute(f"SELECT id, system_id, dataset_id, status, avg_token_usage, total_cost, successful_runs, failed_runs FROM evaluation_runs WHERE id IN ({r_ids})")
        for row in c.fetchall():
            print(dict(row))
            
        print("\nResults Table (Tokens/Cost/Latency) Examples:")
        c.execute(f"SELECT id, run_id, model_name, status, latency_ms, token_usage, token_cost FROM evaluation_results WHERE run_id IN ({r_ids}) LIMIT 5")
        for row in c.fetchall():
            print(dict(row))
    
    conn.close()

if __name__ == "__main__":
    asyncio.run(verify())
