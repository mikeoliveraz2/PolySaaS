"""
PolySaaS AI Bridge Bot for Mattermost.
Routes messages to AI adapters and posts responses back.
"""
import asyncio
import logging
from typing import Dict, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class PolySaaSAIBridgeBot:
    """Main bot orchestrator for AI web chat bridging."""
    
    ADAPTER_REGISTRY = {
        'kimi': 'dose.ai_bridge.adapters.kimi_adapter.KimiAdapter',
        'claude': 'dose.ai_bridge.adapters.claude_adapter.ClaudeAdapter',
        'grok': 'dose.ai_bridge.adapters.grok_adapter.GrokAdapter',
    }
    
    def __init__(self, tenant_id: str, mattermost_url: str, bot_token: str, 
                 poly_sniffer=None, browser_pool=None):
        self.tenant_id = tenant_id
        self.mattermost_url = mattermost_url
        self.bot_token = bot_token
        self.poly_sniffer = poly_sniffer
        self.browser_pool = browser_pool
        self.sessions: Dict[tuple, object] = {}
        self._mm_client = None
    
    async def handle_webhook(self, payload: dict) -> dict:
        """Handle incoming Mattermost webhook."""
        text = payload.get('text', '')
        user_id = payload.get('user_id')
        channel_id = payload.get('channel_id')
        post_id = payload.get('post_id')
        
        service_name = self._detect_ai_service(text)
        if not service_name:
            return {'text': 'Mention an AI with @kimi, @claude, @grok, or use /ai <service> <message>'}
        
        clean_message = self._extract_message(text, service_name)
        session_key = (user_id, service_name)
        adapter = await self._get_or_create_adapter(session_key, service_name)
        
        if not adapter:
            return {'text': f'Sorry, {service_name} is not available.'}
        
        try:
            response = await asyncio.wait_for(adapter.send_message(clean_message), timeout=120)
            formatted = self._format_response(service_name, response)
            return {
                'response_type': 'in_channel',
                'text': formatted['text'],
                'attachments': formatted.get('attachments', [])
            }
        except Exception as e:
            logger.error(f"[AI_BRIDGE] Error: {e}")
            return {'text': f'❌ Error: {str(e)[:200]}'}
    
    async def _get_or_create_adapter(self, session_key: tuple, service_name: str):
        """Get or create adapter session."""
        if session_key in self.sessions:
            adapter = self.sessions[session_key]
            if await adapter.health_check():
                return adapter
            await adapter.close()
            del self.sessions[session_key]
        
        adapter_class = self._load_adapter_class(service_name)
        if not adapter_class:
            return None
        
        browser_context = await self.browser_pool.get_context(
            self.tenant_id, service_name
        ) if self.browser_pool else None
        
        adapter = adapter_class(browser_context, self.poly_sniffer)
        credentials = await self._get_credentials(service_name)
        if credentials:
            login_success = await adapter.login(credentials)
            if not login_success:
                return None
        
        self.sessions[session_key] = adapter
        return adapter
    
    def _load_adapter_class(self, service_name: str):
        """Dynamically load adapter class."""
        class_path = self.ADAPTER_REGISTRY.get(service_name)
        if not class_path:
            return None
        try:
            module_path, class_name = class_path.rsplit('.', 1)
            module = __import__(module_path, fromlist=[class_name])
            return getattr(module, class_name)
        except Exception as e:
            logger.error(f"Failed to load adapter {class_path}: {e}")
            return None
    
    async def _get_credentials(self, service_name: str) -> dict:
        """Retrieve credentials from secure vault."""
        return {}
    
    def _detect_ai_service(self, text: str) -> Optional[str]:
        """Detect which AI service is mentioned."""
        text_lower = text.lower()
        for service in self.ADAPTER_REGISTRY:
            if f'@{service}' in text_lower:
                return service
        aliases = {
            'kimi': ['@kimi', '@moonshot'],
            'claude': ['@claude', '@anthropic'],
            'grok': ['@grok', '@xai', '@x_ai'],
        }
        for service, service_aliases in aliases.items():
            for alias in service_aliases:
                if alias in text_lower:
                    return service
        return None
    
    def _extract_message(self, text: str, service_name: str) -> str:
        """Remove AI mention from message."""
        for prefix in [f'@{service_name}', f'@{service_name.title()}']:
            text = text.replace(prefix, '', 1)
        return text.strip()
    
    def _format_response(self, service_name: str, response) -> dict:
        """Format AI response for Mattermost."""
        emoji_map = {'kimi': '🌙', 'claude': '🧠', 'grok': '⚡'}
        emoji = emoji_map.get(service_name, '🤖')
        time_str = f"{response.metadata.get('response_time_seconds', 0):.1f}s"
        return {
            'text': f"{emoji} **{service_name.title()}** ({time_str}):\n{response.text[:2000]}",
            'attachments': [{
                'footer': f'via PolySaaS AI Bridge',
            }]
        }
    
    async def close_all_sessions(self):
        """Clean up all sessions."""
        for _, adapter in list(self.sessions.items()):
            try:
                await adapter.close()
            except Exception:
                pass
        self.sessions.clear()
