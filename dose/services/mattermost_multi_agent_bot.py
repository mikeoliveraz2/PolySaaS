"""
Mattermost Multi-Agent Bot Service

Provides multiple AI personas in Mattermost Town Square:
- @windsurf - Code assistant, can read files and post source
- @code-reviewer - Code evaluator and analyzer  
- @dev-helper - General development assistant
- @polysaas-guide - PolySaaS platform expert

Usage:
1. Say "hello everyone" -> All bots respond with introductions
2. @windsurf show me mattermost_handler.py -> Bot reads and posts source
3. @code-reviewer evaluate the code above -> Bot analyzes posted code
"""
import os
import re
import json
import logging
import asyncio
from typing import Dict, List, Optional, Callable
from datetime import datetime
from dataclasses import dataclass
from pathlib import Path

import requests
from django.conf import settings

logger = logging.getLogger(__name__)


@dataclass
class AIAgent:
    """Represents an AI agent persona in Mattermost."""
    name: str
    username: str  # Mattermost bot username
    bot_token: str
    icon_emoji: str
    personality: str
    system_prompt: str
    capabilities: List[str]
    trigger_words: List[str]
    response_handler: Optional[Callable] = None


class MattermostMultiAgentBot:
    """
    Multi-agent bot system for Mattermost Town Square.
    
    Manages multiple AI personas that can:
    - Respond to general channel messages
    - Be @mentioned for specific tasks
    - Read files and post source code
    - Evaluate and analyze code
    """
    
    def __init__(self, mattermost_url: str = None, team_name: str = None):
        self.mattermost_url = mattermost_url or getattr(
            settings, 'MATTERMOST_URL', 'https://polysaas-mattermost.onrender.com'
        )
        self.team_name = team_name or 'polysaas-dev-team'
        self.agents: Dict[str, AIAgent] = {}
        self.channel_id: Optional[str] = None
        self._setup_agents()
    
    def _setup_agents(self):
        """Initialize all AI agent personas."""
        
        # Windsurf Agent - Code assistant with file access
        self.agents['windsurf'] = AIAgent(
            name="Windsurf",
            username="windsurf",
            bot_token=os.getenv('WINDSURF_BOT_TOKEN', ''),
            icon_emoji=":computer:",
            personality="Expert code assistant with direct access to the PolySaaS codebase",
            system_prompt="""You are Windsurf, an expert code assistant integrated with the PolySaaS codebase.
You can read source files and provide code snippets. Be concise but thorough.
When asked to show code, read the actual file and post the relevant sections.
Always format code blocks properly with language tags.""",
            capabilities=['read_files', 'post_code', 'explain_code', 'debug'],
            trigger_words=['windsurf', 'show me', 'source', 'code'],
            response_handler=self._handle_windsurf_request
        )
        
        # Code Reviewer Agent - Code evaluator
        self.agents['code-reviewer'] = AIAgent(
            name="Code Reviewer",
            username="code-reviewer",
            bot_token=os.getenv('CODE_REVIEWER_BOT_TOKEN', ''),
            icon_emoji=":mag:",
            personality="Senior code reviewer focused on quality, security, and best practices",
            system_prompt="""You are a senior code reviewer. Analyze code for:
- Security vulnerabilities
- Performance issues
- Code smell and anti-patterns
- Best practices and style
- Maintainability and readability

Be constructive but thorough. Provide specific line-by-line feedback when relevant.
Rate code quality 1-10 with explanation.""",
            capabilities=['evaluate_code', 'security_audit', 'performance_review'],
            trigger_words=['review', 'evaluate', 'analyze code', 'code review'],
            response_handler=self._handle_code_reviewer_request
        )
        
        # Dev Helper Agent - General development assistance
        self.agents['dev-helper'] = AIAgent(
            name="Dev Helper",
            username="dev-helper",
            bot_token=os.getenv('DEV_HELPER_BOT_TOKEN', ''),
            icon_emoji=":hammer_and_wrench:",
            personality="Friendly development assistant for general programming questions",
            system_prompt="""You are a helpful development assistant. Answer programming questions,
suggest solutions, explain concepts, and help debug issues. Be friendly and approachable.
Use examples when helpful. If unsure, be honest about limitations.""",
            capabilities=['answer_questions', 'explain_concepts', 'suggest_solutions'],
            trigger_words=['help', 'how to', 'question', 'explain'],
            response_handler=self._handle_dev_helper_request
        )
        
        # PolySaaS Guide - Platform expert
        self.agents['polysaas-guide'] = AIAgent(
            name="PolySaaS Guide",
            username="polysaas-guide",
            bot_token=os.getenv('POLYSAAS_GUIDE_BOT_TOKEN', ''),
            icon_emoji=":guide_dog:",
            personality="Expert on PolySaaS platform architecture and features",
            system_prompt="""You are the PolySaaS platform guide. You know the entire system architecture:
- Passthrough services (Odoo, Mattermost, Nextcloud)
- PolySniffer and Dynamic Orchestration
- Multi-tenant Django architecture
- ChatKeeper and other integrations

Help users understand how to use PolySaaS features and explain the platform architecture.""",
            capabilities=['explain_platform', 'architecture_help', 'feature_guide'],
            trigger_words=['polysaas', 'platform', 'how does', 'architecture'],
            response_handler=self._handle_polysaas_guide_request
        )
    
    def _get_bot_headers(self, agent: AIAgent) -> Dict:
        """Get HTTP headers for bot API calls."""
        return {
            'Authorization': f'Bearer {agent.bot_token}',
            'Content-Type': 'application/json'
        }
    
    def _find_channel_id(self, agent: AIAgent, channel_name: str = 'town-square') -> Optional[str]:
        """Find channel ID by name."""
        try:
            # Get teams
            resp = requests.get(
                f'{self.mattermost_url}/api/v4/teams/name/{self.team_name}',
                headers=self._get_bot_headers(agent)
            )
            if resp.status_code != 200:
                logger.error(f"Failed to get team: {resp.text}")
                return None
            
            team_id = resp.json()['id']
            
            # Get channels
            resp = requests.get(
                f'{self.mattermost_url}/api/v4/teams/{team_id}/channels',
                headers=self._get_bot_headers(agent)
            )
            if resp.status_code != 200:
                logger.error(f"Failed to get channels: {resp.text}")
                return None
            
            channels = resp.json()
            for ch in channels:
                if ch['name'] == channel_name or ch['display_name'].lower() == channel_name.lower():
                    return ch['id']
            
            return None
        except Exception as e:
            logger.error(f"Error finding channel: {e}")
            return None
    
    def _post_message(self, agent: AIAgent, channel_id: str, message: str, 
                      thread_id: str = None, props: Dict = None) -> bool:
        """Post a message as the bot."""
        try:
            payload = {
                'channel_id': channel_id,
                'message': message,
            }
            if thread_id:
                payload['root_id'] = thread_id
            if props:
                payload['props'] = props
            
            resp = requests.post(
                f'{self.mattermost_url}/api/v4/posts',
                headers=self._get_bot_headers(agent),
                json=payload
            )
            
            if resp.status_code == 201:
                logger.info(f"[{agent.name}] Posted message successfully")
                return True
            else:
                logger.error(f"[{agent.name}] Failed to post: {resp.status_code} {resp.text}")
                return False
        except Exception as e:
            logger.error(f"[{agent.name}] Error posting message: {e}")
            return False
    
    def _read_file_content(self, file_path: str) -> Optional[str]:
        """Read file content from the codebase."""
        try:
            # Resolve path relative to project root
            project_root = Path(settings.BASE_DIR)
            full_path = project_root / file_path
            
            # Security: ensure path is within project
            try:
                full_path.resolve().relative_to(project_root.resolve())
            except ValueError:
                logger.warning(f"Path {file_path} is outside project root")
                return None
            
            if not full_path.exists():
                logger.warning(f"File not found: {full_path}")
                return None
            
            with open(full_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            logger.error(f"Error reading file {file_path}: {e}")
            return None
    
    def _get_ai_response(self, agent: AIAgent, user_message: str, 
                         context: str = None) -> str:
        """Get AI response from LLM provider."""
        try:
            # Use OpenAI for responses
            api_key = os.getenv('OPENAI_API_KEY')
            if not api_key:
                return f"[{agent.name}] AI service not configured (missing OPENAI_API_KEY)"
            
            import openai
            client = openai.OpenAI(api_key=api_key)
            
            messages = [
                {"role": "system", "content": agent.system_prompt}
            ]
            
            if context:
                messages.append({"role": "user", "content": f"Context:\n{context}"})
            
            messages.append({"role": "user", "content": user_message})
            
            response = client.chat.completions.create(
                model="gpt-4",
                messages=messages,
                temperature=0.7,
                max_tokens=2000
            )
            
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Error getting AI response: {e}")
            return f"[{agent.name}] Sorry, I encountered an error processing your request."
    
    # ============== Agent-Specific Handlers ==============
    
    def _handle_windsurf_request(self, agent: AIAgent, message: str, 
                                 channel_id: str, thread_id: str = None) -> bool:
        """Handle requests to Windsurf agent."""
        message_lower = message.lower()
        
        # Check if user wants to see a file
        file_patterns = [
            r'show me ([\w\./]+\.py)',
            r'show ([\w\./]+\.py)',
            r'source of ([\w\./]+\.py)',
            r'code for ([\w\./]+\.py)',
            r'post ([\w\./]+\.py)',
        ]
        
        for pattern in file_patterns:
            match = re.search(pattern, message_lower)
            if match:
                file_path = match.group(1)
                content = self._read_file_content(file_path)
                
                if content:
                    # Truncate if too long
                    if len(content) > 3000:
                        content = content[:3000] + "\n\n... (truncated, file is longer)"
                    
                    formatted = f"```python\n{content}\n```"
                    response = f"Here's the source of `{file_path}`:\n\n{formatted}"
                else:
                    response = f"Sorry, I couldn't find or read `{file_path}`."
                
                return self._post_message(agent, channel_id, response, thread_id)
        
        # General Windsurf response
        ai_response = self._get_ai_response(agent, message)
        return self._post_message(agent, channel_id, ai_response, thread_id)
    
    def _handle_code_reviewer_request(self, agent: AIAgent, message: str,
                                      channel_id: str, thread_id: str = None,
                                      recent_posts: List[Dict] = None) -> bool:
        """Handle requests to Code Reviewer agent."""
        message_lower = message.lower()
        
        # Check if user wants to evaluate code from recent posts
        if any(word in message_lower for word in ['evaluate', 'review', 'analyze']):
            # Look for code blocks in recent posts
            code_to_review = None
            
            if recent_posts:
                for post in reversed(recent_posts):  # Check most recent first
                    content = post.get('message', '')
                    # Extract code blocks
                    code_blocks = re.findall(r'```[\w]*\n(.*?)```', content, re.DOTALL)
                    if code_blocks:
                        code_to_review = code_blocks[-1]  # Most recent code block
                        break
            
            if code_to_review:
                prompt = f"Please evaluate this code:\n\n```\n{code_to_review}\n```"
                ai_response = self._get_ai_response(agent, prompt)
            else:
                ai_response = "I don't see any code to evaluate in the recent messages. Please share the code you'd like me to review (in a code block)."
            
            return self._post_message(agent, channel_id, ai_response, thread_id)
        
        # General code reviewer response
        ai_response = self._get_ai_response(agent, message)
        return self._post_message(agent, channel_id, ai_response, thread_id)
    
    def _handle_dev_helper_request(self, agent: AIAgent, message: str,
                                   channel_id: str, thread_id: str = None) -> bool:
        """Handle requests to Dev Helper agent."""
        ai_response = self._get_ai_response(agent, message)
        return self._post_message(agent, channel_id, ai_response, thread_id)
    
    def _handle_polysaas_guide_request(self, agent: AIAgent, message: str,
                                       channel_id: str, thread_id: str = None) -> bool:
        """Handle requests to PolySaaS Guide agent."""
        ai_response = self._get_ai_response(agent, message)
        return self._post_message(agent, channel_id, ai_response, thread_id)
    
    # ============== Public API ==============
    
    def say_hello_all(self, channel_id: str = None):
        """All agents say hello in the channel."""
        if not channel_id:
            # Find town-square using first agent
            first_agent = list(self.agents.values())[0]
            channel_id = self._find_channel_id(first_agent, 'town-square')
        
        if not channel_id:
            logger.error("Could not find Town Square channel")
            return False
        
        self.channel_id = channel_id
        
        # Each agent introduces themselves
        introductions = [
            ("windsurf", "👋 Hello! I'm **Windsurf**, your code assistant. I can show you source files, explain code, and help with debugging. Just ask me to `show me filename.py` or tag me with @windsurf."),
            ("code-reviewer", "👋 Hi! I'm the **Code Reviewer**. I analyze code for security, performance, and best practices. Share some code and ask me to `@code-reviewer evaluate this`!"),
            ("dev-helper", "👋 Hey there! I'm **Dev Helper**, here to answer your programming questions and help with development challenges. How can I assist you today?"),
            ("polysaas-guide", "👋 Greetings! I'm the **PolySaaS Guide**. I know all about the platform architecture, passthrough services, and how everything works together. Ask me anything about PolySaaS!"),
        ]
        
        for agent_key, intro in introductions:
            agent = self.agents.get(agent_key)
            if agent and agent.bot_token:
                self._post_message(agent, channel_id, intro)
        
        # Main introduction message
        main_bot = self.agents['windsurf']  # Use windsurf as "lead" bot
        welcome = """🎉 **Welcome to PolySaaS Town Square!** 

You now have **4 AI assistants** ready to help:
• **@windsurf** - Shows source code and explains implementation
• **@code-reviewer** - Evaluates code quality and security  
• **@dev-helper** - Answers general development questions
• **@polysaas-guide** - Explains PolySaaS platform architecture

Try saying **"hello everyone"** or mention any bot by name!
"""
        self._post_message(main_bot, channel_id, welcome)
        
        return True
    
    def handle_channel_message(self, message_data: Dict):
        """
        Handle a message posted to the channel.
        
        Args:
            message_data: Mattermost post data including:
                - message: text content
                - user_id: sender
                - channel_id: channel
                - id: post id (for threading)
        """
        message = message_data.get('message', '')
        channel_id = message_data.get('channel_id')
        post_id = message_data.get('id')
        
        if not message or not channel_id:
            return
        
        # Don't respond to bot messages
        props = message_data.get('props', {})
        if props.get('from_bot'):
            return
        
        message_lower = message.lower()
        
        # Check for "hello everyone" greeting
        if 'hello everyone' in message_lower or 'hi everyone' in message_lower:
            # All bots respond with greetings
            self.say_hello_all(channel_id)
            return
        
        # Check for @mentions of specific bots
        for agent_key, agent in self.agents.items():
            mention_patterns = [
                f'@{agent.username}',
                f'@{agent.username.lower()}',
                agent.username.lower(),
            ]
            
            is_mentioned = any(pattern in message_lower for pattern in mention_patterns)
            
            if is_mentioned:
                logger.info(f"[{agent.name}] Was mentioned, handling request")
                
                if agent.response_handler:
                    # Get recent posts for context (for code review)
                    recent_posts = self._get_recent_posts(channel_id, limit=10)
                    
                    if agent_key == 'code-reviewer':
                        agent.response_handler(agent, message, channel_id, post_id, recent_posts)
                    else:
                        agent.response_handler(agent, message, channel_id, post_id)
                return
        
        # Check for trigger words (general channel messages)
        for agent_key, agent in self.agents.items():
            for trigger in agent.trigger_words:
                if trigger in message_lower:
                    if agent.response_handler:
                        agent.response_handler(agent, message, channel_id, post_id)
                    return
    
    def _get_recent_posts(self, channel_id: str, limit: int = 10) -> List[Dict]:
        """Get recent posts from channel for context."""
        try:
            agent = list(self.agents.values())[0]  # Use first agent's token
            resp = requests.get(
                f'{self.mattermost_url}/api/v4/channels/{channel_id}/posts',
                headers=self._get_bot_headers(agent),
                params={'limit': limit}
            )
            
            if resp.status_code == 200:
                data = resp.json()
                posts = list(data.get('posts', {}).values())
                posts.sort(key=lambda p: p.get('create_at', 0))
                return posts
        except Exception as e:
            logger.error(f"Error getting recent posts: {e}")
        
        return []
    
    def start_webhook_listener(self, port: int = 5000):
        """Start webhook listener for Mattermost outgoing webhooks."""
        from flask import Flask, request, jsonify
        
        app = Flask(__name__)
        
        @app.route('/webhook/mattermost-bot', methods=['POST'])
        def webhook_handler():
            data = request.json
            if data:
                self.handle_channel_message(data)
            return jsonify({'status': 'ok'})
        
        logger.info(f"Starting Mattermost bot webhook listener on port {port}")
        app.run(host='0.0.0.0', port=port)


# ============== Celery Tasks ==============

try:
    from celery import shared_task
    
    @shared_task
    def setup_mattermost_agents_in_town_square():
        """Celery task: Initialize all agents in Town Square."""
        bot = MattermostMultiAgentBot()
        return bot.say_hello_all()
    
    @shared_task
    def handle_mattermost_message(message_data: Dict):
        """Celery task: Process a Mattermost message."""
        bot = MattermostMultiAgentBot()
        bot.handle_channel_message(message_data)
        return True

except ImportError:
    # Celery not available
    pass
