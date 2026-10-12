from __future__ import annotations

import re

import sublime
import sublime_plugin

RHOMBUS_LANG = re.compile(r"^#lang\s+rhombus\b")
RACKET_EXTENSIONS = (".rkt", ".rktl", ".rktd")


def apply_lang_syntax(view: sublime.View) -> None:
    """Switch a view between Racket and Rhombus to match its `#lang` line."""
    syntax = view.syntax()
    if syntax is None:
        return
    is_rhombus_lang = bool(RHOMBUS_LANG.match(view.substr(view.line(0))))
    if syntax.scope == "source.racket" and is_rhombus_lang:
        view.assign_syntax("scope:source.rhombus")
    elif (
        syntax.scope == "source.rhombus"
        and (view.file_name() or "").endswith(RACKET_EXTENSIONS)
        and not is_rhombus_lang
    ):
        view.assign_syntax("scope:source.racket")


class RacketLangListener(sublime_plugin.EventListener):
    """Use the Rhombus syntax for Racket files that start with `#lang rhombus`."""

    def on_init(self, views: list[sublime.View]) -> None:
        for view in views:
            apply_lang_syntax(view)

    def on_load(self, view: sublime.View) -> None:
        apply_lang_syntax(view)

    def on_post_save(self, view: sublime.View) -> None:
        apply_lang_syntax(view)

    def on_reload(self, view: sublime.View) -> None:
        apply_lang_syntax(view)

    def on_revert(self, view: sublime.View) -> None:
        apply_lang_syntax(view)
