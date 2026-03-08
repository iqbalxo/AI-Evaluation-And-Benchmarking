import time
import requests
import sys

BASE_URL = "http://localhost:8000/api"

def main():
    print("Testing connection to backend...")
    try:
        requests.get("http://localhost:8000/")
    except requests.ConnectionError:
        print("Backend is not running.")
        sys.exit(1)

    print("Creating dataset...")
    ds_resp = requests.post(f"{BASE_URL}/datasets/", json={
        "name": "Debug Dataset",
        "description": "Small test suite to debug OpenRouter."
    })
    dataset_id = ds_resp.json()["id"]

    print("Adding items to dataset...")
    items = [
        {"prompt": "Say exactly 'hello'", "expected_output": "hello", "evaluation_type": "text", "difficulty": "easy"},
        {"prompt": "What is 2+2?", "expected_output": "4", "evaluation_type": "math", "difficulty": "easy"},
        {"prompt": "Capital of France?", "expected_output": "Paris", "evaluation_type": "qa", "difficulty": "easy"}
    ]
    requests.post(f"{BASE_URL}/datasets/{dataset_id}/items/batch", json=items)

    print("Registering AI System (OpenRouter Free/Auto)...")
    m = {"name": "OpenRouter Free Auto (Debug)", "model_type": "openrouter", "api_endpoint": "openrouter/free", "config_json": "{}"}
    sys_resp = requests.post(f"{BASE_URL}/systems/", json=m)
    system_id = sys_resp.json()["id"]

    print("Starting evaluation...")
    run_resp = requests.post(f"{BASE_URL}/evaluations/run", json={"system_id": system_id, "dataset_id": dataset_id})
    run_id = run_resp.json()["id"]

    print("Waiting for evaluation to complete...", end="", flush=True)
    all_done = False
    while not all_done:
        resp = requests.get(f"{BASE_URL}/evaluations/runs/{run_id}")
        data = resp.json()
        if data.get("status") in ["completed", "failed"]:
            all_done = True
        else:
            print(".", end="", flush=True)
            time.sleep(2)
            
    print(f"\nEvaluation finished with status: {data.get('status')}")
    
    # Fetch details
    detail_resp = requests.get(f"{BASE_URL}/evaluations/runs/{run_id}")
    detail = detail_resp.json()
    
    print("\n--- RESULTS ---")
    for res in detail.get("results", []):
        print(f"Prompt: ID {res['item_id']}")
        print(f"Raw Response: {res['response']}")
        print(f"Latency: {res['latency_ms']} ms")
        print(f"Cost: ${res['token_cost']}")
        print(f"Scores -> Accuracy: {res['accuracy_score']}, Hallucination: {res['hallucination_flag']}, Relevance: {res['relevance_score']}")
        print("-" * 20)
        
    print("\nFinal Run Metrics:")
    print(f"Avg Accuracy: {detail.get('avg_accuracy')}")
    print(f"Avg Latency: {detail.get('avg_latency_ms')}")
    print(f"Hallucination Rate: {detail.get('hallucination_rate')}")

if __name__ == "__main__":
    main()
