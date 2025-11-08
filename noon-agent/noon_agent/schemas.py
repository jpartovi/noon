"""Shared type definitions used across the graph."""

from typing import Any, Dict, List
from typing import TypedDict
from typing_extensions import Annotated

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class AgentState(TypedDict):
    """State tracked inside the LangGraph workflow."""

    messages: Annotated[List[BaseMessage], add_messages]
    context: Dict[str, Any]
