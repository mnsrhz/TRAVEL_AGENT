from __future__ import annotations

from collections.abc import Callable
from typing import TypeVar

from src.config.settings import Settings
from src.observability.trace_logger import TraceLogger
from src.state.travel_state import TravelState, WorkflowState

T = TypeVar("T")


class ToolExecutionError(RuntimeError):
    pass


def run_tool_with_policy(
    *,
    state: TravelState,
    settings: Settings,
    tool_name: str,
    required_key: str,
    live_call: Callable[[], T],
    fallback_call: Callable[[], T],
    input_summary: str,
) -> T:
    logger = TraceLogger(state)

    if not settings.has_key(required_key):
        message = f"Missing {required_key} for {tool_name}"
        if settings.allow_demo_fallbacks:
            result = fallback_call()
            logger.log(
                node=tool_name,
                event_type="tool_completed",
                action="used_demo_fallback",
                input_summary=input_summary,
                output_summary=f"{tool_name} returned labeled fallback data",
                status="fallback",
                tool_calls_used=1,
                error=message,
            )
            return result
        state.current_state = WorkflowState.FAILED
        logger.log(
            node=tool_name,
            event_type="tool_failed",
            action="missing_required_key",
            input_summary=input_summary,
            output_summary="Strict mode blocked fallback",
            status="error",
            tool_calls_used=1,
            error=message,
        )
        raise ToolExecutionError(message)

    try:
        result = live_call()
        logger.log(
            node=tool_name,
            event_type="tool_completed",
            action="live_api_call",
            input_summary=input_summary,
            output_summary=f"{tool_name} returned live data",
            status="success",
            tool_calls_used=1,
        )
        return result
    except Exception as exc:
        message = f"{tool_name} failed: {exc}"
        if settings.allow_demo_fallbacks:
            result = fallback_call()
            logger.log(
                node=tool_name,
                event_type="tool_completed",
                action="fallback_after_live_failure",
                input_summary=input_summary,
                output_summary=f"{tool_name} returned labeled fallback data",
                status="fallback",
                tool_calls_used=1,
                error=message,
            )
            return result
        state.current_state = WorkflowState.FAILED
        logger.log(
            node=tool_name,
            event_type="tool_failed",
            action="live_api_failure",
            input_summary=input_summary,
            output_summary="Strict mode blocked fallback",
            status="error",
            tool_calls_used=1,
            error=message,
        )
        raise ToolExecutionError(message) from exc
