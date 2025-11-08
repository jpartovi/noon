from langchain_core.messages import AIMessage

from noon_agent import AgentSettings, invoke_agent


from langchain_core.runnables import RunnableLambda


class DummyChatModel:
    def __init__(self, responses):
        self._responses = list(responses)

    def bind(self, **kwargs):
        return RunnableLambda(lambda _: self._responses.pop(0))


def test_tool_call_roundtrip():
    tool_call = AIMessage(
        content="",
        tool_calls=[
            {
                "name": "clock",
                "args": {},
                "id": "tool-1",
            }
        ],
    )
    final_response = AIMessage(content="Tool execution complete.")
    fake_llm = DummyChatModel(responses=[tool_call, final_response])

    result = invoke_agent(
        {"query": "What time is it?", "context": {"env": "dev"}},
        AgentSettings(openai_api_key="test"),
        llm=fake_llm,
    )

    assert result["messages"][-1].content == "Tool execution complete."
