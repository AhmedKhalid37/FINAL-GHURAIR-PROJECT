from typing import Any, Dict

class Tool:
    """Minimal interface for tools used by agents."""
    name: str = "base_tool"
    def run(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        raise NotImplementedError("Tool.run must be implemented by subclasses")
