from __future__ import annotations

import re
from unittest.mock import patch

import sublime
import sublime_plugin
from unittesting import TestCase, ViewTestCase

from ..plugin.settings import (  # ty: ignore[unresolved-import]
    RacketEditSettingsCommand,
)


def _load(basename: str):
    """Return the parsed JSON of this package's resources/<basename>."""
    paths = [
        p
        for p in sublime.find_resources(basename)
        if p.endswith("/resources/" + basename)
    ]
    assert paths, basename
    return sublime.decode_value(sublime.load_resource(paths[0]))


class TestSyntaxAssignment(TestCase):
    def _scope(self, name: str) -> str | None:
        syntax = sublime.find_syntax_for_file(name)
        return None if syntax is None else syntax.scope

    def test_racket(self):
        for name in ("a.rkt", "a.rktl", "a.rktd"):
            self.assertEqual(self._scope(name), "source.racket", name)

    def test_scribble(self):
        self.assertEqual(self._scope("a.scrbl"), "text.scribble")


class TestEditing(ViewTestCase):
    def setUp(self):
        self.view.assign_syntax("scope:source.racket")
        self.view.settings().set("auto_indent", True)

    def _set(self, text: str):
        self.view.run_command("append", {"characters": text})

    def _text(self) -> str:
        return self.view.substr(sublime.Region(0, self.view.size()))

    def test_line_comment(self):
        self._set("(a)")
        self.setCaretTo(0, 0)
        self.view.run_command("toggle_comment")
        self.assertEqual(self._text(), "; (a)")
        self.view.run_command("toggle_comment")
        self.assertEqual(self._text(), "(a)")

    def test_block_comment(self):
        self._set("(a)")
        self.view.sel().clear()
        self.view.sel().add(sublime.Region(0, self.view.size()))
        self.view.run_command("toggle_comment", {"block": True})
        text = self._text()
        self.assertTrue(text.startswith("#|"), text)
        self.assertTrue(text.endswith("|#"), text)

    def test_word_arrow(self):
        self._set("(string->list x)")
        self.assertEqual(self.view.substr(self.view.word(3)), "string->list")

    def test_word_predicate(self):
        self._set("(empty? x)")
        self.assertEqual(self.view.substr(self.view.word(2)), "empty?")

    def test_word_bang(self):
        self._set("(set! x 1)")
        self.assertEqual(self.view.substr(self.view.word(2)), "set!")

    def test_settings(self):
        self.assertEqual(self.view.settings().get("racket_executable"), "racket")

    def test_symbols(self):
        self._set(
            "(define (distance p q) 1)\n(struct point (x y))\n(define origin 0)\n"
        )
        names = [s.name for s in self.view.symbol_regions()]
        for name in ("distance", "point", "origin"):
            self.assertIn(name, names)

    def test_indent_after_open(self):
        self._set("(define (f x)")
        self.setCaretTo(0, self.view.size())
        self.view.run_command("insert", {"characters": "\n"})
        row = self.getRowText(1)
        self.assertTrue(row, repr(row))
        self.assertEqual(row.strip(), "", repr(row))


class TestBuildSystem(TestCase):
    def setUp(self):
        self.build = _load("Racket.sublime-build")
        self.regex = re.compile(self.build["file_regex"])

    def test_variants(self):
        names = [v["name"] for v in self.build["variants"]]
        for name in (
            "Run",
            "Test",
            "Test Directory",
            "Compile",
            "Format",
            "Expand",
            "Check Requires",
        ):
            self.assertIn(name, names)
        self.assertEqual(self.build["selector"], "source.racket")

    def test_regex_basic(self):
        m = self.regex.match("foo.rkt:3:5: x: unbound identifier")
        self.assertIsNotNone(m)
        self.assertEqual(m.groups(), ("foo.rkt", "3", "5", "x: unbound identifier"))

    def test_regex_space_in_path(self):
        m = self.regex.match(
            "/tmp/my dir/foo.rkt:10:0: read-syntax: expected a closing bracket"
        )
        self.assertIsNotNone(m)
        self.assertEqual(m.groups()[:3], ("/tmp/my dir/foo.rkt", "10", "0"))

    def test_regex_location(self):
        m = self.regex.match("location:   bar.rkt:12:4")
        self.assertIsNotNone(m)
        self.assertEqual(m.groups()[:3], ("bar.rkt", "12", "4"))

    def test_regex_scribble(self):
        m = self.regex.match("manual.scrbl:7:2: bad")
        self.assertIsNotNone(m)
        self.assertEqual(m.group(1), "manual.scrbl")

    def test_regex_no_match(self):
        self.assertIsNone(self.regex.match("hello world"))
        self.assertIsNone(self.regex.match("foo.txt:1:2: x"))


class TestCommandPalette(TestCase):
    def setUp(self):
        self.items = _load("Default.sublime-commands")

    def test_commands_registered(self):
        window = sublime.active_window()
        # Command.name() derives the command name from the class name
        registered = {
            cls(window).name() for cls in sublime_plugin.window_command_classes
        }
        for item in self.items:
            self.assertIn(item["command"], registered)

    def test_captions(self):
        for item in self.items:
            self.assertTrue(item["caption"].startswith("Racket: "), item["caption"])


class TestMenu(TestCase):
    def setUp(self):
        (preferences,) = _load("Main.sublime-menu")
        (self.settings,) = preferences["children"]

    def test_ids(self):
        # Menus merge into the built-in ones by id
        self.assertEqual(self.settings["id"], "package-settings")

    def test_item(self):
        (item,) = self.settings["children"]
        self.assertEqual(item["caption"], "Sublime Racket")
        registered = {
            cls().name() for cls in sublime_plugin.application_command_classes
        }
        self.assertIn(item["command"], registered)

    def test_base_file_exists(self):
        with patch.object(sublime, "run_command") as run:
            RacketEditSettingsCommand().run()
        name, args = run.call_args[0]
        self.assertEqual(name, "edit_settings")
        path = args["base_file"].replace("${packages}", "Packages")
        self.assertIn(path, sublime.find_resources("Racket.sublime-settings"))
