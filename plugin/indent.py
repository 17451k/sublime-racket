from __future__ import annotations

import sublime
import sublime_plugin

from .utils import indent

_BLANK = " \t"


class RacketNewlineCommand(sublime_plugin.TextCommand):
    """Insert a newline and indent the new line the way raco fmt would."""

    def run(self, edit: sublime.Edit):
        view = self.view
        carets: list[int] = []

        # First to last, shifting each selection by the edits before it
        offset = 0
        for region in list(view.sel()):
            region = sublime.Region(region.a + offset, region.b + offset)
            size = view.size()
            view.erase(edit, region)
            pt = region.begin()
            pt += view.insert(edit, pt, "\n")
            snapshot = indent.Snapshot(view, indent.form_start(view, pt), pt)
            column = snapshot.indent_column(pt)

            if column is not None:
                # Whitespace after the caret and trailing whitespace before it
                end = pt
                while end < view.size() and view.substr(end) in _BLANK:
                    end += 1
                view.erase(edit, sublime.Region(pt, end))
                start = pt - 1
                while start > 0 and view.substr(start - 1) in _BLANK:
                    start -= 1
                view.erase(edit, sublime.Region(start, pt - 1))
                # The erase may reach back over earlier carets
                carets = [min(c, start) for c in carets]
                pt = start + 1
                pt += view.insert(edit, pt, " " * column)

            offset += view.size() - size
            carets.append(pt)

        view.sel().clear()
        view.sel().add_all(carets)


class RacketIndentListener(sublime_plugin.EventListener):
    """Route Enter in Racket code to the command above."""

    def on_text_command(self, view: sublime.View, command_name: str, args):
        if command_name != "insert" or args != {"characters": "\n"}:
            return None
        if not view.settings().get("racket_indent"):
            return None
        if not all(view.match_selector(r.begin(), "source.racket") for r in view.sel()):
            return None
        return ("racket_newline", {})
