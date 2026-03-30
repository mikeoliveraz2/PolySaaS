"""
Multi-tenant membership & isolation tests (Req 1–6).

Structure:
- ``TenantMembershipMiddlewareTests`` — TenantContextMiddleware + session (unit-style).
- ``TenantMembershipContextTests`` — ``tenant_context`` processor + template tag.
- ``TenantMembershipAPITests`` — APIClient: switching, instruction isolation, bundle permission.

Requires PostgreSQL (project default). Schema creation on new Tenant rows is mocked so tests
do not need ``CREATE SCHEMA`` privileges on the dev DB user.

If ``manage.py test`` fails while **creating the test database** with
``InvalidBasesError`` for ``ml_studio.*Proxy`` models, fix that migration
dependency first (project-wide); the tests themselves are valid once the test DB
migrates cleanly.
"""

from unittest import mock

from django.contrib.auth import get_user_model
from django.test import RequestFactory, TestCase
from django.urls import reverse

from rest_framework.test import APIClient, APITestCase

from dose.context_processors import tenant_context
from dose.models import Instruction, Tenant, TenantApp, UserTenantMembership
from dose.tenant_app_bundle import TenantAppBundlePermission, tenant_has_active_bundle
from dose.tenant_session import apply_tenant_to_session
from dose.templatetags.tenant_tags import tenant_header
from mysite.tenant_context_middleware import TenantContextMiddleware


User = get_user_model()


def _noop_create_schema(schema_name):
    """Skip physical PostgreSQL schema creation in tests."""
    del schema_name  # unused


@mock.patch("dose.models.tenant.create_schema_and_copy_tables", side_effect=_noop_create_schema)
class TenantMembershipMiddlewareTests(TestCase):
    """Req 1, 2, 4: session tenant + middleware populates request.current_tenant_*."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="mt_membership_user",
            email="michael.oliver@polysaas.online.test",
            password="test-pass-123",
        )
        self.t1 = Tenant.objects.create(
            name="Oliver Enterprises",
            slug="test-oliver-mt",
            is_active=True,
        )
        self.t2 = Tenant.objects.create(
            name="PolySaaS Online LLC",
            slug="test-polysaas-online-mt",
            is_active=True,
        )
        self.m1 = UserTenantMembership.objects.create(
            user=self.user,
            tenant=self.t1,
            role=UserTenantMembership.Role.OWNER,
        )
        self.m2 = UserTenantMembership.objects.create(
            user=self.user,
            tenant=self.t2,
            role=UserTenantMembership.Role.ADMIN,
        )

    def _process_request(self, request):
        middleware = TenantContextMiddleware(lambda req: None)
        middleware.process_request(request)

    def test_middleware_sets_context_from_session_tenant_1(self):
        factory = RequestFactory()
        request = factory.get("/dose/dashboard/")
        request.user = self.user
        request.session = self.client.session
        request.session.create()
        apply_tenant_to_session(request, self.t1, self.m1)
        self._process_request(request)

        self.assertEqual(request.current_tenant_id, self.t1.id)
        self.assertEqual(request.current_tenant_role, UserTenantMembership.Role.OWNER)

    def test_middleware_sets_context_after_switching_session_to_tenant_2(self):
        factory = RequestFactory()
        request = factory.get("/dose/dashboard/")
        request.user = self.user
        request.session = self.client.session
        request.session.create()
        apply_tenant_to_session(request, self.t2, self.m2)
        self._process_request(request)

        self.assertEqual(request.current_tenant_id, self.t2.id)
        self.assertEqual(request.current_tenant_role, UserTenantMembership.Role.ADMIN)

    def test_middleware_clears_context_when_membership_missing(self):
        factory = RequestFactory()
        request = factory.get("/dose/")
        request.user = self.user
        request.session = self.client.session
        request.session.create()
        request.session["tenant_id"] = 999999
        request.session.save()

        self._process_request(request)

        self.assertIsNone(getattr(request, "current_tenant_id", None))
        self.assertIsNone(getattr(request, "current_tenant_role", None))
        self.assertIsNone(request.session.get("tenant_id"))


@mock.patch("dose.models.tenant.create_schema_and_copy_tables", side_effect=_noop_create_schema)
class TenantMembershipContextTests(TestCase):
    """Req 5: context processor and template tag show name + role."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="mt_ctx_user",
            email="ctx@polysaas.test",
            password="pw",
        )
        self.t1 = Tenant.objects.create(
            name="Oliver Enterprises", slug="ctx-oliver", is_active=True
        )
        self.m1 = UserTenantMembership.objects.create(
            user=self.user,
            tenant=self.t1,
            role=UserTenantMembership.Role.ADMIN,
        )

    def test_tenant_context_includes_role_header_label(self):
        factory = RequestFactory()
        request = factory.get("/")
        request.user = self.user
        request.session = self.client.session
        request.session.create()
        apply_tenant_to_session(request, self.t1, self.m1)
        TenantContextMiddleware(lambda r: None).process_request(request)

        ctx = tenant_context(request)
        self.assertEqual(ctx["current_tenant"].id, self.t1.id)
        self.assertEqual(ctx["current_tenant_role"], "admin")
        self.assertIn("Admin", ctx["current_tenant_role_display"])
        self.assertIn("Oliver Enterprises", ctx["current_tenant_header_label"])
        self.assertIn("Admin", ctx["current_tenant_header_label"])

    def test_tenant_header_template_tag(self):
        factory = RequestFactory()
        request = factory.get("/")
        request.user = self.user
        request.session = self.client.session
        request.session.create()
        apply_tenant_to_session(request, self.t1, self.m1)
        TenantContextMiddleware(lambda r: None).process_request(request)

        label = tenant_header({"request": request})
        self.assertIn("Oliver Enterprises", label)
        self.assertIn("Admin", label)


@mock.patch("dose.models.tenant.create_schema_and_copy_tables", side_effect=_noop_create_schema)
class TenantMembershipAPITests(APITestCase):
    """Req 3, 4, 6: API switching, queryset isolation, TenantApp bundle checks."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="mt_api_user",
            email="api@polysaas.test",
            password="api-pass-456",
        )
        self.t1 = Tenant.objects.create(
            name="Oliver Enterprises", slug="api-oliver", is_active=True
        )
        self.t2 = Tenant.objects.create(
            name="PolySaaS Online LLC", slug="api-polysaas-llc", is_active=True
        )
        self.m1 = UserTenantMembership.objects.create(
            user=self.user,
            tenant=self.t1,
            role=UserTenantMembership.Role.OWNER,
        )
        self.m2 = UserTenantMembership.objects.create(
            user=self.user,
            tenant=self.t2,
            role=UserTenantMembership.Role.ADMIN,
        )
        TenantApp.public_bundles.create(
            tenant=self.t1,
            app_name="mattermost",
            status="active",
        )
        TenantApp.public_bundles.create(
            tenant=self.t2,
            app_name="nextcloud",
            status="active",
        )

        self.client = APIClient(enforce_csrf_checks=False)
        self.client.login(username="mt_api_user", password="api-pass-456")

    def test_switch_tenant_api_updates_session(self):
        sreq = type("SReq", (), {"session": self.client.session, "user": self.user})()
        apply_tenant_to_session(sreq, self.t1, self.m1)
        self.client.session.save()

        url = reverse("dose:api_switch_tenant")
        r = self.client.post(url, {"tenant_id": self.t2.id}, format="json")
        self.assertEqual(r.status_code, 200, r.content)
        self.assertTrue(r.data.get("success"))
        self.assertEqual(r.data.get("tenant_id"), self.t2.id)
        self.assertEqual(r.data.get("tenant_role"), UserTenantMembership.Role.ADMIN)
        self.assertEqual(self.client.session.get("tenant_id"), self.t2.id)

    def test_instruction_list_only_shows_active_tenant_rows(self):
        Instruction.objects.create(
            tenant=self.t1,
            requestpath="/api/oliver-only/",
            requestmethod="GET",
        )
        Instruction.objects.create(
            tenant=self.t2,
            requestpath="/api/llc-only/",
            requestmethod="GET",
        )
        sreq = type("SReq", (), {"session": self.client.session, "user": self.user})()
        apply_tenant_to_session(sreq, self.t1, self.m1)
        self.client.session.save()

        r = self.client.get("/dose/api/instructions/")
        self.assertEqual(r.status_code, 200, r.content)
        rows = r.data
        if isinstance(rows, dict) and "results" in rows:
            rows = rows["results"]
        paths = {row["requestpath"] for row in rows}
        self.assertIn("/api/oliver-only/", paths)
        self.assertNotIn("/api/llc-only/", paths)

        apply_tenant_to_session(sreq, self.t2, self.m2)
        self.client.session.save()
        r2 = self.client.get("/dose/api/instructions/")
        self.assertEqual(r2.status_code, 200, r2.content)
        rows2 = r2.data
        if isinstance(rows2, dict) and "results" in rows2:
            rows2 = rows2["results"]
        paths2 = {row["requestpath"] for row in rows2}
        self.assertIn("/api/llc-only/", paths2)
        self.assertNotIn("/api/oliver-only/", paths2)

    def test_tenant_has_active_bundle_differs_per_tenant(self):
        self.assertTrue(tenant_has_active_bundle(self.t1, "mattermost"))
        self.assertFalse(tenant_has_active_bundle(self.t1, "nextcloud"))
        self.assertTrue(tenant_has_active_bundle(self.t2, "nextcloud"))
        self.assertFalse(tenant_has_active_bundle(self.t2, "mattermost"))

    def test_tenant_app_bundle_permission_matches_active_tenant(self):
        factory = RequestFactory()
        perm = TenantAppBundlePermission()
        view_mm = type("V", (), {"required_tenant_app": "mattermost"})()
        view_nc = type("V", (), {"required_tenant_app": "nextcloud"})()

        request = factory.get("/dose/api/x/")
        request.user = self.user
        request.session = self.client.session
        request.session.create()
        apply_tenant_to_session(request, self.t1, self.m1)
        TenantContextMiddleware(lambda req: None).process_request(request)
        self.assertTrue(perm.has_permission(request, view_mm))
        self.assertFalse(perm.has_permission(request, view_nc))

        apply_tenant_to_session(request, self.t2, self.m2)
        TenantContextMiddleware(lambda req: None).process_request(request)
        self.assertFalse(perm.has_permission(request, view_mm))
        self.assertTrue(perm.has_permission(request, view_nc))

