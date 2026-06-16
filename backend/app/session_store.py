from __future__ import annotations

import base64
import json
import os
from dataclasses import fields
from pathlib import Path
from threading import Lock
from typing import Any
from uuid import uuid4

from src.state.travel_state import TraceEvent, TravelState, WorkflowState


DEFAULT_ASSISTANT_MESSAGE = (
    "Tell me about the trip you want in plain English. I will ask for anything missing."
)


class SessionNotFoundError(KeyError):
    pass


class SessionStore:
    def __init__(self, storage_dir: Path | None = None) -> None:
        self.storage_dir = storage_dir or Path(
            os.environ.get("TRAVEL_AGENT_SESSION_DIR", "backend/data/sessions")
        )
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self._sessions: dict[str, dict[str, Any]] = {}
        self._lock = Lock()

    def create(self) -> tuple[str, TravelState, list[dict[str, str]]]:
        session_id = uuid4().hex
        state = TravelState()
        chat_history = [{"role": "assistant", "content": DEFAULT_ASSISTANT_MESSAGE}]
        with self._lock:
            self._sessions[session_id] = {"state": state, "chat_history": chat_history}
            self._persist(session_id)
        return session_id, state, chat_history

    def get(self, session_id: str) -> tuple[TravelState, list[dict[str, str]]]:
        with self._lock:
            if session_id not in self._sessions:
                self._load(session_id)
            payload = self._sessions.get(session_id)
            if payload is None:
                raise SessionNotFoundError(session_id)
            return payload["state"], payload["chat_history"]

    def save(self, session_id: str) -> None:
        with self._lock:
            if session_id not in self._sessions:
                raise SessionNotFoundError(session_id)
            self._persist(session_id)

    def _path_for(self, session_id: str) -> Path:
        return self.storage_dir / f"{session_id}.json"

    def _persist(self, session_id: str) -> None:
        payload = self._sessions[session_id]
        data = {
            "session_id": session_id,
            "state": state_to_payload(payload["state"]),
            "chat_history": payload["chat_history"],
        }
        self._path_for(session_id).write_text(json.dumps(data, indent=2), encoding="utf-8")

    def _load(self, session_id: str) -> None:
        path = self._path_for(session_id)
        if not path.exists():
            return
        data = json.loads(path.read_text(encoding="utf-8"))
        self._sessions[session_id] = {
            "state": payload_to_state(data.get("state", {})),
            "chat_history": data.get("chat_history") or [
                {"role": "assistant", "content": DEFAULT_ASSISTANT_MESSAGE}
            ],
        }


def state_to_payload(state: TravelState) -> dict[str, Any]:
    data = state.to_dict()
    data["generated_ics_b64"] = (
        base64.b64encode(state.generated_ics).decode("ascii") if state.generated_ics else None
    )
    return data


def payload_to_state(payload: dict[str, Any]) -> TravelState:
    field_names = {field.name for field in fields(TravelState)}
    kwargs = {key: value for key, value in payload.items() if key in field_names}
    current_state = kwargs.get("current_state")
    if isinstance(current_state, str):
        kwargs["current_state"] = WorkflowState(current_state)
    kwargs["trace_events"] = [
        _trace_event_from_payload(event) for event in payload.get("trace_events", [])
    ]
    generated_ics = payload.get("generated_ics_b64")
    kwargs["generated_ics"] = base64.b64decode(generated_ics) if generated_ics else None
    return TravelState(**kwargs)


def _trace_event_from_payload(payload: dict[str, Any]) -> TraceEvent:
    data = dict(payload)
    if isinstance(data.get("state"), str):
        data["state"] = WorkflowState(data["state"])
    return TraceEvent(**data)

