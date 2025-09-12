from langchain_core.tools import Tool
from typing import Dict

_tool_registry: Dict[str, Tool] = {}

def register_tool(cls):
    if not hasattr(cls, "_run"):
        raise TypeError(f"Class {cls.__name__} must define a '_run' method.")

    name = getattr(cls, "name", None)
    description = getattr(cls, "description", None)
    args_schema = getattr(cls, "args_schema", None)

    if not name or not description:
        raise TypeError(f"Class {cls.__name__} must define 'name' and 'description' attributes.")

    # Wrap to instantiate the class on each call so _run has a bound self
    def _callable(*args, **kwargs):
        instance = cls()
        return instance._run(*args, **kwargs)

    tool_instance = Tool(
        name=name,
        description=description,
        func=_callable,
        args_schema=args_schema
    )

    _tool_registry[name] = tool_instance
    return cls


class BaseTool:
    """
    A lightweight base class for custom tools.
    (Not inheriting from langchain.Tool to avoid init conflicts.)
    """
    pass
