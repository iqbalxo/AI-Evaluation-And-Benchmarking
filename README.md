# AI Evaluation & Benchmarking Platform

An automated framework for evaluating and comparing large language models on custom datasets. Features include LLM-as-a-judge scoring for accuracy, hallucination detection, relevance, and latency metrics tracking.

## Model Comparison

This table showcases a baseline evaluation across different models integrated via OpenRouter. These metrics are evaluated against our `Production Validation Dataset` (focusing on logic, math, translation, and QA prompts).

| Model | Avg Accuracy (1-10) | Latency (ms) | Hallucination Rate | Relevance Score (0-10) | Total Token Cost |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Gemini 2.5 Pro** | 1.42 | 0.0 | 100.0% | 1.06 | $0.141 |
| **GPT-4o Mini** | 1.56 | 0.0 | 100.0% | 1.14 | $0.128 |
| **Llama 3 8B (Free)** | 1.30 | 0.0 | 100.0% | 1.16 | $0.080 |

*(Note: These values were captured automatically from our most recent experiment sequence `Production Validation 1.0`. Abnormally low performance can indicate upstream API rejections limits or invalid keys at the time of the test run.)*

## Application Interface

![Dashboard Screenshot](dashboard.png)
