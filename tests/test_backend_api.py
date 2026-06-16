from fastapi.testclient import TestClient

from backend.app.main import app


def test_backend_health():
    client = TestClient(app)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_backend_chat_and_approval_flow(monkeypatch, tmp_path):
    monkeypatch.setenv("ALLOW_DEMO_FALLBACKS", "true")
    monkeypatch.setenv("TRAVEL_AGENT_SESSION_DIR", str(tmp_path))
    client = TestClient(app)

    created = client.post("/api/sessions").json()
    session_id = created["session_id"]
    assert created["state"]["current_state"] == "COLLECTING_REQUIREMENTS"

    chat = client.post(
        f"/api/sessions/{session_id}/chat",
        json={
            "message": "I am traveling from SFO and I want to go to Japan on Sep 1st for 10 days, vegetarian, moderate pace, budget $3500"
        },
    )
    assert chat.status_code == 200
    chat_payload = chat.json()
    assert chat_payload["reply"].startswith("I have the essentials")
    assert chat_payload["ready"] is True
    assert chat_payload["state"]["user_input"]["destination"] == "Japan"
    assert chat_payload["state"]["current_state"] == "AWAITING_PREFERENCE_APPROVAL"

    researched = client.post(
        f"/api/sessions/{session_id}/approve",
        json={"gate": "preference_confirmation"},
    )
    assert researched.status_code == 200
    assert researched.json()["state"]["current_state"] == "AWAITING_DESTINATION_APPROVAL"
    assert researched.json()["state"]["flights"]
    assert researched.json()["state"]["trace_events"]


def test_backend_rejects_unknown_session():
    client = TestClient(app)

    response = client.get("/api/sessions/not-a-session")

    assert response.status_code == 404
    assert response.json()["detail"] == "Session not found"


def test_backend_exports_markdown_after_itinerary(monkeypatch, tmp_path):
    monkeypatch.setenv("ALLOW_DEMO_FALLBACKS", "true")
    monkeypatch.setenv("TRAVEL_AGENT_SESSION_DIR", str(tmp_path))
    client = TestClient(app)

    session_id = client.post("/api/sessions").json()["session_id"]
    client.post(
        f"/api/sessions/{session_id}/chat",
        json={
            "message": "Plan a 3 day Italy trip from NYC starting 2026-09-05, no dietary restrictions, relaxed pace, budget $4200."
        },
    )
    client.post(f"/api/sessions/{session_id}/approve", json={"gate": "preference_confirmation"})
    client.post(f"/api/sessions/{session_id}/approve", json={"gate": "destination_city_split"})

    response = client.get(f"/api/sessions/{session_id}/exports/itinerary.md")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/markdown")
    assert "# Travel Itinerary" in response.text

