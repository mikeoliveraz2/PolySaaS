"""
Grok (xAI) Web Adapter for PolySaaS AI Bridge.
Handles browser automation for Grok web interface at x.ai/grok
"""
import asyncio
import logging
from typing import Optional
from datetime import datetime

from .base import AIWebAdapter, AIResponse

logger = logging.getLogger(__name__)


class GrokAdapter(AIWebAdapter):
    """
    Adapter for Grok (xAI) web interface.
    URL: https://x.ai/grok
    Known for: Real-time X data access, witty personality, image generation
    """
    
    SERVICE_NAME = "grok"
    LOGIN_URL = "https://x.ai/grok"
    CHAT_URL = "https://x.ai/grok"
    
    # CSS Selectors for Grok web interface
    # NOTE: These are estimated based on typical X/Grok UI patterns
    # May need adjustment after testing
    SELECTORS = {
        "email_input": 'input[type="email"], input[name="email"], input[autocomplete="email"]',
        "username_input": 'input[type="text"], input[name="username"], input[autocomplete="username"]',
        "password_input": 'input[type="password"], input[name="password"]',
        "login_button": 'button[type="submit"], button:has-text("Log in"), button:has-text("Sign in")',
        "chat_textarea": 'textarea[placeholder*="Ask"], textarea[placeholder*="Message"], [contenteditable="true"], div[role="textbox"]',
        "send_button": 'button[type="submit"], button:has-text("Send"), button[aria-label*="send"], button[data-testid="send"]', 
        "response_container": '[data-testid="message"], .message-content, .response-content, [role="article"], div[class*="message"]',
        "loading_indicator": '[data-testid="loading"], .animate-pulse, .loading, [class*="loading"]',
        "new_chat_button": 'button:has-text("New chat"), a[href="/grok"], button[aria-label*="new"]',
        "grok_logo": 'img[alt*="Grok"], svg[aria-label*="Grok"]'
    }
    
    def __init__(self, browser_context=None, poly_sniffer=None):
        super().__init__(browser_context, poly_sniffer)
        self.conversation_id = None
        
    async def login(self, credentials: dict) -> bool:
        """
        Login to Grok using X/Twitter credentials.
        
        credentials format:
        {
            'email': 'user@example.com',      # X email
            'username': '@username',          # X handle (alternative)
            'password': 'xxx',                # X password
            'session_cookie': 'xxx'          # Optional: if already authenticated
        }
        """
        try:
            if not self.context:
                logger.error("[GROK] No browser context available")
                return False
                
            self.page = await self.context.new_page()
            
            # Check if we have a stored session
            if credentials.get('session_cookie'):
                logger.info("[GROK] Using stored session cookie")
                await self.page.goto(self.CHAT_URL)
                # TODO: Set cookie and verify
                self.is_logged_in = True
                return True
            
            # Navigate to Grok (will redirect to X login if not authenticated)
            logger.info("[GROK] Navigating to Grok")
            await self.page.goto(self.LOGIN_URL, wait_until="domcontentloaded")
            await asyncio.sleep(2)
            
            # Check if already logged in (stays on x.ai/grok)
            if "/grok" in self.page.url and "login" not in self.page.url.lower():
                logger.info("[GROK] Already logged in")
                self.is_logged_in = True
                return True
            
            # X login flow
            if credentials.get('email') or credentials.get('username'):
                email = credentials.get('email') or credentials.get('username')
                password = credentials.get('password')
                
                if not password:
                    logger.error("[GROK] Password required for login")
                    return False
                
                logger.info(f"[GROK] Attempting login for {email}")
                
                # X login page should have loaded
                # Try email/username field first
                email_selectors = [
                    self.SELECTORS["email_input"],
                    self.SELECTORS["username_input"],
                    'input[autocomplete="username"]',
                    'input[name="text"]'
                ]
                
                email_filled = False
                for selector in email_selectors:
                    try:
                        await self.page.wait_for_selector(selector, timeout=2000)
                        await self.page.fill(selector, email)
                        logger.info(f"[GROK] Filled email/username using {selector}")
                        email_filled = True
                        break
                    except Exception:
                        continue
                
                if not email_filled:
                    logger.error("[GROK] Could not find email input field")
                    return False
                
                # Click next/continue if present
                try:
                    next_button = await self.page.query_selector('button:has-text("Next"), button:has-text("Continue")')
                    if next_button:
                        await next_button.click()
                        await asyncio.sleep(1)
                except Exception:
                    pass
                
                # Fill password
                try:
                    await self.page.wait_for_selector(self.SELECTORS["password_input"], timeout=5000)
                    await self.page.fill(self.SELECTORS["password_input"], password)
                    logger.info("[GROK] Filled password")
                except Exception as e:
                    logger.error(f"[GROK] Could not fill password: {e}")
                    return False
                
                # Click login
                try:
                    login_btn = await self.page.query_selector(self.SELECTORS["login_button"])
                    if login_btn:
                        await login_btn.click()
                        logger.info("[GROK] Clicked login button")
                    else:
                        # Try pressing Enter
                        await self.page.press(self.SELECTORS["password_input"], "Enter")
                        logger.info("[GROK] Submitted with Enter key")
                except Exception as e:
                    logger.warning(f"[GROK] Login click issue: {e}")
                
                # Wait for navigation to Grok
                await asyncio.sleep(3)
                
                # Check if we're now on Grok
                if "/grok" in self.page.url or "x.ai" in self.page.url:
                    logger.info("[GROK] Login successful - on Grok page")
                    self.is_logged_in = True
                    return True
                else:
                    logger.error(f"[GROK] Login failed - still on {self.page.url}")
                    return False
            
            logger.error("[GROK] No credentials provided for login")
            return False
            
        except Exception as e:
            logger.error(f"[GROK] Login error: {e}")
            return False
    
    async def send_message(self, message: str, conversation_id: Optional[str] = None) -> AIResponse:
        """
        Send a message to Grok and get response.
        
        Args:
            message: The message to send
            conversation_id: Optional conversation ID to continue thread
            
        Returns:
            AIResponse with Grok's reply
        """
        if not self.is_logged_in or not self.page:
            logger.error("[GROK] Not logged in")
            return AIResponse(
                text="Error: Not logged in to Grok",
                metadata={"error": "not_logged_in"},
                timestamp=datetime.now()
            )
        
        try:
            # Ensure we're on the chat page
            if "/grok" not in self.page.url:
                logger.info("[GROK] Navigating to chat page")
                await self.page.goto(self.CHAT_URL)
                await asyncio.sleep(2)
            
            # Start new chat if requested
            if conversation_id == "new":
                logger.info("[GROK] Starting new conversation")
                try:
                    new_chat = await self.page.query_selector(self.SELECTORS["new_chat_button"])
                    if new_chat:
                        await new_chat.click()
                        await asyncio.sleep(1)
                except Exception:
                    pass  # May already be on fresh chat
            
            # Find and fill the chat input
            logger.info(f"[GROK] Sending message: {message[:50]}...")
            
            input_selectors = [
                self.SELECTORS["chat_textarea"],
                'textarea',
                '[contenteditable="true"]',
                'div[role="textbox"]'
            ]
            
            input_found = False
            for selector in input_selectors:
                try:
                    await self.page.wait_for_selector(selector, timeout=3000)
                    await self.page.fill(selector, message)
                    logger.info(f"[GROK] Message entered using {selector}")
                    input_found = True
                    break
                except Exception:
                    continue
            
            if not input_found:
                return AIResponse(
                    text="Error: Could not find chat input field",
                    metadata={"error": "input_not_found"},
                    timestamp=datetime.now()
                )
            
            # Send the message
            send_selectors = [
                self.SELECTORS["send_button"],
                'button[type="submit"]',
                'button:has-text("Send")'
            ]
            
            sent = False
            for selector in send_selectors:
                try:
                    btn = await self.page.query_selector(selector)
                    if btn:
                        await btn.click()
                        logger.info("[GROK] Clicked send button")
                        sent = True
                        break
                except Exception:
                    continue
            
            if not sent:
                # Fallback to Enter key
                await self.page.press(input_selectors[0], "Enter")
                logger.info("[GROK] Sent with Enter key")
            
            # Wait for response
            logger.info("[GROK] Waiting for response...")
            await asyncio.sleep(2)  # Initial wait
            
            # Poll for response content
            max_wait = 30  # Max 30 seconds
            waited = 0
            last_response = ""
            
            while waited < max_wait:
                await asyncio.sleep(1)
                waited += 1
                
                # Check if still loading
                loading = await self.page.query_selector(self.SELECTORS["loading_indicator"])
                if loading:
                    logger.debug(f"[GROK] Still loading... ({waited}s)")
                    continue
                
                # Try to get response text
                try:
                    response_el = await self.page.query_selector(self.SELECTORS["response_container"])
                    if response_el:
                        current_text = await response_el.inner_text()
                        if current_text and current_text != last_response:
                            logger.info(f"[GROK] Response updated ({len(current_text)} chars)")
                            last_response = current_text
                            
                            # If response seems complete (no change for 2 seconds)
                            await asyncio.sleep(2)
                            final_el = await self.page.query_selector(self.SELECTORS["response_container"])
                            if final_el:
                                final_text = await final_el.inner_text()
                                if final_text == current_text:
                                    logger.info("[GROK] Response complete")
                                    break
                except Exception:
                    pass
            
            if not last_response:
                return AIResponse(
                    text="Error: No response received from Grok",
                    metadata={"error": "no_response", "waited_seconds": waited},
                    timestamp=datetime.now()
                )
            
            # Update conversation tracking
            self.conversation_id = f"grok_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            return AIResponse(
                text=last_response,
                metadata={
                    "service": "grok",
                    "conversation_id": self.conversation_id,
                    "response_time_seconds": waited,
                    "url": self.page.url
                },
                timestamp=datetime.now(),
                conversation_id=self.conversation_id
            )
            
        except Exception as e:
            logger.error(f"[GROK] Send message error: {e}")
            return AIResponse(
                text=f"Error sending message: {str(e)}",
                metadata={"error": str(e)},
                timestamp=datetime.now()
            )
    
    async def stream_response(self, message: str) -> str:
        """
        Stream response from Grok (simulated - returns full response).
        Grok doesn't expose true streaming via web UI, so we simulate it.
        """
        response = await self.send_message(message)
        
        # Simulate streaming by yielding chunks
        text = response.text
        chunk_size = 50
        for i in range(0, len(text), chunk_size):
            yield text[i:i + chunk_size]
            await asyncio.sleep(0.05)  # Small delay for effect
    
    async def close(self):
        """Clean up browser resources."""
        if self.page:
            try:
                # Extract session cookie for future use
                cookies = await self.page.context.cookies()
                for cookie in cookies:
                    if "x.com" in cookie.get("domain", "") or "x.ai" in cookie.get("domain", ""):
                        logger.info(f"[GROK] Captured session cookie: {cookie['name']}")
            except Exception:
                pass
            
            await self.page.close()
            self.page = None
            logger.info("[GROK] Browser page closed")
        
        self.is_logged_in = False
