from __future__ import annotations

import unittesting

from ..plugin.utils import racket  # ty: ignore[unresolved-import]
from .base import ViewMixin


class RacketTestCase(ViewMixin, unittesting.TestCase):
    def setUp(self) -> None:
        super().setUp()
        self.plain = self.scratch_view("scope:text.plain")


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

    def test_null_setting(self) -> None:
        self.view.settings().set("racket_executable", None)
        self.assertEqual(racket.executable(self.view), "racket")
