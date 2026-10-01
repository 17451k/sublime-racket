from __future__ import annotations

import re
import subprocess

import sublime
import sublime_plugin

from .utils import racket

# A run of characters with no delimiter, quote or comment start
_IDENTIFIER = re.compile(r"[^\s()\[\]{}\"',`;]+")


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

        # raco docs opens the search page in the browser itself; do not wait
        try:
            subprocess.Popen(
                cmd,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except OSError:
            sublime.error_message(f"Could not run {cmd[0]}.")
            return

        sublime.status_message(f"Searching Racket docs for {term}")
