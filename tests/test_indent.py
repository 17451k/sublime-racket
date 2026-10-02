from __future__ import annotations

import sublime
from unittesting import ViewTestCase

from ..plugin.indent import RacketIndentListener  # ty: ignore[unresolved-import]
from ..plugin.utils import indent  # ty: ignore[unresolved-import]


class IndentTestCase(ViewTestCase):
    def setUp(self):
        self.view.assign_syntax("scope:source.racket")
        self.view.settings().set("racket_indent", True)

    def _set(self, marked: str) -> list[int]:
        """Put marked into the view and return the points of its | markers."""
        points = []
        text = marked
        while "|" in text:
            pt = text.index("|")
            points.append(pt)
            text = text[:pt] + text[pt + 1 :]
        # append does not auto-indent or auto-pair
        self.view.run_command("append", {"characters": text})
        self.view.sel().clear()
        self.view.sel().add_all(points)
        return points

    def _text(self) -> str:
        return self.view.substr(sublime.Region(0, self.view.size()))

    def _carets(self) -> list[int]:
        return [r.begin() for r in self.view.sel()]


class TestEnclosingOpen(IndentTestCase):
    def _enclosing(self, marked: str) -> int | None:
        (pt,) = self._set(marked)
        return indent.Snapshot(self.view).enclosing_open(pt)

    def test_balanced(self):
        self.assertEqual(self._enclosing("(a (b) |c)"), 0)

    def test_unbalanced(self):
        self.assertEqual(self._enclosing("(a [b (c) |"), 3)

    def test_top_level(self):
        self.assertIsNone(self._enclosing("(a) |"))

    def test_string(self):
        self.assertEqual(self._enclosing('(a "(" |'), 0)

    def test_stray_closer(self):
        self.assertEqual(self._enclosing(") (a |"), 2)


class TestIndentColumn(IndentTestCase):
    def _column(self, text: str) -> int | None:
        """Return the column for a new line after text."""
        self.view.run_command("append", {"characters": text + "\n"})
        return indent.Snapshot(self.view).indent_column(self.view.size())

    def test_top_level(self):
        self.assertEqual(self._column("(a b)"), 0)

    def test_bracket(self):
        self.assertEqual(self._column("(let ([x 1]"), 6)

    def test_no_elements(self):
        self.assertEqual(self._column("  ("), 3)

    def test_body(self):
        self.assertEqual(self._column("(define (f x)"), 2)

    def test_distinguished_after_previous(self):
        self.assertEqual(self._column("(for/fold ([a 0])"), 10)

    def test_distinguished_alone(self):
        self.assertEqual(self._column("(define"), 4)

    def test_named_let(self):
        self.assertEqual(self._column("(let loop ([i 0])"), 2)
        self.assertEqual(self._column("(let loop"), 5)

    def test_plain_let(self):
        self.assertEqual(self._column("(let ([i 0])"), 2)

    def test_families(self):
        cases = {
            "define/public": 1,
            "match-define": 1,
            "define-struct": 2,
            "let*-values": 1,
            "splicing-letrec": 1,
            "letrec-syntaxes+values": 2,
            "for*/list": 1,
            "for/fold": 2,
            "syntax-parameterize": 1,
            "delay/sync": 0,
            # User-defined forms that follow the naming conventions
            "define-my-thing": 1,
            "for/my-collector": 1,
            # Not body forms
            "defined?": None,
            "letter": None,
            "for-each": None,
            "format": None,
            "if": None,
            None: None,
        }
        for head, n in cases.items():
            with self.subTest(head=head):
                self.assertEqual(indent.body_args(head), n)

    def test_user_defined_form(self):
        self.assertEqual(self._column("(define-my-thing (f x)"), 2)

    def test_application_same_row(self):
        self.assertEqual(self._column("(foo bar"), 5)

    def test_application_head_alone(self):
        self.assertEqual(self._column("(foo\n bar"), 1)

    def test_string_element(self):
        self.assertEqual(self._column('(f "a (b" c'), 3)

    def test_comment_ignored(self):
        self.assertEqual(self._column("(foo #| x |# bar"), 13)

    def test_line_comment_ignored(self):
        self.assertEqual(self._column("(foo ; x\n"), 1)

    def test_inside_string(self):
        self.assertIsNone(self._column('(f "abc'))

    def test_inside_block_comment(self):
        self.assertIsNone(self._column("(f #| abc"))

    def test_struct(self):
        self.assertEqual(self._column("(struct point"), 8)

    def test_struct_super(self):
        self.assertEqual(self._column("(struct point parent"), 8)

    def test_struct_fields(self):
        self.assertEqual(self._column("(struct point (x y)"), 2)

    def test_struct_super_fields(self):
        self.assertEqual(self._column("(struct point parent (x y)"), 2)

    def test_for_keyword(self):
        self.assertEqual(self._column("(for/vector #:length 10"), 12)

    def test_for_keyword_clauses(self):
        self.assertEqual(self._column("(for/vector #:length 10 ([i 1])"), 2)

    def test_for_lists(self):
        self.assertEqual(self._column("(for/lists (a b)"), 11)

    def test_tabs(self):
        self.view.settings().set("tab_size", 4)
        self.assertEqual(self._column("\t(foo bar"), 9)

    def test_form_start(self):
        self.view.run_command("append", {"characters": "(a\n b)\n(foo bar\n"})
        pt = self.view.size()
        local = indent.Snapshot(self.view, indent.form_start(self.view, pt), pt)
        whole = indent.Snapshot(self.view)
        self.assertEqual(local.indent_column(pt), whole.indent_column(pt))
        self.assertEqual(local.indent_column(pt), 5)


class TestNewline(IndentTestCase):
    def _newline(self, marked: str):
        self._set(marked)
        self.view.run_command("racket_newline")

    def test_body(self):
        self._newline("(define (f x)|")
        self.assertEqual(self._text(), "(define (f x)\n  ")
        self.assertEqual(self.view.rowcol(self._carets()[0]), (1, 2))

    def test_split(self):
        self._newline("(foo bar |baz)")
        self.assertEqual(self._text(), "(foo bar\n     baz)")
        self.assertEqual(self._carets(), [14])

    def test_trailing_whitespace(self):
        self._newline("(foo bar  \t|)")
        self.assertEqual(self._text(), "(foo bar\n     )")

    def test_selection(self):
        self._set("(foo bar baz)")
        self.view.sel().clear()
        self.view.sel().add(sublime.Region(8, 12))
        self.view.run_command("racket_newline")
        self.assertEqual(self._text(), "(foo bar\n     )")
        self.assertEqual(self._carets(), [14])

    def test_two_carets(self):
        self._newline("(a b|)\n(define x|)")
        self.assertEqual(self._text(), "(a b\n   )\n(define x\n  )")
        self.assertEqual(self._carets(), [8, 22])

    def test_same_line_carets(self):
        self._newline("(foo |bar |baz)")
        self.assertEqual(self._text(), "(foo\n bar\n baz)")

    def test_blank_between_carets(self):
        self._newline("(a |  |b)")
        self.assertEqual(self._text(), "(a\n\n b)")
        self.assertEqual(self._carets(), [3, 5])

    def test_string(self):
        self._newline('(f "a |b")')
        self.assertEqual(self._text(), '(f "a \nb")')


class TestFixture(IndentTestCase):
    def test_fixture(self):
        """Every line of raco fmt output is already where the indenter puts it."""
        (path,) = [
            p
            for p in sublime.find_resources("indent.rkt")
            if p.endswith("/tests/fixtures/indent.rkt")
        ]
        text = sublime.load_resource(path).replace("\r\n", "\n")
        self._set(text)
        snapshot = indent.Snapshot(self.view)
        for row, line in enumerate(text.split("\n")):
            if not line.strip():
                continue
            with self.subTest(row=row + 1, line=line):
                pt = self.view.text_point(row, 0)
                expected = len(line) - len(line.lstrip())
                self.assertEqual(snapshot.indent_column(pt), expected)


class TestListener(IndentTestCase):
    def _rewrite(self, name: str, args):
        return RacketIndentListener().on_text_command(self.view, name, args)

    def test_enter(self):
        self._set("(a|)")
        self.assertEqual(
            self._rewrite("insert", {"characters": "\n"}), ("racket_newline", {})
        )

    def test_setting_off(self):
        self._set("(a|)")
        self.view.settings().set("racket_indent", False)
        self.assertIsNone(self._rewrite("insert", {"characters": "\n"}))

    def test_plain_text(self):
        self.view.assign_syntax("scope:text.plain")
        self._set("(a|)")
        self.assertIsNone(self._rewrite("insert", {"characters": "\n"}))

    def test_other_characters(self):
        self._set("(a|)")
        self.assertIsNone(self._rewrite("insert", {"characters": "x"}))
