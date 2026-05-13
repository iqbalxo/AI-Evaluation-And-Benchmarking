# Case Study: Cost-Aware LLM Evaluation

## Goal

Select a model for a production LLM workflow by comparing quality, hallucination risk, latency, and cost rather than relying on one-off prompt testing.

## Method

1. Create benchmark datasets from the curated packs:
   - `reasoning_smoke`
   - `hallucination_traps`
   - `instruction_following`
2. Register balanced OpenRouter systems:
   - `openai/gpt-4o-mini`
   - `google/gemini-1.5-flash`
   - `meta-llama/llama-3.1-70b-instruct`
3. Run each system with deterministic config:
   - `temperature: 0`
   - fixed timeout
   - rubric-specific judge settings
4. Compare the runs through:
   - scalar metrics
   - trace inspection
   - deterministic answer matchers
   - blind pairwise judging
   - regression reports

## What To Look For

- A cheaper model can be promoted if accuracy and relevance stay within the accepted regression threshold.
- A model with strong average accuracy can still be rejected if hallucination traps show unsupported claims.
- Pairwise judging is useful when scalar scores are close but responses differ in conciseness or instruction following.
- Cost-per-correct-answer is often more useful than raw token cost.

## Portfolio Talking Points

- The platform separates model-under-test calls from judge calls.
- Every trace stores prompt, response, judge rubric, judge model, confidence, explanation, matcher result, latency, tokens, and cost.
- Failed items are isolated from aggregate metrics so provider instability does not corrupt quality reporting.
- The workflow mirrors real LLM release gates: benchmark, compare, inspect, regress, and decide.
