1. Full Proposal Document (Ready to Save)
PolySaaS AI Governance, Usage Controls & BYOK Framework
Version 1.0
Date: June 14, 2026
Author: Mike Oliver – Chief Architect, PolySaaS
Executive Summary
PolySaaS’s fixed-price model is a major competitive advantage. However, unrestricted AI usage across Grok, Gemini, Copilot, image generation, and Atomic Services creates significant margin risk.
We propose a comprehensive AI Governance Layer with usage quotas, real-time monitoring, and Bring Your Own Key (BYOK) support. This protects profitability while enabling power users and enterprise customers to scale responsibly.
Business Value

Prevent credit burn before subscription revenue catches up
Create clear upsell path (Pro / Enterprise tiers)
Strong enterprise credibility (“secure, governed, customer-controlled AI”)
Reduce financial volatility

Proposed Features
Usage Controls

Soft limits (warning emails/notifications) + Hard limits (block)
Quotas by tenant, user, service, and time period (daily/monthly)
Real-time usage dashboard
Cost estimation engine

BYOK (Bring Your Own Key)

Tenants register their own API keys (Grok, Anthropic, Google, OpenAI, etc.)
Secure per-tenant encrypted storage
Automatic fallback to platform keys when user keys are exhausted
Mix-and-match support

Monetization Tiers

Starter: Limited platform credits
Pro: Higher limits + basic BYOK
Enterprise: Full BYOK + dedicated orchestration + priority support


2. Technical Design – AIUsageTracker Model + Middleware Skeleton
New Model (dose/models/ai_usage.py)
Pythonclass AIUsageLog(models.Model):
    tenant = models.ForeignKey('Tenant', on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL)
    service_name = models.CharField(max_length=100)          # e.g. "Grok", "AIRewrite", "GenerateImage"
    tokens_input = models.IntegerField(default=0)
    tokens_output = models.IntegerField(default=0)
    estimated_cost_usd = models.DecimalField(max_digits=10, decimal_places=6, default=0)
    timestamp = models.DateTimeField(auto_now_add=True)
    instruction = models.ForeignKey('Instruction', null=True, on_delete=models.SET_NULL)
    metadata = models.JSONField(default=dict)

    class Meta:
        indexes = [models.Index(fields=['tenant', 'timestamp'])]
Middleware (to be added early in request processing):
Pythonclass AIUsageMiddleware(MiddlewareMixin):
    def process_request(self, request):
        request.ai_usage_context = {
            'calls': [],
            'total_estimated_cost': 0
        }

    def process_response(self, request, response):
        # Aggregate and save usage from context
        if hasattr(request, 'ai_usage_context') and request.ai_usage_context['calls']:
            # Save to AIUsageLog + check quotas
            pass
        return response

3. BYOK Architecture Sketch
Key Components:

New model: TenantAIKey (encrypted storage using django-fernet-fields or similar)
Updated AI client abstraction layer (single entry point that checks tenant keys first)
Registry for supported providers (Grok, Anthropic, Gemini, etc.)
Fallback logic: Tenant Key → Platform Key → Block (if limits exceeded)

Example Usage in AtomicService:
Pythondef call_ai(self, prompt, provider="grok"):
    key = self.get_tenant_ai_key(provider) or self.get_platform_key(provider)
    if not key:
        raise PermissionError("No AI key available and limits exceeded")
    # call the provider...