# Lazy import to avoid importing main (which requires langchain_openai) 
# when only schemas are needed (e.g., from backend)
# LangGraph references ./agent/main.py:noon_graph directly, so this __init__.py 
# doesn't need to export noon_graph
def __getattr__(name):
    if name == "noon_graph":
        from .main import noon_graph
        return noon_graph
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

__all__ = ["noon_graph"]
