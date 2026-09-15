#!/usr/bin/env python3
"""Write a script-FX pack. No image2."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from common import ROOT, load_brief, parse_names
from fx import (
    effect_record,
    render_css,
    render_js,
    render_preview,
    resolve_effects,
)


def write_pack(dest: Path, names: list[str]) -> tuple[Path, list[dict]]:
    effects = resolve_effects(names)
    dest.mkdir(parents=True, exist_ok=True)
    files = {
        "fx.css": render_css(effects),
        "fx.js": render_js(),
        "preview.html": render_preview(effects),
    }
    records = []
    for name, text in files.items():
        path = dest / name
        path.write_text(text, encoding="utf-8")
        records.append({"name": name, "path": path.name})
    manifest = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "mode": "fx",
        "count": len(effects),
        "effects": [effect_record(effect) for effect in effects],
        "usage": {
            "markup": '<span class="ma-fx" data-ma-fx="pop" data-ma-trigger="mount">...</span>',
            "triggers": ["loop", "mount", "click", "hover", "inview"],
            "stack": "Wrap a pixel-anim sprite with data-ma-fx for hybrid motion.",
        },
        "files": records,
    }
    (dest / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return dest, manifest["effects"]


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Script FX pack (CSS/JS, no image2)")
    parser.add_argument("--effects", default="", help="comma-separated ids; default is the full catalog")
    parser.add_argument("--brief", default="")
    parser.add_argument("--out-dir", default="output")
    args = parser.parse_args(argv)

    brief = load_brief(args.brief)
    names = parse_names(args.effects) or [str(item) for item in brief.get("effects") or []]
    try:
        resolve_effects(names)
    except ValueError as error:
        sys.exit(str(error))

    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    label = "all" if not names else f"{len(names)}"
    dest = ROOT / args.out_dir / f"fx-pack-{label}-{stamp}"
    out_dir, effects = write_pack(dest, names)
    print(f"fx pack {len(effects)} effects -> {out_dir}")
    for effect in effects:
        print(f"  {effect['id']:12} {effect['family']:8} {effect['duration']} {effect['default_trigger']}")
    print(f"preview {out_dir / 'preview.html'}")


if __name__ == "__main__":
    main()
