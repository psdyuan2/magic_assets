#!/usr/bin/env python3
"""Equal-scale icon sheet: one grid, same cell size, then chroma-cut."""

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
    split_grid,
)

DEFAULT_SETS = {
    4: ["home", "search", "user", "settings"],
    8: ["home", "search", "user", "settings", "bell", "chart", "folder", "plus"],
    16: [
        "home",
        "search",
        "user",
        "settings",
        "bell",
        "chart",
        "folder",
        "plus",
        "mail",
        "calendar",
        "heart",
        "camera",
        "lock",
        "cloud",
        "cart",
        "play",
    ],
}
GRID = {
    4: (2, 2, "1024x1024"),
    8: (4, 2, "2048x1024"),
    16: (4, 4, "2048x2048"),
}


def build_prompt(count: int, chroma: str, names: list[str], style: str) -> str:
    cols, rows, _ = GRID[count]
    labeled = ", ".join(f"{i + 1}. {name}" for i, name in enumerate(names))
    return f"""Create ONE sprite sheet of {count} matching stylized web icons.

LAYOUT — follow exactly:
- Entire canvas is a perfectly flat, even fill of {chroma}. No gradient, no texture, no paper, no scene.
- Strict {cols} columns × {rows} rows. Every cell is the same size.
- 12px even gutter of the same {chroma} between cells.
- Each cell contains exactly one icon, centered, occupying about 70% of the cell.
- No text, no labels, no numbers, no captions, no watermark, no logo.

{guide_box_rules(chroma, count, DEFAULT_GUIDE)}

STYLE — all {count} icons must look like one family:
{style}

ICONS left-to-right, top-to-bottom:
{labeled}

This is a production asset sheet. A local script will crop inside the {count} {DEFAULT_GUIDE} boxes, then remove those strokes and {chroma}. Background must stay a single flat {chroma} with no dirt or vignette.
"""


def resolve_names(count: int, names: list[str]) -> list[str]:
    if not names:
        return list(DEFAULT_SETS[count])
    if len(names) != count:
        sys.exit(f"grid path expects {count} names, got {len(names)}")
    return names


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Equal-scale icon sheet via image2")
    parser.add_argument("--count", type=int, choices=sorted(GRID), default=8)
    parser.add_argument("--names", default="")
    parser.add_argument("--style", default="")
    parser.add_argument("--quality", choices=QUALITY_CHOICES, default="medium")
    parser.add_argument("--size", default="")
    parser.add_argument("--chroma", default=DEFAULT_CHROMA)
    parser.add_argument("--brief", default="")
    parser.add_argument("--prompt-file", default="")
    parser.add_argument("--out-dir", default="output")
    parser.add_argument("--skip-generate", action="store_true")
    parser.add_argument("--sheet", default="")
    args = parser.parse_args(argv)

    brief = load_brief(args.brief)
    count = int(brief.get("count") or args.count)
    if count not in GRID:
        sys.exit("grid path only supports count 4, 8, or 16")
    names = parse_names(args.names) or [str(item) for item in brief.get("names") or []]
    names = resolve_names(count, names)
    style = args.style or brief.get("style") or DEFAULT_STYLE
    chroma = args.chroma if args.chroma != DEFAULT_CHROMA else brief.get("chroma") or args.chroma
    quality = brief.get("quality") or args.quality
    cols, rows, default_size = GRID[count]
    size = args.size or brief.get("size") or default_size
    prompt = (
        Path(args.prompt_file).read_text(encoding="utf-8")
        if args.prompt_file
        else build_prompt(count, chroma, names, style)
    )

    def split(sheet, sampled, dest_dir):
        return split_grid(sheet, cols=cols, rows=rows, names=names, chroma=sampled, dest_dir=dest_dir)

    execute_run(
        mode="grid",
        prompt=prompt,
        size=size,
        quality=quality,
        chroma=chroma,
        out_prefix=f"icon-sheet-{count}",
        out_dir_flag=args.out_dir,
        skip_generate=args.skip_generate,
        sheet_path=args.sheet,
        extra_manifest={"grid": {"cols": cols, "rows": rows, "size": size}, "names": names, "style": style},
        split=split,
    )


if __name__ == "__main__":
    main()
