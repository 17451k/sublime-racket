from __future__ import annotations

import re
from bisect import bisect_left, bisect_right
from typing import Optional, Tuple

import sublime

from . import sexp

_OPENERS = "([{"
_CLOSERS = ")]}"
# Characters that end an atom
_STOP = ' \t\n\r\f\v()[]{}"'

_STRING = "string, constant.character"
# Characters that can start a comment or a string
_STARTERS = ';#@"'

# Head, distinguished arguments, and keyword pairs before for clauses
_MAX_ELEMENTS = 8

_FOR = sexp._FOR

_Element = Tuple[int, Optional[str]]

# Body forms: name -> number of distinguished arguments before the body.
# Agrees with fmt's standard-formatter-map for every form listed there; the
# others follow the Racket reference.
_BODY_FORMS: dict[str, int] = {
    "begin": 0,
    "begin-for-syntax": 0,
    "test-begin": 0,
    "lazy": 0,
    "cond": 0,
    "case-lambda": 0,
    "match-lambda": 0,
    "match-lambda*": 0,
    "match-lambda**": 0,
    "syntax-parser": 0,
    "λ": 1,
    "lambda": 1,
    "with-syntax": 1,
    "with-syntax*": 1,
    "with-handlers": 1,
    "with-handlers*": 1,
    "shared": 1,
    "begin0": 1,
    "module+": 1,
    "test-case": 1,
    "test-suite": 1,
    "class": 1,
    "interface": 1,
    "syntax-rules": 1,
    "match": 1,
    "match*": 1,
    "case": 1,
    "pattern": 1,
    "syntax-parse": 1,
    "syntax/loc": 1,
    "quasisyntax/loc": 1,
    "when": 1,
    "unless": 1,
    "struct": 2,
    "letrec-syntaxes+values": 2,
    "class*": 2,
    "interface*": 2,
    "module": 2,
    "module*": 2,
    "syntax-case": 2,
    "instantiate": 2,
    "mixin": 2,
    "for/fold": 2,
    "for*/fold": 2,
    "for/lists": 2,
    "for*/lists": 2,
    "for/foldr": 2,
    "for*/foldr": 2,
    "define-struct": 2,
}

# Families of body forms, tried when the name is not listed above; these also
# cover user-defined forms that follow the naming conventions
_BODY_FAMILIES: list[tuple[re.Pattern[str], int]] = [
    (re.compile(r"(?:match-)?define(?:[-/].+)?"), 1),
    (re.compile(r"(?:match-|splicing-)?let(?:rec)?\*?(?:[-/].+)?"), 1),
    (_FOR, 1),
    (re.compile(r"(?:splicing-)?(?:syntax-)?parameterize\*?"), 1),
    (re.compile(r"delay(?:/.+)?"), 0),
]


def body_args(head: str | None) -> int | None:
    """Return the number of distinguished arguments of a body form, else None."""
    if head is None:
        return None
    if head in _BODY_FORMS:
        return _BODY_FORMS[head]
    for pattern, n in _BODY_FAMILIES:
        if pattern.fullmatch(head):
            return n
    return None


class _Regions:
    """Sorted, non-overlapping regions with point lookup."""

    def __init__(self, regions: list[sublime.Region]):
        self.regions = regions
        self.begins = [r.begin() for r in regions]

    def at(self, pt: int) -> sublime.Region | None:
        """Return the region containing pt."""
        i = bisect_right(self.begins, pt) - 1
        if i >= 0 and pt < self.regions[i].end():
            return self.regions[i]
        return None


def form_start(view: sublime.View, pt: int) -> int:
    """Return the start of the line where the top-level form around pt begins."""
    begin = view.line(pt).begin()
    while begin > 0 and view.match_selector(
        begin - 1, "meta.sexp, string, comment.block"
    ):
        begin = view.line(begin - 1).begin()
    return begin


class Snapshot:
    """Brackets, comments and strings of part of a view, read once."""

    def __init__(self, view: sublime.View, begin: int = 0, end: int | None = None):
        self.view = view
        if end is None:
            end = view.size()
        text = view.substr(sublime.Region(begin, end))
        comments: list[sublime.Region] = []
        strings: list[sublime.Region] = []

        # Bracket points, the innermost opener unclosed right after each one,
        # and the closer of each opener
        self.brackets: list[int] = []
        self.parents: list[int | None] = []
        self.closers: dict[int, int] = {}
        stack: list[int] = []

        p = begin
        while p < end:
            char = text[p - begin]
            # Comments and strings start at one of a few characters, or
            # before begin
            if char in _STARTERS or p == begin:
                found = False
                for selector, regions in (("comment", comments), (_STRING, strings)):
                    if view.match_selector(p, selector):
                        q = p + 1
                        while q < end and view.match_selector(q, selector):
                            q += 1
                        regions.append(sublime.Region(p, q))
                        p = q
                        found = True
                        break
                if found:
                    continue
            if (char in _OPENERS or char in _CLOSERS) and view.match_selector(
                p, sexp._DELIMS
            ):
                if char in _OPENERS:
                    stack.append(p)
                elif stack:
                    self.closers[stack.pop()] = p
                self.brackets.append(p)
                self.parents.append(stack[-1] if stack else None)
            p += 1

        self.comments = _Regions(comments)
        self.strings = _Regions(strings)

    def enclosing_open(self, pt: int) -> int | None:
        """Return the point of the innermost opener that is unclosed at pt."""
        i = bisect_left(self.brackets, pt) - 1
        return self.parents[i] if i >= 0 else None

    def _elements(self, begin: int, end: int) -> list[_Element]:
        """Return up to _MAX_ELEMENTS depth-0 datums between begin and end.

        Each is (start, atom text); the text is None for a balanced form.
        """
        view = self.view
        elements: list[_Element] = []
        p = begin

        while p < end and len(elements) < _MAX_ELEMENTS:
            region = self.comments.at(p)
            if region is not None:
                p = region.end()
                continue

            region = self.strings.at(p)
            if region is not None:
                elements.append((p, view.substr(region)))
                p = region.end()
                continue

            char = view.substr(p)
            if char.isspace():
                p += 1
                continue

            start = p
            if char not in _OPENERS:
                # An atom, or a reader prefix when an opener follows
                while (
                    p < end
                    and view.substr(p) not in _STOP
                    and self.comments.at(p) is None
                    and self.strings.at(p) is None
                ):
                    p += 1
                if p >= end or view.substr(p) not in _OPENERS:
                    elements.append((start, view.substr(sublime.Region(start, p))))
                    continue

            closer = self.closers.get(p)
            if closer is None:
                break
            elements.append((start, None))
            p = closer + 1

        return elements

    def indent_column(self, pt: int) -> int | None:
        """Return the column the line at pt should start at, or None to keep it."""
        view = self.view
        if pt > 0 and view.match_selector(pt - 1, "string, comment.block"):
            return None

        tab_size = view.settings().get("tab_size", 4) or 4

        def column(p: int) -> int:
            text = view.substr(sublime.Region(view.line(p).begin(), p))
            return len(text.expandtabs(tab_size))

        opener = self.enclosing_open(pt)
        if opener is None:
            return 0

        c = column(opener)
        if view.substr(opener) in "[{":
            return c + 1

        elements = self._elements(opener + 1, pt)
        if not elements:
            return c + 1

        head = elements[0][1]
        second = elements[1][0] if len(elements) > 1 else None

        n = body_args(head)
        if n is not None:
            if head == "let" and len(elements) > 1 and elements[1][1] is not None:
                n = 2
            if head == "struct" and len(elements) > 2 and elements[2][1] is not None:
                n = 3
            args = elements[1:]
            if head is not None and _FOR.fullmatch(head):
                # Keyword arguments before the for clauses
                while args and args[0][1] is not None and args[0][1].startswith("#:"):
                    args = args[2:]
            if len(args) >= n:
                return c + 2
            return c + 4 if second is None else column(second)

        if (
            second is not None
            and view.rowcol(second)[0] == view.rowcol(elements[0][0])[0]
        ):
            return column(second)
        return c + 1
