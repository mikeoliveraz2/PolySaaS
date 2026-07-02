"""HubSpot session service — unit tests."""
from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase

from dose.services.hubspot_session import (
    DEFAULT_PLACEHOLDER_PORTAL_ID,
    HubspotSessionService,
)


class HubspotSessionServiceTests(SimpleTestCase):
    def _request_with_session(self):
        class SessionDict(dict):
            modified = False

        request = MagicMock()
        request.session = SessionDict()
        request.method = 'GET'
        request._polysniffer_client_path = '/pt/polysniff/4/home/'
        request._polysniffer_endpoint_id = 4
        return request

    def test_portal_id_from_extra_config(self):
        request = self._request_with_session()
        ta = MagicMock()
        ta.extra_config = {'hs_portal_id': '246571499'}
        svc = HubspotSessionService(request, endpoint_id=4)
        svc.tenant_app = ta
        with patch.object(HubspotSessionService, '_resolve_tenant', return_value=MagicMock()):
            self.assertEqual(svc.portal_id(), 246571499)

    def test_portal_id_placeholder_when_no_oauth(self):
        request = self._request_with_session()
        svc = HubspotSessionService(request, endpoint_id=4)
        svc.tenant_app = MagicMock(extra_config={})
        with patch.object(HubspotSessionService, '_resolve_tenant', return_value=MagicMock()):
            self.assertEqual(
                svc.portal_id(placeholder=DEFAULT_PLACEHOLDER_PORTAL_ID),
                DEFAULT_PLACEHOLDER_PORTAL_ID,
            )

    def test_cookies_for_upstream_skips_login_post(self):
        request = self._request_with_session()
        request.method = 'POST'
        request._polysniffer_client_path = '/pt/polysniff/4/login/'
        svc = HubspotSessionService(request, endpoint_id=4)
        self.assertEqual(svc.cookies_for_upstream(client_path=request._polysniffer_client_path, method='POST'), {})

    def test_cookies_for_upstream_skips_api_paths(self):
        request = self._request_with_session()
        svc = HubspotSessionService(request, endpoint_id=4)
        out = svc.cookies_for_upstream(
            client_path='/pt/polysniff/4/home/v2/api/portal',
            method='GET',
        )
        self.assertEqual(out, {})

    @patch('dose.services.hubspot_session.http_requests.get')
    def test_validate_web_cookies_accepts_portal_json(self, mock_get):
        mock_get.return_value = MagicMock(
            status_code=200,
            json=lambda: {'portalId': 246571499},
        )
        request = self._request_with_session()
        svc = HubspotSessionService(request, endpoint_id=4)
        ok = svc.validate_web_cookies({'hubspotapi': 'abc', 'csrf.app': 'xyz'})
        self.assertTrue(ok)

    @patch('dose.services.hubspot_session.http_requests.get')
    def test_validate_web_cookies_rejects_401(self, mock_get):
        mock_get.return_value = MagicMock(status_code=401, text='unauthorized')
        request = self._request_with_session()
        svc = HubspotSessionService(request, endpoint_id=4)
        self.assertFalse(svc.validate_web_cookies({'hubspotapi': 'abc'}))

    def test_persist_web_cookies_writes_session_and_extra_config(self):
        request = self._request_with_session()
        ta = MagicMock()
        ta.extra_config = {}
        svc = HubspotSessionService(request, endpoint_id=4)
        svc.tenant_app = ta
        svc.persist_web_cookies(
            {'hubspotapi': 'tok', 'csrf.app': 'csrf'},
            source='popup_sync',
        )
        self.assertEqual(request.session['hubspot_cookies_4']['hubspotapi'], 'tok')
        self.assertEqual(ta.extra_config['hs_web_cookies']['hubspotapi'], 'tok')
        self.assertEqual(ta.extra_config['hs_web_cookies_source'], 'popup_sync')
        ta.save.assert_called_once_with(update_fields=['extra_config'])

    @patch('dose.services.hubspot_session.HubspotApiService')
    def test_ensure_api_token_delegates_to_hubspot_api_service(self, mock_api_cls):
        mock_api_cls.return_value._refresh_if_needed.return_value = 'pat-na1-test'
        request = self._request_with_session()
        tenant = MagicMock()
        ta = MagicMock()
        svc = HubspotSessionService(request, endpoint_id=4)
        svc.tenant = tenant
        svc.tenant_app = ta
        self.assertEqual(svc.ensure_api_token(), 'pat-na1-test')
        mock_api_cls.assert_called_once_with(tenant, ta)
