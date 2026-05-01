"""
Kimi (Moonshot AI) Web Adapter for PolySaaS AI Bridge.
Handles browser automation for Kimi web interface at kimi.moonshot.cn
"""
import asyncio
import logging
from typing import Optional
from datetime import datetime

from .base import AIWebAdapter, AIResponse

logger = logging.getLogger(__name__)


class KimiAdapter(AIWebAdapter):
    """
    Adapter for Kimi (Moonshot AI) web interface.
    URL: https://kimi.moonshot.cn
    """
    
    SERVICE_NAME = "kimi"
    LOGIN_URL = "https://kimi.moonshot.cn"
    CHAT_URL = "https://kimi.moonshot.cn"
    
    # CSS Selectors for Kimi web interface (adjust as needed)
    SELECTORS = {
        "login_button": 'button[data-testid="login"], .login-btn, button:has-text("登录")',
        "phone_input": 'input[type="tel"], input[placeholder*="手机号"], input[placeholder*="phone"]',
        "code_input": 'input[type="number"], input[placeholder*="验证码"], input[placeholder*="code"]',
        "chat_input": 'textarea[placeholder], .chat-input, div[contenteditable="true"]',
        "send_button": 'button[type="submit"], .send-btn, button:has-text("发送")',
        "response_container": '.response-content, .message-content, [data-testid="assistant-message"]',
        "loading_indicator": '.loading, .thinking, [data-testid="loading"]'
    }
    
    def __init__(self, browser_context=None, poly_sniffer=None):
        super().__init__(browser_context, poly_sniffer)
        self.conversation_id = None
        
    async def login(self, credentials: dict) -> bool:
        """
        Login to Kimi using phone + SMS code or existing session.
        
        credentials format:
        {
            'phone': '13800138000',  # Chinese phone number
            'sms_code': '123456',     # Optional: if already have code
            'session_token': 'xxx'    # Optional: if already authenticated
        }
        """
        try:
            if not self.context:
                logger.error("[KIMI] No browser context available")
                return False
                
            self.page = await self.context.new_page()
            
            # Check if we have a stored session
            if credentials.get('session_token'):
                logger.info("[KIMI] Using stored session token")
                # Set cookies/session storage
                await self.page.goto(self.LOGIN_URL)
                # TODO: Implement session restoration
                self.is_logged_in = True
                return True
            
            # Navigate to login page
            logger.info("[KIMI] Navigating to login page")
            await self.page.goto(self.LOGIN_URL, wait_until="domcontentloaded")
            await asyncio.sleep(2)  # Wait for JS to load
            
            # Check if already logged in (redirected to chat)
            if "/chat" in self.page.url:
                logger.info("[KIMI] Already logged in")
                self.is_logged_in = True
                return True
            
            # Click login button if present
            try:
                login_btn = await self.page.query_selector(self.SELECTORS["login_button"])
                if login_btn:
                    await login_btn.click()
                    await asyncio.sleep(1)
            except Exception as e:
                logger.debug(f"[KIMI] No login button found: {e}")
            
            # Enter phone number
            if credentials.get('phone'):
                phone_input = await self.page.wait_for_selector(
                    self.SELECTORS["phone_input"], timeout=5000
                )
                await phone_input.fill(credentials['phone'])
                
                # Click to get SMS code
                send_code_btn = await self.page.query_selector('button:has-text("获取验证码")')
                if send_code_btn:
                    await send_code_btn.click()
                    logger.info("[KIMI] SMS code requested, waiting for user input")
                    # In production, this would wait for webhook/callback with code
                    await asyncio.sleep(30)  # Wait for manual entry in headful mode
                    
                if credentials.get('sms_code'):
                    code_input = await self.page.wait_for_selector(
                        self.SELECTORS["code_input"], timeout=5000
                    )
                    await code_input.fill(credentials['sms_code'])
                    await code_input.press("Enter")
            
            # Wait for login to complete
            await self.page.wait_for_load_state("networkidle")
            await asyncio.sleep(3)
            
            # Verify login success
            if "/chat" in self.page.url or await self.page.query_selector(self.SELECTORS["chat_input"]):
                logger.info("[KIMI] Login successful")
                self.is_logged_in = True
                return True
            else:
                logger.warning("[KIMI] Login may have failed - unexpected page state")
                return False
                
        except Exception as e:
            logger.error(f"[KIMI] Login failed: {e}", exc_info=True)
            return False
    
    async def send_message(self, message: str, conversation_id: Optional[str] = None) -> AIResponse:
        """
        Send a message to Kimi and get the response.
        
        Args:
            message: The message text to send
            conversation_id: Optional ID to continue existing conversation
            
        Returns:
            AIResponse with the response text and metadata
        """
        start_time = datetime.now()
        
        if not self.is_logged_in:
            logger.error("[KIMI] Not logged in")
            return AIResponse(
                text="Error: Not authenticated with Kimi",
                metadata={"error": "not_authenticated"},
                timestamp=start_time
            )
        
        try:
            # Navigate to specific conversation or new chat
            if conversation_id:
                url = f"{self.CHAT_URL}/chat/{conversation_id}"
                self.conversation_id = conversation_id
            else:
                url = f"{self.CHAT_URL}/chat"
                
            await self.page.goto(url, wait_until="domcontentloaded")
            await asyncio.sleep(2)
            
            # Find and fill chat input
            chat_input = await self.page.wait_for_selector(
                self.SELECTORS["chat_input"], timeout=10000
            )
            
            # Type message with human-like delays (anti-bot detection)
            await self._human_type(chat_input, message)
            
            # Send message
            await chat_input.press("Enter")
            
            # Wait for loading to start then complete
            await asyncio.sleep(1)
            
            # Wait for response to appear
            response_text = await self._wait_for_response(timeout=60)
            
            # Extract conversation ID from URL if new
            current_url = self.page.url
            if "/chat/" in current_url:
                self.conversation_id = current_url.split("/chat/")[-1].split("?")[0]
            
            # Capture event via PolySniffer if available
            if self.sniffer:
                await self.sniffer.capture_ai_event(
                    service='kimi',
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
                    "service": "kimi",
                    "conversation_id": self.conversation_id,
                    "response_time_seconds": (datetime.now() - start_time).total_seconds()
                },
                timestamp=datetime.now(),
                conversation_id=self.conversation_id
            )
            
        except Exception as e:
            logger.error(f"[KIMI] Send message failed: {e}", exc_info=True)
            return AIResponse(
                text=f"Error communicating with Kimi: {str(e)}",
                metadata={"error": str(e)},
                timestamp=datetime.now()
            )
    
    async def _human_type(self, element, text: str):
        """Type text with human-like delays to avoid bot detection."""
        for char in text:
            await element.type(char)
            # Random delay between 10-50ms per character
            await asyncio.sleep(0.01 + (0.04 * (hash(char) % 100) / 100))
    
    async def _wait_for_response(self, timeout: int = 60) -> str:
        """Wait for AI response and extract text."""
        start = datetime.now()
        
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
                    return text.strip()
            
            await asyncio.sleep(0.5)
        
        return "[Timeout waiting for response]"
    
    async def health_check(self) -> bool:
        """Check if Kimi service is accessible."""
        try:
            if not self.page:
                return False
            await self.page.goto(self.CHAT_URL, timeout=10000)
            return await self.page.query_selector(self.SELECTORS["chat_input"]) is not None
        except Exception as e:
            logger.error(f"[KIMI] Health check failed: {e}")
            return False
    
    async def close(self):
        """Clean up browser resources."""
        if self.page:
            try:
                # Save session state for future reuse
                # TODO: Implement session storage
                await self.page.close()
            except Exception as e:
                logger.debug(f"[KIMI] Error closing page: {e}")
            finally:
                self.page = None
