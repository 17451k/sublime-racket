from __future__ import annotations

import re
import subprocess
import threading

import sublime
import sublime_plugin

from .utils import racket

# A run of characters with no delimiter, quote or comment start
_IDENTIFIER = re.compile(r"[^\s()\[\]{}\"',`;]+")


def _look_up(cmd: list[str]) -> None:
    """Run raco docs and report a failure."""
    try:
        result = subprocess.run(
            cmd,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            check=False,
        )
    except OSError:
        sublime.error_message(f"Could not run {cmd[0]}.")
        return

    if result.returncode != 0:
        detail = result.stderr.decode("utf-8", errors="replace").strip()
        detail = detail or f"exit code {result.returncode}"
        sublime.error_message(f"raco docs failed:\n\n{detail}")


class RacketLookUpDocsCommand(sublime_plugin.WindowCommand):
    """Search the Racket documentation for the identifier at the cursor."""

    def is_enabled(self) -> bool:
        return racket.is_racket(self.window.active_view())

    def run(self) -> None:
        view = self.window.active_view()

        if not view:
            return

        if len(view.sel()) != 1:
            sublime.status_message("Cannot look up multiple selections.")
            return

        sel = view.sel()[0]
        term = view.substr(sel if not sel.empty() else view.word(sel.b)).strip()

        if not term or not _IDENTIFIER.fullmatch(term):
            sublime.status_message("No identifier at cursor.")
            return

        # `--` stops raco from parsing identifiers such as `->` as switches;
        # `racket -l- raco` honours the racket_executable setting
        cmd = [racket.executable(view), "-l-", "raco", "docs", "--", term]

        # raco docs opens the search page in the browser itself; the wait for it
        # happens off the UI thread
        sublime.status_message(f"Searching Racket docs for {term}")
        threading.Thread(target=_look_up, args=(cmd,), daemon=True).start()
