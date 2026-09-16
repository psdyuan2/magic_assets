#!/usr/bin/env python3
"""Unit tests for script FX catalog and pack writer. No image2."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from common import PROJECT_ROOT, SETTINGS_PATH, SKILL_ROOT
from fx import (
    EFFECTS,
    FAMILY_ORDER,
    LAYOUT_PROPS,
    effect_ids,
    render_css,
    render_js,
    render_preview,
    resolve_effects,
    uses_layout_property,
)
from generate_fx import write_pack


class ScriptFxTests(unittest.TestCase):
    def test_skill_is_portable_from_host_root(self) -> None:
        self.assertTrue((SKILL_ROOT / "SKILL.md").exists())
        self.assertTrue((SKILL_ROOT / "run.py").exists())
        self.assertTrue((SKILL_ROOT / "requirements.txt").exists())
        self.assertNotEqual(PROJECT_ROOT, SKILL_ROOT)
        self.assertEqual(SETTINGS_PATH, SKILL_ROOT / "ma_settings.json")
        self.assertTrue((PROJECT_ROOT / ".git").exists() or PROJECT_ROOT == SKILL_ROOT.parents[2])

    def test_catalog_covers_five_families(self) -> None:
        families = {effect.family for effect in EFFECTS.values()}
        self.assertEqual(families, set(FAMILY_ORDER))
        self.assertGreaterEqual(len(EFFECTS), 10)
        self.assertEqual(len(effect_ids()), len(set(effect_ids())))

    def test_no_layout_properties(self) -> None:
        for effect in EFFECTS.values():
            self.assertFalse(uses_layout_property(effect), effect.id)
            blob = f"{effect.keyframes} {effect.rest}"
            for prop in LAYOUT_PROPS:
                self.assertNotIn(f"{prop}:", blob)

    def test_css_contains_reduced_motion_and_keyframes(self) -> None:
        css = render_css()
        self.assertIn("prefers-reduced-motion", css)
        self.assertIn("will-change: transform, opacity, filter, clip-path", css)
        for effect in EFFECTS.values():
            self.assertIn(f"@keyframes ma-fx-{effect.id}", css)
            self.assertIn(f".ma-fx--{effect.id}", css)

    def test_subset_omits_other_effects(self) -> None:
        css = render_css(resolve_effects(["pulse", "wipe-right"]))
        self.assertIn("@keyframes ma-fx-pulse", css)
        self.assertIn("@keyframes ma-fx-wipe-right", css)
        self.assertNotIn("@keyframes ma-fx-hue", css)

    def test_unknown_effect_raises(self) -> None:
        with self.assertRaises(ValueError) as ctx:
            resolve_effects(["pulse", "explode"])
        self.assertIn("explode", str(ctx.exception))

    def test_js_exposes_play_stop_bind(self) -> None:
        js = render_js()
        for token in ("function play", "function stop", "function bind", "IntersectionObserver", "MagicFx"):
            self.assertIn(token, js)

    def test_once_effects_have_rest_state(self) -> None:
        for effect in EFFECTS.values():
            if effect.loop:
                continue
            if effect.id in {"shake", "flash"}:
                continue
            self.assertTrue(effect.rest, effect.id)
            css = render_css([effect])
            self.assertIn(":not(.is-playing):not(.ma-fx-loop)", css)

    def test_preview_wires_data_attributes(self) -> None:
        html = render_preview(resolve_effects(["pop", "bob"]))
        self.assertIn('data-ma-fx="pop"', html)
        self.assertIn('data-ma-fx="bob"', html)
        self.assertIn('href="fx.css"', html)
        self.assertIn('src="fx.js"', html)
        self.assertIn("MagicFx.play", html)

    def test_write_pack_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            dest, effects = write_pack(Path(tmp) / "pack", ["flash", "reveal"])
            self.assertTrue((dest / "fx.css").exists())
            self.assertTrue((dest / "fx.js").exists())
            self.assertTrue((dest / "preview.html").exists())
            manifest = json.loads((dest / "manifest.json").read_text(encoding="utf-8"))
        self.assertEqual([item["id"] for item in effects], ["flash", "reveal"])
        self.assertEqual(manifest["mode"], "fx")
        self.assertEqual(manifest["count"], 2)


if __name__ == "__main__":
    unittest.main()
