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
            return _run_fallback(
                state=state,
                logger=logger,
                tool_name=tool_name,
                fallback_call=fallback_call,
                input_summary=input_summary,
                source_error=message,
                action="used_demo_fallback",
                tool_calls_used=0,
            )
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
            return _run_fallback(
                state=state,
                logger=logger,
                tool_name=tool_name,
                fallback_call=fallback_call,
                input_summary=input_summary,
                source_error=message,
                action="fallback_after_live_failure",
                tool_calls_used=1,
            )
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


def _run_fallback(
    *,
    state: TravelState,
    logger: TraceLogger,
    tool_name: str,
    fallback_call: Callable[[], T],
    input_summary: str,
    source_error: str,
    action: str,
    tool_calls_used: int,
) -> T:
    try:
        result = fallback_call()
    except Exception as exc:
        message = f"{tool_name} fallback failed after {source_error}: {exc}"
        state.current_state = WorkflowState.FAILED
        logger.log(
            node=tool_name,
            event_type="tool_failed",
            action="fallback_failure",
            input_summary=input_summary,
            output_summary="Fallback data generation failed",
            status="error",
            tool_calls_used=tool_calls_used,
            error=message,
        )
        raise ToolExecutionError(message) from exc

    logger.log(
        node=tool_name,
        event_type="tool_completed",
        action=action,
        input_summary=input_summary,
        output_summary=f"{tool_name} returned labeled fallback data",
        status="fallback",
        tool_calls_used=tool_calls_used,
        error=source_error,
    )
    return result
