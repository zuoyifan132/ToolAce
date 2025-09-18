"""
Agents Module - Multi-Agent Dialog Generation

This module contains the implementation of three agents that collaborate
to generate function-calling dialogs: UserAgent, AssistantAgent, and ToolAgent.
"""

from .user_agent import UserAgent
from .assistant_agent import AssistantAgent  
from .tool_agent import ToolAgent

__all__ = [
    'UserAgent',
    'AssistantAgent',
    'ToolAgent'
]
