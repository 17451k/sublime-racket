from __future__ import annotations

import sublime
import sublime_plugin


def _available() -> bool:
    """Whether Terminus is installed; tells the user when it is not."""
    classes: list[type] = sublime_plugin.window_command_classes
    if any(c.__name__ == "TerminusOpenCommand" for c in classes):
        return True
    sublime.error_message("Racket REPL needs the Terminus package.")
    return False


def open_terminal(
    window: sublime.Window,
    cmd: list[str],
    cwd: str | None,
    tag: str,
    title: str,
    focus: bool,
) -> bool:
    """Open a terminal; returns False when Terminus is missing."""
    if not _available():
        return False

    # terminus_open kills the terminal already holding the tag and reuses its view.
    window.run_command(
        "terminus_open",
        {
            "cmd": cmd,
            "cwd": cwd,
            "tag": tag,
            "title": title,
            "auto_close": False,
            "focus": focus,
        },
    )
    return True


def send_to_terminal(window: sublime.Window, text: str, tag: str) -> None:
    """Send text to the existing terminal holding the given tag."""
    if not _available():
        return

    window.run_command(
        "terminus_send_string",
        {
            "tag": tag,
            "string": text,
        },
    )


def find_terminal(window: sublime.Window, tag: str) -> sublime.View | None:
    """Return the live Terminus view holding the given tag, or None."""
    for view in window.views():
        settings = view.settings()
        # Terminus marks the view finished once its process has exited.
        if settings.get("terminus_view.tag") == tag and not settings.get(
            "terminus_view.finished"
        ):
            return view
    return None


def send_when_ready(
    window: sublime.Window, text: str, tag: str, retries: int = 50
) -> None:
    """Send text once the terminal opened by open_terminal shows up."""
    if find_terminal(window, tag):
        # The view is tagged just before the process starts; give it one more tick.
        sublime.set_timeout(lambda: send_to_terminal(window, text, tag), 100)
    elif retries > 0:
        sublime.set_timeout(
            lambda: send_when_ready(window, text, tag, retries - 1), 100
        )
    else:
        sublime.status_message("The terminal did not start; nothing was sent.")
