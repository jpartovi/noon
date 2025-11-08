"""Utility helpers for building prompts and LangChain components."""

from typing import Dict

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder


SYSTEM_TEMPLATE = (
    "You are Noon, a pragmatic executive assistant. "
    "Use the provided context when it is relevant."
)


def build_prompt(extra_instructions: str | None = None) -> ChatPromptTemplate:
    """Return the default chat prompt used by the agent."""

    system_message = SYSTEM_TEMPLATE
    if extra_instructions:
        system_message = f"{system_message}\n\nAdditional instructions: {extra_instructions}"

    return ChatPromptTemplate.from_messages(
        [
            ("system", system_message),
            MessagesPlaceholder(variable_name="messages"),
        ]
    )


def build_context_block(context: Dict[str, str] | None) -> str:
    """Render context into a short English paragraph."""

    if not context:
        return "No additional context provided."

    lines = [f"- {key}: {value}" for key, value in context.items()]
    return "Context:\n" + "\n".join(lines)
