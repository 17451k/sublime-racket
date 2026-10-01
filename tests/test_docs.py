from __future__ import annotations

from unittest.mock import Mock, patch

import sublime
import unittesting

from ..plugin import docs  # ty: ignore[unresolved-import]


class DocsTestCase(unittesting.TestCase):
    def setUp(self) -> None:
        self.window = sublime.active_window()
        self.previous = self.window.active_view()
        self.view = self.window.new_file()
        self.view.set_scratch(True)
        self.view.assign_syntax("scope:source.racket")

        self.popen = self.mock(docs.subprocess, "Popen")
        self.status_message = self.mock(docs.sublime, "status_message")
        self.error_message = self.mock(docs.sublime, "error_message")

    def tearDown(self) -> None:
        self.view.close()
        if self.previous and self.previous.is_valid():
            self.window.focus_view(self.previous)

    def mock(self, target: object, attr: str) -> Mock:
        patcher = patch.object(target, attr)
        self.addCleanup(patcher.stop)
        return patcher.start()

    def set_text(self, marked: str) -> None:
        cursor = max(marked.find("|"), 0)
        self.view.run_command("append", {"characters": marked.replace("|", "", 1)})
        self.select((cursor, cursor))

    def select(self, *regions: tuple[int, int]) -> None:
        self.view.sel().clear()
        for a, b in regions:
            self.view.sel().add(sublime.Region(a, b))

    def run_command(self) -> None:
        self.window.focus_view(self.view)
        self.assertEqual(self.window.active_view(), self.view)
        docs.RacketLookUpDocsCommand(self.window).run()

    def assert_looked_up(self, term: str) -> None:
        self.popen.assert_called_once()
        self.assertEqual(
            self.popen.call_args[0][0], ["racket", "-l-", "raco", "docs", "--", term]
        )
        self.error_message.assert_not_called()

    def assert_nothing_looked_up(self) -> None:
        self.popen.assert_not_called()
        self.status_message.assert_called_once()


class TestLookUp(DocsTestCase):
    def test_identifier(self) -> None:
        self.set_text("(string->li|st x)")
        self.run_command()
        self.assert_looked_up("string->list")

    def test_after_identifier(self) -> None:
        self.set_text("(map| f xs)")
        self.run_command()
        self.assert_looked_up("map")

    def test_switch_like(self) -> None:
        self.set_text("(f -|> x)")
        self.run_command()
        self.assert_looked_up("->")

    def test_selection(self) -> None:
        self.set_text("(for/list ([x xs]) x)")
        self.select((1, 9))
        self.run_command()
        self.assert_looked_up("for/list")

    def test_no_identifier(self) -> None:
        self.set_text("(a)  |  (b)")
        self.run_command()
        self.assert_nothing_looked_up()

    def test_multiple(self) -> None:
        self.set_text("(a b)")
        self.select((1, 1), (3, 3))
        self.run_command()
        self.assert_nothing_looked_up()

    def test_custom_executable(self) -> None:
        self.view.settings().set("racket_executable", "/opt/racket/bin/racket")
        self.set_text("(ma|p f xs)")
        self.run_command()
        self.assertEqual(self.popen.call_args[0][0][0], "/opt/racket/bin/racket")

    def test_os_error(self) -> None:
        self.popen.side_effect = OSError
        self.set_text("(ma|p f xs)")
        self.run_command()
        self.error_message.assert_called_once()


class TestIsEnabled(DocsTestCase):
    def test_racket_view(self) -> None:
        self.window.focus_view(self.view)
        self.assertTrue(docs.RacketLookUpDocsCommand(self.window).is_enabled())

    def test_plain_view(self) -> None:
        view = self.window.new_file()
        view.set_scratch(True)
        view.assign_syntax("scope:text.plain")
        self.addCleanup(view.close)
        self.window.focus_view(view)
        self.assertFalse(docs.RacketLookUpDocsCommand(self.window).is_enabled())
