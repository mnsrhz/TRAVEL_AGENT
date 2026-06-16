from __future__ import annotations

import html

import streamlit as st

from src.config.settings import Settings
from src.state.travel_state import TravelState, WorkflowState


def render_environment(settings: Settings) -> None:
    badge = "tc-badge-green" if settings.allow_demo_fallbacks else "tc-badge-amber"
    st.markdown(f'<span class="tc-badge {badge}">{settings.mode_label}</span>', unsafe_allow_html=True)
    if settings.missing_keys:
        st.caption("Missing keys: " + ", ".join(settings.missing_keys))


def render_workflow_sidebar(state: TravelState, settings: Settings) -> None:
    st.markdown("### Travel Concierge")
    st.caption("Agentic AI system")
    render_environment(settings)
    st.markdown('<div class="tc-label">Workflow</div>', unsafe_allow_html=True)
    gates = [
        ("Preference confirmation", "preference_confirmation"),
        ("Destination split", "destination_city_split"),
        ("High-risk day", "high_risk_day"),
        ("Final itinerary", "final_itinerary"),
        ("Calendar creation", "calendar_creation"),
    ]
    for label, key in gates:
        status = "Done" if state.approvals.get(key) else "Pending"
        st.markdown(
            f'<div class="tc-card"><div class="tc-value">{html.escape(label)}</div><div class="tc-label">{status}</div></div>',
            unsafe_allow_html=True,
        )
    st.metric("Tool calls", state.tool_call_count, help="Maximum 25 per session")
    st.metric("Estimated tokens", state.token_count, help="Pause at 95,000 of 100,000")


def render_preferences(state: TravelState) -> None:
    st.markdown('<div class="tc-label">Trip preferences</div>', unsafe_allow_html=True)
    cols = st.columns(2)
    for index, (label, value) in enumerate(state.preferences.items()):
        with cols[index % 2]:
            st.markdown(
                f'<div class="tc-card"><div class="tc-label">{html.escape(label)}</div><div class="tc-value">{html.escape(str(value))}</div></div>',
                unsafe_allow_html=True,
            )


def render_status(state: TravelState) -> None:
    if state.current_state != WorkflowState.FAILED:
        return
    errors = [event.error for event in state.trace_events if event.error]
    message = errors[-1] if errors else "The workflow stopped before completing."
    st.error(message)


def render_itinerary(state: TravelState) -> None:
    st.markdown('<div class="tc-label">Draft itinerary</div>', unsafe_allow_html=True)
    for day in state.itinerary:
        st.markdown(f"**Day {day['day']} - {day['date']} · {day.get('city', '')}**")
        for event in day.get("events", []):
            st.markdown(
                f"""
                <div class="tc-event">
                  <div class="tc-time">{html.escape(event['start'][11:16])} - {html.escape(event['end'][11:16])}</div>
                  <div>
                    <div class="tc-event-title">{html.escape(event['title'])}</div>
                    <div class="tc-event-sub">{html.escape(event.get('location', ''))}</div>
                  </div>
                </div>
                """,
                unsafe_allow_html=True,
            )


def render_approval_panel(title: str, body: str) -> None:
    st.markdown(
        f"""
        <div class="tc-approval">
          <div class="tc-approval-head">{html.escape(title)}</div>
          <div class="tc-approval-body">{html.escape(body)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_trace_panel(state: TravelState) -> None:
    st.markdown("### Agent reasoning")
    if not state.trace_events:
        st.markdown(
            """
            <div class="tc-trace">
              <div class="tc-trace-title">Ready</div>
              <div class="tc-trace-body">Start planning to see the agent trace, tool calls, loop counts, and approval decisions.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return
    for event in reversed(state.trace_events[-8:]):
        st.markdown(
            f"""
            <div class="tc-trace">
              <div class="tc-trace-title">Step {event.step} · {html.escape(event.node)} · {html.escape(event.status)}</div>
              <div class="tc-trace-body">{html.escape(event.output_summary)}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
