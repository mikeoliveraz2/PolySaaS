"""
Base AI Web Adapter for PolySaaS AI Bridge.
All AI service adapters inherit from this class.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import AsyncIterator, Optional


@dataclass
class AIResponse:
    """Standardized response from any AI service."""
    text: str
    metadata: dict
    timestamp: datetime
    conversation_id: Optional[str] = None


class AIWebAdapter(ABC):
    """
    Base class for AI web chat adapters.
    Handles browser automation, login, and message sending.
    """
    
    SERVICE_NAME = "base"
    
    def __init__(self, browser_context=None, poly_sniffer=None):
        self.context = browser_context
        self.sniffer = poly_sniffer
        self.page = None
        self.is_logged_in = False
        
    @abstractmethod
    async def login(self, credentials: dict) -> bool:
        """Authenticate with the AI service."""
        pass
    
    @abstractmethod
    async def send_message(self, message: str, conversation_id: Optional[str] = None) -> AIResponse:
        """Send message and get response."""
        pass
    
    async def stream_response(self, message: str) -> AsyncIterator[str]:
        """
        Stream response chunks for real-time feel.
        Default implementation returns full response at once.
        Override for services that support true streaming.
        """
        response = await self.send_message(message)
        yield response.text
        
    async def health_check(self) -> bool:
        """Check if the AI service is accessible."""
        try:
            if self.page:
                await self.page.goto(self.CHAT_URL, timeout=5000)
                return True
            return False
        except Exception:
            return False
    
    async def close(self):
        """Clean up browser resources."""
        if self.page:
            await self.page.close()
            self.page = None
