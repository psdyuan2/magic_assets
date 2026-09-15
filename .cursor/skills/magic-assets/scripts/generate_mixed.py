#!/usr/bin/env python3
"""Mixed-scale asset sheet: one hero plus smaller objects, then blob-cut."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from common import (
    DEFAULT_CHROMA,
    DEFAULT_GUIDE,
    DEFAULT_STYLE,
    QUALITY_CHOICES,
    execute_run,
    guide_box_rules,
    load_brief,
    parse_names,
    split_blobs,
)

DEFAULT_SIZE = "2048x2048"
DEFAULT_HERO = "original retro-futurist home game console, front view, invent the design, do not copy Nintendo Sony Xbox or Sega"
DEFAULT_SMALL = ["joystick", "gamepad", "cartridge", "dpad", "headset"]


def build_prompt(chroma: str, hero: str, small: list[str], style: str) -> str:
    labeled = "; ".join(f"{i + 1}. {name}" for i, name in enumerate(small))
    count = 1 + len(small)
    return f"""Create ONE production asset sheet with mixed-scale objects on a perfectly flat {chroma} background.

This is NOT a scene, desk, shelf, store display, or room. No table, no hands, no floor, no text, no labels, no numbers, no watermark, no logo, no grid.

LAYOUT — mixed sizes, must be easy to cut into separate PNGs:
- Left ~58% of the canvas: ONE large hero asset: {hero}. The hero must be about 2.5x to 3x larger than every small icon.
- Right ~42%: a vertical column of {len(small)} much smaller matching objects. Each small object is simple and chunky, not a tiny duplicate of the hero.
- Every object floats separately. Leave at least 90px of empty flat {chroma} between every object. Objects must never touch, overlap, share a shadow, or sit on a common platform.

{guide_box_rules(chroma, count, DEFAULT_GUIDE)}

SMALL OBJECTS top to bottom:
{labeled}

STYLE — one product family:
{style}

If a contact shadow exists, it must stay a darker shade of {chroma} and must not connect two objects. Background remains a single even {chroma} fill. A local script will crop inside the {count} {DEFAULT_GUIDE} boxes, then remove those strokes and {chroma}.
"""


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Mixed-scale asset sheet via image2")
    parser.add_argument("--hero", default="")
    parser.add_argument("--small", default="")
    parser.add_argument("--style", default="")
    parser.add_argument("--quality", choices=QUALITY_CHOICES, default="high")
    parser.add_argument("--size", default="")
    parser.add_argument("--chroma", default=DEFAULT_CHROMA)
    parser.add_argument("--brief", default="")
    parser.add_argument("--prompt-file", default="")
    parser.add_argument("--out-dir", default="output")
    parser.add_argument("--skip-generate", action="store_true")
    parser.add_argument("--sheet", default="")
    args = parser.parse_args(argv)

    brief = load_brief(args.brief)
    hero = args.hero or brief.get("hero") or DEFAULT_HERO
    small = parse_names(args.small) or [str(item) for item in brief.get("small") or []] or list(DEFAULT_SMALL)
    if not small:
        sys.exit("mixed path needs at least one --small asset")
    style = args.style or brief.get("style") or DEFAULT_STYLE
    chroma = args.chroma if args.chroma != DEFAULT_CHROMA else brief.get("chroma") or args.chroma
    quality = brief.get("quality") or args.quality
    size = args.size or brief.get("size") or DEFAULT_SIZE
    names = [hero, *small]
    prompt = (
        Path(args.prompt_file).read_text(encoding="utf-8")
        if args.prompt_file
        else build_prompt(chroma, hero, small, style)
    )

    def split(sheet, sampled, dest_dir):
        return split_blobs(sheet, names=names, chroma=sampled, dest_dir=dest_dir)

    execute_run(
        mode="mixed",
        prompt=prompt,
        size=size,
        quality=quality,
        chroma=chroma,
        out_prefix="mixed-sheet",
        out_dir_flag=args.out_dir,
        skip_generate=args.skip_generate,
        sheet_path=args.sheet,
        extra_manifest={"hero": hero, "small": small, "expected": names, "style": style},
        split=split,
    )


if __name__ == "__main__":
    main()
