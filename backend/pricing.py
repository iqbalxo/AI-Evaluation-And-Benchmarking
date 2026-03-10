"""
Pricing configuration for token costs.

All costs are represented as cost per 1M tokens in USD.
Since most OpenRouter models blend input/output pricing or have separate pricing,
we store a blended approximation per token, or exact input/output if needed.
For simplicity in this engine, we'll map blended average prices per 1 token.
"""

# Prices as $ per 1M tokens (blended average for simplicity, or specific if known)
# Note: True precision requires distinguishing prompt vs completion tokens,
# but passing the total usage is acceptable for this level of the benchmark.
MODEL_PRICING_PER_1M = {
    # OpenAI
    "openai/gpt-4o": 10.00,        # Blended ~$5 IN / $15 OUT
    "openai/gpt-4o-mini": 0.30,   # Blended ~$0.15 IN / $0.60 OUT
    
    # Anthropic
    "anthropic/claude-3-5-sonnet": 9.00,  # ~$3 IN / $15 OUT
    "anthropic/claude-3-haiku": 0.75,     # ~$0.25 IN / $1.25 OUT
    
    # Google
    "google/gemini-1.5-pro": 7.00,
    "google/gemini-1.5-flash": 0.50,
    
    # Meta / Open Source
    "meta-llama/llama-3.1-70b-instruct": 0.70,
    "meta-llama/llama-3.1-8b-instruct": 0.10,
    
    # OpenRouter free tier
    "openrouter/free": 0.0,
}

def calculate_cost(model_id: str, total_tokens: int) -> float | None:
    """
    Calculate the total cost for a given model and token usage.
    Returns None if pricing is unavailable for the model.
    """
    if not model_id or total_tokens is None:
        return None
        
    # Attempt to normalize model ID if it contains extras
    base_model = model_id.lower().strip()
    
    if base_model in MODEL_PRICING_PER_1M:
        price_per_1m = MODEL_PRICING_PER_1M[base_model]
        return round((total_tokens / 1_000_000.0) * price_per_1m, 6)
        
    # Catch-all for free models
    if "free" in base_model:
        return 0.0
        
    return None
