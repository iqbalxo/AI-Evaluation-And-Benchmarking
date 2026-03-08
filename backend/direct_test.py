import os
import sys
import httpx
from dotenv import load_dotenv

load_dotenv()

def test():
    api_key = os.getenv("OPENROUTER_API_KEY", "")
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "openrouter/free",
        "messages": [{"role": "user", "content": "hello"}]
    }
    with httpx.Client() as client:
        resp = client.post(url, headers=headers, json=payload)
        with open("api_err.txt", "w") as f:
            f.write(f"Status: {resp.status_code}\n")
            f.write(resp.text)

if __name__ == "__main__":
    test()
