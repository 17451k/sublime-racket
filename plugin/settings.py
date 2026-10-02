from __future__ import annotations

import sublime
import sublime_plugin

_DEFAULT = "// Settings in here override those in Racket.sublime-settings\n{\n\t$0\n}\n"


class RacketEditSettingsCommand(sublime_plugin.ApplicationCommand):
    """Open the package settings next to the user's Racket syntax settings."""

    def run(self) -> None:
        # The package directory name differs between installs and checkouts
        package = __name__.split(".")[0]
        base_file = f"${{packages}}/{package}/resources/Racket.sublime-settings"
        sublime.run_command(
            "edit_settings", {"base_file": base_file, "default": _DEFAULT}
        )
