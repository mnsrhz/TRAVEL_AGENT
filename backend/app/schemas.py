from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1)


class ApprovalRequest(BaseModel):
    gate: str = Field(..., min_length=1)


class SessionResponse(BaseModel):
    session_id: str
    state: dict[str, Any]
    chat_history: list[dict[str, str]]


class ChatResponse(SessionResponse):
    reply: str
    ready: bool

