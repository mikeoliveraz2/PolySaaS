from dose.views.main import (
debug_session_view,
subscribe_view,
passthrough_iframe_view,
passthrough_html_view,
google_profile_view,
facebook_profile_view,
github_profile_view,
RequestLogViewSet,
ErrorLogViewSet,
SubscriptionViewSet,
AtomicServiceViewSet,
debug_tenant_session,
login_view,
logout_view,
dashboard,
landing_page,
switch_tenant,
tenant_settings,
tenant_users,
get_user_tenants_api,
get_tenant_info_api,
update_tenant_api,
track_navigation_click,
track_dashboard_button_click,
debug_view,
setup_demo_view,
create_sample_dashboard_buttons,
health_check,
custom_swagger_view,
index,
connect_social_after_subscribe,
select_tenant_view,
)

from dose.views.about import (
about_page,
)

from dose.views.gmail_api import (
dynamic_gmail_api,
gmail_inbox,
gmail_send,
)

from dose.views.orchestration import (
orchestration_dashboard,
create_instruction,
)

from dose.views.tenant_switch_api import switch_tenant_api
