from __future__ import annotations

from unittest.mock import Mock, patch

import unittesting

from ..plugin.utils import terminus  # ty: ignore[unresolved-import]

TERMINUS = [type("TerminusOpenCommand", (), {})]


def _view(settings: dict) -> Mock:
    view = Mock()
    view.settings.return_value = settings
    return view


class TerminusTestCase(unittesting.TestCase):
    def setUp(self) -> None:
        self.window = Mock()
        patcher = patch.object(terminus.sublime, "error_message")
        self.error_message = patcher.start()
        self.addCleanup(patcher.stop)

    def with_terminus(self, available: bool):
        return patch.object(
            terminus.sublime_plugin,
            "window_command_classes",
            TERMINUS if available else [],
        )


class TestAvailable(TerminusTestCase):
    def test_installed(self) -> None:
        with self.with_terminus(True):
            self.assertTrue(terminus._available())
        self.error_message.assert_not_called()

    def test_missing(self) -> None:
        with self.with_terminus(False):
            self.assertFalse(terminus._available())
        self.error_message.assert_called_once()


class TestOpenTerminal(TerminusTestCase):
    def open(self) -> bool:
        return terminus.open_terminal(
            self.window, ["racket", "-i"], "/tmp", tag="t", title="T", focus=True
        )

    def test_opens(self) -> None:
        with self.with_terminus(True):
            self.assertTrue(self.open())
        self.window.run_command.assert_called_once_with(
            "terminus_open",
            {
                "cmd": ["racket", "-i"],
                "cwd": "/tmp",
                "tag": "t",
                "title": "T",
                "auto_close": False,
                "focus": True,
            },
        )

    def test_missing(self) -> None:
        with self.with_terminus(False):
            self.assertFalse(self.open())
        self.window.run_command.assert_not_called()


class TestSendToTerminal(TerminusTestCase):
    def test_sends(self) -> None:
        with self.with_terminus(True):
            terminus.send_to_terminal(self.window, "x\n", "t")
        self.window.run_command.assert_called_once_with(
            "terminus_send_string", {"tag": "t", "string": "x\n"}
        )

    def test_missing(self) -> None:
        with self.with_terminus(False):
            terminus.send_to_terminal(self.window, "x\n", "t")
        self.window.run_command.assert_not_called()


class TestFindTerminal(TerminusTestCase):
    def find(self, *views: Mock):
        self.window.views.return_value = list(views)
        return terminus.find_terminal(self.window, "t")

    def test_no_views(self) -> None:
        self.assertIsNone(self.find())

    def test_live(self) -> None:
        view = _view({"terminus_view.tag": "t"})
        self.assertIs(self.find(view), view)

    def test_finished(self) -> None:
        view = _view({"terminus_view.tag": "t", "terminus_view.finished": True})
        self.assertIsNone(self.find(view))

    def test_other_tag(self) -> None:
        self.assertIsNone(self.find(_view({"terminus_view.tag": "other"})))

    def test_skips_finished(self) -> None:
        finished = _view({"terminus_view.tag": "t", "terminus_view.finished": True})
        live = _view({"terminus_view.tag": "t"})
        self.assertIs(self.find(finished, live), live)


class TestSendWhenReady(TerminusTestCase):
    def setUp(self) -> None:
        super().setUp()
        patcher = patch.object(terminus.sublime, "set_timeout")
        self.set_timeout = patcher.start()
        self.addCleanup(patcher.stop)

    def callback(self):
        self.set_timeout.assert_called_once()
        callback, delay = self.set_timeout.call_args[0]
        self.assertEqual(delay, 100)
        return callback

    def test_found(self) -> None:
        with patch.object(terminus, "find_terminal", return_value=Mock()):
            terminus.send_when_ready(self.window, "x\n", "t")
        callback = self.callback()
        with patch.object(terminus, "send_to_terminal") as send:
            callback()
        send.assert_called_once_with(self.window, "x\n", "t")

    def test_retries(self) -> None:
        with patch.object(terminus, "find_terminal", return_value=None):
            terminus.send_when_ready(self.window, "x\n", "t", 3)
        callback = self.callback()
        with patch.object(terminus, "send_when_ready") as retry:
            callback()
        retry.assert_called_once_with(self.window, "x\n", "t", 2)

    def test_gives_up(self) -> None:
        with patch.object(terminus, "find_terminal", return_value=None):
            terminus.send_when_ready(self.window, "x\n", "t", 0)
        self.set_timeout.assert_not_called()
        self.error_message.assert_called_once()
