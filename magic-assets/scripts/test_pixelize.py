#!/usr/bin/env python3
"""Unit tests for pixel snap / palette / SVG. No image2 calls."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from PIL import Image, ImageDraw

from common import PROJECT_ROOT, remove_chroma, sample_chroma
from pixelize import (
    collect_colors,
    detect_grid,
    merge_palette,
    pixelize_sheet_icons,
    write_pixel_svg,
)

CHROMA = (255, 0, 255)
NAVY = (5, 37, 74)
NAVY_NEAR = (3, 37, 73)
CORAL = (250, 103, 84)
CREAM = (255, 236, 180)
TEAL = (48, 176, 176)


def solid(size: int, color: tuple[int, int, int, int] | tuple[int, int, int]) -> Image.Image:
    image = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    image.paste(color if len(color) == 4 else (*color, 255), [0, 0, size, size])
    return image


def draw_logical_icon(kind: str, size: int = 16) -> Image.Image:
    image = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    if kind == "heart":
        draw.point([(3, 3), (4, 3), (6, 3), (7, 3)], fill=(*NAVY, 255))
        draw.rectangle((2, 4, 8, 8), fill=(*CORAL, 255))
        draw.point([(5, 9)], fill=(*CORAL, 255))
        for x, y in ((2, 4), (8, 4), (3, 8), (7, 8), (5, 10)):
            image.putpixel((x, y), (*NAVY, 255))
    elif kind == "block":
        draw.rectangle((3, 3, 12, 12), fill=(*TEAL, 255))
        draw.rectangle((3, 3, 12, 12), outline=(*NAVY, 255))
        draw.rectangle((6, 6, 9, 9), fill=(*CREAM, 255))
    else:
        raise AssertionError(kind)
    return image


def upscale_sheet(icons: list[Image.Image], texel: int, canvas: int = 512) -> Image.Image:
    sheet = Image.new("RGB", (canvas, canvas), CHROMA)
    cols = 2
    cell = canvas // cols
    for index, icon in enumerate(icons):
        big = icon.resize((icon.width * texel, icon.height * texel), Image.Resampling.NEAREST)
        col, row = index % cols, index // cols
        x = col * cell + (cell - big.width) // 2
        y = row * cell + (cell - big.height) // 2
        sheet.paste(big.convert("RGB"), (x, y))
    return sheet


class PixelizeTests(unittest.TestCase):
    def test_detects_integer_texel_on_clean_sheet(self) -> None:
        sheet = upscale_sheet([draw_logical_icon("heart"), draw_logical_icon("block")], texel=16)
        keyed = remove_chroma(sheet, CHROMA)
        texel, _px, _py = detect_grid(keyed)
        self.assertEqual(texel, 16)

    def test_recovers_shared_palette_and_square_family(self) -> None:
        sheet = upscale_sheet([draw_logical_icon("heart"), draw_logical_icon("block")], texel=16)
        icons, meta = pixelize_sheet_icons(
            sheet,
            cols=2,
            rows=2,
            chroma=CHROMA,
            logical=0,
            colors=8,
            merge_distance=18,
        )
        self.assertEqual(meta["texel"], 16)
        self.assertEqual(len(icons), 4)
        self.assertTrue(all(icon.size == tuple(meta["family_size"]) for icon in icons))
        self.assertLessEqual(meta["palette_size"], 6)
        heart_colors = collect_colors(icons[0])
        self.assertTrue(heart_colors)
        self.assertNotIn(CHROMA, heart_colors)

    def test_merges_near_duplicate_navy(self) -> None:
        counts = {
            NAVY: 80,
            NAVY_NEAR: 12,
            CORAL: 40,
            CREAM: 10,
        }
        mapping = merge_palette(counts, max_colors=8, min_distance=18)
        self.assertEqual(mapping[NAVY_NEAR], mapping[NAVY])
        self.assertNotEqual(mapping[CORAL], mapping[NAVY])

    def test_svg_uses_crisp_rects(self) -> None:
        icon = draw_logical_icon("block")
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "block.svg"
            write_pixel_svg(icon, path)
            text = path.read_text(encoding="utf-8")
        self.assertIn('shape-rendering="crispEdges"', text)
        self.assertIn("<rect ", text)
        self.assertNotIn("filter", text)

    def test_real_sample_sheet_stays_near_16px(self) -> None:
        sample = PROJECT_ROOT / "output/pixel-sheet-4-20260912-082812/sheet.png"
        if not sample.exists():
            self.skipTest("sample sheet not in workspace")
        sheet = Image.open(sample)
        chroma = sample_chroma(sheet)
        _icons, meta = pixelize_sheet_icons(
            sheet,
            cols=2,
            rows=2,
            chroma=chroma,
            logical=0,
            colors=12,
        )
        self.assertGreaterEqual(meta["texel"], 12)
        self.assertLessEqual(meta["texel"], 20)
        self.assertLessEqual(meta["palette_size"], 12)
        self.assertGreaterEqual(meta["palette_size"], 3)


if __name__ == "__main__":
    unittest.main()
