#!/usr/bin/env python3
"""Unit tests for pixel animation snap / register / GIF. No image2 calls."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from PIL import Image, ImageDraw

from animate import (
    GIF_TRANSPARENT,
    expand_holds,
    expand_loop,
    jitter_report,
    parse_holds,
    stabilize_x,
    write_cycle_css,
    write_pixel_gif,
    write_preview_gif,
    write_strip,
)
from generate_pixel_anim import DEFAULT_CHARACTER, build_prompt
from pixelize import align_frames, cut_anim_frames, collect_colors, pad_anchor, pixelize_sheet_frames, shared_trim

CHROMA = (255, 0, 255)
CORAL = (250, 103, 84)
NAVY = (5, 37, 74)


def draw_blob(size: int, box: tuple[int, int, int, int], color=CORAL) -> Image.Image:
    image = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    draw.rectangle(box, fill=(*color, 255))
    draw.rectangle(box, outline=(*NAVY, 255))
    return image


def anim_sheet(blobs: list[Image.Image], texel: int = 16, canvas: int = 512) -> Image.Image:
    sheet = Image.new("RGB", (canvas, canvas), CHROMA)
    cols = 2
    cell = canvas // cols
    for index, blob in enumerate(blobs):
        big = blob.resize((blob.width * texel, blob.height * texel), Image.Resampling.NEAREST)
        col, row = index % cols, index // cols
        x = col * cell + (cell - big.width) // 2
        y = row * cell + (cell - big.height) // 2
        placed = Image.new("RGB", big.size, CHROMA)
        placed.paste(big.convert("RGB"), mask=big.getchannel("A"))
        sheet.paste(placed, (x, y))
    return sheet


def opaque_bottom(image: Image.Image) -> int:
    box = image.getbbox()
    assert box is not None
    return box[3]


def opaque_top(image: Image.Image) -> int:
    box = image.getbbox()
    assert box is not None
    return box[1]


class PixelAnimTests(unittest.TestCase):
    def test_shared_trim_keeps_relative_offset(self) -> None:
        low = draw_blob(16, (5, 9, 10, 14))
        high = draw_blob(16, (5, 3, 10, 8))
        trimmed = shared_trim([low, high], margin=0)
        self.assertEqual(trimmed[0].size, trimmed[1].size)
        self.assertGreater(opaque_top(trimmed[0]), opaque_top(trimmed[1]))
        self.assertEqual(opaque_top(trimmed[0]) - opaque_top(trimmed[1]), 6)

    def test_feet_register_kills_vertical_jitter(self) -> None:
        low = draw_blob(16, (4, 8, 10, 14))
        shifted = draw_blob(16, (4, 2, 10, 8))
        aligned, size = align_frames([low, shifted], register="bottom-center", margin=1)
        self.assertEqual(opaque_bottom(aligned[0]), opaque_bottom(aligned[1]))
        self.assertEqual(opaque_bottom(aligned[0]), size[1] - 1)

    def test_center_register_centers_bbox(self) -> None:
        sprite = draw_blob(16, (2, 2, 6, 6))
        padded = pad_anchor(sprite, (12, 12), anchor="center", margin=0)
        box = padded.getbbox()
        self.assertEqual(box, (3, 3, 8, 8))

    def test_stage_sheet_preserves_jump(self) -> None:
        rest = draw_blob(16, (5, 9, 10, 14))
        hop = draw_blob(16, (5, 4, 10, 9))
        sheet = anim_sheet([rest, hop, rest, hop])
        frames, meta = pixelize_sheet_frames(
            sheet,
            cols=2,
            rows=2,
            chroma=CHROMA,
            colors=8,
            register="stage",
        )
        self.assertEqual(len(frames), 4)
        self.assertEqual(meta["texel"], 16)
        self.assertTrue(all(frame.size == tuple(meta["family_size"]) for frame in frames))
        self.assertGreater(opaque_top(frames[0]), opaque_top(frames[1]))

    def test_gif_and_strip_match_frame_count(self) -> None:
        frames = [draw_blob(8, (2, 2, 5, 5)), draw_blob(8, (2, 1, 5, 4)), draw_blob(8, (2, 2, 5, 5))]
        aligned, _size = align_frames(frames, register="stage", margin=0)
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            strip = write_strip(aligned, folder / "strip.png")
            write_pixel_gif(aligned, folder / "cycle.gif", frame_ms=120)
            with Image.open(folder / "cycle.gif") as gif:
                self.assertEqual(gif.n_frames, 3)
            self.assertEqual(strip.size, (aligned[0].width * 3, aligned[0].height))

    def test_pingpong_expands_without_repeating_ends(self) -> None:
        frames = [Image.new("RGBA", (2, 2), c) for c in ((1, 0, 0, 255), (0, 1, 0, 255), (0, 0, 1, 255))]
        playable = expand_loop(frames, "pingpong")
        self.assertEqual(len(playable), 4)
        self.assertIs(playable[3], frames[1])

    def test_css_uses_steps_and_pixelated(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "cycle.css"
            write_cycle_css(path, strip_name="strip.png", frame_size=(16, 16), frames=4, frame_ms=140)
            text = path.read_text(encoding="utf-8")
        self.assertIn("steps(4)", text)
        self.assertIn("image-rendering: pixelated", text)
        self.assertIn("background-position: -64px 0", text)

    def test_gif_keeps_contrast_when_colors_exceed_256(self) -> None:
        frame = Image.new("RGBA", (48, 48), (0, 0, 0, 0))
        for y in range(8, 40):
            for x in range(8, 40):
                cream = (250 - (x % 7), 240 - (y % 5), 200 + (x % 9), 255)
                frame.putpixel((x, y), cream)
        frame.putpixel((18, 22), (*NAVY, 255))
        frame.putpixel((30, 22), (*NAVY, 255))
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "rich.gif"
            write_pixel_gif([frame], path, frame_ms=100)
            with Image.open(path) as gif:
                rgba = gif.convert("RGBA")
        left = rgba.getpixel((18, 22))
        body = rgba.getpixel((24, 28))
        self.assertLess(left[2], 120)
        self.assertGreater(body[0], 180)

    def test_gif_keeps_navy_and_clears_corners(self) -> None:
        frame = draw_blob(8, (2, 2, 5, 5), color=NAVY)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "cycle.gif"
            write_pixel_gif([frame, frame], path, frame_ms=100)
            with Image.open(path) as gif:
                self.assertEqual(gif.info.get("transparency"), 0)
                palette = gif.getpalette() or []
                self.assertEqual(tuple(palette[:3]), GIF_TRANSPARENT)
                rgba = gif.convert("RGBA")
        self.assertLess(rgba.getpixel((0, 0))[3], 40)
        self.assertGreaterEqual(rgba.getpixel((3, 3))[3], 200)
        self.assertEqual(rgba.getpixel((3, 3))[:3], NAVY)

    def test_preview_gif_is_nearest_scaled(self) -> None:
        frame = draw_blob(8, (2, 2, 5, 5))
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "cycle@4x.gif"
            write_preview_gif([frame], path, scale=4, frame_ms=100)
            with Image.open(path) as gif:
                self.assertEqual(gif.size, (32, 32))

    def test_holds_repeat_source_frames(self) -> None:
        frames = [draw_blob(4, (1, 1, 2, 2)), draw_blob(4, (1, 1, 2, 2), color=NAVY)]
        playable = expand_holds(frames, [2, 1])
        self.assertEqual(len(playable), 3)
        self.assertIs(playable[0], frames[0])
        self.assertIs(playable[1], frames[0])
        self.assertEqual(parse_holds("2,1,1,1", 4), [2, 1, 1, 1])

    def test_stabilize_x_kills_horizontal_jitter_keeps_height(self) -> None:
        left = draw_blob(16, (2, 8, 6, 12))
        right = draw_blob(16, (8, 8, 12, 12))
        shifted, deltas = stabilize_x([left, right])
        report = jitter_report(shifted)
        self.assertNotEqual(deltas, [0, 0])
        self.assertLessEqual(report["x_span"], 1)
        self.assertEqual(opaque_top(shifted[0]), opaque_top(shifted[1]))

    def test_prompt_locks_continuity_and_size(self) -> None:
        prompt = build_prompt(
            chroma="#FF00FF",
            character=DEFAULT_CHARACTER,
            action="idle",
            beats=["a", "b", "c", "d"],
            style="hard pixels",
            sprite=32,
            cols=2,
            rows=2,
        )
        self.assertIn("CONTINUOUS ANIMATION", prompt)
        self.assertIn("Exactly 4 frames", prompt)
        self.assertIn("32×32", prompt)
        self.assertIn("will not redraw", prompt)
        self.assertIn("invisible baseline", prompt)
        self.assertIn("Frame 4 must read back into frame 1", prompt)
        self.assertIn("#00FFFF", prompt)
        self.assertIn("2 canvas pixels", prompt)

    def test_light_cut_keeps_source_colors(self) -> None:
        rest = draw_blob(16, (5, 9, 10, 14))
        hop = draw_blob(16, (5, 4, 10, 9))
        sheet = anim_sheet([rest, hop, rest, hop])
        frames, meta = cut_anim_frames(sheet, cols=2, rows=2, chroma=CHROMA, register="stage")
        self.assertEqual(meta["mode"], "cut")
        self.assertGreater(frames[0].width, 40)
        colors = collect_colors(frames[0])
        self.assertIn(CORAL, colors)
        self.assertIn(NAVY, colors)
        self.assertGreater(opaque_top(frames[0]), opaque_top(frames[1]))


if __name__ == "__main__":
    unittest.main()
