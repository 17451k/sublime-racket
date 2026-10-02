from __future__ import annotations

import sublime


def is_racket(view: sublime.View | None) -> bool:
    return bool(view and view.match_selector(0, "source.racket"))


def executable(view: sublime.View | None) -> str:
    """Return the racket executable from the Racket syntax settings."""
    # A non-Racket view carries no syntax-specific settings; read the file directly
    settings = (
        view.settings()
        if view and is_racket(view)
        else sublime.load_settings("Racket.sublime-settings")
    )
    return str(settings.get("racket_executable") or "racket")
