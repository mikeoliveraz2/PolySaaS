# PolySaaS AI WebChat Bridge Architecture Plan

## Executive Summary
Create a Mattermost-based universal AI chat bridge that connects to web-based AI interfaces (Grok, Gemini, Copilot, ChatGPT, Llama, etc.) using browser automation and PolySniffer event capture.

---

## 1. Core Architecture

### 1.1 High-Level Components
```
┌─────────────────────────────────────────────────────────────┐
│                    Mattermost Server                        │
│  ┌─────────────────────────────────────────────────────┐  │
│  │              PolySaaS AI Bridge Bot                 │  │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐            │  │
│  │  │  Grok    │ │  Gemini  │ │  Copilot │  Adapters  │  │
│  │  │ Adapter  │ │ Adapter  │ │ Adapter  │            │  │
│  │  └────┬─────┘ └────┬─────┘ └────┬─────┘            │  │
│  │       └─────────────┼─────────────┘                 │  │
│  │                     │                                 │  │
│  │              ┌──────┴──────┐                          │  │
│  │              │   Browser   │  Playwright/Selenium      │  │
│  │              │  Automation │  Multi-context isolation  │  │
│  │              └──────┬──────┘                          │  │
│  └────────────────────┼───────────────────────────────────┘  │
│                       │                                     │
│              ┌────────┴────────┐                           │
│              │   PolySniffer   │  Captures AI conversations │
│              │   (Event Bus)   │  for audit/AI training    │
│              └─────────────────┘                           │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 Key Design Principles
- **Multi-tenant isolation**: Each tenant gets isolated browser contexts
- **Event-driven**: All AI conversations captured via PolySniffer
- **Plugin architecture**: Easy to add new AI service adapters
- **Rate limiting**: Built-in throttling per AI service
- **Session persistence**: Reuse sessions to avoid repeated logins

---

## 2. Technical Implementation Plan

### 2.1 Phase 1: Foundation (Week 1-2)

#### Mattermost Bot Framework Setup
```python
# dose/ai_bridge/mattermost_bot.py
from mattermostdriver import Driver

class PolySaaSAIBridgeBot:
    """
    Main bot orchestrator for AI web chat bridging.
    Handles:
    - Mattermost message routing
    - User session management  
    - AI adapter lifecycle
    - PolySniffer event emission
    """
    
    def __init__(self, tenant_id, settings):
        self.tenant_id = tenant_id
        self.mm_driver = Driver({
            'url': settings.MATTERMOST_URL,
            'token': settings.BOT_TOKEN,
            'scheme': 'https',
            'port': 443
        })
        self.adapters = {}
        self.browser_pool = BrowserContextPool()
        
    async def handle_message(self, post_data):
        """Route messages to appropriate AI adapter"""
        ai_service = self.detect_ai_request(post_data['message'])
        if ai_service:
            adapter = await self.get_adapter(ai_service)
            response = await adapter.send_message(post_data['message'])
            await self.reply_to_thread(post_data, response)
```

#### Browser Automation Core
```python
# dose/ai_bridge/browser_core.py
from playwright.async_api import async_playwright

class BrowserContextPool:
    """
    Manages isolated browser contexts per tenant/AI service combination.
    Ensures session persistence and multi-tenancy isolation.
    """
    
    def __init__(self, max_contexts=50):
        self.contexts = {}
        self.max_contexts = max_contexts
        self.playwright = None
        
    async def get_context(self, tenant_id: str, ai_service: str):
        key = f"{tenant_id}:{ai_service}"
        if key not in self.contexts:
            browser = await self.playwright.chromium.launch(headless=True)
            context = await browser.new_context(
                storage_state=self.load_session(tenant_id, ai_service),
                viewport={'width': 1920, 'height': 1080}
            )
            self.contexts[key] = context
        return self.contexts[key]
```

### 2.2 Phase 2: AI Service Adapters (Week 3-4)

#### Base Adapter Interface
```python
# dose/ai_bridge/adapters/base.py
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import AsyncIterator, Optional

@dataclass
class AIResponse:
    text: str
    metadata: dict
    timestamp: datetime
    conversation_id: str

class AIWebAdapter(ABC):
    """Base class for AI web chat adapters"""
    
    def __init__(self, browser_context, poly_sniffer):
        self.context = browser_context
        self.sniffer = poly_sniffer
        self.page = None
        
    @abstractmethod
    async def login(self, credentials: dict) -> bool:
        """Authenticate with the AI service"""
        pass
    
    @abstractmethod
    async def send_message(self, message: str, conversation_id: Optional[str] = None) -> AIResponse:
        """Send message and get response"""
        pass
    
    @abstractmethod
    async def stream_response(self, message: str) -> AsyncIterator[str]:
        """Stream response chunks for real-time feel"""
        pass
```

#### Grok Adapter (Example)
```python
# dose/ai_bridge/adapters/grok_adapter.py
class GrokAdapter(AIWebAdapter):
    """
    Adapter for x.ai Grok web interface.
    Handles: login, chat, conversation management
    """
    
    LOGIN_URL = "https://x.ai/login"
    CHAT_URL = "https://x.ai/chat"
    
    async def login(self, credentials: dict) -> bool:
        self.page = await self.context.new_page()
        await self.page.goto(self.LOGIN_URL)
        
        # Handle X.com OAuth flow
        await self.page.fill('input[name="username"]', credentials['username'])
        await self.page.click('button[type="submit"]')
        await self.page.fill('input[name="password"]', credentials['password'])
        await self.page.click('button[type="submit"]')
        
        # Wait for chat interface
        await self.page.wait_for_selector('[data-testid="chat-input"]')
        return True
    
    async def send_message(self, message: str, conversation_id: Optional[str] = None) -> AIResponse:
        # Navigate to specific conversation or new chat
        if conversation_id:
            await self.page.goto(f"{self.CHAT_URL}/{conversation_id}")
        else:
            await self.page.goto(self.CHAT_URL)
        
        # Type and send message
        await self.page.fill('[data-testid="chat-input"]', message)
        await self.page.press('[data-testid="chat-input"]', 'Enter')
        
        # Wait for response with PolySniffer capturing
        response_selector = '[data-testid="assistant-message"]:last-child'
        await self.page.wait_for_selector(response_selector)
        
        response_text = await self.page.inner_text(response_selector)
        
        # Emit to PolySniffer for event capture
        await self.sniffer.capture_ai_event(
            service='grok',
            direction='outbound',
            message=message,
            response=response_text,
            tenant_id=self.context.tenant_id
        )
        
        return AIResponse(
            text=response_text,
            metadata={'service': 'grok', 'model': 'grok-2'},
            timestamp=datetime.now(),
            conversation_id=self.extract_conversation_id()
        )
```

### 2.3 Phase 3: PolySniffer Integration (Week 5)

```python
# dose/ai_bridge/poly_sniffer_bridge.py
class AISnifferBridge:
    """
    Bridges AI conversations into PolySniffer event stream.
    Enables AI training, audit trails, and cross-AI context sharing.
    """
    
    def __init__(self, tenant_id: str):
        self.tenant_id = tenant_id
        
    async def capture_ai_event(self, service: str, direction: str, 
                               message: str, response: str, metadata: dict = None):
        """
        Capture AI interaction as PolySniffer event.
        
        Event Schema:
        - event_type: 'ai_chat_message'
        - source: service name (grok, gemini, etc.)
        - direction: 'inbound' | 'outbound'
        - payload: {message, response, conversation_id}
        - timestamp: ISO8601
        - tenant_id: tenant identifier
        """
        event = {
            'event_type': 'ai_chat_message',
            'source': f'ai_bridge:{service}',
            'direction': direction,
            'payload': {
                'message': message,
                'response': response,
                'metadata': metadata or {}
            },
            'tenant_id': self.tenant_id,
            'timestamp': datetime.now().isoformat()
        }
        
        # Send to PolySniffer event bus
        await poly_sniffer.ingest(event)
        
        # Also emit to Mattermost thread for visibility
        await self.emit_to_mattermost_thread(event)
```

### 2.4 Phase 4: Multi-AI Orchestration (Week 6-7)

#### Multi-AI Chat Controller
```python
# dose/ai_bridge/multi_ai_controller.py
class MultiAIController:
    """
    Manages conversations across multiple AI services simultaneously.
    Enables "AI panel" discussions where multiple AIs respond to the same query.
    """
    
    def __init__(self, tenant_id: str, enabled_ais: list):
        self.tenant_id = tenant_id
        self.adapters = {}
        self.enabled_ais = enabled_ais
        
    async def broadcast_message(self, message: str) -> dict:
        """
        Send message to all enabled AI services concurrently.
        Returns aggregated responses.
        """
        tasks = []
        for ai_name in self.enabled_ais:
            adapter = await self.get_adapter(ai_name)
            tasks.append(self._safe_send(adapter, message))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        return {
            'message': message,
            'responses': {
                ai_name: result for ai_name, result in zip(self.enabled_ais, results)
                if not isinstance(result, Exception)
            }
        }
    
    async def ai_panel_discussion(self, topic: str, rounds: int = 3):
        """
        Facilitate a discussion between multiple AIs on a topic.
        Each round, AIs can respond to previous AI responses.
        """
        conversation = []
        for round_num in range(rounds):
            responses = await self.broadcast_message(topic)
            conversation.append(responses)
            
            # Synthesize responses for next round input
            topic = self.synthesize_responses(responses)
            
        return conversation
```

---

## 3. AI Service-Specific Implementation Details

### 3.1 Grok (x.ai)
- **Auth**: X.com OAuth
- **Interface**: Web-based chat
- **Challenges**: Rate limiting, anti-automation detection
- **Mitigation**: Human-like delays, session persistence

### 3.2 Gemini (Google)
- **Auth**: Google OAuth
- **Interface**: Web + API (prefer API for reliability)
- **API Endpoint**: `generativelanguage.googleapis.com`
- **Fallback**: Web automation if API limits hit

### 3.3 Copilot (Microsoft)
- **Auth**: Microsoft Account
- **Interface**: Web-based with heavy JavaScript
- **Challenges**: Dynamic DOM, bot detection
- **Mitigation**: Slow typing simulation, random delays

### 3.4 ChatGPT (OpenAI)
- **Auth**: OpenAI account
- **Interface**: Web + API
- **Recommendation**: Use API for primary, web as fallback
- **API Model**: `gpt-4`, `gpt-4-turbo`, `gpt-3.5-turbo`

### 3.5 Llama (Meta/Various)
- **Options**:
  - Self-hosted via Ollama (preferred for privacy)
  - Web interfaces (HuggingFace, etc.)
- **Implementation**: REST API to local Ollama instance

---

## 4. Deployment Architecture

### 4.1 Docker Services
```yaml
# docker-compose.ai-bridge.yml
version: '3.8'
services:
  ai-bridge-bot:
    build: ./ai_bridge
    environment:
      - MATTERMOST_URL=https://mattermost.polysaas.online
      - BOT_TOKEN=${MATTERMOST_BOT_TOKEN}
      - POLYSNIFFER_ENDPOINT=http://polysniffer:8080
    volumes:
      - browser_sessions:/app/sessions
      - playwright_cache:/root/.cache/ms-playwright
    
  browser-pool:
    image: browserless/chrome:latest
    environment:
      - MAX_CONCURRENT_SESSIONS=50
      - CONNECTION_TIMEOUT=300000
    ports:
      - "3000:3000"
    
  ollama:
    image: ollama/ollama:latest
    volumes:
      - ollama_models:/root/.ollama
    # Self-hosted Llama models
```

### 4.2 Kubernetes Considerations
- **Browser automation**: Run in dedicated pods with VNC for debugging
- **Session storage**: Redis for session persistence across restarts
- **Secrets**: Kubernetes secrets for AI service credentials
- **Scaling**: Horizontal pod autoscaling based on queue depth

---

## 5. Security & Compliance

### 5.1 Credential Management
```python
# dose/ai_bridge/credential_vault.py
from django.conf import settings
import hvac  # HashiCorp Vault client

class AICredentialVault:
    """
    Secure storage for AI service credentials.
    Uses HashiCorp Vault or Django encrypted fields.
    """
    
    def store_credentials(self, tenant_id: str, service: str, credentials: dict):
        """Encrypt and store credentials"""
        path = f"ai-bridge/{tenant_id}/{service}"
        self.vault.secrets.kv.v2.create_or_update_secret(
            path=path,
            secret=credentials
        )
    
    def get_credentials(self, tenant_id: str, service: str) -> dict:
        """Retrieve decrypted credentials"""
        path = f"ai-bridge/{tenant_id}/{service}"
        secret = self.vault.secrets.kv.v2.read_secret_version(path=path)
        return secret['data']['data']
```

### 5.2 Data Privacy
- **PII scrubbing**: Remove sensitive data before sending to AI
- **Audit logging**: All AI interactions logged via PolySniffer
- **Data retention**: Configurable retention policies per tenant
- **GDPR compliance**: Right to be forgotten implemented

---

## 6. Mattermost Integration UX

### 6.1 Bot Commands
```
/ai grok "What are the latest trends in SaaS?"
/ai gemini "Analyze this code snippet..."
/ai all "What do you think about AI bridges?"
/ai panel "Discuss: Best practices for multi-tenant architectures"
```

### 6.2 Thread-Based Conversations
- Each AI conversation starts a Mattermost thread
- Replies in thread = follow-up questions to same AI
- @mentions route to specific AI service
- Thread persistence = conversation history

### 6.3 Rich Responses
```python
# Example rich response with metadata
{
    "attachments": [{
        "fallback": "Grok response",
        "color": "#1DA1F2",
        "title": "Grok says:",
        "text": "The latest trends in SaaS include...",
        "fields": [
            {"title": "Model", "value": "grok-2", "short": True},
            {"title": "Latency", "value": "1.2s", "short": True}
        ],
        "footer": "via PolySaaS AI Bridge"
    }]
}
```

---

## 7. Implementation Roadmap

| Phase | Duration | Deliverable | Priority |
|-------|----------|-------------|----------|
| 1.1 | Week 1 | Mattermost bot foundation + auth | High |
| 1.2 | Week 2 | Browser automation core | High |
| 2.1 | Week 3 | Grok + Gemini adapters | High |
| 2.2 | Week 4 | Copilot + ChatGPT adapters | High |
| 3.0 | Week 5 | PolySniffer integration | Medium |
| 4.0 | Week 6 | Multi-AI orchestration | Medium |
| 4.1 | Week 7 | AI panel discussions | Low |
| 5.0 | Week 8 | Security hardening + docs | High |

---

## 8. Success Metrics

- **Response time**: < 5 seconds for simple queries
- **Availability**: 99.5% uptime for bot service
- **Concurrent users**: Support 100+ concurrent AI conversations
- **Cost efficiency**: Use APIs where cheaper than browser automation
- **User adoption**: > 50% of tenants enable at least one AI bridge

---

## 9. Open Questions

1. **Legal**: Terms of service compliance for automated access to AI services
2. **Rate limiting**: How to handle aggressive rate limits from AI providers
3. **Multi-tenancy**: Should tenants share browser pool or be fully isolated
4. **Fallback**: Strategy when AI service blocks automation
5. **Training data**: Can we use captured conversations to fine-tune models

---

**Document Version**: 1.0  
**Last Updated**: 2026-05-02  
**Next Review**: After Phase 2 completion
