from __future__ import annotations

import os

import sublime
import sublime_plugin

from .utils import terminus

REPL_TAG = "racket-repl"


def _racket(view: sublime.View | None) -> str:
    if not view:
        return "racket"
    return str(view.settings().get("racket_executable", "racket"))


def _is_racket(view: sublime.View | None) -> bool:
    return bool(view and view.match_selector(0, "source.racket"))


def _open_repl(
    window: sublime.Window, cmd: list[str], cwd: str | None, focus: bool
) -> bool:
    return terminus.open_terminal(
        window, cmd, cwd, tag=REPL_TAG, title="Racket REPL", focus=focus
    )


class RacketOpenReplCommand(sublime_plugin.WindowCommand):
    """Start a fresh Racket REPL in Terminus."""

    def run(self) -> None:
        racket = _racket(self.window.active_view())
        _open_repl(self.window, [racket, "-i"], cwd=None, focus=True)


class RacketRunInReplCommand(sublime_plugin.WindowCommand):
    """Start a fresh REPL in Terminus inside the current file's module."""

    def is_enabled(self) -> bool:
        return _is_racket(self.window.active_view())

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

        racket = _racket(view)
        _open_repl(
            self.window,
            [racket, "-i", "-e", enter],
            cwd=cwd,
            focus=False,
        )


class RacketSendSelectionToReplCommand(sublime_plugin.WindowCommand):
    """Send the selection, or the line at the cursor, to the REPL."""

    def is_enabled(self) -> bool:
        return _is_racket(self.window.active_view())

    def run(self) -> None:
        view = self.window.active_view()

        if not view:
            return

        if len(view.sel()) != 1:
            sublime.status_message("Cannot send multiple selections to the REPL.")
            return

        sel = view.sel()[0]
        text = view.substr(sel if not sel.empty() else view.line(sel.b)).strip()

        if not text:
            sublime.status_message("Nothing to send to the REPL.")
            return

        text += "\n"

        if terminus.find_terminal(self.window, REPL_TAG):
            terminus.send_to_terminal(self.window, text, REPL_TAG)
            return

        # No live REPL; start one and send once the terminal is up
        racket = _racket(view)
        if _open_repl(self.window, [racket, "-i"], cwd=None, focus=False):
            terminus.send_when_ready(self.window, text, REPL_TAG)
