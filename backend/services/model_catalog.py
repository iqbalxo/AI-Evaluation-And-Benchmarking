from dataclasses import asdict, dataclass
from typing import Literal


ModelQuality = Literal["balanced", "premium", "budget", "free"]
CostProfile = Literal["low", "medium", "high", "free"]


@dataclass(frozen=True)
class ModelPreset:
    id: str
    name: str
    provider: str
    tier: str
    quality: ModelQuality
    cost_profile: CostProfile
    recommended_for: str


DEFAULT_MODEL_PRESET_ID = "openai/gpt-4o-mini"
DEFAULT_JUDGE_MODEL_ID = "openai/gpt-4o-mini"


MODEL_PRESETS: tuple[ModelPreset, ...] = (
    ModelPreset(
        id="openai/gpt-4o-mini",
        name="GPT-4o Mini",
        provider="OpenAI",
        tier="Balanced",
        quality="balanced",
        cost_profile="low",
        recommended_for="Default benchmark runs and LLM judge scoring.",
    ),
    ModelPreset(
        id="google/gemini-1.5-flash",
        name="Gemini 1.5 Flash",
        provider="Google",
        tier="Balanced",
        quality="balanced",
        cost_profile="low",
        recommended_for="Fast, affordable comparison runs.",
    ),
    ModelPreset(
        id="meta-llama/llama-3.1-70b-instruct",
        name="Llama 3.1 70B Instruct",
        provider="Meta",
        tier="Balanced",
        quality="balanced",
        cost_profile="medium",
        recommended_for="Open model quality comparisons.",
    ),
    ModelPreset(
        id="openai/gpt-4o",
        name="GPT-4o",
        provider="OpenAI",
        tier="Premium",
        quality="premium",
        cost_profile="high",
        recommended_for="Higher quality baselines for smaller benchmark suites.",
    ),
    ModelPreset(
        id="anthropic/claude-3-5-sonnet",
        name="Claude 3.5 Sonnet",
        provider="Anthropic",
        tier="Premium",
        quality="premium",
        cost_profile="high",
        recommended_for="Reasoning-heavy benchmark comparisons.",
    ),
    ModelPreset(
        id="meta-llama/llama-3.1-8b-instruct",
        name="Llama 3.1 8B Instruct",
        provider="Meta",
        tier="Budget",
        quality="budget",
        cost_profile="low",
        recommended_for="Low-cost sanity checks before running larger models.",
    ),
    ModelPreset(
        id="openrouter/free",
        name="OpenRouter Free",
        provider="OpenRouter",
        tier="Free",
        quality="free",
        cost_profile="free",
        recommended_for="Connectivity checks when paid routing is unavailable.",
    ),
)


def list_model_presets() -> list[dict[str, str]]:
    return [asdict(preset) for preset in MODEL_PRESETS]


def get_model_preset(model_id: str) -> ModelPreset | None:
    normalized = model_id.strip().lower()
    for preset in MODEL_PRESETS:
        if preset.id == normalized:
            return preset
    return None
