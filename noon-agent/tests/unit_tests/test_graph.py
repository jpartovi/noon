from langchain_core.messages import AIMessage

from noon_agent import AgentSettings, invoke_agent


from langchain_core.runnables import RunnableLambda


class DummyChatModel:
    def __init__(self, responses):
        self._responses = list(responses)

    def bind(self, **kwargs):
        return RunnableLambda(lambda _: self._responses.pop(0))


def test_invoke_agent_with_fake_model():
    fake_llm = DummyChatModel(responses=[AIMessage(content="ready to help!")])
    payload = {"query": "status?", "context": {"env": "test"}}
    result = invoke_agent(payload, AgentSettings(openai_api_key="test"), llm=fake_llm)

    assert result["messages"][-1].content == "ready to help!"
