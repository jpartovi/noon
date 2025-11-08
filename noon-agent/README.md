# Noon Agent

This directory hosts a small LangGraph prototype for the Noon project. It exposes a
single assistant-style graph that can be run directly or embedded into other tools.

## Getting started

```bash
cd noon-agent
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt  # optional, see below for pyproject
```

Alternatively, install dependencies via the `pyproject.toml` with `pip install -e .`
or `uv pip install -e .`.

## Running the graph

```python
from noon_agent import AgentSettings, invoke_agent

payload = {"query": "Summarize the plan for tomorrow.", "context": {"user": "Anika"}}
result = invoke_agent(payload, AgentSettings(openai_api_key="sk-...")))
print(result["messages"][-1].content)
```

The graph currently wires in two local tools (`ping` and `clock`) so we can
exercise tool-call loops end-to-end. Customize `noon_agent/helpers.py` and
`noon_agent/main.py` to add richer behavior.
