"""
Agent factory — creates AIAgent instances from configuration.

This is the bridge between our REST API and the Hermes agent.
We import the Hermes agent directly as Python code (not subprocess),
which gives us clean control over sessions, streaming, and tool use.

Engineering lesson: Importing Python code directly is ALWAYS better
than spawning subprocesses and parsing text output. Direct imports
give you type safety, exception handling, and access to internal state.
"""

import sys
import os
from typing import Optional

# Add the Hermes agent source to Python path
# This is how we import Hermes as a Python module
HERMES_AGENT_PATH = os.path.expanduser("~/.hermes/hermes-agent")
if HERMES_AGENT_PATH not in sys.path:
    sys.path.insert(0, HERMES_AGENT_PATH)


def create_agent(
    model: str = "",
    base_url: str = "",
    max_turns: int = 10,
    enabled_toolsets: Optional[list[str]] = None,
    disabled_toolsets: Optional[list[str]] = None,
    save_trajectories: bool = False,
    verbose: bool = False,
) -> object:
    """
    Create and return an AIAgent instance.

    Args:
        model: Model name (e.g. "anthropic/claude-sonnet-4")
        base_url: API endpoint URL
        max_turns: Max conversation iterations
        enabled_toolsets: Toolsets to enable
        disabled_toolsets: Toolsets to disable
        save_trajectories: Record conversation for debugging
        verbose: Enable detailed logging

    Returns:
        AIAgent instance ready to chat

    Raises:
        RuntimeError: If agent initialization fails
    """
    try:
        from run_agent import AIAgent

        # AIAgent expects List[str], not None
        _enabled = enabled_toolsets or []
        _disabled = disabled_toolsets or []

        agent = AIAgent(
            base_url=base_url,
            model=model,
            max_iterations=max_turns,
            enabled_toolsets=_enabled,
            disabled_toolsets=_disabled,
            save_trajectories=save_trajectories,
            verbose_logging=verbose,
        )
        return agent

    except Exception as e:
        raise RuntimeError(f"Failed to create agent: {str(e)}")


def get_available_toolsets() -> dict:
    """Get the list of available toolsets from Hermes."""
    try:
        from model_tools import get_all_tool_names
        from toolsets import get_all_toolsets, get_toolset_info

        toolsets = get_all_toolsets()
        result = {}
        for name, toolset in toolsets.items():
            info = get_toolset_info(name)
            if info:
                result[name] = {
                    "description": info.get("description", ""),
                    "tools": info.get("resolved_tools", []),
                    "tool_count": info.get("tool_count", 0),
                }
        return result
    except Exception as e:
        return {"_error": str(e)}
