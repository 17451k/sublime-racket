from __future__ import annotations

from typing import TYPE_CHECKING
from unittest import TestCase
from unittest.mock import Mock, patch

import sublime

# Type as a TestCase without making the mixin a collected test case
_Base = TestCase if TYPE_CHECKING else object


class ViewMixin(_Base):
    """Open a scratch Racket view for each test and restore focus afterwards."""

    def setUp(self) -> None:
        super().setUp()
        self.window = sublime.active_window()
        self.previous = self.window.active_view()
        self.view = self.scratch_view("scope:source.racket", cleanup=False)

    def tearDown(self) -> None:
        self.view.close()
        if self.previous and self.previous.is_valid():
            self.window.focus_view(self.previous)
        super().tearDown()

    def mock(self, target: object, attr: str) -> Mock:
        patcher = patch.object(target, attr)
        self.addCleanup(patcher.stop)
        return patcher.start()

    def scratch_view(self, syntax: str, cleanup: bool = True) -> sublime.View:
        view = self.window.new_file()
        view.set_scratch(True)
        view.assign_syntax(syntax)
        if cleanup:
            self.addCleanup(view.close)
        return view
