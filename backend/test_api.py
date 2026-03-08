import os
import sys
from dotenv import load_dotenv

# load dotenv
load_dotenv()

# Add backend directory to path
sys.path.append("d:/iqbal/github projects/AI Evaluation & Benchmarking Platform/backend")

from services.evaluation_engine import _get_openrouter_response

def test():
    try:
        response, latency = _get_openrouter_response("Say exactly 'hello'", "google/gemma-2-9b-it:free")
        print(f"Response: {response}")
        print(f"Latency: {latency}")
    except Exception as e:
        print(f"Test failed: {e}")

if __name__ == "__main__":
    test()
