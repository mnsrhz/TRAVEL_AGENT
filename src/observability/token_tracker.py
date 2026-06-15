from __future__ import annotations


def estimate_tokens(text: str) -> int:
    if not text or not text.strip():
        return 0
    return max(1, len(text.split()) * 2)


def token_budget_status(token_count: int, budget: int = 100_000) -> dict[str, float | bool | int]:
    if budget <= 0:
        return {
            "used": token_count,
            "budget": budget,
            "ratio": 1.0,
            "should_pause": True,
        }
    ratio = token_count / budget
    return {
        "used": token_count,
        "budget": budget,
        "ratio": ratio,
        "should_pause": ratio >= 0.95,
    }
