"""LangGraph entrypoints for the Noon agent."""

from __future__ import annotations

from typing import Any, Dict, List, Literal

from datetime import datetime 
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.tools import StructuredTool
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import ToolNode

# from .config import AgentSettings, get_settings
# from .helpers import build_context_block, build_prompt
# from .mocks import clock_tool, ping_tool
from .schemas import AgentState, TaskInput

class State(TypedDict):
    something: str
    action: Literal["create", "delete", "update", "read"]
    start_time: datetime
    end_time: datetime
    auth: dict 
    """any params relevant for auth when making google calendar api calls"""

class OutputState(TypedDict):
    summary: dict

def route_action(state: State):
    if state["action"] == "create":
        return create_event(state)
    elif state["action"] == "read":
        return read_event(state)
    elif state["update"] == "update":
        return update_event(state)
    else:
        return delete_event(state)


def create_event(state: State):
    #todo
    pass


def read_event(state: State):
    pass

def update_event(state: State):
    pass

def delete_event(state: State):
    pass

graph_builder = StateGraph(State, output_schema=OutputState)
graph_builder.add_conditional_edges(
    START, route_action, ["list off poss actions"]
)
graph_builder.add_node(..)
graoh_builder.add_node(..., END)
graph = graph_builder.compile(name="NOON")




# other ideas
# • - search_free_time – scan attendee calendars for the
#     earliest mutually available windows.
#   - propose_slots – generate a ranked shortlist
#     of candidate start/end times (with time‑zone
#     normalization).
#   - adjust_event – move an existing event by
#     ±N minutes/hours while keeping participant
#     constraints intact.
#   - sync_external – pull in events from external
#     sources (invites, shared calendars) and reconcile
#     duplicates.
#   - notify_attendees – draft/send updates or reminders
#     when an event is created, moved, or canceled.
#   - summarize_day – return a natural-language rundown
#     of the user’s schedule, conflicts, and gaps.
#   - set_preferences – store user defaults (meeting
#     lengths, working hours, buffer rules) for
#     downstream actions.
#   - resolve_conflict – pick which overlapping event
#     to keep, reschedule, or decline based on priority
#     rules.
#   - collect_requirements – gather missing metadata
#     (agenda, location, video link) before finalizing
#     an event.