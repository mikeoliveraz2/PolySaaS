# --- Gmail Admin View Integration ---
from django.apps import apps
from django.contrib import admin
from django.urls import path
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from django.views import View
from django.shortcuts import render

class GmailAdminView(View):
    """Gmail view for admin interface - requires staff status"""
    @method_decorator(staff_member_required)
    def get(self, request):
        # Get admin site context to ensure sidebar, theme, and other admin UI elements render
        context = admin.site.each_context(request)
        context.update({'user': request.user})
        return render(request, 'admin/gmail_content.html', context)

class GmailUserView(View):
    """Gmail view for regular users - only requires login"""
    @method_decorator(login_required)
    def get(self, request):
        # Regular user context (no admin sidebar)
        context = {'user': request.user}
        return render(request, 'admin/gmail_content.html', context)

# Removed custom admin.site.get_urls override to restore default admin URL patterns
from .models import DeepSeekPrompt, AtomicService
from .admin_base import TenantAwareModelAdmin
class AtomicServiceAdmin(admin.ModelAdmin):
    list_display = ('service_name', 'python_file', 'description', 'created_at', 'updated_at')
    search_fields = ('service_name', 'description')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        (None, {
            'fields': ('service_name', 'python_file', 'description', 'config_json')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def get_changeform_initial_data(self, request):
        return {'config_json': {'name': 'value'}}

admin.site.register(AtomicService, AtomicServiceAdmin)

class DoseAIPromptAdmin(admin.ModelAdmin):
    list_display = ('user', 'prompt', 'response', 'created_at')
    search_fields = ('user__username', 'prompt', 'response')
    readonly_fields = ('response', 'created_at')
    ordering = ('-created_at',)
    # Update verbose names for DoseAI branding
    def get_model_perms(self, request):
        return super().get_model_perms(request)
    def get_queryset(self, request):
        return super().get_queryset(request)
        def get_form(self, request, obj=None, **kwargs):
            # Guarantee tenant exists in DB before any form processing or save
            from dose.tenant_utils import get_current_tenant
            from dose.models.tenant import Tenant
            tenant = get_current_tenant(request)
            if tenant:
                try:
                    Tenant.objects.get(slug=tenant.slug)
                except Tenant.DoesNotExist:
                    Tenant.objects.create(
                        slug=getattr(tenant, 'slug', f'session-{tenant.id}'),
                        name=getattr(tenant, 'name', 'Session Tenant'),
                        schema_name=getattr(tenant, 'schema_name', f'session_{tenant.id}')
                    )
            form = super().get_form(request, obj, **kwargs)
            return form
    def get_fieldsets(self, request, obj=None):
        return super().get_fieldsets(request, obj)
    def get_list_display(self, request):
        return super().get_list_display(request)
    def get_search_fields(self, request):
        return super().get_search_fields(request)
    def get_readonly_fields(self, request, obj=None):
        return super().get_readonly_fields(request, obj)
    def get_ordering(self, request):
        return super().get_ordering(request)
    class Meta:
        verbose_name = "DoseAI Prompt"
        verbose_name_plural = "DoseAI Prompts"

admin.site.register(DeepSeekPrompt, DoseAIPromptAdmin)
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from django import forms
from admin_interface.models import Theme

# Import existing models
from .models import Instruction, CallBackData, Task, MLEngine, MLPrompt, PassThroughEndpoint, DoseMessage, UserProfile, UserTenantMembership, PolySnifferRun, Subscription, AppCredential
# Import polysniffer admin to register TrafficLog
try:
    import dose.polysniffer.admin  # noqa: F401
except ImportError:
    pass
# UserProfile admin for view/edit
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'tenant', 'created_at')
    search_fields = ('user__username', 'tenant__name')
    readonly_fields = ('created_at',)
    fieldsets = (
        (None, {
            'fields': ('user', 'tenant')
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )

    def save_model(self, request, obj, form, change):
        if not change and obj.tenant:
            from dose.utils import check_user_limit
            allowed, msg = check_user_limit(obj.tenant)
            if not allowed:
                from django.contrib import messages
                messages.error(request, msg)
                return
        super().save_model(request, obj, form, change)

admin.site.register(UserProfile, UserProfileAdmin)


class UserTenantMembershipAdmin(admin.ModelAdmin):
    list_display = ("user", "tenant", "role", "updated_at")
    list_filter = ("role",)
    search_fields = ("user__username", "tenant__name")
    raw_id_fields = ("user", "tenant")


admin.site.register(UserTenantMembership, UserTenantMembershipAdmin)

from django import forms
from dose.services.atomic_services_registry import init_atomic_services_registry, ATOMIC_SERVICE_REGISTRY

# Try to import new session-based models (they may not exist yet)
try:
    from .models import Tenant, UserProfile, MLTaxonomy, MLDataset, NavigationPanel, NavigationItem, DashboardButton, IgnorePath, UserRequestTracker, MQInput, MQOutput, MQConfig, TenantApp
    NEW_MODELS_AVAILABLE = True
except ImportError:
    NEW_MODELS_AVAILABLE = False

import logging
logger = logging.getLogger(__name__)
logger.info("Now logging in admin")

# Your existing admin classes
class CallBackDataAdmin(TenantAwareModelAdmin):
    fieldsets = [
        (None, {'fields': ['matchingEventKey', 'description', 'parameters_json', 'callbackdata', 'pub_date']}),
    ]

    list_display = ('matchingEventKey', 'description', 'parameters_json', 'callbackdata')
    list_filter = ['pub_date']
    search_fields = ['matchingEventKey']

    def change_view(self, request, object_id, form_url='', extra_context=None):
        from django.contrib import messages
        messages.add_message(request, messages.INFO, "Viewing CallBackData details.")
        return super().change_view(request, object_id, form_url, extra_context)

class TaskAdmin(TenantAwareModelAdmin):
    fieldsets = [
        (None, {'fields': ['title', 'description', 'completed',
                          'matchingEventKey', 'parameters_json']}),
    ]

    list_display = ('title', 'description', 'completed',
                   'matchingEventKey', 'parameters_json', 'created_at',
                   'completed_at')
    list_filter = ['created_at']
    search_fields = ['title']
    readonly_fields = ('created_at', 'completed_at')

class MLEngineAdmin(admin.ModelAdmin):
    class MLEngineForm(forms.ModelForm):
        ENGINE_CHOICES = [
            ("MLflow", "MLflow (Experiment Tracking & Registry)"),
            ("ClearML", "ClearML (Experiment & Data Management)"),
            ("ZenML", "ZenML (Production Pipelines)"),
            ("BentoML", "BentoML (Model Serving APIs)"),
            ("Metaflow", "Metaflow (Workflow Orchestration)"),
            ("Hugging Face Transformers", "Hugging Face Transformers (LLM/NLP)"),
            ("Kedro", "Kedro (Modular Pipelines)"),
        ]

        engineName = forms.ChoiceField(
            choices=ENGINE_CHOICES,
            required=True,
            label="Engine name",
            help_text="Select one of the recommended ML engines for tenant configuration.",
        )

        class Meta:
            model = MLEngine
            fields = "__all__"

    form = MLEngineForm
    fieldsets = [
        (None, {'fields': ['engineName', 'engineEndPoint', 'matchingEventKey', 'description']}),
    ]

    list_display = ('engineName', 'matchingEventKey', 'description')
    list_filter = ['engineName']
    search_fields = ['engineName']


class MLPromptAdmin(TenantAwareModelAdmin):
    fieldsets = [
        (
            None,
            {
                'fields': ['tenant', 'key', 'description'],
                'description': (
                    'Named prompts for this tenant. Use the same key string in matchingEventKey '
                    'on engines, taxonomies, or datasets when you want to align them.'
                ),
            },
        ),
        ('Prompt text', {'fields': ['prompt_text']}),
    ]
    list_display = ('key', 'description', 'tenant')
    list_filter = ('tenant',)
    search_fields = ('key', 'description', 'prompt_text')

class InstructionForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        init_atomic_services_registry()
        choices = [(name, name) for name in ATOMIC_SERVICE_REGISTRY.keys()]
        choices.append(('', 'Custom Endpoint URL'))
        self.fields['executescript'] = forms.ChoiceField(
            choices=choices,
            required=False,
            label='Atomic Service',
            help_text='Select an atomic service or choose Custom Endpoint URL.'
        )

    class Meta:
        model = Instruction
        fields = '__all__'

class InstructionAdmin(TenantAwareModelAdmin):
    form = InstructionForm
    fieldsets = [
        ('Matching Rule', {
            'fields': ['match_type', 'requestpath', 'match_extra'],
            'description': (
                '<b>match_type</b>: how requestpath is interpreted. '
                'Examples — <i>path</i>: "/odoo/accounting", '
                '<i>action_id</i>: "account.action_invoice", '
                '<i>menu_id</i>: "116", '
                '<i>regex</i>: r"/odoo/(accounting|invoic)", '
                '<i>contains</i>: "invoice".<br>'
                '<b>match_extra</b> adds AND conditions (all must be true): '
                '<code>{"menu_id": "116"}</code> — also require menu_id in URL; '
                '<code>{"action_id": "account.action_move_out_invoice_type"}</code> — also require action in URL; '
                '<code>{"method": "GET"}</code> — restrict HTTP method. '
                'Example for Odoo Invoicing: match_type=<i>path</i>, requestpath=<i>/odoo/accounting</i>, '
                'match_extra=<code>{"menu_id": "116"}</code>.'
            ),
        }),
        ('Action', {
            'fields': ['executescript', 'save_callbackdata', 'eventKey'],
        }),
        ('Advanced', {
            'classes': ['collapse'],
            'fields': ['requestmethod', 'direction', 'urllist', 'appusername',
                       'description', 'parameters_json', 'pub_date'],
        }),
    ]

    list_display = ('requestpath', 'match_type', 'executescript', 'save_callbackdata', 'requestmethod', 'pub_date', 'was_published_recently')
    list_filter = ['match_type', 'save_callbackdata', 'pub_date']
    search_fields = ['requestpath', 'description', 'eventKey']

    @method_decorator(never_cache)
    def add_view(self, request, form_url='', extra_context=None):
        # This bypasses potential atomic transaction issues for add operations
        return super().add_view(request, form_url, extra_context)

    @method_decorator(never_cache)
    def change_view(self, request, object_id, form_url='', extra_context=None):
        # This bypasses potential atomic transaction issues for change operations
        return super().change_view(request, object_id, form_url, extra_context)

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        from django.db import transaction
        from dose.services.atomic_services_registry import ATOMIC_SERVICE_REGISTRY, init_atomic_services_registry
        from django.contrib import messages
        init_atomic_services_registry()
        executescript_name = obj.executescript
        print(f"[DEBUG] executescript_name: {executescript_name}")
        print(f"[DEBUG] ATOMIC_SERVICE_REGISTRY keys: {list(ATOMIC_SERVICE_REGISTRY.keys())}")
        if executescript_name:
            cls = ATOMIC_SERVICE_REGISTRY.get(executescript_name)
            print(f"[DEBUG] cls: {cls}")
            if cls and hasattr(cls, 'execute_and_save'):
                print(f"[DEBUG] Executing atomic service: {executescript_name}")
                try:
                    with transaction.atomic():
                        cls.execute_and_save(request, obj)
                    messages.add_message(request, messages.INFO, f"Atomic service '{executescript_name}' executed successfully.")
                except Exception as e:
                    print(f"[ERROR] Failed to execute atomic service '{executescript_name}': {e}")
                    messages.add_message(request, messages.WARNING, f"Atomic service '{executescript_name}' failed, but the instruction was saved. You can retry from the admin list view. Error: {str(e)}")
            else:
                print(f"[DEBUG] Atomic service '{executescript_name}' not found or missing 'execute_and_save'.")

class PassThroughEndpointAdmin(TenantAwareModelAdmin):
    list_display = ('get_menu_title', 'provider', 'endpoint_url', 'show_in_menu', 'is_enabled', 'debug_button', 'created_at')
    search_fields = ('provider', 'endpoint_url', 'description', 'menu_title', 'slug')
    list_filter = ('provider', 'show_in_menu', 'is_enabled', 'integration_mode')
    change_form_template = 'admin/dose/passthroughendpoint/change_form.html'

    def _render_admin_exception(self, request, exc, operation):
        import html
        import traceback
        from django.http import HttpResponseServerError

        traceback_text = traceback.format_exc()
        body = (
            "<html><head><title>PassThroughEndpoint Admin Error</title>"
            "<style>body{font-family:Consolas,monospace;padding:24px;background:#111;color:#eee;}"
            "h1{color:#ff6b6b;} pre{white-space:pre-wrap;background:#1b1b1b;padding:16px;border-radius:8px;border:1px solid #333;}"
            "code{color:#ffd166;}</style></head><body>"
            f"<h1>PassThroughEndpoint {html.escape(operation)} failed</h1>"
            f"<p><strong>{html.escape(exc.__class__.__name__)}</strong>: {html.escape(str(exc))}</p>"
            f"<p>Path: <code>{html.escape(request.path)}</code></p>"
            f"<p>Method: <code>{html.escape(request.method)}</code></p>"
            f"<pre>{html.escape(traceback_text)}</pre>"
            "</body></html>"
        )
        return HttpResponseServerError(body)

    def add_view(self, request, form_url='', extra_context=None):
        try:
            return super().add_view(request, form_url, extra_context)
        except Exception as exc:
            import logging
            logging.getLogger(__name__).exception("[PassThroughEndpointAdmin] add_view error")
            return self._render_admin_exception(request, exc, 'add')

    def change_view(self, request, object_id, form_url='', extra_context=None):
        try:
            return super().change_view(request, object_id, form_url, extra_context)
        except Exception as exc:
            import logging
            logging.getLogger(__name__).exception("[PassThroughEndpointAdmin] change_view error")
            return self._render_admin_exception(request, exc, 'change')

    def get_queryset(self, request):
        """Override to handle missing migration columns gracefully - adds all missing columns automatically"""
        qs = super().get_queryset(request)
        # Try to add missing columns if they don't exist (one-time fix).
        # Wrapped in transaction.atomic() so any DDL failure rolls back only the
        # savepoint and never poisons the outer request transaction.
        try:
            from django.db import connection, transaction
            from dose.utils import get_current_tenant
            tenant = get_current_tenant(request) or getattr(request, 'tenant', None)
            schema = tenant.schema_name if tenant and tenant.schema_name else 'public'

            with transaction.atomic():
                with connection.cursor() as cursor:
                    cursor.execute(f'SET search_path TO "{schema}",public;')

                    columns_to_add = [
                        ('bypass_middleware', 'BOOLEAN DEFAULT FALSE NOT NULL'),
                        ('passthrough_type', "VARCHAR(20) DEFAULT 'scraper' NOT NULL"),
                        ('integration_mode', "VARCHAR(20) DEFAULT 'web_only' NOT NULL"),
                        ('api_endpoint', "VARCHAR(300) DEFAULT ''"),
                        ('api_auth_type', "VARCHAR(20) DEFAULT 'bearer' NOT NULL"),
                        ('api_key', "VARCHAR(500) DEFAULT ''"),
                        ('api_key_header', "VARCHAR(100) DEFAULT 'Authorization'"),
                        ('auth_username', "VARCHAR(200) DEFAULT ''"),
                        ('auth_password', "VARCHAR(500) DEFAULT ''"),
                        ('inject_proxy_script', 'BOOLEAN DEFAULT FALSE NOT NULL'),
                        ('passthrough_stream_debug', 'BOOLEAN DEFAULT FALSE NOT NULL'),
                        ('show_in_menu', 'BOOLEAN DEFAULT TRUE NOT NULL'),
                        ('menu_title', "VARCHAR(100) DEFAULT ''"),
                        ('menu_icon', "VARCHAR(100) DEFAULT '🔗'"),
                        ('menu_sort_order', 'INTEGER DEFAULT 100 NOT NULL'),
                        ('slug', "VARCHAR(100) DEFAULT ''"),
                    ]

                    for column_name, column_def in columns_to_add:
                        cursor.execute(f"""
                            ALTER TABLE {schema}.dose_passthroughendpoint
                            ADD COLUMN IF NOT EXISTS {column_name} {column_def}
                        """)
                        print(f"[AUTO-FIX] Ensured column {column_name} in {schema} schema")
        except Exception as e:
            print(f"[AUTO-FIX] Error checking/adding columns: {e}")

        # Filter to only show endpoints the tenant has subscribed to.
        # Use only('id', 'endpoint_url') — these columns have always existed.
        try:
            from dose.models import TenantApp
            from dose.utils import get_current_tenant

            if getattr(request.user, 'is_staff', False) or getattr(request.user, 'is_superuser', False):
                return qs

            _tenant = get_current_tenant(request) or getattr(request, 'tenant', None)
            _subscribed = set(
                TenantApp.public_bundles.filter(
                    tenant=_tenant,
                    status__in=['active', 'provisioning'],
                ).values_list('app_name', flat=True)
            ) if _tenant else set()

            def _visible(endpoint_url):
                # Extract hostname from endpoint_url for matching
                from urllib.parse import urlparse
                host = urlparse(endpoint_url).netloc.lower().replace('-', '_')
                return 'gmail' in host or any(
                    app in host for app in _subscribed
                )

            visible_ids = [
                ep.id for ep in qs.only('id', 'endpoint_url')
                if _visible(ep.endpoint_url)
            ]
            qs = qs.filter(id__in=visible_ids)
        except Exception as e:
            print(f"[PassThroughEndpointAdmin] Subscription filter error (showing all): {e}")

        return qs

    # Media removed - using integrated Django view instead of external PolySniffer

    def debug_button(self, obj):
        """Render PolySniffer Analysis button that opens the live capture viewer"""
        from django.utils.html import format_html
        from django.utils.safestring import mark_safe
        if obj and obj.endpoint_url:
            capture_url = f'/admin/polysniffer/capture/{obj.id}/'
            return format_html(
                '<a href="{}" target="_blank" '
                'style="padding: 6px 12px; font-size: 13px; font-weight: bold; cursor: pointer; background: #417ccc; color: white; border: none; border-radius: 4px; text-decoration: none; display: inline-block; white-space: nowrap;">'
                '🔍 PolySniffer Analysis'
                '</a>',
                capture_url
            )
        return mark_safe('<span style="color: #999;">-</span>')
    debug_button.short_description = '🔍 PolySniffer'
    debug_button.allow_tags = True
    debug_button.admin_order_field = None

    fieldsets = [
        ('Endpoint Configuration', {
            'fields': ('provider', 'endpoint_url', 'slug', 'is_enabled'),
            'description': (
                '<strong>Endpoint URL:</strong> hostname becomes the passthrough path '
                '(<code>/pt/admin/&lt;hostname&gt;/…</code>). '
                '<strong>Slug:</strong> optional separate id for non-passthrough use (menus, internal links); '
                'leave blank if you do not need it.'
            ),
        }),
        ('Menu Integration', {
            'fields': ('show_in_menu', 'menu_title', 'menu_icon', 'menu_sort_order', 'description'),
            'description': '<strong>Automatic Menu Integration:</strong> When enabled, this endpoint appears in the top navigation menu. <strong>Menu Title:</strong> Auto-generates from description/URL if left blank. <strong>Menu Icon:</strong> Use emoji (🔗) or Font Awesome class.',
            'classes': ['collapse']
        }),
        ('Integration Mode', {
            'fields': ('integration_mode', 'passthrough_type', 'bypass_middleware', 'passthrough_stream_debug'),
            'description': '<strong>Integration Type:</strong> Choose between Web UI only, Web UI + API, or API only (custom Dose UI). '
            '<strong>Passthrough stream debug:</strong> when enabled, logs upstream/final response diagnostics to the server console for this endpoint (or use POLYSNIFFER_PASSTHROUGH_DEBUG in settings for all).',
            'classes': ['collapse']
        }),
        ('API Configuration', {
            'fields': ('api_endpoint', 'api_auth_type', 'api_key', 'api_key_header'),
            'description': '<strong>API Access:</strong> Configure API endpoint and authentication for services with both web UI and API access.',
            'classes': ['collapse']
        }),
        ('Credentials for Auto-Login', {
            'fields': ('auth_username', 'auth_password'),
            'description': '<strong>⚠️ DEMO ONLY:</strong> Simple credentials for auto-login. Each tenant has their own credentials in their schema. <strong>Future:</strong> Migrate to OAuth2 for multi-user support.',
            'classes': ['collapse']
        }),
        # PolySniffer Debug section removed - fields don't exist on model
        # ('PolySniffer Debug', {
        #     'fields': ('polysniffer_debug_output', 'polysniffer_last_run'),
        #     'description': '<strong>PolySniffer Output:</strong> Debug information captured from running PolySniffer on this endpoint. Click the "🔍 Sniff" button to capture traffic. <strong>Expand this section to view detailed request/response data.</strong>',
        #     'classes': []  # Not collapsed - always visible for debugging
        # }),
        ('Advanced', {
            'fields': ('discovered_subpaths', 'created_at'),
            'description': '<strong>Auto-discovered paths:</strong> System-detected subpaths for this endpoint. <strong>Created:</strong> Timestamp when this endpoint was created.',
            'classes': ['collapse']
        }),
        ('Content Preview', {
            'fields': ('content_preview',),
            'description': '<strong>Live Content Preview:</strong> Fetches and displays the current content from the endpoint URL. Useful for testing and debugging.',
            'classes': ['collapse']
        }),
    ]
    readonly_fields = ('created_at', 'discovered_subpaths', 'content_preview')

    def get_menu_title(self, obj):
        """Display the computed menu title in the admin list"""
        title = obj.get_menu_title()
        if obj.menu_title and obj.menu_title != title:
            return f"{title} (custom)"
        return title
    get_menu_title.short_description = 'Menu Title'

    def content_preview(self, obj):
        """Display a preview of the external content"""
        from django.utils.safestring import mark_safe
        if obj and obj.endpoint_url:
            try:
                import requests
                response = requests.get(obj.endpoint_url, timeout=10)
                if response.status_code == 200:
                    return mark_safe(response.text)
                else:
                    return f"Error: HTTP {response.status_code}"
            except Exception as e:
                return f"Error fetching content: {e}"
        return "No endpoint URL"
    content_preview.short_description = "Content Preview"

    def save_model(self, request, obj, form, change):
        import traceback
        from django.contrib import messages
        from dose.utils import get_current_tenant

        # TenantAwareModelAdmin saves into the schema for session tenant_id. If there is no
        # tenant, the row is written to public — reloading under Oliver Enterprises reads
        # olient and the edit looks "lost". The tenant session is expected to be
        # aligned automatically on real /admin/ requests.
        if not get_current_tenant(request):
            messages.warning(
                request,
                "No active tenant in session: this endpoint was saved in the public schema. "
                "If the URL reverts after reload, re-open the admin once so tenant_id is "
                "restored in session, then edit again so the row saves to your tenant schema.",
            )

        # Call parent save which will trigger the signal to create/update navigation items
        try:
            super().save_model(request, obj, form, change)
        except Exception as exc:
            tb = traceback.format_exc()
            messages.error(
                request,
                f'❌ Save failed: {exc.__class__.__name__}: {exc} — Full traceback: {tb}',
            )
            import logging
            logging.getLogger(__name__).exception("[PassThroughEndpointAdmin] save_model error")
            return  # stay on the form with the error message, no 500

        # Show a success message about menu integration
        if obj.show_in_menu:
            menu_title = obj.get_menu_title()
            messages.success(
                request,
                f'✅ Passthrough endpoint saved successfully! Menu item "{menu_title}" will appear in the navigation for all tenants.'
            )
        else:
            messages.info(
                request,
                'Passthrough endpoint saved. Menu integration is disabled - no navigation item will be created.'
            )

    actions = ['create_sniffer_stream_actions']

    def create_sniffer_stream_actions(self, request, queryset):
        """
        Admin action: for each selected PassThroughEndpoint, scan its PolySniffer
        TrafficLog for POST requests and auto-create an Instruction + MQOutput
        (topic: {trigger}-{post-path}) for every unique POST path found.
        """
        from django.contrib import messages
        from dose.services.sniffer_stream_actions import create_stream_actions_for_endpoint
        from dose.utils import get_current_tenant

        tenant = get_current_tenant(request) or getattr(request, 'tenant', None)

        created_count = 0
        skipped_count = 0
        endpoint_count = 0

        for endpoint in queryset:
            endpoint_count += 1
            results = create_stream_actions_for_endpoint(endpoint, tenant)
            for r in results:
                status = r.get('status', '')
                if status == 'created':
                    created_count += 1
                elif status in ('already_exists', 'no_posts_found', 'dry_run'):
                    skipped_count += 1

        if created_count:
            messages.success(
                request,
                f'✅ Created {created_count} Instruction + MQOutput pair(s) across '
                f'{endpoint_count} endpoint(s). {skipped_count} already existed or had no POST traffic.'
            )
        else:
            messages.warning(
                request,
                f'No new actions created for {endpoint_count} endpoint(s). '
                f'{skipped_count} paths already existed or no POST traffic was found in PolySniffer.'
            )

    create_sniffer_stream_actions.short_description = (
        '🔁 Create stream actions from sniffer POST traffic'
    )

class DoseMessageAdmin(TenantAwareModelAdmin):
    list_display = ('user', 'message', 'level', 'created_at', 'is_read')
    list_filter = ('level', 'is_read', 'created_at')
    search_fields = ('message',)

# TrafficLog admin — shows actual passthrough capture data (PolySnifferRun is deprecated/empty)
from dose.polysniffer.models import TrafficLog

# Unregister the default TrafficLog admin (registered in dose.polysniffer.admin)
# and re-register with TenantAwareModelAdmin so it appears in tenant-scoped admin
try:
    admin.site.unregister(TrafficLog)
except admin.sites.NotRegistered:
    pass

class TrafficLogAdmin(TenantAwareModelAdmin):
    list_display = ('method', 'path', 'client_path', 'capture_source', 'status_code',
                    'endpoint_name', 'user', 'captured_at', 'duration_ms')
    list_filter = ('method', 'status_code', 'capture_source', 'endpoint_name', 'captured_at')
    search_fields = ('url', 'path', 'endpoint_name', 'user__username')
    readonly_fields = (
        'method', 'url', 'path', 'client_path', 'capture_source',
        'headers', 'cookies', 'query_params', 'body',
        'status_code', 'response_headers', 'response_body', 'response_size',
        'endpoint_name', 'user', 'captured_at', 'duration_ms', 'har_data'
    )
    ordering = ('-captured_at',)

from .models import RequestLog, ErrorLog
from .models import Mapping, InstructionMapping


class InstructionMappingInline(admin.TabularInline):
    model = InstructionMapping
    extra = 1
    fields = ('mapping', 'order', 'enabled')
    autocomplete_fields = ['mapping']


InstructionAdmin.inlines = [InstructionMappingInline]


class MappingAdmin(TenantAwareModelAdmin):
    list_display = ('name', 'slug', 'direction', 'source_endpoint', 'target_endpoint',
                    'is_active', 'version', 'updated_at')
    list_filter = ('direction', 'is_active', 'source_endpoint', 'target_endpoint')
    search_fields = ('name', 'slug', 'description')
    readonly_fields = ('created_at', 'updated_at')
    prepopulated_fields = {'slug': ('name',)}
    fieldsets = (
        (None, {
            'fields': ('name', 'slug', 'description', 'direction', 'is_active', 'version')
        }),
        ('Endpoints', {
            'fields': ('source_endpoint', 'target_endpoint', 'tenant'),
            'classes': ('collapse',),
        }),
        ('Field Mappings', {
            'fields': ('field_mappings',),
            'description': (
                'JSON dict: {"target_field": "source_expression"}. '
                'Expressions: request.POST.name|strip, payload.email|lower|default:None, '
                'now:iso, \'literal\''
            ),
        }),
        ('Transformations', {
            'fields': ('transformations',),
            'classes': ('collapse',),
            'description': (
                'JSON list of post-mapping rules. '
                '[{"field": "full_name", "concat": ["first", "last"], "separator": " "}]'
            ),
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )


# Register existing models
admin.site.register(Task, TaskAdmin)
admin.site.register(Instruction, InstructionAdmin)
admin.site.register(CallBackData, CallBackDataAdmin)
admin.site.register(MLEngine, MLEngineAdmin)
admin.site.register(MLPrompt, MLPromptAdmin)
admin.site.register(PassThroughEndpoint, PassThroughEndpointAdmin)
admin.site.register(DoseMessage, DoseMessageAdmin)
admin.site.register(TrafficLog, TrafficLogAdmin)
admin.site.register(RequestLog)
admin.site.register(ErrorLog)
admin.site.register(Mapping, MappingAdmin)

class AppCredentialAdmin(admin.ModelAdmin):
    list_display = ('app_name', 'username', 'updated_at')
    search_fields = ('app_name', 'username', 'notes')

admin.site.register(AppCredential, AppCredentialAdmin)

# Add session-based tenant admin classes if models are available
if NEW_MODELS_AVAILABLE:
    @admin.register(Tenant)
    class TenantAdmin(admin.ModelAdmin):
        list_display = ('name', 'schema_name', 'user_count_display', 'is_active', 'created_at')
        search_fields = ('name', 'slug', 'schema_name', 'tagline', 'description')
        list_filter = ('is_active', 'created_at')
        prepopulated_fields = {'slug': ('name',)}
        readonly_fields = ('schema_name', 'created_at')

        def user_count_display(self, obj):
            try:
                return f"{obj.userprofile_set.count()} users"
            except:
                return "0 users"
        user_count_display.short_description = "Users"

    def get_queryset(self, request):
        """Optimize queryset to include user count."""
        queryset = super().get_queryset(request)
        return queryset.prefetch_related('userprofile_set')

    def save_model(self, request, obj, form, change):
        # Ensure schema_name is generated before saving
        if not obj.schema_name and obj.slug:
            obj.schema_name = obj.slug.replace('-', '_').lower()
        super().save_model(request, obj, form, change)

    fieldsets = [
        (None, {
            'fields': ['name', 'slug', 'schema_name', 'description', 'tagline', 'logo', 'primary_color', 'is_active', 'created_at']
        }),
    ]

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'admin_theme':
            kwargs["queryset"] = Theme.objects.all()
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

        def get_queryset(self, request):
            """Optimize queryset to include user count."""
            queryset = super().get_queryset(request)
            return queryset.prefetch_related('userprofile_set')

        def save_model(self, request, obj, form, change):
            # Ensure schema_name is generated before saving
            if not obj.schema_name and obj.slug:
                obj.schema_name = obj.slug.replace('-', '_').lower()
            super().save_model(request, obj, form, change)

        fieldsets = [
            ('Basic Information', {
                'fields': ['name', 'slug', 'schema_name', 'description', 'tagline']
            }),
            ('Admin Interface Theme', {
                'fields': ['admin_theme'],
                'description': 'Choose the color theme for this tenant\'s admin interface'
            }),
            ('Branding', {
                'fields': ['logo'],
                'classes': ['collapse']
            }),
            ('Status', {
                'fields': ['is_active', 'created_at']
            }),
        ]

    @admin.register(Subscription)
    class SubscriptionAdmin(TenantAwareModelAdmin):
        list_display = ('tenant', 'active', 'stripe_customer_id', 'card_name', 'created_at', 'updated_at')
        list_filter = ('active', 'created_at', 'updated_at')
        search_fields = ('tenant__name', 'tenant__slug', 'stripe_customer_id', 'stripe_subscription_id', 'card_name')
        readonly_fields = ('created_at', 'updated_at')
        ordering = ('-created_at',)

        fieldsets = [
            (None, {
                'fields': ['tenant', 'stripe_customer_id', 'stripe_subscription_id', 'card_name', 'active', 'created_at', 'updated_at']
            }),
        ]

        def get_queryset(self, request):
            """Optimize queryset to include tenant information."""
            queryset = super().get_queryset(request)
            return queryset.select_related('tenant')

    @admin.register(TenantApp)
    class TenantAppAdmin(admin.ModelAdmin):
        list_display = ('tenant', 'app_name', 'status', 'app_url', 'provisioned_at')
        list_filter = ('app_name', 'status')
        search_fields = ('tenant__name', 'app_name', 'app_url')
        readonly_fields = ('provisioned_at',)
        raw_id_fields = ('oauth_application',) if apps.is_installed('oauth2_provider') else ()

    # Custom User Form to include tenant selection
    class UserProfileInlineForm(forms.ModelForm):
        class Meta:
            model = UserProfile
            fields = ['tenant']

        def __init__(self, *args, **kwargs):
            import logging
            logger = logging.getLogger(__name__)

            super().__init__(*args, **kwargs)

            try:
                from dose.tenant_utils import tenants_for_user_assignment

                qs = tenants_for_user_assignment()
                # Real tenants only — never the PostgreSQL public catalog as a "tenant workspace"
                tenant_count = qs.count()
                logger.info(f"UserProfileInlineForm: tenants_for_user_assignment returned {tenant_count} tenants")
                
                # Log all tenants in queryset
                for tenant in qs:
                    logger.info(f"  Tenant in queryset: {tenant.slug} (schema={tenant.schema_name}, active={tenant.is_active})")
                
                self.fields['tenant'].queryset = qs
                self.fields['tenant'].empty_label = "Select a tenant..."
                self.fields['tenant'].required = False
                
                logger.info(f"UserProfileInlineForm: Set tenant field queryset with {tenant_count} items")
                logger.info(f"UserProfileInlineForm: Field widget is {type(self.fields['tenant'].widget).__name__}")

                # If this is an existing UserProfile, keep the current tenant selection
                if self.instance.pk and self.instance.tenant:
                    # Don't override existing tenant assignment
                    logger.info(f"UserProfileInlineForm: Editing existing UserProfile {self.instance.pk} with tenant {self.instance.tenant}")
                elif not self.instance.pk:
                    # For new UserProfiles, default to first assignable tenant
                    if qs.exists():
                        self.fields['tenant'].initial = qs.first()
                        logger.info(f"UserProfileInlineForm: New UserProfile, defaulting to tenant {qs.first()}")
                    else:
                        logger.warning("UserProfileInlineForm: No tenants available for assignment!")
            except Exception as e:
                logger.error(f"UserProfileInlineForm.__init__ error: {e}", exc_info=True)

    # Removed signal that auto-creates UserProfile for superusers to prevent duplicate key errors

    class UserProfileInline(admin.StackedInline):
        model = UserProfile
        form = UserProfileInlineForm
        can_delete = False
        verbose_name = 'Tenant Assignment'
        verbose_name_plural = 'Tenant Assignment'
        fields = ('tenant',)
        extra = 1  # Ensure form always shows
        max_num = 1
        min_num = 1  # Ensure at least one tenant assignment exists
        
        def get_queryset(self, request):
            """Handle UserProfiles that reference users in different schemas"""
            from django.db import connection
            import logging
            logger = logging.getLogger(__name__)
            
            qs = super().get_queryset(request)
            
            # Force public schema to find user profiles
            with connection.cursor() as cursor:
                cursor.execute("SET search_path TO public")
                logger.info("UserProfileInline.get_queryset: Set search_path to public")
            
            # Re-query from public schema
            qs = UserProfile.objects.all()
            
            # Filter to only include profiles where we can actually find the user
            valid_ids = []
            for profile in qs:
                try:
                    # Try to access the user - this will fail if user not in schema
                    _ = profile.user.username
                    valid_ids.append(profile.pk)
                except User.DoesNotExist:
                    logger.warning(f"UserProfileInline: Skipping profile {profile.pk} - user not accessible")
                    pass
            
            if valid_ids:
                return UserProfile.objects.filter(pk__in=valid_ids)
            return UserProfile.objects.none()

    # Unregister the default User admin and register our custom one
    admin.site.unregister(User)
    class CustomUserAdmin(BaseUserAdmin):
        inlines = [UserProfileInline]
        list_display = ('username', 'email', 'is_active', 'is_staff', 'is_superuser')
        
        def get_queryset(self, request):
            """Always query User from public schema - users are shared across tenants"""
            from django.db import connection
            import logging
            logger = logging.getLogger(__name__)
            
            # Set search_path to public to find all users
            with connection.cursor() as cursor:
                cursor.execute("SET search_path TO public")
                logger.info("CustomUserAdmin.get_queryset: Set search_path to public")
            
            return super().get_queryset(request)
        
        def get_object(self, request, object_id, from_field=None):
            """Force public schema when retrieving user object"""
            from django.db import connection
            import logging
            logger = logging.getLogger(__name__)
            
            # First, check what schemas exist and where the user might be
            logger.info(f"CustomUserAdmin.get_object: Looking for user id={object_id}")
            
            # Check all schemas for this user
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT schema_name 
                    FROM information_schema.schemata 
                    WHERE schema_name NOT IN ('pg_catalog', 'information_schema', 'pg_toast')
                    AND schema_name NOT LIKE 'pg_%'
                """)
                schemas = [row[0] for row in cursor.fetchall()]
                logger.info(f"CustomUserAdmin.get_object: Available schemas: {schemas}")
                
                # Check each schema for the user
                for schema in schemas:
                    cursor.execute(f"SET search_path TO {schema}")
                    cursor.execute("SELECT id, username FROM auth_user WHERE id = %s", [object_id])
                    result = cursor.fetchone()
                    if result:
                        logger.info(f"CustomUserAdmin.get_object: FOUND user {result[1]} (id={result[0]}) in schema '{schema}'")
                        # Found the user - set search_path back to public for the actual query
                        cursor.execute("SET search_path TO public")
                        break
                else:
                    logger.error(f"CustomUserAdmin.get_object: User id={object_id} not found in ANY schema")
                    # Show all users in all schemas
                    for schema in schemas:
                        cursor.execute(f"SET search_path TO {schema}")
                        cursor.execute("SELECT id, username FROM auth_user LIMIT 5")
                        users = cursor.fetchall()
                        if users:
                            logger.info(f"CustomUserAdmin.get_object: Schema '{schema}' has users: {users}")
                    # Reset to public
                    cursor.execute("SET search_path TO public")
            
            # Force public schema before the actual Django query
            with connection.cursor() as cursor:
                cursor.execute("SET search_path TO public")
            
            # DEBUG: Check current search_path and public schema contents
            with connection.cursor() as cursor:
                cursor.execute("SHOW search_path")
                current_search_path = cursor.fetchone()[0]
                cursor.execute("SELECT id, username FROM auth_user ORDER BY id LIMIT 10")
                all_users = cursor.fetchall()
            
            diagnostic_msg = f"search_path={current_search_path}, available_users={all_users}"
            
            try:
                obj = super().get_object(request, object_id, from_field)
                if obj:
                    logger.info(f"CustomUserAdmin.get_object: Django found user {obj.username}")
                return obj
            except User.DoesNotExist:
                logger.error(f"CustomUserAdmin.get_object: Django ORM could not find user id={object_id}. {diagnostic_msg}")
                # Raise with diagnostic info
                raise User.DoesNotExist(f"User id={object_id} not found. DIAGNOSTIC: {diagnostic_msg}")
        
        def change_view(self, request, object_id, form_url='', extra_context=None):
            """Ensure we're looking in public schema for the user"""
            from django.db import connection
            import logging
            logger = logging.getLogger(__name__)
            
            logger.info(f"CustomUserAdmin.change_view: object_id={object_id}")
            
            # Force public schema
            with connection.cursor() as cursor:
                cursor.execute("SET search_path TO public")
                cursor.execute("SHOW search_path")
                search_path = cursor.fetchone()
                logger.info(f"CustomUserAdmin.change_view: search_path set to {search_path}")
            
            return super().change_view(request, object_id, form_url, extra_context)

        @staticmethod
        def _force_public_schema():
            """auth_user lives in the public schema; SessionTenantMiddleware sets search_path
            to the tenant schema which can shadow public.auth_user with a tenant-local copy
            (created by migrations into each tenant schema). Force public for User admin queries."""
            from django.db import connection
            with connection.cursor() as cursor:
                cursor.execute("SET search_path TO public;")

        def get_queryset(self, request):
            self._force_public_schema()
            return super().get_queryset(request)

        def get_object(self, request, object_id, from_field=None):
            self._force_public_schema()
            return super().get_object(request, object_id, from_field=from_field)

        def save_model(self, request, obj, form, change):
            self._force_public_schema()
            super().save_model(request, obj, form, change)

        def delete_model(self, request, obj):
            self._force_public_schema()
            super().delete_model(request, obj)

    admin.site.register(User, CustomUserAdmin)

    # Register other new models if they exist
    try:
        admin.site.register(MLTaxonomy)
    except:
        pass

    try:
        admin.site.register(MLDataset)
    except:
        pass

    # Navigation Panel Admin
    @admin.register(NavigationPanel)
    class NavigationPanelAdmin(TenantAwareModelAdmin):
        list_display = ('title', 'tenant', 'panel_type', 'get_item_count', 'is_active', 'sort_order', 'updated_at')
        list_filter = ('panel_type', 'is_active', 'tenant', 'created_at')
        search_fields = ('title', 'description', 'tenant__name')
        ordering = ('tenant', 'sort_order', 'title')

        fieldsets = [
            (None, {
                'fields': ['title', 'panel_type', 'description', 'is_active', 'sort_order', 'panel_css_class', 'panel_background_color']
            }),
        ]

        # Remove tenant field from form; always set from session in save_model

        def get_item_count(self, obj):
            """Display the number of navigation items in this panel."""
            count = obj.navigation_items.count()
            active_count = obj.navigation_items.filter(is_active=True).count()
            return f"{active_count}/{count} active"
        get_item_count.short_description = 'Items'

        def get_queryset(self, request):
            """Filter queryset to show only panels from user's session tenant."""
            queryset = super().get_queryset(request)
            queryset = queryset.select_related('tenant').prefetch_related('navigation_items')

            try:
                from dose.utils import get_current_tenant
                tenant = get_current_tenant(request)
                if tenant:
                    queryset = queryset.filter(tenant=tenant)
                    print(f"[NAV_PANEL_ADMIN] Filtered panels to tenant: {tenant.name}")
            except Exception as e:
                print(f"[NAV_PANEL_ADMIN] Error filtering by tenant: {e}")

            return queryset

        def get_form(self, request, obj=None, **kwargs):
            """Auto-set tenant field to session tenant, hide dropdown, and make readonly."""
            form = super().get_form(request, obj, **kwargs)
            try:
                from dose.tenant_utils import get_current_tenant
                tenant = get_current_tenant(request)
                if tenant and 'tenant' in form.base_fields:
                    if not obj:
                        form.base_fields['tenant'].initial = tenant.slug
                    # Only set background color for clarity, do not block interaction
                    form.base_fields['tenant'].widget.can_add_related = False
                    form.base_fields['tenant'].widget.can_change_related = False
                    form.base_fields['tenant'].widget.can_delete_related = False
                    form.base_fields['tenant'].widget.attrs['style'] = 'background-color: #e9ecef;'
            except Exception as e:
                print(f"[NAV_PANEL_ADMIN] Error setting tenant: {e}")
            return form

        def save_model(self, request, obj, form, change):
            """Always assign tenant from session, auto-create if missing (guaranteed before save)."""
            from dose.tenant_utils import get_current_tenant
            from dose.models.tenant import Tenant
            import logging
            logger = logging.getLogger(__name__)
            tenant = get_current_tenant(request)
            logger.info(f"[DEBUG] save_model: session tenant from get_current_tenant = {tenant}")
            # Log all tenants in public schema
            all_tenants = list(Tenant.objects.all().values('slug', 'name', 'schema_name', 'is_active'))
            logger.info(f"[DEBUG] save_model: all tenants in public schema: {all_tenants}")
            if tenant:
                # Ensure tenant exists in DB before saving
                try:
                    db_tenant = Tenant.objects.get(slug=tenant.slug)
                except Tenant.DoesNotExist:
                    db_tenant = Tenant.objects.create(
                        slug=tenant.slug,
                        name=getattr(tenant, 'name', 'Session Tenant'),
                        schema_name=getattr(tenant, 'schema_name', f'session_{tenant.slug}')
                    )
                    logger.info(f"[DEBUG] save_model: created tenant {db_tenant}")
                obj.tenant = db_tenant
                logger.info(f"[DEBUG] save_model: assigned obj.tenant = {db_tenant}")
            elif not obj.tenant_id:
                # Fallback: Try to get user's tenant from profile
                try:
                    user_profile = UserProfile.objects.get(user=request.user)
                    obj.tenant = user_profile.tenant
                    logger.info(f"[DEBUG] save_model: fallback assigned obj.tenant = {obj.tenant}")
                except UserProfile.DoesNotExist:
                    logger.warning(f"[DEBUG] save_model: no tenant found for user {request.user}")
            super().save_model(request, obj, form, change)

    @admin.register(NavigationItem)
    class NavigationItemAdmin(TenantAwareModelAdmin):
        list_display = ('title', 'get_tenant', 'get_panel_title', 'item_type', 'url', 'get_icon_display', 'is_active', 'click_count', 'last_clicked')
        list_filter = ('item_type', 'is_active', 'panel__tenant', 'panel__panel_type', 'requires_authentication')
        search_fields = ('title', 'description', 'url', 'panel__title', 'panel__tenant__name')
        ordering = ('panel__tenant', 'panel__sort_order', 'sort_order', 'title')

        fieldsets = [
            (None, {
                'fields': ['panel', 'title', 'item_type', 'url', 'description', 'icon_style', 'icon_value', 'target', 'item_css_class', 'button_color', 'requires_authentication', 'requires_permissions', 'is_active', 'sort_order']
            }),
            ('Analytics', {
                'fields': ['click_count', 'last_clicked']
            }),
        ]

        readonly_fields = ['click_count', 'last_clicked']

        def get_tenant(self, obj):
            """Display the tenant name through panel relationship."""
            return obj.panel.tenant.name
        get_tenant.short_description = 'Tenant'
        get_tenant.admin_order_field = 'panel__tenant__name'

        def get_panel_title(self, obj):
            """Display the panel title."""
            return obj.panel.title
        get_panel_title.short_description = 'Panel'
        get_panel_title.admin_order_field = 'panel__title'

        def get_icon_display(self, obj):
            """Display the icon in a user-friendly format."""
            if obj.icon_style == 'emoji' and obj.icon_value:
                return f"{obj.icon_value} ({obj.icon_style})"
            elif obj.icon_style == 'none':
                return "No Icon"
            elif obj.icon_value:
                return f"{obj.icon_value[:20]}... ({obj.icon_style})" if len(obj.icon_value) > 20 else f"{obj.icon_value} ({obj.icon_style})"
            else:
                return f"No icon ({obj.icon_style})"
        get_icon_display.short_description = 'Icon'

        def get_queryset(self, request):
            """Filter queryset to show only items from user's tenant, searching across all schemas."""
            from django.db import connection
            from dose.utils import get_current_tenant
            from dose.models.tenant import Tenant

            tenant = get_current_tenant(request)
            all_items = []
            seen_ids = set()

            # Search across all schemas (like we do for panels)
            all_tenants = Tenant.objects.all()
            for tenant_obj in all_tenants:
                schema_name = tenant_obj.schema_name if tenant_obj.schema_name else 'public'
                try:
                    with connection.cursor() as cursor:
                        cursor.execute(f'SET search_path TO "{schema_name}",public;')
                        # Filter by tenant if provided
                        if tenant:
                            items = NavigationItem.objects.filter(panel__tenant=tenant).select_related('panel__tenant')
                        else:
                            items = NavigationItem.objects.all().select_related('panel__tenant')

                        for item in items:
                            if item.id not in seen_ids:
                                all_items.append(item)
                                seen_ids.add(item.id)
                except Exception as e:
                    print(f"[NAV_ITEM_ADMIN] Error querying schema {schema_name}: {e}")

            # Return a queryset-like object (or use a custom manager)
            # For now, return items from current schema but log that we found items in other schemas
            queryset = super().get_queryset(request)
            queryset = queryset.select_related('panel__tenant')

            if tenant:
                queryset = queryset.filter(panel__tenant=tenant)

            if all_items:
                print(f"[NAV_ITEM_ADMIN] Found {len(all_items)} total items across all schemas, {queryset.count()} in current schema")

            return queryset

        def get_form(self, request, obj=None, **kwargs):
            """Filter panel dropdown to only show panels from user's tenant, searching across all schemas."""
            from django.db import connection
            from dose.utils import get_current_tenant
            from dose.models.tenant import Tenant

            form = super().get_form(request, obj, **kwargs)

            # Filter panel queryset to user's tenant, searching across all schemas
            try:
                tenant = get_current_tenant(request)
                if tenant and 'panel' in form.base_fields:
                    # Search for panels across all schemas that belong to the current tenant
                    all_panels = []
                    all_tenants = Tenant.objects.all()

                    for tenant_obj in all_tenants:
                        schema_name = tenant_obj.schema_name if tenant_obj.schema_name else 'public'
                        try:
                            with connection.cursor() as cursor:
                                cursor.execute(f'SET search_path TO "{schema_name}",public;')
                                panels = NavigationPanel.objects.filter(tenant=tenant, is_active=True)
                                for panel in panels:
                                    all_panels.append(panel)
                        except Exception as e:
                            print(f"[NAV_ITEM_ADMIN] Error querying panels in schema {schema_name}: {e}")

                    # Create a queryset from the found panels
                    # We'll use the first panel's schema for the queryset, or use a custom manager
                    if all_panels:
                        # Use the current tenant's schema for the queryset
                        with connection.cursor() as cursor:
                            cursor.execute(f'SET search_path TO "{tenant.schema_name if tenant.schema_name else "public"}",public;')
                            # Get panel IDs
                            panel_ids = [p.id for p in all_panels]
                            form.base_fields['panel'].queryset = NavigationPanel.objects.filter(id__in=panel_ids)
                            print(f"[NAV_ITEM_ADMIN] Filtered panels to tenant: {tenant.name} ({len(all_panels)} panels found across schemas)")
                    else:
                        # No panels found, use empty queryset
                        form.base_fields['panel'].queryset = NavigationPanel.objects.none()
                        print(f"[NAV_ITEM_ADMIN] No panels found for tenant: {tenant.name}")
            except Exception as e:
                print(f"[NAV_ITEM_ADMIN] Error filtering panel queryset: {e}")
                import traceback
                print(traceback.format_exc())

            return form

        def save_model(self, request, obj, form, change):
            """Validate that panel belongs to user's tenant and ensure item is saved in the same schema as panel."""
            from dose.utils import get_current_tenant
            from django.db import connection

            tenant = get_current_tenant(request)
            if tenant and obj.panel:
                # Get the panel's tenant to determine which schema to use
                # First, we need to find which schema the panel exists in
                panel_schema = None
                panel_tenant = None

                # Try to get panel tenant from the panel object if it's already loaded
                try:
                    # Access panel.tenant in current schema context first
                    if hasattr(obj.panel, 'tenant') and obj.panel.tenant:
                        panel_tenant = obj.panel.tenant
                        panel_schema = panel_tenant.schema_name if panel_tenant.schema_name else 'public'
                        print(f"[NAV_ITEM_ADMIN] Panel tenant from object: {panel_tenant.name} (schema: {panel_schema})")
                except Exception as e:
                    print(f"[NAV_ITEM_ADMIN] Could not get panel tenant from object: {e}")

                # If we couldn't get it from the object, search across schemas
                if not panel_schema:
                    all_tenants = Tenant.objects.all()
                    for tenant_obj in all_tenants:
                        schema_name = tenant_obj.schema_name if tenant_obj.schema_name else 'public'
                        try:
                            with connection.cursor() as cursor:
                                cursor.execute(f'SET search_path TO "{schema_name}",public;')
                                panel_check = NavigationPanel.objects.filter(id=obj.panel.id).first()
                                if panel_check:
                                    panel_schema = schema_name
                                    panel_tenant = panel_check.tenant if hasattr(panel_check, 'tenant') and panel_check.tenant else None
                                    print(f"[NAV_ITEM_ADMIN] Found panel in schema: {schema_name}")
                                    break
                        except Exception as e:
                            print(f"[NAV_ITEM_ADMIN] Error checking schema {schema_name}: {e}")

                if panel_schema:
                    # Save the item in the same schema as the panel
                    with connection.cursor() as cursor:
                        cursor.execute(f'SET search_path TO "{panel_schema}",public;')
                        # Get the panel in the correct schema context
                        panel_in_schema = NavigationPanel.objects.filter(id=obj.panel.id).first()
                        if panel_in_schema:
                            obj.panel = panel_in_schema
                            super().save_model(request, obj, form, change)
                            panel_title = panel_in_schema.title if hasattr(panel_in_schema, 'title') else 'Unknown'
                            print(f"[NAV_ITEM_ADMIN] Saved NavigationItem '{obj.title}' in schema {panel_schema} with panel '{panel_title}'")
                        else:
                            raise ValueError(f"Panel ID {obj.panel.id} not found in schema {panel_schema}")
                else:
                    # Fallback: use current schema
                    super().save_model(request, obj, form, change)
                    print(f"[NAV_ITEM_ADMIN] Saved NavigationItem '{obj.title}' (could not determine panel schema, used current)")
            else:
                super().save_model(request, obj, form, change)
                print(f"[NAV_ITEM_ADMIN] Saved NavigationItem '{obj.title}'")

    # Dashboard Button Admin
    @admin.register(DashboardButton)
    class DashboardButtonAdmin(TenantAwareModelAdmin):
        list_display = ('title', 'user', 'tenant', 'button_type', 'size', 'get_icon_display', 'is_active', 'click_count', 'sort_order', 'last_clicked')
        list_filter = ('button_type', 'size', 'icon_style', 'is_active', 'tenant', 'created_at')
        search_fields = ('title', 'description', 'url', 'user__username', 'user__email', 'tenant__name')
        ordering = ('tenant', 'user', 'sort_order', 'title')
        readonly_fields = ('click_count', 'last_clicked', 'created_at', 'updated_at')

        fieldsets = [
            (None, {
                'fields': ['tenant', 'user', 'title', 'description', 'url', 'button_type', 'icon_style', 'icon_value', 'color', 'size', 'target', 'is_active', 'sort_order', 'button_css_class']
            }),
            ('Analytics', {
                'fields': ['click_count', 'last_clicked', 'created_at', 'updated_at']
            }),
        ]

        def get_icon_display(self, obj):
            """Display icon with style information."""
            if obj.icon_style == 'emoji' and obj.icon_value:
                return f"{obj.icon_value} (emoji)"
            elif obj.icon_style == 'fontawesome' and obj.icon_value:
                return f"🎨 {obj.icon_value} (FA)"
            elif obj.icon_style == 'bootstrap' and obj.icon_value:
                return f"⚡ {obj.icon_value} (BS)"
            elif obj.icon_style == 'custom' and obj.icon_value:
                return f"🖼️ Custom Image"
            elif obj.icon_style == 'none':
                return "No Icon"
            else:
                return f"No icon ({obj.icon_style})"
        get_icon_display.short_description = 'Icon'

        def get_queryset(self, request):
            """Optimize queryset to include related information."""
            queryset = super().get_queryset(request)
            return queryset.select_related('user', 'tenant')

    # MQ Input and Output Admin
    @admin.register(MQInput)
    class MQInputAdmin(TenantAwareModelAdmin):
        list_display = ('name', 'provider', 'request_path', 'request_method', 'is_active', 'message_count', 'error_count', 'last_message_received', 'tenant')
        list_filter = ('provider', 'is_active', 'request_method', 'message_format', 'tenant', 'created_at')
        search_fields = ('name', 'request_path', 'description', 'tenant__name')
        ordering = ('tenant', 'name')
        readonly_fields = ('last_message_received', 'message_count', 'error_count', 'created_at', 'updated_at')

        fieldsets = [
            ('Basic Information', {
                'fields': ['tenant', 'name', 'provider', 'is_active', 'description']
            }),
            ('Path Matching', {
                'fields': ['request_path', 'request_method']
            }),
            ('RabbitMQ Settings', {
                'fields': ['rabbitmq_host', 'rabbitmq_port', 'rabbitmq_username', 'rabbitmq_password',
                          'rabbitmq_vhost', 'rabbitmq_exchange', 'rabbitmq_queue', 'rabbitmq_routing_key'],
                'classes': ['collapse']
            }),
            ('Google Pub/Sub Settings', {
                'fields': ['pubsub_project_id', 'pubsub_subscription', 'pubsub_topic', 'pubsub_credentials_json'],
                'classes': ['collapse']
            }),
            ('AWS SQS Settings', {
                'fields': ['sqs_queue_url', 'sqs_region', 'sqs_access_key_id', 'sqs_secret_access_key'],
                'classes': ['collapse']
            }),
            ('Message Processing', {
                'fields': ['message_format', 'message_schema', 'auto_ack', 'prefetch_count']
            }),
            ('Error Handling', {
                'fields': ['error_queue', 'max_retries']
            }),
            ('Statistics', {
                'fields': ['last_message_received', 'message_count', 'error_count', 'created_at', 'updated_at'],
                'classes': ['collapse']
            }),
        ]

    @admin.register(MQOutput)
    class MQOutputAdmin(TenantAwareModelAdmin):
        list_display = ('name', 'provider', 'instruction_path', 'is_active', 'message_count', 'error_count', 'last_message_sent', 'tenant')
        list_filter = ('provider', 'is_active', 'message_format', 'tenant', 'created_at')
        search_fields = ('name', 'instruction_path', 'description', 'tenant__name')
        ordering = ('tenant', 'name')
        readonly_fields = ('last_message_sent', 'message_count', 'error_count', 'created_at', 'updated_at')

        fieldsets = [
            ('Basic Information', {
                'fields': ['tenant', 'name', 'provider', 'is_active', 'description']
            }),
            ('Routing', {
                'fields': ['instruction_path'],
                'description': 'Path pattern that triggers this output (matches Instruction.requestpath, optional)'
            }),
            ('RabbitMQ Settings', {
                'fields': ['rabbitmq_host', 'rabbitmq_port', 'rabbitmq_username', 'rabbitmq_password',
                          'rabbitmq_vhost', 'rabbitmq_exchange', 'rabbitmq_queue', 'rabbitmq_routing_key'],
                'classes': ['collapse']
            }),
            ('Google Pub/Sub Settings', {
                'fields': ['pubsub_project_id', 'pubsub_topic', 'pubsub_credentials_json'],
                'classes': ['collapse']
            }),
            ('AWS SQS Settings', {
                'fields': ['sqs_queue_url', 'sqs_region', 'sqs_access_key_id', 'sqs_secret_access_key'],
                'classes': ['collapse']
            }),
            ('Message Formatting', {
                'fields': ['message_format', 'message_template', 'include_request_metadata', 'include_response_data']
            }),
            ('Publishing Options', {
                'fields': ['persistent', 'priority', 'expiration']
            }),
            ('Error Handling', {
                'fields': ['error_queue', 'retry_on_failure', 'max_retries']
            }),
            ('Statistics', {
                'fields': ['last_message_sent', 'message_count', 'error_count', 'created_at', 'updated_at'],
                'classes': ['collapse']
            }),
        ]

    @admin.register(MQConfig)
    class MQConfigAdmin(TenantAwareModelAdmin):
        list_display = ('name', 'provider', 'is_active', 'tenant', 'created_at')
        list_filter = ('provider', 'is_active', 'tenant', 'created_at')
        search_fields = ('name', 'description', 'tenant__name')
        ordering = ('tenant', 'name')

        fieldsets = [
            ('Basic Information', {
                'fields': ['tenant', 'name', 'provider', 'is_active', 'description']
            }),
            ('RabbitMQ Settings', {
                'fields': ['rabbitmq_host', 'rabbitmq_port', 'rabbitmq_username', 'rabbitmq_password',
                          'rabbitmq_vhost', 'rabbitmq_exchange', 'rabbitmq_queue', 'rabbitmq_routing_key'],
                'classes': ['collapse']
            }),
            ('Google Pub/Sub Settings', {
                'fields': ['pubsub_project_id', 'pubsub_subscription', 'pubsub_topic', 'pubsub_credentials_json'],
                'classes': ['collapse']
            }),
            ('AWS SQS Settings', {
                'fields': ['sqs_queue_url', 'sqs_region', 'sqs_access_key_id', 'sqs_secret_access_key'],
                'classes': ['collapse']
            }),
            ('Response Queue', {
                'fields': ['response_queue_enabled', 'response_queue_name', 'response_routing_key'],
                'classes': ['collapse']
            }),
            ('Timestamps', {
                'fields': ['created_at', 'updated_at'],
                'classes': ['collapse']
            }),
        ]

    @admin.register(IgnorePath)
    class IgnorePathAdmin(admin.ModelAdmin):
        list_display = ('url', 'description', 'get_tenant', 'is_active', 'created_at', 'updated_at')
        list_filter = ('is_active', 'tenant', 'created_at', 'updated_at')
        search_fields = ('url', 'description', 'tenant__name')
        ordering = ('tenant', 'url')

        fieldsets = [
            (None, {
                'fields': ['tenant', 'url', 'description', 'is_active', 'parameters', 'created_at', 'updated_at']
            }),
        ]

        readonly_fields = ('created_at', 'updated_at')

        def get_tenant(self, obj):
            """Display tenant name."""
            return obj.tenant.name if obj.tenant else 'No Tenant'
        get_tenant.short_description = 'Tenant'
        get_tenant.admin_order_field = 'tenant__name'

        def get_queryset(self, request):
            """Optimize queryset to include tenant information."""
            queryset = super().get_queryset(request)
            return queryset.select_related('tenant')

        def save_model(self, request, obj, form, change):
            """Auto-assign tenant if user belongs to only one tenant."""
            if not obj.tenant_id:
                # Try to get user's tenant
                try:
                    user_profile = UserProfile.objects.get(user=request.user)
                    obj.tenant = user_profile.tenant
                except UserProfile.DoesNotExist:
                    pass
            super().save_model(request, obj, form, change)

    # UserRequestTracker is now registered in active_urls app for separate box display

# Custom Admin for SocialApp to fix Sites field in multi-tenant environment
try:
    from allauth.socialaccount.models import SocialApp
    from django.contrib.sites.models import Site
    from django.db import connection

    class CustomSocialAppAdmin(admin.ModelAdmin):
        """Custom admin for SocialApp that ensures Sites field shows all sites from public schema"""

        def get_form(self, request, obj=None, **kwargs):
            form = super().get_form(request, obj, **kwargs)

            # Override the sites field queryset to always show sites from public schema
            if 'sites' in form.base_fields:
                # Get all sites from public schema using the patched Site.objects.filter
                # The patched methods in adapters.py will handle the public schema query
                # We'll get all sites and let the form handle ordering
                all_sites = Site.objects.filter()
                # If the result is a SiteQuerySet, it already has order_by support
                # If it's a regular queryset, we can call order_by
                if hasattr(all_sites, 'order_by'):
                    all_sites = all_sites.order_by('id')
                form.base_fields['sites'].queryset = all_sites

            # Set default for settings field if creating new object
            if obj is None and 'settings' in form.base_fields:
                form.base_fields['settings'].initial = {}

            return form

        def save_model(self, request, obj, form, change):
            # Ensure settings field is never null
            if obj.settings is None:
                obj.settings = {}
            super().save_model(request, obj, form, change)

        def save_related(self, request, form, formsets, change):
            """Override to ensure sites are saved correctly in multi-tenant context"""
            # Save the main object and all formsets first
            super().save_related(request, form, formsets, change)

            # Explicitly ensure sites are saved
            # The form should have already saved them, but let's verify
            try:
                if 'sites' in form.cleaned_data:
                    selected_sites = form.cleaned_data['sites']
                    # Ensure sites are in the relationship
                    form.instance.sites.set(selected_sites)
                    logger.info(f"[CUSTOM SOCIALAPP ADMIN] ✅ Saved {len(selected_sites)} site(s) to SocialApp {form.instance.id}: {[s.domain for s in selected_sites]}")
                else:
                    # If no sites in cleaned_data, check if they were in the form data
                    sites_from_form = form.data.getlist('sites')
                    if sites_from_form:
                        from django.contrib.sites.models import Site
                        site_ids = [int(sid) for sid in sites_from_form if sid.isdigit()]
                        sites = Site.objects.filter(id__in=site_ids)
                        form.instance.sites.set(sites)
                        logger.info(f"[CUSTOM SOCIALAPP ADMIN] ✅ Saved {len(sites)} site(s) from form data to SocialApp {form.instance.id}")
            except Exception as e:
                logger.error(f"[CUSTOM SOCIALAPP ADMIN] ❌ Error saving sites: {e}")
                import traceback
                logger.error(traceback.format_exc())

        def response_post_save_change(self, request, obj):
            """Called after saving - verify sites were saved"""
            try:
                sites_count = obj.sites.count()
                sites_list = [s.domain for s in obj.sites.all()]
                logger.info(f"[CUSTOM SOCIALAPP ADMIN] Verification: SocialApp {obj.id} has {sites_count} site(s): {sites_list}")
            except Exception as e:
                logger.warning(f"[CUSTOM SOCIALAPP ADMIN] Error checking sites after save: {e}")
            return super().response_post_save_change(request, obj)

    # Unregister default SocialApp admin and register our custom one
    try:
        admin.site.unregister(SocialApp)
    except admin.sites.NotRegistered:
        pass  # Not registered yet, that's fine

    admin.site.register(SocialApp, CustomSocialAppAdmin)
except ImportError:
    pass  # allauth not installed, skip
except Exception as e:
    print(f"[ADMIN] Warning: Could not register custom SocialApp admin: {e}")

# Site customization
admin.site.site_url = 'http://localhost:8000/'
#admin.site.site_header = "D.O.S.E. Administration"
admin.site.site_title = "D.O.S.E. Administration"
admin.site.index_title = "Welcome to the D.O.S.E. Administration"
