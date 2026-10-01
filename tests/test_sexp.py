from __future__ import annotations

from unittesting import ViewTestCase

from ..plugin.utils import sexp  # ty: ignore[unresolved-import]


class SexpTestCase(ViewTestCase):
    def setUp(self):
        self.view.assign_syntax("scope:source.racket")

    def _form(self, func, marked: str) -> str | None:
        """Return the form func finds at the | marker in marked."""
        pt = marked.index("|")
        text = marked[:pt] + marked[pt + 1 :]
        # append does not auto-indent or auto-pair
        self.view.run_command("append", {"characters": text})
        region = func(self.view, pt)
        return None if region is None else self.view.substr(region)


class TestToplevelForm(SexpTestCase):
    def _top(self, marked: str) -> str | None:
        return self._form(sexp.toplevel_form, marked)

    def test_nested_cursor(self):
        text = "(define (f x)\n  (+ x 1))"
        self.assertEqual(self._top("(define (f x)\n  (+ x| 1))"), text)

    def test_between_forms(self):
        self.assertIsNone(self._top("(a 1)\n|\n(b 2)"))

    def test_after_close(self):
        self.assertEqual(self._top("(a 1)|"), "(a 1)")

    def test_adjacent_second(self):
        self.assertEqual(self._top("(a)(b|)"), "(b)")

    def test_adjacent_first(self):
        self.assertEqual(self._top("(a|)(b)"), "(a)")

    def test_module_plus_child(self):
        marked = "(module+ test\n  (check 1)\n  (check| 2))"
        self.assertEqual(self._top(marked), "(check 2)")

    def test_module_header(self):
        self.assertIsNone(self._top("(module+ te|st\n  (check 1))"))

    def test_nested_modules(self):
        marked = "(module m racket\n  (module+ test\n    (f| 1)))"
        self.assertEqual(self._top(marked), "(f 1)")

    def test_module_star(self):
        self.assertEqual(self._top("(module* m #f\n  (g| 1))"), "(g 1)")

    def test_quote(self):
        self.assertEqual(self._top("'(a |b)"), "'(a b)")

    def test_syntax_quote(self):
        self.assertEqual(self._top("#'(x| y)"), "#'(x y)")

    def test_quasiquote(self):
        self.assertEqual(self._top("`(a ,@(b|))"), "`(a ,@(b))")

    def test_hash(self):
        self.assertEqual(self._top("#hash((a| . 1))"), "#hash((a . 1))")

    def test_vector(self):
        self.assertEqual(self._top("#(1 |2)"), "#(1 2)")

    def test_bracket_in_string(self):
        self.assertEqual(self._top('(display "(|")'), '(display "(")')

    def test_comment(self):
        self.assertIsNone(self._top("(f x) ; (com|ment)"))

    def test_square_brackets(self):
        self.assertEqual(self._top("[a |b]"), "[a b]")

    def test_braces(self):
        self.assertEqual(self._top("{a |b}"), "{a b}")

    def test_bare_symbol(self):
        self.assertIsNone(self._top("x|yz"))


class TestInnermostForm(SexpTestCase):
    def _inner(self, marked: str) -> str | None:
        return self._form(sexp.innermost_form, marked)

    def test_inside(self):
        self.assertEqual(self._inner("(a (b |c) d)"), "(b c)")

    def test_after_close(self):
        self.assertEqual(self._inner("(a (b c)| d)"), "(b c)")

    def test_outer(self):
        self.assertEqual(self._inner("(a| (b c) d)"), "(a (b c) d)")

    def test_before_open(self):
        self.assertEqual(self._inner("|(a)"), "(a)")

    def test_between_forms(self):
        self.assertIsNone(self._inner("(a) | (b)"))

    def test_quote(self):
        self.assertEqual(self._inner("(f '(1 |2))"), "'(1 2)")

    def test_syntax_quote(self):
        self.assertEqual(self._inner("(f #'(x|))"), "#'(x)")

    def test_unquote_splicing(self):
        self.assertEqual(self._inner("`(f ,@(g |x))"), ",@(g x)")

    def test_unquote(self):
        self.assertEqual(self._inner("`(f ,(g |x))"), ",(g x)")

    def test_struct(self):
        self.assertEqual(self._inner("(f #s(p|t 1 2))"), "#s(pt 1 2)")

    def test_vector(self):
        self.assertEqual(self._inner("(f #(1 |2))"), "#(1 2)")

    def test_hash(self):
        self.assertEqual(self._inner("(f #hash((a . |1)))"), "(a . 1)")

    def test_square_brackets(self):
        self.assertEqual(self._inner("(let ([x 1|]) x)"), "[x 1]")

    def test_bracket_in_string(self):
        self.assertEqual(self._inner('(display "(|)")'), '(display "()")')

    def test_multiline(self):
        marked = "(define (f x)\n  (g (h\n      x|)))"
        self.assertEqual(self._inner(marked), "(h\n      x)")
