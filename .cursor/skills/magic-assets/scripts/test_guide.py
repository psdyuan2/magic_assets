#!/usr/bin/env python3
"""Unit tests for cyan guide-box cutting. No image2 calls."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from PIL import Image, ImageDraw

from common import (
    DEFAULT_GUIDE,
    GUIDE_RGB,
    find_guide_boxes,
    guide_box_rules,
    is_guide_color,
    split_blobs,
    split_grid,
)
from generate_grid import build_prompt as build_grid_prompt
from pixelize import cut_anim_frames

CHROMA = (255, 0, 255)
CORAL = (250, 103, 84)
NAVY = (5, 37, 74)
CREAM = (255, 236, 180)
TEAL = (48, 176, 176)


def boxed_sheet(
    placements: list[tuple[tuple[int, int, int, int], tuple[int, int, int]]],
    canvas: int = 400,
    stroke: int = 2,
) -> Image.Image:
    sheet = Image.new("RGB", (canvas, canvas), CHROMA)
    draw = ImageDraw.Draw(sheet)
    for (left, top, right, bottom), color in placements:
        draw.rectangle((left, top, right, bottom), outline=GUIDE_RGB, width=stroke)
        inset = stroke + 4
        draw.rectangle((left + inset, top + inset, right - inset, bottom - inset), fill=color)
    return sheet


class GuideBoxTests(unittest.TestCase):
    def test_electric_cyan_is_guide_muted_teal_is_not(self) -> None:
        self.assertTrue(is_guide_color(0, 255, 255))
        self.assertTrue(is_guide_color(16, 240, 240))
        self.assertFalse(is_guide_color(*TEAL))
        self.assertFalse(is_guide_color(*CHROMA))
        self.assertFalse(is_guide_color(*CORAL))

    def test_finds_four_closed_boxes_in_reading_order(self) -> None:
        sheet = boxed_sheet(
            [
                ((20, 20, 140, 140), CORAL),
                ((220, 30, 360, 150), NAVY),
                ((30, 210, 150, 350), CREAM),
                ((230, 220, 370, 360), TEAL),
            ]
        )
        boxes = find_guide_boxes(sheet, expected=4)
        self.assertEqual(len(boxes), 4)
        lefts = [box["inner"][0] for box in boxes]
        tops = [box["inner"][1] for box in boxes]
        self.assertLess(lefts[0], lefts[1])
        self.assertLess(tops[0], tops[2])

    def test_irregular_boxes_beat_equal_cell_math(self) -> None:
        sheet = boxed_sheet(
            [
                ((18, 18, 120, 130), CORAL),
                ((240, 40, 370, 140), NAVY),
                ((40, 230, 160, 360), CREAM),
                ((210, 250, 380, 370), TEAL),
            ]
        )
        with tempfile.TemporaryDirectory() as tmp:
            paths, records = split_grid(
                sheet,
                cols=2,
                rows=2,
                names=["a", "b", "c", "d"],
                chroma=CHROMA,
                dest_dir=Path(tmp),
            )
            self.assertEqual(len(paths), 4)
            self.assertTrue(all(item["cut"] == "guide-box" for item in records))
            colors = [Image.open(path).convert("RGB").getpixel((12, 12)) for path in paths]
        self.assertEqual(colors[0], CORAL)
        self.assertEqual(colors[1], NAVY)
        self.assertEqual(colors[2], CREAM)
        self.assertEqual(colors[3], TEAL)

    def test_fallback_without_boxes_still_splits_cells(self) -> None:
        sheet = Image.new("RGB", (200, 200), CHROMA)
        draw = ImageDraw.Draw(sheet)
        draw.rectangle((20, 20, 80, 80), fill=CORAL)
        draw.rectangle((120, 20, 180, 80), fill=NAVY)
        draw.rectangle((20, 120, 80, 180), fill=CREAM)
        draw.rectangle((120, 120, 180, 180), fill=TEAL)
        self.assertEqual(find_guide_boxes(sheet, expected=4), [])
        with tempfile.TemporaryDirectory() as tmp:
            _paths, records = split_grid(
                sheet,
                cols=2,
                rows=2,
                names=["a", "b", "c", "d"],
                chroma=CHROMA,
                dest_dir=Path(tmp),
            )
        self.assertEqual([item["cut"] for item in records], ["cell"] * 4)

    def test_mixed_uses_largest_box_as_hero(self) -> None:
        sheet = boxed_sheet(
            [
                ((20, 20, 220, 260), CORAL),
                ((260, 30, 360, 110), NAVY),
                ((260, 150, 360, 230), CREAM),
            ],
            canvas=400,
        )
        with tempfile.TemporaryDirectory() as tmp:
            paths, records = split_blobs(
                sheet,
                names=["hero", "stick", "pad"],
                chroma=CHROMA,
                dest_dir=Path(tmp),
            )
            self.assertEqual([item["cut"] for item in records], ["guide-box"] * 3)
            hero = Image.open(paths[0]).convert("RGB")
            width = hero.width
            sample = hero.getpixel((20, 20))
        self.assertGreater(width, 140)
        self.assertEqual(sample, CORAL)

    def test_seals_one_pixel_gap_in_stroke(self) -> None:
        sheet = Image.new("RGB", (180, 180), CHROMA)
        draw = ImageDraw.Draw(sheet)
        draw.rectangle((30, 30, 140, 140), outline=GUIDE_RGB, width=2)
        draw.rectangle((40, 40, 130, 130), fill=CORAL)
        sheet.putpixel((85, 30), CHROMA)
        sheet.putpixel((86, 30), CHROMA)
        boxes = find_guide_boxes(sheet, expected=1)
        self.assertEqual(len(boxes), 1)

    def test_ignores_outer_sheet_frame_keeps_inner_boxes(self) -> None:
        sheet = boxed_sheet(
            [
                ((20, 20, 150, 150), CORAL),
                ((220, 20, 360, 150), NAVY),
                ((20, 220, 150, 360), CREAM),
                ((220, 220, 360, 360), TEAL),
            ]
        )
        draw = ImageDraw.Draw(sheet)
        draw.rectangle((6, 6, 393, 393), outline=GUIDE_RGB, width=2)
        boxes = find_guide_boxes(sheet, expected=4)
        self.assertEqual(len(boxes), 4)

    def test_cut_anim_prefers_guide_boxes(self) -> None:
        sheet = boxed_sheet(
            [
                ((16, 16, 170, 170), CORAL),
                ((210, 16, 370, 170), NAVY),
                ((16, 210, 170, 370), CREAM),
                ((210, 210, 370, 370), TEAL),
            ]
        )
        frames, meta = cut_anim_frames(sheet, cols=2, rows=2, chroma=CHROMA, register="stage")
        self.assertEqual(meta["cut"], "guide-box")
        self.assertEqual(len(frames), 4)
        self.assertEqual(len(meta["boxes"]), 4)

    def test_prompt_requires_two_pixel_cyan_boxes(self) -> None:
        rules = guide_box_rules("#FF00FF", 4, DEFAULT_GUIDE)
        self.assertIn(DEFAULT_GUIDE, rules)
        self.assertIn("2 canvas pixels", rules)
        prompt = build_grid_prompt(4, "#FF00FF", ["home", "search", "user", "settings"], "clay")
        self.assertIn("CUT MARKERS", prompt)
        self.assertIn(DEFAULT_GUIDE, prompt)
        self.assertNotIn("No frames, no cards, no outlines around cells.", prompt)


if __name__ == "__main__":
    unittest.main()
