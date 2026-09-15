#!/usr/bin/env python3
"""Pixel-art sheet: equal grid, then snap to a texel grid and emit SVG."""

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
    GRID_LAYOUTS,
    QUALITY_CHOICES,
    execute_run,
    guide_box_rules,
    load_brief,
    parse_names,
)
from pixelize import split_pixel_grid

PIXEL_STYLE = (
    "True pixel art sprites, not a filtered photo. Each icon is a small integer texel drawing "
    "shown as chunky nearest-neighbor squares. Hard edges only. No anti-aliasing, no blur, "
    "no gradients, no soft shadows, no outlines that fade. Limited shared palette: "
    "cream, coral, muted teal, navy, graphite. Never use magenta, electric cyan, "
    "the chroma-key color, or the guide-box color."
)
DEFAULT_SETS = {
    4: ["heart", "star", "coin", "potion"],
    8: ["heart", "star", "coin", "potion", "sword", "shield", "key", "chest"],
    16: [
        "heart",
        "star",
        "coin",
        "potion",
        "sword",
        "shield",
        "key",
        "chest",
        "boot",
        "map",
        "bomb",
        "gem",
        "bow",
        "flask",
        "skull",
        "flag",
    ],
}


def build_prompt(count: int, chroma: str, names: list[str], style: str, logical: int) -> str:
    cols, rows, _ = GRID_LAYOUTS[count]
    labeled = ", ".join(f"{i + 1}. {name}" for i, name in enumerate(names))
    grid_note = (
        f"The sprite itself is a {logical}x{logical} texel drawing enlarged with nearest-neighbor so individual pixels are clearly visible squares."
        if logical
        else "The sprite is a small integer pixel-art drawing (about 24–40 texels) enlarged with nearest-neighbor so individual pixels are clearly visible squares."
    )
    return f"""Create ONE pixel-art sprite sheet of {count} matching icons.

LAYOUT — follow exactly:
- Entire canvas is a perfectly flat, even fill of {chroma}. No scene, no paper, no desk.
- Strict {cols} columns × {rows} rows. Every cell is the same size.
- 16px even gutter of the same {chroma} between cells.
- Each cell contains exactly one sprite, centered. {grid_note}
- No text, no labels, no numbers, no watermark.

{guide_box_rules(chroma, count, DEFAULT_GUIDE)}

PIXEL RULES:
- Every edge is a hard pixel stair. No anti-aliased pixels. No half-transparent edge dust.
- One shared integer pixel grid and one shared palette for all {count} icons.
- {style}

ICONS left-to-right, top-to-bottom:
{labeled}

This sheet will be cropped inside the {count} {DEFAULT_GUIDE} boxes, then quantized and vectorized. Background must stay a single flat {chroma}.
"""


def resolve_names(count: int, names: list[str]) -> list[str]:
    if not names:
        return list(DEFAULT_SETS[count])
    if len(names) != count:
        sys.exit(f"pixel path expects {count} names, got {len(names)}")
    return names


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Pixel-art icon sheet via image2")
    parser.add_argument("--count", type=int, choices=sorted(GRID_LAYOUTS), default=4)
    parser.add_argument("--names", default="")
    parser.add_argument("--style", default="")
    parser.add_argument("--logical", type=int, default=0, help="force square output size; 0 = keep detected aspect")
    parser.add_argument("--texel", type=int, default=0, help="source block size in px; 0 = auto-detect")
    parser.add_argument("--colors", type=int, default=12)
    parser.add_argument("--merge-distance", type=float, default=22)
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
    if count not in GRID_LAYOUTS:
        sys.exit("pixel path only supports count 4, 8, or 16")
    logical = int(brief.get("logical") or args.logical)
    texel = int(brief.get("texel") or args.texel)
    colors = int(brief.get("colors") or args.colors)
    merge_distance = float(brief.get("merge_distance") or args.merge_distance)
    if logical < 0 or logical > 128:
        sys.exit("--logical must be 0 (auto) or 8-128")
    if texel < 0 or texel > 64:
        sys.exit("--texel must be 0 (auto) or 4-64")
    if colors < 2 or colors > 32:
        sys.exit("--colors must be between 2 and 32")
    names = parse_names(args.names) or [str(item) for item in brief.get("names") or []]
    names = resolve_names(count, names)
    style = args.style or brief.get("style") or PIXEL_STYLE
    chroma = args.chroma if args.chroma != DEFAULT_CHROMA else brief.get("chroma") or args.chroma
    quality = brief.get("quality") or args.quality
    cols, rows, default_size = GRID_LAYOUTS[count]
    size = args.size or brief.get("size") or default_size
    prompt = (
        Path(args.prompt_file).read_text(encoding="utf-8")
        if args.prompt_file
        else build_prompt(count, chroma, names, style, logical)
    )

    def split(sheet, sampled, dest_dir):
        return split_pixel_grid(
            sheet,
            cols=cols,
            rows=rows,
            names=names,
            chroma=sampled,
            dest_dir=dest_dir,
            logical=logical,
            colors=colors,
            texel=texel,
            merge_distance=merge_distance,
        )

    execute_run(
        mode="pixel",
        prompt=prompt,
        size=size,
        quality=quality,
        chroma=chroma,
        out_prefix=f"pixel-sheet-{count}",
        out_dir_flag=args.out_dir,
        skip_generate=args.skip_generate,
        sheet_path=args.sheet,
        extra_manifest={
            "grid": {"cols": cols, "rows": rows, "size": size},
            "names": names,
            "style": style,
            "logical": logical,
            "texel": texel,
            "colors": colors,
            "merge_distance": merge_distance,
        },
        split=split,
    )


if __name__ == "__main__":
    main()
