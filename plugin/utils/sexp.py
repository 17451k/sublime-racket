from __future__ import annotations

import re

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
