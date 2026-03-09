import time
import requests
import sys

BASE_URL = "http://localhost:8000/api"

def main():
    print("Testing connection to backend...")
    try:
        requests.get("http://localhost:8000/")
    except requests.ConnectionError:
        print("Backend is not running. Please start the backend server on port 8000.")
        sys.exit(1)

    print("Creating dataset...")
    # 1. Create a dataset
    ds_resp = requests.post(f"{BASE_URL}/datasets/", json={
        "name": "Production Validation Dataset",
        "description": "A small test suite to validate real OpenRouter models."
    })
    if ds_resp.status_code != 200:
        print("Failed to create dataset", ds_resp.json())
        sys.exit(1)
    dataset_id = ds_resp.json()["id"]

    # 2. Add items
    print("Adding items to dataset...")
    items = [
        {
            "prompt": "If all Zords are Fords, and some Fords are Gords, are some Zords definitely Gords? Respond with only Yes or No.",
            "expected_output": "No",
            "evaluation_type": "logic",
            "difficulty": "medium"
        },
        {
            "prompt": "What is 25 * 14? Just output the number.",
            "expected_output": "350",
            "evaluation_type": "math",
            "difficulty": "easy"
        },
        {
            "prompt": "Translate 'hello world' to French.",
            "expected_output": "bonjour le monde",
            "evaluation_type": "translation",
            "difficulty": "easy"
        },
        {
            "prompt": "Who wrote Romeo and Juliet?",
            "expected_output": "William Shakespeare",
            "evaluation_type": "qa",
            "difficulty": "medium"
        },
        {
            "prompt": "What is the capital of Australia?",
            "expected_output": "Canberra",
            "evaluation_type": "qa",
            "difficulty": "medium"
        }
    ]
    
    items_resp = requests.post(f"{BASE_URL}/datasets/{dataset_id}/items/batch", json=items)
    if items_resp.status_code != 200:
        print("Failed to add items", items_resp.json())
        sys.exit(1)

    # 3. Create AI Systems
    print("Registering AI Systems...")
    models = [
        # Premium
        {"name": "GPT-4o", "model_type": "openrouter", "provider": "OpenAI", "tier": "Premium", "api_endpoint": "openai/gpt-4o", "config_json": "{}"},
        {"name": "Claude 3.5 Sonnet", "model_type": "openrouter", "provider": "Anthropic", "tier": "Premium", "api_endpoint": "anthropic/claude-3.5-sonnet", "config_json": "{}"},
        {"name": "Gemini 1.5 Pro", "model_type": "openrouter", "provider": "Google", "tier": "Premium", "api_endpoint": "google/gemini-1.5-pro", "config_json": "{}"},
        # Mid-Tier
        {"name": "GPT-4o Mini", "model_type": "openrouter", "provider": "OpenAI", "tier": "Mid-tier", "api_endpoint": "openai/gpt-4o-mini", "config_json": "{}"},
        {"name": "Gemini 1.5 Flash", "model_type": "openrouter", "provider": "Google", "tier": "Mid-tier", "api_endpoint": "google/gemini-1.5-flash", "config_json": "{}"},
        {"name": "Llama 3.1 70B", "model_type": "openrouter", "provider": "Meta", "tier": "Mid-tier", "api_endpoint": "meta-llama/llama-3.1-70b-instruct", "config_json": "{}"},
        # Open / Low-Cost
        {"name": "Llama 3.1 8B", "model_type": "openrouter", "provider": "Meta", "tier": "Open/low-cost", "api_endpoint": "meta-llama/llama-3.1-8b-instruct", "config_json": "{}"},
        {"name": "Mistral Nemo", "model_type": "openrouter", "provider": "Mistral", "tier": "Open/low-cost", "api_endpoint": "mistralai/mistral-nemo", "config_json": "{}"}
    ]
    
    system_ids = []
    for m in models:
        resp = requests.post(f"{BASE_URL}/systems/", json=m)
        if resp.status_code == 200:
            system_ids.append(resp.json()["id"])
        else:
            print("Failed to create system:", m["name"])

    # 4. Trigger Evaluations
    print("Starting evaluations...")
    run_ids = []
    for sid in system_ids:
        resp = requests.post(f"{BASE_URL}/evaluations/run", json={
            "system_id": sid,
            "dataset_id": dataset_id
        })
        if resp.status_code == 200:
            run_ids.append(resp.json()["id"])
        else:
            print(f"Failed to start run for system {sid}", resp.json())

    # 5. Wait for evaluations to finish
    print("Waiting for evaluations to complete...", end="", flush=True)
    all_done = False
    while not all_done:
        all_done = True
        for rid in run_ids:
            resp = requests.get(f"{BASE_URL}/evaluations/runs/{rid}")
            if resp.status_code == 200:
                status = resp.json().get("status")
                if status in ["pending", "running"]:
                    all_done = False
                    break
            else:
                print(f"\nError checking run {rid}")
        if not all_done:
            print(".", end="", flush=True)
            time.sleep(2)
    print("\nEvaluations completed!")

    # 6. Create Experiment
    print("Creating Experiment report...")
    exp_resp = requests.post(f"{BASE_URL}/experiments/", json={
        "name": "Multi-Tier OpenRouter Benchmark",
        "description": "Comprehensive evaluation of 8 LLMs across Premium, Mid-tier, and Open/low-cost tiers.",
        "run_ids": run_ids
    })
    
    if exp_resp.status_code == 200:
        print("Experiment created successfully!")
    else:
        print("Failed to create experiment", exp_resp.json())

    print("\nRun the frontend and navigate to the Experiments tab to view the results.")

if __name__ == "__main__":
    main()
