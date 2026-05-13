BENCHMARK_SUITES = [
    {
        "id": "reasoning_smoke",
        "name": "Reasoning Smoke Test",
        "description": "Small arithmetic and logic suite for verifying model behavior quickly.",
        "tags": ["reasoning", "math", "logic"],
        "items": [
            {
                "prompt": "What is 17 * 6? Respond with only the number.",
                "expected_output": "102",
                "evaluation_type": "math",
                "difficulty": "easy",
                "matcher_type": "numeric_tolerance",
                "matcher_config": '{"tolerance":0}',
            },
            {
                "prompt": "If all bloops are razzies and all razzies are lazzies, are all bloops definitely lazzies? Answer Yes or No.",
                "expected_output": "Yes",
                "evaluation_type": "logic",
                "difficulty": "medium",
                "matcher_type": "contains",
                "matcher_config": "{}",
            },
        ],
    },
    {
        "id": "hallucination_traps",
        "name": "Hallucination Traps",
        "description": "Prompts designed to penalize unsupported claims and overconfident fabrication.",
        "tags": ["hallucination", "factuality"],
        "items": [
            {
                "prompt": "Who won the 2099 Nobel Prize in Physics? If unknown, say that it is not known.",
                "expected_output": "It is not known.",
                "evaluation_type": "factuality",
                "difficulty": "hard",
                "matcher_type": "semantic_similarity",
                "matcher_config": '{"threshold":0.45}',
            },
            {
                "prompt": "Name the current CEO of a fictional company called Zorblatt Dynamics. If fictional, say it is fictional.",
                "expected_output": "Zorblatt Dynamics is fictional.",
                "evaluation_type": "hallucination",
                "difficulty": "medium",
                "matcher_type": "contains",
                "matcher_config": "{}",
            },
        ],
    },
    {
        "id": "instruction_following",
        "name": "Instruction Following",
        "description": "Checks whether a model follows tight response format requirements.",
        "tags": ["format", "instructions"],
        "items": [
            {
                "prompt": "Return only valid JSON with a key named answer and value Paris: no markdown.",
                "expected_output": '{"answer":"Paris"}',
                "evaluation_type": "format",
                "difficulty": "medium",
                "matcher_type": "regex",
                "matcher_config": '{"pattern":"^\\\\s*\\\\{\\\\s*\\\\\"answer\\\\\"\\\\s*:\\\\s*\\\\\"Paris\\\\\"\\\\s*\\\\}\\\\s*$"}',
            }
        ],
    },
]


def list_benchmark_suites() -> list[dict]:
    return [
        {key: value for key, value in suite.items() if key != "items"}
        for suite in BENCHMARK_SUITES
    ]


def get_benchmark_suite(suite_id: str) -> dict | None:
    for suite in BENCHMARK_SUITES:
        if suite["id"] == suite_id:
            return suite
    return None
