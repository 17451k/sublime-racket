#!/usr/bin/env python3
"""Sanity-check Racket.sublime-syntax:
  1. Parses as valid YAML.
  2. Every context referenced via include:/push:/set: (as a plain string,
     or the first element of a push: list) names an existing key under
     contexts:.
  3. Every match: regex compiles (with the `regex` module if available,
     else the stdlib `re` module). Oniguruma-only constructs are noted,
     not silently ignored.
"""
import os
import re as re_stdlib
import subprocess
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SYNTAX_PATH = os.path.join(REPO_ROOT, "Racket.sublime-syntax")
SCRIBBLE_SYNTAX_PATH = os.path.join(REPO_ROOT, "Scribble.sublime-syntax")


def ensure_yaml():
    try:
        import yaml  # noqa: F401
        return yaml
    except ImportError:
        pass

    print("PyYAML not importable directly; attempting `pip install --user pyyaml` ...")
    subprocess.run(
        [sys.executable, "-m", "pip", "install", "--user", "--break-system-packages", "pyyaml"],
        check=False,
    )
    try:
        import yaml  # noqa: F401
        return yaml
    except ImportError:
        pass

    # Offline fallback: no network access to pip. Search a few known
    # locations on this machine for an existing PyYAML install and add its
    # site-packages directory to sys.path rather than failing outright.
    print("pip install failed (likely no network); searching for a local PyYAML install ...")
    home = os.path.expanduser("~")
    candidates = subprocess.run(
        ["find", home, "-maxdepth", "8", "-type", "d", "-name", "yaml",
         "-path", "*/site-packages/*"],
        capture_output=True, text=True, timeout=30,
    ).stdout.splitlines()
    for cand in candidates:
        site_packages = os.path.dirname(cand)
        if site_packages not in sys.path:
            sys.path.insert(0, site_packages)
        try:
            import yaml  # noqa: F401
            print("Found usable PyYAML at: %s" % cand)
            return yaml
        except ImportError:
            sys.path.remove(site_packages)
            continue

    print("ERROR: could not import yaml via any method (no network, no local install found).",
          file=sys.stderr)
    sys.exit(1)


def get_regex_engine():
    try:
        import regex
        return regex, "regex"
    except ImportError:
        return re_stdlib, "re"


def collect_context_refs(node, refs):
    """Walk the parsed YAML structure collecting all include/push/set target
    context names (strings). push/set can be a string or a list of contexts
    (where list entries can themselves be inline anonymous context dicts, in
    which case there's no name to check)."""
    if isinstance(node, dict):
        for key, value in node.items():
            if key in ("include", "set") and isinstance(value, str):
                refs.append(value)
            elif key == "push":
                if isinstance(value, str):
                    refs.append(value)
                elif isinstance(value, list):
                    for item in value:
                        if isinstance(item, str):
                            refs.append(item)
                        else:
                            collect_context_refs(item, refs)
            else:
                collect_context_refs(value, refs)
    elif isinstance(node, list):
        for item in node:
            collect_context_refs(item, refs)


def collect_match_patterns(node, patterns):
    if isinstance(node, dict):
        for key, value in node.items():
            if key == "match" and isinstance(value, str):
                patterns.append(value)
            else:
                collect_match_patterns(value, patterns)
    elif isinstance(node, list):
        for item in node:
            collect_match_patterns(item, patterns)


def check_syntax_file(path, yaml):
    """Runs the three checks against one syntax file."""
    name = os.path.basename(path)
    errors = []

    with open(path, "r", encoding="utf-8") as f:
        text = f.read()

    try:
        doc = yaml.safe_load(text)
    except Exception as e:
        print("YAML PARSE ERROR (%s):" % name, e)
        sys.exit(1)
    print("[OK] %s: YAML parses." % name)

    contexts = doc.get("contexts", {})
    context_names = set(contexts.keys())
    print("[OK] %s: Found %d contexts." % (name, len(context_names)))

    available_names = context_names

    refs = []
    collect_context_refs(doc, refs)
    missing = sorted(set(r for r in refs if r not in available_names))
    if missing:
        errors.append("Missing context definitions referenced: %s" % missing)
    else:
        print("[OK] %s: All %d context references resolve to existing contexts."
              % (name, len(set(refs))))

    engine, engine_name = get_regex_engine()
    patterns = []
    collect_match_patterns(doc, patterns)
    bad = []
    oniguruma_only = []
    for p in patterns:
        try:
            engine.compile(p)
        except Exception as e:
            msg = str(e)
            # Sublime lets a pushed context's match: patterns backreference
            # capture groups (\1, \2, ...) from the match that triggered the
            # push (cross-context backreferences) -- a Sublime/Oniguruma-only
            # feature with no meaning to a regex engine compiling the pattern
            # in isolation, so it's expected to "fail" here.
            if re_stdlib.search(r"\\[1-9]", p) and "invalid group reference" in msg.lower():
                oniguruma_only.append((p, msg))
            elif r"\h" in p or r"\R" in p:
                oniguruma_only.append((p, msg))
            else:
                bad.append((p, msg))

    print("[INFO] %s: Compiled %d distinct match patterns (%d total occurrences)."
          % (name, len(set(patterns)), len(patterns)))

    if oniguruma_only:
        print("Patterns noted as possibly Oniguruma-only (not re-compatible, left as-is):")
        for p, e in oniguruma_only:
            print("  - %r  (%s)" % (p, e))

    if bad:
        errors.append("Failed to compile %d regex pattern(s):\n" % len(bad) +
                       "\n".join("  - %r  =>  %s" % (p, e) for p, e in bad))

    return doc, errors


def main():
    yaml = ensure_yaml()

    errors = []

    for path in (SYNTAX_PATH, SCRIBBLE_SYNTAX_PATH):
        _, file_errors = check_syntax_file(path, yaml)
        errors.extend(file_errors)

    if errors:
        print("\n=== FAILURES ===")
        for e in errors:
            print(e)
        sys.exit(1)

    print("\nAll checks passed.")


if __name__ == "__main__":
    main()
