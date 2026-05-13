from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class RubricDimension:
    name: str
    description: str
    scale: str = "0-10"


@dataclass(frozen=True)
class EvaluationRubric:
    id: str
    name: str
    description: str
    dimensions: tuple[RubricDimension, ...]


DEFAULT_RUBRIC_ID = "general_quality"


RUBRICS: tuple[EvaluationRubric, ...] = (
    EvaluationRubric(
        id="general_quality",
        name="General Quality",
        description="Balanced rubric for factual QA, short-form reasoning, and instruction following.",
        dimensions=(
            RubricDimension("accuracy_score", "Factual correctness versus the expected answer."),
            RubricDimension("relevance_score", "How directly the response answers the prompt."),
            RubricDimension("instruction_following", "Whether the response follows formatting and scope instructions."),
            RubricDimension("conciseness", "Whether the response is appropriately concise."),
        ),
    ),
    EvaluationRubric(
        id="hallucination_focus",
        name="Hallucination Focus",
        description="Strict rubric for unsupported claims, fabricated facts, and misleading elaboration.",
        dimensions=(
            RubricDimension("accuracy_score", "Correctness of the final answer."),
            RubricDimension("factuality", "Whether every material claim is supported by the expected answer or prompt."),
            RubricDimension("hallucination_risk", "Risk that the answer introduces false or unverifiable information."),
            RubricDimension("relevance_score", "Directness and topical alignment."),
        ),
    ),
    EvaluationRubric(
        id="instruction_following",
        name="Instruction Following",
        description="Rubric for formatting constraints, refusal behavior, and task adherence.",
        dimensions=(
            RubricDimension("accuracy_score", "Correctness of the answer under the user constraints."),
            RubricDimension("instruction_following", "Compliance with requested format and boundaries."),
            RubricDimension("safety", "Appropriate refusal or safe handling when relevant."),
            RubricDimension("relevance_score", "Whether the answer stays on task."),
        ),
    ),
)


def list_rubrics() -> list[dict]:
    return [
        {
            **asdict(rubric),
            "dimensions": [asdict(dimension) for dimension in rubric.dimensions],
        }
        for rubric in RUBRICS
    ]


def get_rubric(rubric_id: str | None) -> EvaluationRubric:
    selected = (rubric_id or DEFAULT_RUBRIC_ID).strip().lower()
    for rubric in RUBRICS:
        if rubric.id == selected:
            return rubric
    return next(rubric for rubric in RUBRICS if rubric.id == DEFAULT_RUBRIC_ID)


def format_rubric_for_prompt(rubric: EvaluationRubric) -> str:
    lines = [f"Rubric: {rubric.name}", rubric.description, "Dimensions:"]
    for dimension in rubric.dimensions:
        lines.append(f"- {dimension.name} ({dimension.scale}): {dimension.description}")
    return "\n".join(lines)
