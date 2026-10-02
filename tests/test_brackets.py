from __future__ import annotations

import sublime
from unittesting import ViewTestCase

from ..plugin.utils import sexp  # ty: ignore[unresolved-import]


class BracketTestCase(ViewTestCase):
    auto_match = True

    def setUp(self):
        self.view.assign_syntax("scope:source.racket")
        self.view.settings().set("auto_match_enabled", self.auto_match)

    def _set(self, marked: str) -> list[int]:
        """Set the text and put a caret at each | marker."""
        points = []
        text = ""
        for part in marked.split("|")[:-1]:
            text += part
            points.append(len(text))
        text += marked.split("|")[-1]
        # append does not auto-indent or auto-pair
        self.view.run_command("append", {"characters": text})
        self.view.sel().clear()
        self.view.sel().add_all([sublime.Region(p) for p in points])
        return points

    def _text(self) -> str:
        return self.view.substr(sublime.Region(0, self.view.size()))

    def _carets(self) -> list[int]:
        return [r.b for r in self.view.sel()]

    def _open(self):
        self.view.run_command("racket_smart_open_bracket")

    def _close(self, char: str):
        self.view.run_command("racket_smart_close_bracket", {"char": char})


class TestSmartOpen(BracketTestCase):
    def _smart(self, marked: str) -> str:
        (pt,) = self._set(marked)
        return sexp.smart_open(self.view, pt)

    def test_examples(self):
        cases = [
            ("(let (|", "["),
            ("(match-let (|", "["),
            ("(delete (|", "("),
            ("(let loop (|", "["),
            ("(let ([x 1] |", "["),
            ("(let ([x |", "("),
            ("(let ([x 1]) |", "("),
            ("(cond |", "["),
            ("(cond [(a) |", "("),
            ("(case |", "("),
            ("(case x |", "["),
            ("(match (f x) |", "["),
            ("(syntax-case stx |", "("),
            ("(syntax-case stx () |", "["),
            ("(for (|", "["),
            ("(for/fold ([a 0]) |", "("),
            ("(for/fold ([a 0]) (|", "["),
            ("(define (f x) |", "("),
            ("(with-handlers (|", "["),
            ("(init |", "["),
            ("|", "("),
            ("(f (a) |", "("),
            ("(for-each (|", "("),
            ("(for/lists (a b) (|", "["),
            ("(for/vector #:length n (|", "["),
            ("(let/cc k (|", "("),
            ("(let ; note\n (|", "["),
            ("(syntax-case stx ; a b\n |", "("),
            ('(syntax-case "a b" |', "("),
        ]
        for marked, expected in cases:
            with self.subTest(marked=marked):
                self.view.run_command("select_all")
                self.view.run_command("right_delete")
                self.assertEqual(self._smart(marked), expected)


class TestEnclosingOpen(BracketTestCase):
    def _enclosing(self, marked: str) -> int | None:
        (pt,) = self._set(marked)
        return sexp.enclosing_open(self.view, pt)

    def test_balanced(self):
        self.assertEqual(self._enclosing("(a (b) |c)"), 0)

    def test_unbalanced(self):
        self.assertEqual(self._enclosing("(a [b (c) |"), 3)

    def test_top_level(self):
        self.assertIsNone(self._enclosing("(a) |"))

    def test_string(self):
        self.assertEqual(self._enclosing('(a "(" |'), 0)


class TestIndentPoint(BracketTestCase):
    def _smart(self, marked: str) -> str:
        (pt,) = self._set(marked)
        return sexp.smart_open(self.view, sexp.indent_point(self.view, pt))

    def test_examples(self):
        let = "(define (dist2 p q)\n  (let ([d (vcvd a d)])))\n"
        cases = [
            (let + "        |", "["),
            (let + "    |", "("),
            (let + "  |", "("),
            (let + "|", "("),
            ("(cond [(a) 1])\n      |", "["),
            ("(cond [(a) 1]) ; note\n      |", "["),
            ("(cond [(a) 1])\n\n      |", "["),
            ("(let ([a 1]\n      |", "["),
            ("(cond [(a) 1])\n  x |", "("),
        ]
        for marked, expected in cases:
            with self.subTest(marked=marked):
                self.view.run_command("select_all")
                self.view.run_command("right_delete")
                self.assertEqual(self._smart(marked), expected)


class TestOpenCommand(BracketTestCase):
    def test_pair(self):
        self._set("(cond |")
        self._open()
        self.assertEqual(self._text(), "(cond []")
        self.assertEqual(self._carets(), [7])

    def test_wrap(self):
        self._set("(cond x)")
        self.view.sel().clear()
        self.view.sel().add(sublime.Region(6, 7))
        self._open()
        self.assertEqual(self._text(), "(cond [x])")

    def test_char_literal(self):
        self._set("(cond #\\|")
        self._open()
        self.assertEqual(self._text(), "(cond #\\[")

    def test_after_close(self):
        self._set("(f (a)|")
        self._open()
        self.assertEqual(self._text(), "(f (a)()")

    def test_at_expression(self):
        self._set("@foo|")
        self._open()
        self.assertEqual(self._text(), "@foo[]")

    def test_unquote_splicing(self):
        self._set("`(a ,@|")
        self._open()
        self.assertEqual(self._text(), "`(a ,@()")

    def test_two_carets(self):
        self._set("(cond |)\n(f |)")
        self._open()
        self.assertEqual(self._text(), "(cond [])\n(f ())")
        self.assertEqual(self._carets(), [7, 14])

    def test_indent_context(self):
        self._set("(define (dist2 p q)\n  (let ([d (vcvd a d)])))\n        |")
        self._open()
        self.assertTrue(self._text().endswith("\n        []"))
        self.assertEqual(self._carets(), [len(self._text()) - 1])


class TestOpenNoAutoMatch(BracketTestCase):
    auto_match = False

    def test_no_pair(self):
        self._set("(cond |")
        self._open()
        self.assertEqual(self._text(), "(cond [")

    def test_char_literal(self):
        self._set("(f #\\|")
        self._open()
        self.assertEqual(self._text(), "(f #\\[")


class TestCloseCommand(BracketTestCase):
    auto_match = False

    def test_matching(self):
        self._set("(let ([x 1|")
        self._close(")")
        self.assertEqual(self._text(), "(let ([x 1]")
        self._close(")")
        self.assertEqual(self._text(), "(let ([x 1])")

    def test_top_level(self):
        self._set("(a) |")
        self._close(")")
        self.assertEqual(self._text(), "(a) )")

    def test_char_literal(self):
        self._set("[f #\\|")
        self._close(")")
        self.assertEqual(self._text(), "[f #\\)")


class TestCloseAutoMatch(BracketTestCase):
    def test_type_over(self):
        self._set("[a|]")
        self._close(")")
        self.assertEqual(self._text(), "[a]")
        self.assertEqual(self._carets(), [3])

    def test_char_literal(self):
        self._set("(f #\\|)")
        self._close(")")
        self.assertEqual(self._text(), "(f #\\))")
