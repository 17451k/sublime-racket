from __future__ import annotations

from unittest.mock import patch

import sublime
import unittesting

from ..plugin.lang import (  # ty: ignore[unresolved-import]
    RacketLangListener,
    apply_lang_syntax,
)
from .base import ViewMixin


class TestLangSyntax(ViewMixin, unittesting.TestCase):
    def _make(self, syntax: str, first_line: str) -> sublime.View:
        view = self.scratch_view(syntax)
        view.run_command("append", {"characters": first_line + "\n1\n"})
        return view

    def _scope(self, view: sublime.View) -> str | None:
        syntax = view.syntax()
        return None if syntax is None else syntax.scope

    def test_racket_to_rhombus(self):
        view = self._make("scope:source.racket", "#lang rhombus")
        apply_lang_syntax(view)
        self.assertEqual(self._scope(view), "source.rhombus")

    def test_rhombus_static(self):
        view = self._make("scope:source.racket", "#lang rhombus/static")
        apply_lang_syntax(view)
        self.assertEqual(self._scope(view), "source.rhombus")

    def test_racket_unchanged(self):
        view = self._make("scope:source.racket", "#lang racket")
        apply_lang_syntax(view)
        self.assertEqual(self._scope(view), "source.racket")

    def test_rhombus_back_to_racket(self):
        view = self._make("scope:source.rhombus", "#lang racket")
        with patch.object(view, "file_name", return_value="a.rkt"):
            apply_lang_syntax(view)
        self.assertEqual(self._scope(view), "source.racket")

    def test_rhm_unchanged(self):
        view = self._make("scope:source.rhombus", "#lang racket")
        with patch.object(view, "file_name", return_value="a.rhm"):
            apply_lang_syntax(view)
        self.assertEqual(self._scope(view), "source.rhombus")

    def test_unnamed_unchanged(self):
        # Only Racket files switch back; an unsaved buffer keeps the chosen syntax
        view = self._make("scope:source.rhombus", "#lang racket")
        apply_lang_syntax(view)
        self.assertEqual(self._scope(view), "source.rhombus")

    def test_on_load(self):
        view = self._make("scope:source.racket", "#lang rhombus")
        RacketLangListener().on_load(view)
        self.assertEqual(self._scope(view), "source.rhombus")

    def test_on_init(self):
        view = self._make("scope:source.racket", "#lang rhombus")
        RacketLangListener().on_init([view])
        self.assertEqual(self._scope(view), "source.rhombus")
