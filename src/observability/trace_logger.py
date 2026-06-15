from __future__ import annotations

import json
from numbers import Integral

from src.state.travel_state import TraceEvent, TravelState


class TraceLogger:
    def __init__(self, state: TravelState):
        self.state = state

    def log(
        self,
        *,
        node: str,
        event_type: str,
        action: str,
        input_summary: str,
        output_summary: str,
        status: str,
        decision: str | None = None,
        tokens_used: int = 0,
        tool_calls_used: int = 0,
        loop_count: int = 0,
        max_loop_count: int = 0,
        error: str | None = None,
    ) -> TraceEvent:
        tokens_used = _non_negative_int(tokens_used)
        tool_calls_used = _non_negative_int(tool_calls_used)
        event = TraceEvent(
            step=len(self.state.trace_events) + 1,
            timestamp=self.state.now(),
            state=self.state.current_state,
            node=node,
            event_type=event_type,
            action=action,
            input_summary=input_summary,
            output_summary=output_summary,
            decision=decision,
            tokens_used=tokens_used,
            tool_calls_used=tool_calls_used,
            loop_count=loop_count,
            max_loop_count=max_loop_count,
            status=status,
            error=error,
        )
        self.state.trace_events.append(event)
        self.state.token_count += tokens_used
        self.state.tool_call_count += tool_calls_used
        if error:
            self.state.errors.append(error)
        return event

    def to_json(self) -> str:
        return json.dumps([event.to_dict() for event in self.state.trace_events], indent=2)


def _non_negative_int(value: int) -> int:
    if not isinstance(value, Integral):
        return 0
    return max(0, int(value))
