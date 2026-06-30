"""
Agent factory — creates AIAgent instances.

This module provides the factory interface for creating agents
with different configurations.
"""

from app.sessions import MockAgent


class AgentFactory:
    """Creates and configures agent instances."""

    @staticmethod
    def create_agent(model: str = "", base_url: str = "", **kwargs) -> MockAgent:
        return MockAgent(model=model, base_url=base_url, **kwargs)

