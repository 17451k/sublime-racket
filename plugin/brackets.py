from __future__ import annotations

import re
from typing import Callable

import sublime
import sublime_plugin

from .utils import sexp

# Same condition as the default auto-pairing key bindings
_PAIR_BEFORE = re.compile(r"^(?:\t| |\)|]|;|\}|$)")
_CLOSERS = {"(": ")", "[": "]", "{": "}"}


def _per_region(view: sublime.View, step: Callable[[sublime.Region], None]) -> None:
    """Run step with each selection region alone, last region first."""
    sel = view.sel()
    done: list[sublime.Region] = []

    for region in reversed(list(sel)):
        size = view.size()
        sel.clear()
        sel.add(region)
        step(region)
        delta = view.size() - size
        done = [sublime.Region(r.a + delta, r.b + delta) for r in done]
        done.extend(sel)

    sel.clear()
    sel.add_all(done)


class RacketSmartOpenBracketCommand(sublime_plugin.TextCommand):
    """Insert "(" or "[" depending on the context."""

    def run(self, edit: sublime.Edit) -> None:
        _per_region(self.view, self._open)

    def _open(self, region: sublime.Region) -> None:
        view = self.view
        pt = region.begin()
        before = view.substr(sublime.Region(max(0, pt - 2), pt))

        if before == "#\\":
            # Character literal #\[
            view.run_command("insert", {"characters": "["})
            return

        if (
            before
            and before != ",@"
            and not before[-1].isspace()
            and before[-1] not in "()[]{}'`,"
        ):
            # Typed right after an atom, such as #[ or @foo[, but not after
            # the reader prefix ,@
            opener = "["
        else:
            opener = sexp.smart_open(view, sexp.indent_point(view, pt))

        closer = _CLOSERS[opener]
        auto_match = view.settings().get("auto_match_enabled")

        if auto_match and not region.empty():
            contents = opener + "${0:$SELECTION}" + closer
            view.run_command("insert_snippet", {"contents": contents})
        elif auto_match and _PAIR_BEFORE.match(
            view.substr(sublime.Region(pt, view.line(pt).end()))
        ):
            view.run_command("insert_snippet", {"contents": opener + "$0" + closer})
        else:
            view.run_command("insert", {"characters": opener})


class RacketSmartCloseBracketCommand(sublime_plugin.TextCommand):
    """Insert the closer that matches the innermost unclosed opener."""

    def run(self, edit: sublime.Edit, char: str) -> None:
        _per_region(self.view, lambda region: self._close(region, char))

    def _close(self, region: sublime.Region, char: str) -> None:
        view = self.view
        pt = region.begin()

        if view.substr(sublime.Region(max(0, pt - 2), pt)) == "#\\":
            # Character literal #\)
            view.run_command("insert", {"characters": char})
            return

        opener = sexp.enclosing_open(view, pt)
        closer = char if opener is None else _CLOSERS[view.substr(opener)]

        if (
            view.settings().get("auto_match_enabled")
            and region.empty()
            and view.substr(pt) == closer
        ):
            view.run_command("move", {"by": "characters", "forward": True})
        else:
            view.run_command("insert", {"characters": closer})
