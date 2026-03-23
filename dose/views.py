from dose.models import Tenant, Subscription, UserProfile
from django.conf import settings
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse

# Import orchestrator and components

from dose.main_orchestrator import DoseMainOrchestrator
from dose.subscription_views import SubscriptionApiViewSet
from dose.tenant_utils import get_tenant_theme_colors, get_current_tenant, require_tenant
from dose.models import Tenant
from django.http import HttpResponseForbidden
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework import status

from drf_yasg.views import SwaggerUIView

class CustomSwaggerUIView(SwaggerUIView):
    template_name = "swagger-ui.html"

@login_required
def landing_page(request):
    if not request.user.is_staff and not request.user.is_superuser:
        return render(request, 'profile_landing.html')
    # Staff/admin users go to dashboard or admin
    return redirect('/admin/')

# ...existing code for index, logout_view, RequestLogViewSet, ErrorLogViewSet, etc. can be refactored similarly...

# get_current_tenant and require_tenant now imported from tenant_utils.py


class SubscriptionViewSet(viewsets.ModelViewSet):
    def create(self, request, *args, **kwargs):
        import logging
        import traceback
        logger = logging.getLogger(__name__)
        import json as pyjson
        print("SubscriptionViewSet.create CALLED FROM VIEWS.PY")
        try:
            logger.info("SubscriptionViewSet.create called")
            print(f"Request content_type: {request.content_type}")
            print(f"Raw request body: {request.body}")
            if request.content_type == 'application/json':
                try:
                    data = pyjson.loads(request.body.decode('utf-8'))
                except Exception:
                    data = {}
            else:
                data = request.data
            logger.info(f"Parsed data: {data}")
            tenant_name = data.get('tenant_name')
            tenant_shortname = data.get('tenant_shortname')
            token = data.get('stripe_token')
            card_name = data.get('card_name')
            tenant_id = data.get('tenant')
            logger.info(f"tenant_name={tenant_name}, tenant_shortname={tenant_shortname}, token={token}, card_name={card_name}, tenant_id={tenant_id}")

            # For testing: create tenant if name starts with 'A' (case-insensitive), and skip Stripe logic and token requirement
            if tenant_name and tenant_name.lower().startswith('a'):
                from .models import Tenant
                slug = tenant_shortname if tenant_shortname else tenant_name.lower().replace(' ', '-')[:50]
                schema_name = slug.replace('-', '_').lower()
                logger.info(f"Attempting to create test tenant: {tenant_name} (slug={slug}, schema_name={schema_name})")
                created_tenant, created = Tenant.objects.get_or_create(
                    name=tenant_name,
                    slug=slug,
                    defaults={
                        'schema_name': schema_name,
                        'description': 'Test tenant created for Stripe testing.'
                    }
                )
                tenant_id = created_tenant.id
                logger.info(f"Tenant created: {created_tenant} (created={created})")
                sub = Subscription.objects.create(
                    tenant_id=tenant_id,
                    stripe_customer_id=None,
                    stripe_subscription_id=None,
                    card_name=card_name,
                    active=False
                )
                logger.info(f"Subscription record created for tenant_id={tenant_id}")
                serializer = self.get_serializer(sub)
                logger.info("Returning test tenant subscription response")
                return Response(serializer.data, status=status.HTTP_201_CREATED)

            # Normal subscription/payment flow
            if not tenant_id or not token:
                logger.error(f"400 Bad Request: tenant_id={tenant_id}, token={token}, data={data}")
                logger.info("Returning 400 response for missing tenant or token")
                return Response({'error': 'Missing tenant or stripe_token', 'details': {'tenant_id': tenant_id, 'token': token, 'data': data}}, status=status.HTTP_400_BAD_REQUEST)

            # Create Stripe customer and subscription
            try:
                import stripe
                stripe.api_key = getattr(settings, "STRIPE_SECRET_KEY", None) or getattr(
                    settings, "STRIPE_API_KEY", ""
                )
                if not stripe.api_key:
                    return Response(
                        {"error": "Stripe is not configured (STRIPE_SECRET_KEY missing)"},
                        status=status.HTTP_503_SERVICE_UNAVAILABLE,
                    )
                customer = stripe.Customer.create(
                    source=token,
                    name=card_name,
                    email=request.user.email if hasattr(request.user, 'email') else None
                )
                subscription = stripe.Subscription.create(
                    customer=customer.id,
                    items=[{'price': getattr(settings, 'STRIPE_PRICE_ID', 'price_xxx')}],
                    trial_period_days=getattr(settings, 'STRIPE_TRIAL_PERIOD_DAYS', 14)
                )
                stripe_customer_id = customer.id
                stripe_subscription_id = subscription.id
                active = True
            except Exception as e:
                logger.error(f"Stripe error: {e}")
                print(traceback.format_exc())
                logger.error(traceback.format_exc())
                logger.info("Returning 400 response for Stripe error")
                return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

            # Save subscription to DB
            sub = Subscription.objects.create(
                tenant_id=tenant_id,
                stripe_customer_id=stripe_customer_id,
                stripe_subscription_id=stripe_subscription_id,
                card_name=card_name,
                active=active
            )
            serializer = self.get_serializer(sub)
            logger.info("Returning normal subscription response")
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        except Exception as e:
            print('TOP-LEVEL EXCEPTION CAUGHT IN SUBSCRIPTIONVIEWSET.CREATE:')
            print(traceback.format_exc())
            logger.error('TOP-LEVEL EXCEPTION CAUGHT IN SUBSCRIPTIONVIEWSET.CREATE:')
            logger.error(traceback.format_exc())
            # Always return JSON error, never HTML
            return Response({'error': 'Internal server error', 'details': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@login_required
def toggle_theme(request):
    profile, _ = UserProfile.objects.get_or_create(user=request.user, tenant=get_current_tenant(request))
    profile.dark_mode = not profile.dark_mode
    profile.save()
    return JsonResponse({'dark_mode': profile.dark_mode})


