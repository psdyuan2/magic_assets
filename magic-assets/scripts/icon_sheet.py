#!/usr/bin/env python3
"""Back-compat dispatcher. Prefer magic-assets/run.py from the host project root."""

from __future__ import annotations

import sys
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[1]
if str(SKILL_ROOT) not in sys.path:
    sys.path.insert(0, str(SKILL_ROOT))

from run import COMMANDS, main as run_main


def _argv(raw: list[str]) -> list[str]:
    if raw and raw[0] == "--mode" and len(raw) >= 2:
        return [raw[1], *raw[2:]]
    if raw and raw[0] in COMMANDS:
        return raw
    return ["grid", *raw]


if __name__ == "__main__":
    run_main(_argv(sys.argv[1:]))
