import sublime
import sublime_plugin

from .utils import terminus


def _open_repl(window, cmd, cwd, focus):
    terminus.open_terminal(window, cmd, cwd, tag="racket-repl", title="Racket REPL", focus=focus)


class RacketOpenReplCommand(sublime_plugin.WindowCommand):
    """Start a fresh Racket REPL in Terminus."""

    def run(self):
        view = self.window.active_view()
        if not view:
            sublime.error_message("No Racket file is open.")
            return

        racket = view.settings().get("racket_executable", "racket")
        _open_repl(self.window, [racket, "-i"], cwd=None, focus=True)


class RacketRunInReplCommand(sublime_plugin.WindowCommand):
    """Start a fresh Racket REPL in Terminus inside the current file's module."""

    def run(self):
        view = self.window.active_view()
        if not view:
            sublime.error_message("No Racket file is open.")
            return

        path = view.file_name()
        if not path:
            sublime.error_message("Save the file before running it in the REPL.")
            return

        if view.is_dirty():
            view.run_command("save")

        # Some modifications potentially useful on Windows, but not tested
        path = path.replace("\\", "/")
        racket = view.settings().get("racket_executable", "racket")
        enter = '(enter! (file "{}"))'.format(path.replace('"', '\\"'))
        _open_repl(self.window, [racket, "-i", "-e", enter], cwd=path.rsplit("/", 1)[0], focus=False)


class RacketSendSelectionToReplCommand(sublime_plugin.WindowCommand):
    """Send the current selection (or the current line) to the Racket REPL."""

    def run(self):
        view = self.window.active_view()
        if not view:
            sublime.error_message("No Racket file is open.")
            return

        if not terminus.is_installed():
            sublime.error_message("Racket REPL needs the Terminus package.")
            return

        regions = [r if not r.empty() else view.line(r) for r in view.sel()]
        text = "\n".join(view.substr(r) for r in regions).strip()
        if not text:
            return
        text += "\n"

        if terminus.find_terminal(self.window, "racket-repl"):
            terminus.send_to_terminal(self.window, text)
            return

        # No live REPL; start one and send once the terminal is up
        racket = view.settings().get("racket_executable", "racket")
        _open_repl(self.window, [racket, "-i"], cwd=None, focus=False)
        terminus.send_when_ready(self.window, text)
