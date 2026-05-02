"""
Claude (Anthropic) Web Adapter for PolySaaS AI Bridge.
Handles browser automation for Claude web interface at claude.ai
"""
import asyncio
import logging
from typing import Optional
from datetime import datetime

from .base import AIWebAdapter, AIResponse

logger = logging.getLogger(__name__)


class ClaudeAdapter(AIWebAdapter):
    """
    Adapter for Claude (Anthropic) web interface.
    URL: https://claude.ai
    Known for: Excellent reasoning, long context, artifacts/code
    """
    
    SERVICE_NAME = "claude"
    LOGIN_URL = "https://claude.ai/login"
    CHAT_URL = "https://claude.ai/chat"
    
    # CSS Selectors for Claude web interface
    SELECTORS = {
        "email_input": 'input[type="email"], input[name="email"]',
        "continue_button": 'button:has-text("Continue"), button[type="submit"]',
        "verification_code": 'input[type="text"], input[placeholder*="code"], input[placeholder*="verification"]',
        "chat_textarea": 'textarea[placeholder*="Message"], textarea[placeholder*="Claude"], [contenteditable="true"]',
        "send_button": 'button[aria-label*="Send"], button:has-text("Send Message")',
        "response_container": '.response-content, [data-testid="assistant-message"], .prose, .font-claude-message',
        "loading_indicator": '.loading-spinner, [data-testid="loading"], .animate-pulse',
        "new_chat_button": 'button:has-text("New chat"), a[href="/new"], button[aria-label*="new"]'
    }
    
    def __init__(self, browser_context=None, poly_sniffer=None):
        super().__init__(browser_context, poly_sniffer)
        self.conversation_id = None
        
    async def login(self, credentials: dict) -> bool:
        """
        Login to Claude using email + verification code.
        
        credentials format:
        {
            'email': 'user@example.com',
            'verification_code': '123456',  # Optional: if already have code
            'session_cookie': 'xxx'         # Optional: if already authenticated
        }
        """
        try:
            if not self.context:
                logger.error("[CLAUDE] No browser context available")
                return False
                
            self.page = await self.context.new_page()
            
            # Check if we have a stored session
            if credentials.get('session_cookie'):
                logger.info("[CLAUDE] Using stored session cookie")
                await self.page.goto(self.CHAT_URL)
                # TODO: Set cookie and verify
                self.is_logged_in = True
                return True
            
            # Navigate to login page
            logger.info("[CLAUDE] Navigating to Claude")
            await self.page.goto(self.LOGIN_URL, wait_until="domcontentloaded")
            await asyncio.sleep(2)
            
            # Check if already logged in (redirected to chat)
            if "/chat" in self.page.url or self.page.url == "https://claude.ai/":
                logger.info("[CLAUDE] Already logged in")
                self.is_logged_in = True
                return True
            
            # Enter email
            if credentials.get('email'):
                email_input = await self.page.wait_for_selector(
                    self.SELECTORS["email_input"], timeout=10000
                )
                await email_input.fill(credentials['email'])
                
                # Click continue
                continue_btn = await self.page.query_selector(self.SELECTORS["continue_button"])
                if continue_btn:
                    await continue_btn.click()
                    logger.info("[CLAUDE] Continue clicked, waiting for verification code")
                
                # Wait for verification code input or redirect
                try:
                    code_input = await self.page.wait_for_selector(
                        self.SELECTORS["verification_code"], timeout=30000
                    )
                    
                    if credentials.get('verification_code'):
                        await code_input.fill(credentials['verification_code'])
                        await code_input.press("Enter")
                        logger.info("[CLAUDE] Verification code submitted")
                    else:
                        logger.info("[CLAUDE] Waiting for manual code entry...")
                        await asyncio.sleep(30)  # Wait for manual entry
                        
                except Exception as e:
                    logger.debug(f"[CLAUDE] No verification code screen: {e}")
            
            # Wait for login to complete
            await self.page.wait_for_load_state("networkidle")
            await asyncio.sleep(3)
            
            # Verify login success
            if "/chat" in self.page.url or await self.page.query_selector(self.SELECTORS["chat_textarea"]):
                logger.info("[CLAUDE] Login successful")
                self.is_logged_in = True
                return True
            else:
                logger.warning(f"[CLAUDE] Login may have failed - current URL: {self.page.url}")
                return False
                
        except Exception as e:
            logger.error(f"[CLAUDE] Login failed: {e}", exc_info=True)
            return False
    
    async def send_message(self, message: str, conversation_id: Optional[str] = None) -> AIResponse:
        """
        Send a message to Claude and get the response.
        
        Args:
            message: The message text to send
            conversation_id: Optional ID to continue existing conversation
            
        Returns:
            AIResponse with the response text and metadata
        """
        start_time = datetime.now()
        
        if not self.is_logged_in:
            logger.error("[CLAUDE] Not logged in")
            return AIResponse(
                text="Error: Not authenticated with Claude",
                metadata={"error": "not_authenticated"},
                timestamp=start_time
            )
        
        try:
            # Navigate to specific conversation or new chat
            if conversation_id:
                url = f"{self.CHAT_URL}/{conversation_id}"
                self.conversation_id = conversation_id
            else:
                # Start new chat
                url = self.CHAT_URL
                self.conversation_id = None
                
            await self.page.goto(url, wait_until="domcontentloaded")
            await asyncio.sleep(2)
            
            # Find chat input
            chat_input = await self.page.wait_for_selector(
                self.SELECTORS["chat_textarea"], timeout=15000
            )
            
            # Clear any existing text
            await chat_input.click()
            await chat_input.press("Control+a")
            await chat_input.press("Delete")
            
            # Type message with human-like delays
            await self._human_type(chat_input, message)
            
            # Send message
            await chat_input.press("Enter")
            logger.info("[CLAUDE] Message sent, waiting for response")
            
            # Wait for response
            response_text = await self._wait_for_response(timeout=120)
            
            # Extract conversation ID from URL if new
            current_url = self.page.url
            if "/chat/" in current_url:
                self.conversation_id = current_url.split("/chat/")[-1].split("?")[0]
            
            # Capture event via PolySniffer if available
            if self.sniffer:
                await self.sniffer.capture_ai_event(
                    service='claude',
                    direction='outbound',
                    message=message,
                    response=response_text,
                    metadata={
                        'conversation_id': self.conversation_id,
                        'response_time_ms': (datetime.now() - start_time).total_seconds() * 1000
                    }
                )
            
            return AIResponse(
                text=response_text,
                metadata={
                    "service": "claude",
                    "conversation_id": self.conversation_id,
                    "response_time_seconds": (datetime.now() - start_time).total_seconds()
                },
                timestamp=datetime.now(),
                conversation_id=self.conversation_id
            )
            
        except Exception as e:
            logger.error(f"[CLAUDE] Send message failed: {e}", exc_info=True)
            return AIResponse(
                text=f"Error communicating with Claude: {str(e)}",
                metadata={"error": str(e)},
                timestamp=datetime.now()
            )
    
    async def _human_type(self, element, text: str):
        """Type text with human-like delays to avoid bot detection."""
        for char in text:
            await element.type(char)
            # Random delay between 10-50ms per character
            await asyncio.sleep(0.01 + (0.04 * (hash(char) % 100) / 100))
    
    async def _wait_for_response(self, timeout: int = 120) -> str:
        """Wait for Claude response and extract text."""
        start = datetime.now()
        last_text = ""
        stable_count = 0
        
        while (datetime.now() - start).total_seconds() < timeout:
            # Check if still loading
            loading = await self.page.query_selector(self.SELECTORS["loading_indicator"])
            if loading:
                await asyncio.sleep(1)
                continue
            
            # Try to get response
            responses = await self.page.query_selector_all(self.SELECTORS["response_container"])
            if responses:
                # Get the last response (most recent)
                last_response = responses[-1]
                text = await last_response.inner_text()
                
                if text and len(text.strip()) > 10:
                    # Check if text is stable (not still typing)
                    if text == last_text:
                        stable_count += 1
                        if stable_count >= 3:  # Text stable for 3 checks
                            return text.strip()
                    else:
                        stable_count = 0
                        last_text = text
            
            await asyncio.sleep(0.5)
        
        # Return whatever we have even if timeout
        if last_text:
            return last_text.strip()
        return "[Timeout waiting for response]"
    
    async def health_check(self) -> bool:
        """Check if Claude service is accessible."""
        try:
            if not self.page:
                return False
            await self.page.goto(self.CHAT_URL, timeout=10000)
            return await self.page.query_selector(self.SELECTORS["chat_textarea"]) is not None
        except Exception as e:
            logger.error(f"[CLAUDE] Health check failed: {e}")
            return False
    
    async def close(self):
        """Clean up browser resources."""
        if self.page:
            try:
                await self.page.close()
            except Exception as e:
                logger.debug(f"[CLAUDE] Error closing page: {e}")
            finally:
                self.page = None
