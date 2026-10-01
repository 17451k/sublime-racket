from __future__ import annotations

import os
import shutil
import tempfile
from unittest.mock import Mock, patch

import sublime
import unittesting

from ..plugin import repl  # ty: ignore[unresolved-import]

TAG = "racket-repl"
TITLE = "Racket REPL"


class ReplTestCase(unittesting.DeferrableTestCase):
    def setUp(self) -> None:
        self.window = sublime.active_window()
        self.previous = self.window.active_view()
        self.view = self.window.new_file()
        self.view.set_scratch(True)
        self.view.assign_syntax("scope:source.racket")

        self.open_terminal = self.mock(repl.terminus, "open_terminal")
        self.open_terminal.return_value = True
        self.send_to_terminal = self.mock(repl.terminus, "send_to_terminal")
        self.find_terminal = self.mock(repl.terminus, "find_terminal")
        self.find_terminal.return_value = None
        self.send_when_ready = self.mock(repl.terminus, "send_when_ready")
        self.error_message = self.mock(repl.sublime, "error_message")
        self.status_message = self.mock(repl.sublime, "status_message")

    def tearDown(self) -> None:
        self.view.close()
        if self.previous and self.previous.is_valid():
            self.window.focus_view(self.previous)

    def mock(self, target: object, attr: str) -> Mock:
        patcher = patch.object(target, attr)
        self.addCleanup(patcher.stop)
        return patcher.start()

    def plain_view(self) -> sublime.View:
        view = self.window.new_file()
        view.set_scratch(True)
        view.assign_syntax("scope:text.plain")
        self.addCleanup(view.close)
        return view

    def set_text(self, marked: str) -> None:
        cursor = max(marked.find("|"), 0)
        self.view.run_command("append", {"characters": marked.replace("|", "", 1)})
        self.select((cursor, cursor))

    def select(self, *regions: tuple[int, int]) -> None:
        self.view.sel().clear()
        for a, b in regions:
            self.view.sel().add(sublime.Region(a, b))

    def run_command(self, cls: type) -> None:
        self.window.focus_view(self.view)
        self.assertEqual(self.window.active_view(), self.view)
        cls(self.window).run()

    def live_repl(self) -> None:
        self.find_terminal.return_value = Mock()

    def assert_sent(self, text: str) -> None:
        self.send_to_terminal.assert_called_once_with(self.window, text, TAG)
        self.open_terminal.assert_not_called()

    def assert_nothing_sent(self) -> None:
        self.send_to_terminal.assert_not_called()
        self.open_terminal.assert_not_called()
        self.status_message.assert_called_once()


class TestHelpers(ReplTestCase):
    def test_is_racket(self) -> None:
        self.assertTrue(repl._is_racket(self.view))
        self.assertFalse(repl._is_racket(None))
        self.assertFalse(repl._is_racket(self.plain_view()))

    def test_racket(self) -> None:
        self.assertEqual(repl._racket(self.view), "racket")
        self.assertEqual(repl._racket(self.plain_view()), "racket")
        self.assertEqual(repl._racket(None), "racket")

    def test_racket_setting(self) -> None:
        self.view.settings().set("racket_executable", "/opt/racket/bin/racket")
        self.assertEqual(repl._racket(self.view), "/opt/racket/bin/racket")


class TestIsEnabled(ReplTestCase):
    COMMANDS = (
        repl.RacketRunInReplCommand,
        repl.RacketSendSelectionToReplCommand,
        repl.RacketSendDefinitionToReplCommand,
        repl.RacketSendSexpToReplCommand,
    )

    def test_racket_view(self) -> None:
        self.window.focus_view(self.view)
        for cls in self.COMMANDS:
            self.assertTrue(cls(self.window).is_enabled(), cls.__name__)

    def test_plain_view(self) -> None:
        view = self.plain_view()
        self.window.focus_view(view)
        for cls in self.COMMANDS:
            self.assertFalse(cls(self.window).is_enabled(), cls.__name__)


class TestOpenRepl(ReplTestCase):
    def test_opens(self) -> None:
        self.run_command(repl.RacketOpenReplCommand)
        self.open_terminal.assert_called_once_with(
            self.window, ["racket", "-i"], None, tag=TAG, title=TITLE, focus=True
        )

    def test_custom_executable(self) -> None:
        self.view.settings().set("racket_executable", "/opt/racket/bin/racket")
        self.run_command(repl.RacketOpenReplCommand)
        self.open_terminal.assert_called_once_with(
            self.window,
            ["/opt/racket/bin/racket", "-i"],
            None,
            tag=TAG,
            title=TITLE,
            focus=True,
        )


class TestSendToRepl(ReplTestCase):
    def test_live(self) -> None:
        self.live_repl()
        repl._send_to_repl(self.window, self.view, "  (a)\n\n")
        self.assert_sent("(a)\n")

    def test_whitespace(self) -> None:
        repl._send_to_repl(self.window, self.view, " \n\t")
        self.send_when_ready.assert_not_called()
        self.assert_nothing_sent()

    def test_starts_repl(self) -> None:
        repl._send_to_repl(self.window, self.view, "(a)")
        self.open_terminal.assert_called_once_with(
            self.window, ["racket", "-i"], None, tag=TAG, title=TITLE, focus=False
        )
        self.send_when_ready.assert_called_once_with(self.window, "(a)\n", TAG)
        self.send_to_terminal.assert_not_called()

    def test_start_fails(self) -> None:
        self.open_terminal.return_value = False
        repl._send_to_repl(self.window, self.view, "(a)")
        self.send_when_ready.assert_not_called()


class TestSendSelection(ReplTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.live_repl()
        self.set_text("(define a 1)\n(define b 2)\n")

    def test_selection(self) -> None:
        self.select((13, 25))
        self.run_command(repl.RacketSendSelectionToReplCommand)
        self.assert_sent("(define b 2)\n")

    def test_line(self) -> None:
        self.select((3, 3))
        self.run_command(repl.RacketSendSelectionToReplCommand)
        self.assert_sent("(define a 1)\n")

    def test_multiple(self) -> None:
        self.select((0, 0), (13, 13))
        self.run_command(repl.RacketSendSelectionToReplCommand)
        self.assert_nothing_sent()


class TestSendDefinition(ReplTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.live_repl()

    def test_definition(self) -> None:
        self.set_text("(define (f x)\n  (+ x| 1))")
        self.run_command(repl.RacketSendDefinitionToReplCommand)
        self.assert_sent("(define (f x)\n  (+ x 1))\n")

    def test_no_form(self) -> None:
        self.set_text("(a)\n|\n(b)")
        self.run_command(repl.RacketSendDefinitionToReplCommand)
        self.assert_nothing_sent()

    def test_multiple(self) -> None:
        self.set_text("(a)\n(b)")
        self.select((1, 1), (5, 5))
        self.run_command(repl.RacketSendDefinitionToReplCommand)
        self.assert_nothing_sent()


class TestSendSexp(ReplTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.live_repl()

    def test_sexp(self) -> None:
        self.set_text("(a (b |c) d)")
        self.run_command(repl.RacketSendSexpToReplCommand)
        self.assert_sent("(b c)\n")

    def test_no_sexp(self) -> None:
        self.set_text("(a) | (b)")
        self.run_command(repl.RacketSendSexpToReplCommand)
        self.assert_nothing_sent()

    def test_multiple(self) -> None:
        self.set_text("(a)\n(b)")
        self.select((1, 1), (5, 5))
        self.run_command(repl.RacketSendSexpToReplCommand)
        self.assert_nothing_sent()


class TestRunInRepl(ReplTestCase):
    def open_module(self):
        directory = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, directory, True)
        path = os.path.join(directory, "mod.rkt")
        with open(path, "w") as f:
            f.write("#lang racket\n")

        view = self.window.open_file(path)

        def close() -> None:
            view.set_scratch(True)
            view.close()

        self.addCleanup(close)
        yield lambda: not view.is_loading()
        return view

    def run_in_repl(self, view: sublime.View) -> None:
        self.window.focus_view(view)
        self.assertEqual(self.window.active_view(), view)
        repl.RacketRunInReplCommand(self.window).run()

    def assert_opened(self, view: sublime.View) -> None:
        path = view.file_name()
        self.open_terminal.assert_called_once_with(
            self.window,
            ["racket", "-i", "-e", f'(enter! (file "{path}"))'],
            os.path.dirname(path),
            tag=TAG,
            title=TITLE,
            focus=False,
        )

    def test_unsaved(self) -> None:
        self.run_command(repl.RacketRunInReplCommand)
        self.error_message.assert_called_once()
        self.open_terminal.assert_not_called()

    def test_saved(self):
        view = yield from self.open_module()
        self.run_in_repl(view)
        self.assert_opened(view)

    def test_dirty(self):
        view = yield from self.open_module()
        view.run_command("append", {"characters": "(define a 1)\n"})
        self.assertTrue(view.is_dirty())
        self.run_in_repl(view)
        self.assertFalse(view.is_dirty())
        with open(view.file_name()) as f:
            self.assertIn("(define a 1)\n", f.read())
        self.open_terminal.assert_called_once()
