#!/usr/bin/env python3
"""Host-project CLI for the magic-assets skill. Run from the app root."""

from __future__ import annotations

import argparse
import sys
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from generate_fx import main as fx_main
from generate_grid import main as grid_main
from generate_mixed import main as mixed_main
from generate_pixel import main as pixel_main
from generate_pixel_anim import main as pixel_anim_main


COMMANDS = ("fx", "grid", "pixel", "pixel-anim", "mixed", "test")
TESTS = {
    "fx": "test_fx.py",
    "pixel": "test_pixelize.py",
    "pixel-anim": "test_pixel_anim.py",
    "guide": "test_guide.py",
}


def run_tests(names: list[str]) -> None:
    files = [TESTS[name] for name in names] if names else list(TESTS.values())
    suite = unittest.TestSuite()
    loader = unittest.TestLoader()
    for filename in files:
        suite.addTests(loader.discover(str(SCRIPTS), pattern=filename))
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if not result.wasSuccessful():
        sys.exit(1)


def main(argv: list[str] | None = None) -> None:
    raw = list(argv) if argv is not None else sys.argv[1:]
    parser = argparse.ArgumentParser(
        description="magic-assets skill runner. Copy this folder into another project to install."
    )
    parser.add_argument("command", choices=COMMANDS)
    if not raw or raw[0] in ("-h", "--help"):
        parser.print_help()
        return
    command, *rest = raw
    if command not in COMMANDS:
        parser.error(f"unknown command '{command}'")

    if command == "test":
        selected = [item for item in rest if item in TESTS]
        unknown = [item for item in rest if item not in TESTS and not item.startswith("-")]
        if unknown:
            sys.exit(f"unknown test '{unknown[0]}'. known: {', '.join(TESTS)}")
        run_tests(selected)
        return
    if command == "fx":
        fx_main(rest)
    elif command == "grid":
        grid_main(rest)
    elif command == "pixel":
        pixel_main(rest)
    elif command == "pixel-anim":
        pixel_anim_main(rest)
    else:
        mixed_main(rest)


if __name__ == "__main__":
    main()
