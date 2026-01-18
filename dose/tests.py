from django.test import TestCase, RequestFactory
from dose.subscription_views import SubscriptionViewSet
from dose.models import Tenant, Subscription
from django.contrib.auth.models import AnonymousUser
from dose.tenant_utils import get_tenant_theme_colors
from dose.main_orchestrator import DoseMainOrchestrator

class SubscriptionViewSetTests(TestCase):
    def test_subscription_create_test_tenant(self):
        factory = RequestFactory()
        data = {
            'tenant_name': 'AlphaTenant',
            'card_name': 'Test Card',
            'stripe_token': None,
            'tenant': None
        }
        request = factory.post('/dose/api/subscriptions/', data, content_type='application/json')
        request.user = AnonymousUser()
        viewset = SubscriptionViewSet()
        viewset.get_serializer = lambda obj: type('Serializer', (), {'data': {'id': obj.id}})()
        response = viewset.create(request)
        self.assertEqual(response.status_code, 201)
        self.assertIn('id', response.data)

    def test_subscription_create_missing_token(self):
        factory = RequestFactory()
        data = {
            'tenant_name': 'BetaTenant',
            'card_name': 'Test Card',
            'stripe_token': None,
            'tenant': 1
        }
        request = factory.post('/dose/api/subscriptions/', data, content_type='application/json')
        request.user = AnonymousUser()
        viewset = SubscriptionViewSet()
        viewset.get_serializer = lambda obj: type('Serializer', (), {'data': {'id': obj.id}})()
        response = viewset.create(request)
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.data)

class TenantUtilsTests(TestCase):
    def test_get_tenant_theme_colors_default(self):
        colors = get_tenant_theme_colors('unknown_theme')
        self.assertEqual(colors['name'], 'Tech Blue')

    def test_get_tenant_theme_colors_specific(self):
        colors = get_tenant_theme_colors('forest_green')
        self.assertEqual(colors['name'], 'Forest Green')

class OrchestratorTests(TestCase):
    def test_orchestrator_imports(self):
        orchestrator = DoseMainOrchestrator()
        self.assertTrue(hasattr(orchestrator, 'subscription_viewset'))
        self.assertTrue(hasattr(orchestrator, 'get_tenant_theme_colors'))
        self.assertTrue(hasattr(orchestrator, 'get_current_tenant'))
        self.assertTrue(hasattr(orchestrator, 'require_tenant'))
