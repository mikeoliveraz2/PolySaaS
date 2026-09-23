"""Type 3 invoice refine — unit tests (no live Odoo / LLM)."""
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase

from dose.services.enqueue_odoo_invoice_refine import (
    EnqueueOdooInvoiceRefine,
    _extract_move_ids,
    _is_invoice_action_post,
)
from dose.services.refine_odoo_invoice_description import (
    RefineOdooInvoiceDescription,
    _text_hash,
)
from dose.messaging import feedback_text_for_result


class EnqueueParseTests(SimpleTestCase):
    def test_detects_action_post_account_move(self):
        body = {
            "params": {
                "model": "account.move",
                "method": "action_post",
                "args": [[42]],
            }
        }
        self.assertTrue(_is_invoice_action_post(body, "/web/dataset/call_button"))
        self.assertFalse(
            _is_invoice_action_post(
                {"params": {"model": "sale.order", "method": "action_confirm"}},
                "/web/dataset/call_button",
            )
        )

    def test_extract_move_ids(self):
        body = {"params": {"args": [[7, 8]], "method": "action_post", "model": "account.move"}}
        self.assertEqual(_extract_move_ids(body), [7, 8])


class ConfirmQueueTests(SimpleTestCase):
    def _confirm_request(self):
        body = {
            "params": {
                "model": "account.move",
                "method": "action_post",
                "args": [[42]],
            }
        }
        return SimpleNamespace(
            path="/web/dataset/call_button",
            body=__import__("json").dumps(body).encode(),
            tenant=SimpleNamespace(schema_name="polysaas"),
            mq_message_data=None,
        )

    @patch("dose.webhook_events.publish_odoo_invoice_refine_event")
    @patch("dose.services.refine_odoo_invoice_description.OdooRpcClient")
    def test_confirm_queues_and_does_not_call_odoo(self, client_cls, publish):
        publish.return_value = {"success": True, "mailbox_id": 3, "event_id": "abc"}
        instruction = SimpleNamespace(save_callbackdata=False, parameters_json={})
        result = RefineOdooInvoiceDescription.execute_and_save(self._confirm_request(), instruction)
        self.assertEqual(result["status"], "success")
        self.assertTrue(result["queued"])
        self.assertEqual(result["move_ids"], [42])
        publish.assert_called_once()
        client_cls.from_config.assert_not_called()

    @patch("dose.webhook_events.publish_odoo_invoice_refine_event")
    def test_enqueue_alias_delegates(self, publish):
        publish.return_value = {"success": True, "mailbox_id": 4, "event_id": "def"}
        result = EnqueueOdooInvoiceRefine.execute_and_save(
            self._confirm_request(),
            SimpleNamespace(save_callbackdata=False, parameters_json={}),
        )
        self.assertTrue(result["queued"])
        self.assertEqual(result["move_ids"], [42])

    def test_unrelated_post_skipped(self):
        request = SimpleNamespace(
            path="/web/dataset/call_button",
            body=b'{"params":{"model":"sale.order","method":"action_confirm","args":[[1]]}}',
            tenant=SimpleNamespace(schema_name="polysaas"),
        )
        result = RefineOdooInvoiceDescription.execute_and_save(
            request, SimpleNamespace(save_callbackdata=False, parameters_json={})
        )
        self.assertEqual(result["status"], "skipped")
        self.assertEqual(result["reason"], "not_account_move_action_post")


class RefineAtomicTests(SimpleTestCase):
    def test_selector(self):
        self.assertEqual(RefineOdooInvoiceDescription.atomic_apps, ("odoo",))
        self.assertEqual(EnqueueOdooInvoiceRefine.atomic_apps, ("odoo",))

    def test_hash_idempotent(self):
        self.assertEqual(_text_hash("Hello  world"), _text_hash("hello world"))

    @patch("dose.services.refine_odoo_invoice_description._ai_clean", return_value="Clean note.")
    @patch("dose.services.refine_odoo_invoice_description.load_odoo_rpc_config")
    @patch("dose.services.refine_odoo_invoice_description.OdooRpcClient")
    def test_writes_when_changed(self, client_cls, load_cfg, _ai):
        load_cfg.return_value = {"url": "http://odoo", "db": "odoo", "username": "a", "password": "b"}
        client = MagicMock()
        client_cls.from_config.return_value = client

        def _exec(model, method, *args, **kwargs):
            if model == "account.move" and method == "read":
                return [{"id": 9, "name": "INV/2026/0001", "narration": "filty mess", "state": "posted"}]
            if model == "account.move" and method == "write":
                return True
            if model == "account.move.line" and method == "search_read":
                return []
            return True

        client.execute_kw.side_effect = _exec
        request = SimpleNamespace(tenant=SimpleNamespace(schema_name="olient"), mq_message_data={"move_ids": [9]})
        instruction = SimpleNamespace(save_callbackdata=False, parameters_json={})
        result = RefineOdooInvoiceDescription.execute_and_save(request, instruction)
        self.assertEqual(result["status"], "success")
        self.assertTrue(result["changed"])
        self.assertEqual(result["outcomes"][0]["after"], "Clean note.")

    @patch("dose.services.refine_odoo_invoice_description._ai_clean", return_value="same")
    @patch("dose.services.refine_odoo_invoice_description.load_odoo_rpc_config")
    @patch("dose.services.refine_odoo_invoice_description.OdooRpcClient")
    def test_no_write_when_unchanged(self, client_cls, load_cfg, _ai):
        load_cfg.return_value = {"url": "http://odoo", "db": "odoo", "username": "a", "password": "b"}
        client = MagicMock()
        client_cls.from_config.return_value = client

        def _exec(model, method, *args, **kwargs):
            if model == "account.move" and method == "read":
                return [{"id": 9, "name": "INV/1", "narration": "same", "state": "posted"}]
            if model == "account.move.line":
                return []
            return True

        client.execute_kw.side_effect = _exec
        request = SimpleNamespace(tenant=SimpleNamespace(schema_name="olient"), mq_message_data={"move_ids": [9]})
        result = RefineOdooInvoiceDescription.execute_and_save(
            request, SimpleNamespace(save_callbackdata=False, parameters_json={})
        )
        self.assertFalse(result["changed"])

    @patch(
        "dose.services.refine_odoo_invoice_description._ai_clean",
        side_effect=RuntimeError("down"),
    )
    @patch("dose.services.refine_odoo_invoice_description.load_odoo_rpc_config")
    @patch("dose.services.refine_odoo_invoice_description.OdooRpcClient")
    def test_ai_fail_soft(self, client_cls, load_cfg, _ai):
        load_cfg.return_value = {"url": "http://odoo", "db": "odoo", "username": "a", "password": "b"}
        client = MagicMock()
        client_cls.from_config.return_value = client

        def _exec(model, method, *args, **kwargs):
            if model == "account.move" and method == "read":
                return [{"id": 9, "name": "INV/1", "narration": "messy text here", "state": "posted"}]
            if model == "account.move.line":
                return []
            return True

        client.execute_kw.side_effect = _exec
        result = RefineOdooInvoiceDescription.execute_and_save(
            SimpleNamespace(
                tenant=SimpleNamespace(schema_name="olient"),
                mq_message_data={"move_ids": [9]},
            ),
            SimpleNamespace(save_callbackdata=False, parameters_json={}),
        )
        self.assertEqual(result["status"], "success")
        self.assertFalse(result["changed"])
        self.assertEqual(result["outcomes"][0]["reason"], "ai_failed_soft")

    @patch(
        "dose.services.refine_odoo_invoice_description._ai_clean",
        side_effect=RuntimeError("[llm_router] ANTHROPIC_API_KEY not configured."),
    )
    @patch("dose.services.refine_odoo_invoice_description.load_odoo_rpc_config")
    @patch("dose.services.refine_odoo_invoice_description.OdooRpcClient")
    def test_line_note_ai_failure_is_not_no_change(self, client_cls, load_cfg, _ai):
        load_cfg.return_value = {"url": "http://odoo", "db": "odoo", "username": "a", "password": "b"}
        client = MagicMock()
        client_cls.from_config.return_value = client

        def _exec(model, method, *args, **kwargs):
            if model == "account.move" and method == "read":
                return [{"id": 9, "name": "2Inv #13", "narration": "", "state": "posted"}]
            if model == "account.move.line" and method == "search_read":
                return [{"id": 50, "name": "now we seee if this gets refucking fined", "display_type": "line_note"}]
            return True

        client.execute_kw.side_effect = _exec
        result = RefineOdooInvoiceDescription.execute_and_save(
            SimpleNamespace(
                tenant=SimpleNamespace(schema_name="polysaas"),
                mq_message_data={"move_ids": [9]},
            ),
            SimpleNamespace(save_callbackdata=False, parameters_json={}),
        )
        self.assertFalse(result["changed"])
        self.assertEqual(result["outcomes"][0]["reason"], "ai_failed_soft")
        text, _level = feedback_text_for_result(
            SimpleNamespace(eventKey="odoo.invoice.refine", executescript="RefineOdooInvoiceDescription"),
            result,
            "RefineOdooInvoiceDescription",
        )
        self.assertIn("skipped", text.lower())
        self.assertNotIn("no change", text.lower())

    @patch("dose.services.refine_odoo_invoice_description._cached_odoo_session")
    @patch("dose.webhook_events.publish_odoo_invoice_refine_event")
    @patch("dose.services.refine_odoo_invoice_description.OdooRpcClient")
    def test_confirm_stashes_session_outside_the_bar_result(self, client_cls, publish, session):
        session.return_value = {
            "odoo_session_id": "sid-secret",
            "odoo_url": "http://odoo:8069",
        }
        publish.return_value = {"success": True, "mailbox_id": 9, "event_id": "e1"}
        body = {
            "params": {
                "model": "account.move",
                "method": "action_post",
                "args": [[42]],
            }
        }
        result = RefineOdooInvoiceDescription.execute_and_save(
            SimpleNamespace(
                path="/web/dataset/call_button",
                body=__import__("json").dumps(body).encode(),
                tenant=SimpleNamespace(schema_name="polysaas"),
                mq_message_data=None,
            ),
            SimpleNamespace(save_callbackdata=False, parameters_json={}),
        )
        job = publish.call_args[0][1]
        self.assertEqual(job["odoo_session_id"], "sid-secret")
        self.assertEqual(job["odoo_url"], "http://odoo:8069")
        self.assertNotIn("sid-secret", __import__("json").dumps(result))
        client_cls.from_config.assert_not_called()
        client_cls.for_session.assert_not_called()

    @patch("dose.services.refine_odoo_invoice_description._ai_clean", return_value="Clean note.")
    @patch("dose.services.refine_odoo_invoice_description.load_odoo_rpc_config")
    @patch("dose.services.refine_odoo_invoice_description.OdooRpcClient")
    def test_replay_uses_session_cookie_not_password(self, client_cls, load_cfg, _ai):
        client = MagicMock()
        client_cls.for_session.return_value = client

        def _exec(model, method, *args, **kwargs):
            if model == "account.move" and method == "read":
                return [{"id": 9, "name": "INV/1", "narration": "filty mess", "state": "posted"}]
            if model == "account.move" and method == "write":
                return True
            if model == "account.move.line" and method == "search_read":
                return []
            return True

        client.execute_kw.side_effect = _exec
        result = RefineOdooInvoiceDescription.execute_and_save(
            SimpleNamespace(
                tenant=SimpleNamespace(schema_name="polysaas"),
                mq_message_data={
                    "move_ids": [9],
                    "odoo_session_id": "sid-secret",
                    "odoo_url": "http://odoo:8069",
                },
            ),
            SimpleNamespace(save_callbackdata=False, parameters_json={}),
        )
        self.assertTrue(result["changed"])
        client_cls.for_session.assert_called_once_with("http://odoo:8069", "sid-secret")
        client.authenticate.assert_called_once()
        load_cfg.assert_not_called()
        client_cls.from_config.assert_not_called()
        self.assertNotIn("sid-secret", __import__("json").dumps(result))


class SessionCookieRpcTests(SimpleTestCase):
    @patch("dose.services.odoo_rpc.requests.post")
    def test_session_calls_send_cookie_not_password(self, post):
        from dose.services.odoo_rpc import OdooRpcClient

        response = MagicMock()
        response.status_code = 200
        response.json.side_effect = [
            {"result": {"uid": 7}},
            {"result": [{"id": 9, "narration": "x"}]},
        ]
        post.return_value = response
        client = OdooRpcClient.for_session("http://odoo:8069", "sid-secret")
        self.assertEqual(client.authenticate(), 7)
        client.execute_kw("account.move", "read", [[9], ["narration"]])
        auth_call, read_call = post.call_args_list
        self.assertEqual(auth_call.kwargs["cookies"], {"session_id": "sid-secret"})
        self.assertNotIn("password", str(auth_call.kwargs["json"]))
        self.assertTrue(read_call.args[0].endswith("/web/dataset/call_kw"))
        self.assertEqual(read_call.kwargs["cookies"]["session_id"], "sid-secret")
        self.assertEqual(read_call.kwargs["json"]["params"]["model"], "account.move")

    def test_envelope_keeps_session_on_the_job_only(self):
        from dose.webhook_events import build_odoo_invoice_refine_envelope

        envelope = build_odoo_invoice_refine_envelope(
            SimpleNamespace(schema_name="polysaas"),
            {
                "move_ids": [13],
                "source_path": "/web/dataset/call_button",
                "odoo_session_id": "sid-secret",
                "odoo_url": "http://odoo:8069",
            },
        )
        self.assertEqual(envelope["payload"]["odoo_session_id"], "sid-secret")
        self.assertEqual(envelope["payload"]["move_ids"], [13])
        self.assertNotIn("sid-secret", envelope["event_id"])


class RefineFeedbackTests(SimpleTestCase):
    def test_feedback_refined(self):
        instr = SimpleNamespace(eventKey="odoo.invoice.refine", executescript="RefineOdooInvoiceDescription")
        text, level = feedback_text_for_result(
            instr,
            {
                "status": "success",
                "changed": True,
                "invoice_ref": "INV/2026/0001",
                "outcomes": [{"changed": True, "invoice_name": "INV/2026/0001"}],
            },
            "RefineOdooInvoiceDescription",
        )
        self.assertIn("refined", text.lower())
        self.assertEqual(level, "success")

    def test_feedback_no_change(self):
        instr = SimpleNamespace(eventKey="odoo.invoice.refine", executescript="RefineOdooInvoiceDescription")
        text, level = feedback_text_for_result(
            instr,
            {
                "status": "success",
                "changed": False,
                "invoice_ref": "INV/1",
                "outcomes": [{"changed": False, "reason": "no_change"}],
            },
            "RefineOdooInvoiceDescription",
        )
        self.assertIn("no change", text.lower())

    def test_feedback_queued(self):
        instr = SimpleNamespace(eventKey="odoo.invoice.action_post", executescript="RefineOdooInvoiceDescription")
        text, level = feedback_text_for_result(
            instr,
            {"status": "success", "queued": True, "move_ids": [42]},
            "RefineOdooInvoiceDescription",
        )
        self.assertIn("refining note", text.lower())
        self.assertEqual(level, "info")

    def test_feedback_session_failure_is_visible_on_the_bar(self):
        instr = SimpleNamespace(eventKey="odoo.invoice.refine", executescript="RefineOdooInvoiceDescription")
        text, level = feedback_text_for_result(
            instr,
            {
                "status": "error",
                "error": "auth_failed",
                "detail": "Odoo authentication failed",
                "move_ids": [13],
                "fail_soft": True,
            },
            "RefineOdooInvoiceDescription",
        )
        self.assertIn("refine skipped", text.lower())
        self.assertEqual(level, "warning")

    def test_feedback_ai_unavailable(self):
        instr = SimpleNamespace(eventKey="odoo.invoice.refine", executescript="RefineOdooInvoiceDescription")
        text, level = feedback_text_for_result(
            instr,
            {
                "status": "success",
                "changed": False,
                "invoice_ref": "INV/1",
                "outcomes": [{"changed": False, "reason": "ai_failed_soft"}],
            },
            "RefineOdooInvoiceDescription",
        )
        self.assertIn("unavailable", text.lower())
        self.assertEqual(level, "warning")
