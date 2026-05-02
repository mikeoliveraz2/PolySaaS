"""
AI Service Adapters for PolySaaS AI Bridge.
Each adapter handles web automation for a specific AI service.
"""
from .base import AIWebAdapter, AIResponse
from .kimi_adapter import KimiAdapter
from .claude_adapter import ClaudeAdapter

__all__ = ['AIWebAdapter', 'AIResponse', 'KimiAdapter', 'ClaudeAdapter']
