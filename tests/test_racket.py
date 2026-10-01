from __future__ import annotations

import sublime
import unittesting

from ..plugin.utils import racket  # ty: ignore[unresolved-import]


class RacketTestCase(unittesting.TestCase):
    def setUp(self) -> None:
        self.window = sublime.active_window()
        self.view = self.scratch_view("scope:source.racket")
        self.plain = self.scratch_view("scope:text.plain")

    def scratch_view(self, syntax: str) -> sublime.View:
        view = self.window.new_file()
        view.set_scratch(True)
        view.assign_syntax(syntax)
        self.addCleanup(view.close)
        return view


class TestIsRacket(RacketTestCase):
    def test_is_racket(self) -> None:
        self.assertTrue(racket.is_racket(self.view))
        self.assertFalse(racket.is_racket(None))
        self.assertFalse(racket.is_racket(self.plain))


class TestExecutable(RacketTestCase):
    def test_default(self) -> None:
        self.assertEqual(racket.executable(self.view), "racket")
        self.assertEqual(racket.executable(self.plain), "racket")
        self.assertEqual(racket.executable(None), "racket")

    def test_setting(self) -> None:
        self.view.settings().set("racket_executable", "/opt/racket/bin/racket")
        self.assertEqual(racket.executable(self.view), "/opt/racket/bin/racket")
