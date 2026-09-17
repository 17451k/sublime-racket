import sublime
import sublime_plugin


def is_installed():
    return any(c.__name__ == "TerminusOpenCommand" for c in sublime_plugin.window_command_classes)


def open_terminal(window, cmd, cwd, tag, title, focus):
    if not is_installed():
        sublime.error_message("Racket REPL needs the Terminus package.")
        return

    # terminus_open kills the terminal already holding the tag and reuses its view.
    window.run_command("terminus_open", {
        "cmd": cmd,
        "cwd": cwd,
        "tag": tag,
        "title": title,
        "auto_close": False,
        "focus": focus,
    })


def send_to_terminal(window, text, tag="racket-repl"):
    """Send text to an existing Racket REPL terminal."""
    if not is_installed():
        sublime.error_message("Racket REPL needs the Terminus package.")
        return

    window.run_command("terminus_send_string", {
        "tag": tag,
        "string": text,
    })


def find_terminal(window, tag):
    """Return the live Terminus view holding the given tag, or None."""
    for view in window.views():
        settings = view.settings()
        # Terminus marks the view finished once its process has exited.
        if settings.get("terminus_view.tag") == tag and not settings.get("terminus_view.finished"):
            return view
    return None


def send_when_ready(window, text, tag="racket-repl", retries=50):
    """Send text once the terminal opened by open_terminal shows up."""
    if find_terminal(window, tag):
        # The view is tagged just before the process starts; give it one more tick.
        sublime.set_timeout(lambda: send_to_terminal(window, text, tag), 100)
    elif retries > 0:
        sublime.set_timeout(lambda: send_when_ready(window, text, tag, retries - 1), 100)
