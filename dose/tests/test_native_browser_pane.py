"""The workspace pane renders the captured browser and drives it back."""
import threading
import types
from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase

from dose.polysniffer.native_browser_capture import (
    _FrameBuffer,
    _NativeBrowserRun,
    _RUNS,
    _RUNS_LOCK,
    _ScreencastPump,
    _dispatch_input,
    _safe_post_data,
    next_native_frame,
    queue_native_input,
)


class SafePostDataTests(SimpleTestCase):
    def test_text_bodies_are_kept(self):
        request = MagicMock()
        request.post_data = "hello=world"

        self.assertEqual(_safe_post_data(request), "hello=world")

    def test_binary_bodies_do_not_raise(self):
        request = MagicMock()
        type(request).post_data = property(
            lambda self: (_ for _ in ()).throw(
                UnicodeDecodeError("utf-8", b"\x8b", 1, 2, "invalid")
            )
        )
        request.post_data_buffer = b"\x1f\x8bcompressed"

        self.assertEqual(_safe_post_data(request), "<binary 14 bytes>")


class FrameBufferTests(SimpleTestCase):
    def test_latest_frame_is_available_immediately(self):
        buffer = _FrameBuffer()
        buffer.publish(b"first")

        self.assertEqual(buffer.latest(), (1, b"first"))

    def test_publishing_replaces_rather_than_queues(self):
        buffer = _FrameBuffer()
        buffer.publish(b"stale")
        buffer.publish(b"fresh")

        seq, data = buffer.latest()
        self.assertEqual(data, b"fresh")
        self.assertEqual(seq, 2)

    def test_reader_waits_until_a_newer_frame_arrives(self):
        buffer = _FrameBuffer()
        buffer.publish(b"seen")
        seen_seq = buffer.latest()[0]
        result = {}

        def read():
            result["frame"] = buffer.wait_for_frame_after(seen_seq, 2.0)

        reader = threading.Thread(target=read)
        reader.start()
        buffer.publish(b"next")
        reader.join(timeout=3)

        self.assertEqual(result["frame"][1], b"next")

    def test_reader_gives_up_when_nothing_is_rendered(self):
        buffer = _FrameBuffer()

        seq, data = buffer.wait_for_frame_after(0, 0.05)

        self.assertEqual((seq, data), (0, b""))


class NativeRunRegistryTests(SimpleTestCase):
    def setUp(self):
        self.key = ("olient", "app.slack.com")
        self.run = _NativeBrowserRun()
        with _RUNS_LOCK:
            _RUNS[self.key] = self.run
        self.addCleanup(self._forget)

    def _forget(self):
        with _RUNS_LOCK:
            _RUNS.pop(self.key, None)

    def test_input_is_queued_for_the_browser_thread(self):
        queued = queue_native_input(
            tenant_schema="olient",
            endpoint_host="app.slack.com",
            event={"kind": "text", "text": "hello"},
        )

        self.assertTrue(queued)
        self.assertEqual(self.run.inputs.get_nowait()["text"], "hello")

    def test_input_for_an_unknown_endpoint_is_rejected(self):
        queued = queue_native_input(
            tenant_schema="olient",
            endpoint_host="not.running.example",
            event={"kind": "text", "text": "hello"},
        )

        self.assertFalse(queued)

    def test_first_read_returns_the_current_frame(self):
        self.run.frames.publish(b"jpeg")

        seq, data = next_native_frame(
            tenant_schema="olient", endpoint_host="app.slack.com", after_seq=0
        )

        self.assertEqual(data, b"jpeg")
        self.assertEqual(seq, 1)


class InputDispatchTests(SimpleTestCase):
    def test_click_becomes_a_mouse_event(self):
        session = MagicMock()

        _dispatch_input(
            session,
            {"kind": "mouse", "action": "down", "x": 12, "y": 34, "button": 0},
        )

        name, payload = session.send.call_args[0]
        self.assertEqual(name, "Input.dispatchMouseEvent")
        self.assertEqual(payload["type"], "mousePressed")
        self.assertEqual((payload["x"], payload["y"]), (12.0, 34.0))
        self.assertEqual(payload["button"], "left")

    def test_typing_is_inserted_as_text(self):
        session = MagicMock()

        _dispatch_input(session, {"kind": "text", "text": "hi"})

        session.send.assert_called_once_with("Input.insertText", {"text": "hi"})

    def test_enter_is_sent_as_a_key_press_and_release(self):
        session = MagicMock()

        _dispatch_input(session, {"kind": "key", "key": "Enter"})

        types = [call[0][1]["type"] for call in session.send.call_args_list]
        self.assertEqual(types, ["keyDown", "keyUp"])

    def test_unknown_keys_are_ignored(self):
        session = MagicMock()

        _dispatch_input(session, {"kind": "key", "key": "F13"})

        session.send.assert_not_called()

    def test_scrolling_becomes_a_wheel_event(self):
        session = MagicMock()

        _dispatch_input(session, {"kind": "wheel", "x": 5, "y": 6, "delta_y": 120})

        name, payload = session.send.call_args[0]
        self.assertEqual(name, "Input.dispatchMouseEvent")
        self.assertEqual(payload["type"], "mouseWheel")
        self.assertEqual(payload["deltaY"], 120.0)


class ScreencastPumpTests(SimpleTestCase):
    def test_frames_are_published_and_acknowledged_from_the_worker(self):
        run = _NativeBrowserRun()
        context = MagicMock()
        session = context.new_cdp_session.return_value
        pump = _ScreencastPump(context, run)
        pump.attach(MagicMock())

        session.on.assert_called_once()
        self.assertEqual(session.send.call_args[0][0], "Page.startScreencast")
        # Playwright sets an attribute on the handler it is given, which a
        # builtin method cannot carry, so the handler must be a real function.
        handler = session.on.call_args[0][1]
        self.assertIsInstance(handler, types.FunctionType)

        session.send.reset_mock()
        pump._pending.append({"data": "aGk=", "sessionId": 7})
        pump.pump()

        self.assertEqual(run.frames.latest()[1], b"hi")
        session.send.assert_called_once_with(
            "Page.screencastFrameAck", {"sessionId": 7}
        )

    def test_reattaching_the_same_page_does_not_restart_the_screencast(self):
        run = _NativeBrowserRun()
        context = MagicMock()
        page = MagicMock()
        pump = _ScreencastPump(context, run)

        pump.attach(page)
        pump.attach(page)

        context.new_cdp_session.assert_called_once_with(page)

    def test_a_corrupt_frame_is_skipped_without_killing_the_stream(self):
        run = _NativeBrowserRun()
        context = MagicMock()
        pump = _ScreencastPump(context, run)
        pump.attach(MagicMock())

        pump._pending.append({"data": "not base64 !!", "sessionId": 1})
        pump._pending.append({"data": "aGk=", "sessionId": 2})
        pump.pump()

        self.assertEqual(run.frames.latest()[1], b"hi")


class NativeViewTests(SimpleTestCase):
    @patch("dose.polysniffer.native_view.queue_native_input")
    @patch("dose.polysniffer.native_view.bind_request_tenant")
    def test_input_view_rejects_a_body_that_is_not_an_event(
        self, bind_tenant, queue_input
    ):
        from types import SimpleNamespace

        from django.test import RequestFactory

        from dose.polysniffer.native_view import native_input

        bind_tenant.return_value = SimpleNamespace(schema_name="olient")
        request = RequestFactory().post(
            "/admin/polysniffer/sniff/app.slack.com/native/input/",
            data="[]",
            content_type="application/json",
        )
        request.user = SimpleNamespace(
            is_active=True, is_staff=True, is_authenticated=True
        )

        response = native_input(request, "app.slack.com")

        self.assertEqual(response.status_code, 400)
        queue_input.assert_not_called()

    @patch("dose.polysniffer.native_view.queue_native_input")
    @patch("dose.polysniffer.native_view.bind_request_tenant")
    def test_input_view_reports_when_no_browser_is_running(
        self, bind_tenant, queue_input
    ):
        from types import SimpleNamespace

        from django.test import RequestFactory

        from dose.polysniffer.native_view import native_input

        bind_tenant.return_value = SimpleNamespace(schema_name="olient")
        queue_input.return_value = False
        request = RequestFactory().post(
            "/admin/polysniffer/sniff/app.slack.com/native/input/",
            data='{"kind": "text", "text": "x"}',
            content_type="application/json",
        )
        request.user = SimpleNamespace(
            is_active=True, is_staff=True, is_authenticated=True
        )

        response = native_input(request, "app.slack.com")

        self.assertEqual(response.status_code, 409)
