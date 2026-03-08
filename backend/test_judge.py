import os
import sys
from dotenv import load_dotenv

load_dotenv()
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.llm_judge import judge_response

# 10 trivial gold-standard prompts
TEST_CASES = [
    {
        "prompt": "What is 2+2?",
        "expected": "4",
        "response": "The sum of 2 and 2 is 4. This is a basic arithmetic operation."
    },
    {
        "prompt": "Capital of France?",
        "expected": "Paris",
        "response": "The capital of France is Paris."
    },
    {
        "prompt": "Who wrote Romeo and Juliet?",
        "expected": "William Shakespeare",
        "response": "William Shakespeare wrote Romeo and Juliet."
    },
    {
        "prompt": "What color is the sky on a clear day?",
        "expected": "Blue",
        "response": "The sky is blue during a clear day due to Rayleigh scattering."
    },
    {
        "prompt": "Is water wet?",
        "expected": "Yes",
        "response": "Water is a liquid that makes things wet."
    },
    # Hallucination test case
    {
        "prompt": "When did the moon landing occur?",
        "expected": "1969",
        "response": "The moon landing occurred in 1969, led by secret aliens from Mars who helped NASA build the rocket."
    },
    # Poor accuracy test case
    {
        "prompt": "What is 10 * 10?",
        "expected": "100",
        "response": "10 times 10 is 50."
    },
    {
        "prompt": "Name the first president of the United States.",
        "expected": "George Washington",
        "response": "George Washington was the first POTUS."
    },
    {
        "prompt": "Is the Earth flat?",
        "expected": "No, it's round / spherical.",
        "response": "No, it is an oblate spheroid."
    },
    {
        "prompt": "How many legs does a spider have?",
        "expected": "8",
        "response": "A spider typically has 8 legs."
    }
]

def run_tests():
    print("Starting Judge Validation Suite...\n")
    for i, test in enumerate(TEST_CASES, 1):
        print(f"--- TEST CASE {i} ---")
        scores = judge_response(test["prompt"], test["response"], test["expected"])
        # No need to print here since judge_response now prints everything
        print("\n\n")

if __name__ == "__main__":
    run_tests()
