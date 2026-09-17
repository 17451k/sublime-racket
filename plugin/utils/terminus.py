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
