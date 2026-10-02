from __future__ import annotations

import re
from bisect import bisect_left

import sublime

_OPEN = (
    "punctuation.section.parens.begin, "
    "punctuation.section.brackets.begin, "
    "punctuation.section.braces.begin, "
    "punctuation.definition.vector.begin, "
    "punctuation.definition.hash.begin, "
    "punctuation.definition.struct.begin"
)
_CLOSE = (
    "punctuation.section.parens.end, "
    "punctuation.section.brackets.end, "
    "punctuation.section.braces.end"
)
_DELIMS = _OPEN + ", " + _CLOSE

_MODULE_HEAD = re.compile(r"[(\[{]\s*module[+*]?(?=[\s()\[\]{}])")

_LITERAL_PREFIX = "keyword.other.literal-prefix"

# Reader prefixes, longest first
_PREFIXES = ("#,@", "#'", "#`", "#,", ",@", "'", "`", ",")


def _forms(view: sublime.View, region: sublime.Region) -> list[sublime.Region]:
    """Return the balanced lists at depth 0 inside region."""
    forms: list[sublime.Region] = []
    depth = 0
    start = 0

    for delims in view.find_by_selector(_DELIMS):
        # Adjacent delimiters are merged into one region, so scan every point
        part = delims.intersection(region)

        for p in range(part.begin(), part.end()):
            if view.match_selector(p, _OPEN):
                if depth == 0:
                    start = p
                depth += 1
            elif view.match_selector(p, _CLOSE):
                if depth > 0:
                    depth -= 1
                    if depth == 0:
                        forms.append(sublime.Region(start, p + 1))

    return forms


def _pick(forms: list[sublime.Region], pt: int) -> sublime.Region | None:
    """Return the first form containing pt."""
    for form in forms:
        if form.begin() <= pt <= form.end():
            return form
    return None


def _with_prefix(view: sublime.View, form: sublime.Region) -> sublime.Region:
    """Extend form backwards over reader prefixes such as quote or unquote."""
    begin = form.begin()

    # Literal prefixes such as #hash or #s
    while begin > 0 and view.match_selector(begin - 1, _LITERAL_PREFIX):
        begin -= 1

    while True:
        before = view.substr(sublime.Region(max(0, begin - 3), begin))
        for prefix in _PREFIXES:
            if before.endswith(prefix):
                begin -= len(prefix)
                break
        else:
            break

    return sublime.Region(begin, form.end())


def toplevel_form(view: sublime.View, pt: int) -> sublime.Region | None:
    """Return the top-level form at pt, descending into module forms."""
    outer = _pick(view.find_by_selector("meta.sexp.racket"), pt)

    if outer is None:
        return None

    # Also splits (a)(b) written without whitespace
    form = _pick(_forms(view, outer), pt)

    if form is None:
        return None

    while _MODULE_HEAD.match(view.substr(form)):
        inner = sublime.Region(form.begin() + 1, form.end() - 1)
        child = _pick(_forms(view, inner), pt)
        if child is None:
            # Cursor on the module header or between its children
            return None
        form = child

    return _with_prefix(view, form)


def innermost_form(view: sublime.View, pt: int) -> sublime.Region | None:
    """Return the innermost balanced form containing pt, with reader prefixes."""
    outer = _pick(view.find_by_selector("meta.sexp.racket"), pt)

    if outer is None:
        return None

    stack: list[int] = []

    for delims in view.find_by_selector(_DELIMS):
        # Adjacent delimiters are merged into one region, so scan every point
        part = delims.intersection(outer)

        for p in range(part.begin(), part.end()):
            if view.match_selector(p, _OPEN):
                stack.append(p)
            elif view.match_selector(p, _CLOSE) and stack:
                start = stack.pop()
                # Inner forms close first, so the first match is innermost
                if start <= pt <= p + 1:
                    return _with_prefix(view, sublime.Region(start, p + 1))

    return None


_HEAD = re.compile(r"\s*([^\s()\[\]{}\"',`;]+)")
_ATOM = re.compile(r"[^\s()\[\]{}]+")
# Characters and strings (group 1), and line and block comments
_OPAQUE = re.compile(r'(#\\.|"(?:\\.|[^"\\])*")|;[^\n]*|#\|.*?\|#', re.DOTALL)

# Clause forms and the number of elements after the head before clauses start
_CLAUSES = {
    "cond": 0,
    "case": 1,
    "match": 1,
    "match*": 1,
    "syntax-case": 2,
    "syntax-parse": 1,
    "syntax-rules": 1,
}
# let, let*, letrec, let-values, match-let, ...; not delete
_LET = re.compile(r"(?:^|-)let")
_LET_LIKE = {
    "parameterize",
    "parameterize*",
    "with-handlers",
    "with-handlers*",
    "with-syntax",
    "with-syntax*",
}
_FOR = re.compile(r"for\*?(?:/.+)?")
# for forms with an accumulator list before the clauses
_ACCUMULATORS = {
    "for/fold",
    "for*/fold",
    "for/foldr",
    "for*/foldr",
    "for/lists",
    "for*/lists",
}
_CLASS_CLAUSES = {"init", "init-field", "field", "inherit", "inherit-field"}


def enclosing_open(view: sublime.View, pt: int) -> int | None:
    """Return the point of the innermost opener that is unclosed at pt."""
    regions = view.find_by_selector(_DELIMS)
    depth = 0

    # Walk backwards from the last region that starts before pt
    for i in range(bisect_left([r.begin() for r in regions], pt) - 1, -1, -1):
        region = regions[i]
        for p in range(min(region.end(), pt) - 1, region.begin() - 1, -1):
            char = view.substr(p)
            if char in ")]}":
                depth += 1
            elif char in "([{":
                if depth == 0:
                    return p
                depth -= 1

    return None


def indent_point(view: sublime.View, pt: int) -> int:
    """Return the point whose context the indentation at pt implies.

    On a whitespace-only line, this is the first trailing closer of the
    previous code line whose opener is left of pt's column.
    """
    line = view.line(pt)
    if view.substr(line).strip():
        return pt
    col = pt - line.begin()
    if col == 0:
        return pt

    end = line.begin()
    while end > 0 and (
        view.substr(end - 1).isspace() or view.match_selector(end - 1, "comment")
    ):
        end -= 1
    begin = end
    while begin > 0 and view.match_selector(begin - 1, _CLOSE):
        begin -= 1

    for p in range(begin, end):
        opener = enclosing_open(view, p)
        if opener is None:
            return pt
        if opener - view.line(opener).begin() < col:
            return p
    return pt


def _head(view: sublime.View, opener: int) -> str | None:
    """Return the symbol right after opener, if the first element is one."""
    text = view.substr(sublime.Region(opener + 1, min(view.size(), opener + 80)))
    m = _HEAD.match(text)
    return m.group(1) if m else None


def _elements(view: sublime.View, begin: int, end: int) -> tuple[list[str], int]:
    """Return the atoms and the number of forms at depth 0 between begin and end."""
    forms = [_with_prefix(view, f) for f in _forms(view, sublime.Region(begin, end))]
    text = view.substr(sublime.Region(begin, end))
    for form in reversed(forms):
        a = max(form.begin(), begin) - begin
        b = form.end() - begin
        text = text[:a] + " " + text[b:]
    # A character or a string is one atom; a comment is none
    text = _OPAQUE.sub(lambda m: "x" if m.group(1) else " ", text)
    return _ATOM.findall(text), len(forms)


def _count(view: sublime.View, begin: int, end: int) -> int:
    atoms, forms = _elements(view, begin, end)
    return len(atoms) + forms


def smart_open(view: sublime.View, pt: int) -> str:
    """Return the opener that fits the context at pt: "(" or "["."""
    parent = enclosing_open(view, pt)

    if parent is None:
        return "("

    head = _head(view, parent)

    # Clauses of cond, case, match and similar
    if head in _CLAUSES and _count(view, parent + 1, pt) - 1 >= _CLAUSES[head]:
        return "["

    # Follow the previous sibling
    forms = _forms(view, sublime.Region(parent + 1, pt))
    if forms:
        last = forms[-1]
        if not view.substr(sublime.Region(last.end(), pt)).strip():
            char = view.substr(last.begin())
            if char in "([{":
                return char

    # Binding lists of let- and for-like forms
    grand = enclosing_open(view, parent)
    if grand is not None:
        outer = _head(view, grand) or ""
        atoms, forms = _elements(view, grand + 1, parent)
        i = len(atoms) + forms
        if _LET.search(outer) or outer in _LET_LIKE:
            # Named let has one atom between the head and the bindings
            named = outer == "let" and len(atoms) == 2 and forms == 0
            if i == 1 or named:
                return "["
        elif _FOR.fullmatch(outer):
            # Keyword arguments, such as #:length n, come before the clauses
            i -= 2 * sum(atom.startswith("#:") for atom in atoms)
            if i == 1 or (i == 2 and outer in _ACCUMULATORS):
                return "["

    if head in _CLASS_CLAUSES:
        return "["

    return "("
