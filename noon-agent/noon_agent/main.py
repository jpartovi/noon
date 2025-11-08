"""LangGraph entrypoints for the Noon agent."""

from __future__ import annotations

from typing import Any, Dict, List

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.tools import StructuredTool
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import ToolNode

from .config import AgentSettings, get_settings
from .helpers import build_context_block, build_prompt
from .mocks import clock_tool, ping_tool
from .schemas import AgentState, TaskInput


def _make_model(settings: AgentSettings) -> BaseChatModel:
    """Lazy construct the model with the project's defaults."""

    if not settings.openai_api_key:
        raise ValueError("OPENAI_API_KEY is not configured")

    return ChatOpenAI(
        model=settings.model,
        temperature=settings.temperature,
        max_retries=settings.max_retries,
        api_key=settings.openai_api_key,
    )


def _route_after_agent(state: AgentState) -> str:
    """Decide whether to call a tool or finish the run."""

    messages: List[BaseMessage] = state["messages"]
    if not messages:
        return END

    last = messages[-1]
    if isinstance(last, AIMessage) and last.tool_calls:
        return "tools"
    return END


def build_agent_graph(settings: AgentSettings | None = None, llm: BaseChatModel | None = None):
    """Create and compile the LangGraph agent."""

    resolved_settings = settings or get_settings()
    active_llm = llm or _make_model(resolved_settings)

    tools = [
        StructuredTool.from_function(ping_tool, name="ping", description="Health-check tool."),
        StructuredTool.from_function(
            clock_tool, name="clock", description="Return the current UTC timestamp."
        ),
    ]
    tool_node = ToolNode(tools=tools)

    prompt = build_prompt()
    chain = prompt | active_llm.bind(tools=tools)

    def agent_node(state: AgentState) -> Dict[str, List[BaseMessage]]:
        response = chain.invoke({"messages": state["messages"]})
        return {"messages": [response]}

    graph = StateGraph(AgentState)
    graph.add_node("agent", agent_node)
    graph.add_node("tools", tool_node)
    graph.add_edge(START, "agent")
    graph.add_conditional_edges(
        "agent",
        _route_after_agent,
        {
            "tools": "tools",
            END: END,
        },
    )
    graph.add_edge("tools", "agent")

    return graph.compile()


def _format_initial_state(payload: TaskInput) -> AgentState:
    context = payload.get("context") or {}
    query = payload.get("query", "").strip()
    if not query:
        raise ValueError("A query is required to run the agent.")

    context_block = build_context_block(context)
    composed_prompt = f"{query}\n\n{context_block}"
    return AgentState(messages=[HumanMessage(content=composed_prompt)], context=context)


def invoke_agent(
    payload: TaskInput, settings: AgentSettings | None = None, llm: BaseChatModel | None = None
) -> Any:
    """Convenience helper to invoke the compiled graph."""

    graph = build_agent_graph(settings=settings, llm=llm)
    return graph.invoke(_format_initial_state(payload))
