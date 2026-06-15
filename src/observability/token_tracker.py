def estimate_tokens(text: str) -> int:
    if not text:
        return 0
    return max(1, len(text.split()) * 2)


def token_budget_status(token_count: int, budget: int = 100_000) -> dict[str, float | bool | int]:
    ratio = token_count / budget
    return {
        "used": token_count,
        "budget": budget,
        "ratio": ratio,
        "should_pause": ratio >= 0.95,
    }
