"""
Office AI Agent package (scaffold).

This is the initial Step 1 scaffolding. Public exports like OfficeAIAgent and
Config will be wired up in later steps as implementations land.
"""

from .core.agent_orchestrator import OfficeAIAgent
from .core.config import Config

__all__ = ["OfficeAIAgent", "Config"]
__version__ = "0.1.0"
