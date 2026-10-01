from __future__ import annotations

import os

import sublime
import sublime_plugin

from .utils import racket, sexp, terminus

REPL_TAG = "racket-repl"


def _open_repl(
    window: sublime.Window, cmd: list[str], cwd: str | None, focus: bool
) -> bool:
    return terminus.open_terminal(
        window, cmd, cwd, tag=REPL_TAG, title="Racket REPL", focus=focus
    )


def _send_to_repl(window: sublime.Window, view: sublime.View, text: str) -> None:
    """Send text to the live REPL, starting one when needed."""
    text = text.strip()

    if not text:
        sublime.status_message("Nothing to send to the REPL.")
        return

    text += "\n"

    if terminus.find_terminal(window, REPL_TAG):
        terminus.send_to_terminal(window, text, REPL_TAG)
        return

    # No live REPL; start one and send once the terminal is up
    exe = racket.executable(view)
    if _open_repl(window, [exe, "-i"], cwd=None, focus=False):
        terminus.send_when_ready(window, text, REPL_TAG)


class RacketOpenReplCommand(sublime_plugin.WindowCommand):
    """Start a fresh Racket REPL in Terminus."""

    def run(self) -> None:
        exe = racket.executable(self.window.active_view())
        _open_repl(self.window, [exe, "-i"], cwd=None, focus=True)


class RacketRunInReplCommand(sublime_plugin.WindowCommand):
    """Start a fresh REPL in Terminus inside the current file's module."""

    def is_enabled(self) -> bool:
        return racket.is_racket(self.window.active_view())

    def run(self) -> None:
        view = self.window.active_view()

        if not view:
            return

        path = view.file_name()

        if not path:
            sublime.error_message("Save the file before running it in the REPL.")
            return

        if view.is_dirty():
            view.run_command("save")
            if view.is_dirty():
                sublime.error_message("Could not save the file.")
                return

        cwd = os.path.dirname(path)

        # Some modifications potentially useful on Windows, but not tested
        path = path.replace("\\", "/")
        enter = '(enter! (file "{}"))'.format(path.replace('"', '\\"'))

        exe = racket.executable(view)
        _open_repl(
            self.window,
            [exe, "-i", "-e", enter],
            cwd=cwd,
            focus=False,
        )


class RacketSendSelectionToReplCommand(sublime_plugin.WindowCommand):
    """Send the selection, or the line at the cursor, to the REPL."""

    def is_enabled(self) -> bool:
        return racket.is_racket(self.window.active_view())

    def run(self) -> None:
        view = self.window.active_view()

        if not view:
            return

        if len(view.sel()) != 1:
            sublime.status_message("Cannot send multiple selections to the REPL.")
            return

        sel = view.sel()[0]
        _send_to_repl(
            self.window, view, view.substr(sel if not sel.empty() else view.line(sel.b))
        )


class RacketSendDefinitionToReplCommand(sublime_plugin.WindowCommand):
    """Send the top-level form at the cursor to the REPL."""

    def is_enabled(self) -> bool:
        return racket.is_racket(self.window.active_view())

    def run(self) -> None:
        view = self.window.active_view()

        if not view:
            return

        if len(view.sel()) != 1:
            sublime.status_message("Cannot send multiple selections to the REPL.")
            return

        form = sexp.toplevel_form(view, view.sel()[0].b)

        if form is None:
            sublime.status_message("No top-level form at cursor.")
            return

        _send_to_repl(self.window, view, view.substr(form))


class RacketSendSexpToReplCommand(sublime_plugin.WindowCommand):
    """Send the innermost form at the cursor to the REPL."""

    def is_enabled(self) -> bool:
        return racket.is_racket(self.window.active_view())

    def run(self) -> None:
        view = self.window.active_view()

        if not view:
            return

        if len(view.sel()) != 1:
            sublime.status_message("Cannot send multiple selections to the REPL.")
            return

        form = sexp.innermost_form(view, view.sel()[0].b)

        if form is None:
            sublime.status_message("No s-expression at cursor.")
            return

        _send_to_repl(self.window, view, view.substr(form))
