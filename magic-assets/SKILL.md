---
name: magic-assets
description: Generates production UI raster assets with Packy GPT-Image-2, or writes CSS/JS script FX when motion does not need new pixels. Cuts sheets into transparent PNGs, crisp pixel SVGs, or 4-frame pixel animation cycles. Prefer script FX for pulse, bob, shake, flash, fade, filter, and mask. Prefer equal-scale icon sheets (4/8/16). Use mixed-scale sheets only when one hero asset and smaller accessories must share a style. Use the pixel path for static retro sprites. Use pixel-anim for looping pixel cycles (idle/walk/bounce). Use when a web or app UI needs custom stylized icons, pixel icons, pixel GIFs, CSS motion, product-hero-plus-glyphs, chroma-key sprite sheets, or when CSS/SVG cannot cover the look.
---

# Magic Assets

Produce UI motion or raster assets during coding. Write a brief, pick **one** path. Script FX writes CSS/JS and never calls image2. Raster paths call image2, then run the shared cut/save pipeline.

This folder is the skill. In this repository it lives at `magic-assets/`. After install into an app it lives at `.cursor/skills/magic-assets/`. This repo keeps a symlink at `.cursor/skills/magic-assets`, so both command prefixes work here. Run every command from the **host project root**.

## Choose a path

Default to **grid**. Use **fx** when motion needs no new pixels. Use **pixel** for retro / texel icons. Use **pixel-anim** for a 4-frame pixel cycle. Use **mixed** only when scale or type cannot be equal.

| Path | When | Script |
| --- | --- | --- |
| FX | Scale, move, filter, mask, flash. No image2 | `python3 magic-assets/run.py fx` |
| Grid | Same role, same cell size, smooth/clay/flat icons | `python3 magic-assets/run.py grid` |
| Pixel | Same cell size, but pixel-art / hard texel edges | `python3 magic-assets/run.py pixel` |
| Pixel-anim | One character, 4 consecutive pixel frames → GIF/strip | `python3 magic-assets/run.py pixel-anim` |
| Mixed | One large hero plus smaller matching objects | `python3 magic-assets/run.py mixed` |

Do not generate if CSS, SVG, or an existing icon library is enough.

```
Need motion or rasters?
  only scale/fade/flash/shake/mask/filter → fx (no image2)
  pixel cycle / GIF / sprite strip → pixel-anim
  pixel-art / retro / hard pixels → pixel
  all items same size and type → grid
  one hero + smaller satellites, or mixed types → mixed
```

Prompts stay path-specific. Guide-box crop, chroma key, trim, naming, `manifest.json`, and file drop are shared.

## Workflow

1. Read the current page/component and any `DESIGN.md`.
2. List only the missing motion or rasters. Write names, style, and destination paths. Optional: save them as a JSON brief and pass `--brief`.
3. Pick fx, grid, pixel, pixel-anim, or mixed. Do not combine raster paths in one request. FX may wrap a finished raster.
4. Run `python3 magic-assets/run.py <path>` from the **host project root**. Do not hand-write image2 curl. FX must not call image2.
5. Inspect the pack. FX: open `preview.html`, then copy `fx.css` / `fx.js`. Rasters: inspect `sheet.png` for the 2px `#00FFFF` boxes, then `assets/*.png` (pixel also writes `.svg` / `palette.json`; pixel-anim cuts the sheet into `cycle.gif` / `strip.png` / `cycle.css` without redrawing). Re-cut rasters with `--skip-generate --sheet` if only the splitter is wrong. Tests: `python3 magic-assets/run.py test`.
6. Copy accepted files into the app. FX: `fx.css` + `fx.js`. Rasters: PNGs into `public/assets/...` or `src/assets/...`. Wire `src` / `data-ma-fx` / CSS.
7. Verify the real UI. Keep `manifest.json` so later regenerations can lock style.

## Shared rules

- Packy `gpt-image-2`: `n` is always 1, `background: transparent` is unsupported, `response_format` is rejected. Use opaque `#FF00FF` and cut locally.
- Every raster asset is wrapped in a closed 2px `#00FFFF` box. Scripts crop the interiors, then drop cyan and magenta. Old sheets without boxes fall back to equal cells or blobs.
- Never put magenta / fuchsia or electric cyan on the objects themselves.
- No text, labels, watermarks, desks, or extra frames. The cyan boxes are the only allowed frames.
- This skill is self-contained. Scripts live in this folder (`run.py`, `scripts/`). Read `ma_settings.json` in this folder (`endpoint`, `apikey`, `model_name`).
- Output lands in the host `output/`, never inside the skill folder.
- High-res jobs can take ~2 minutes. The client already retries and bypasses proxies.

## Commands

Always run from the host project root. After copying this folder into an app, replace `magic-assets/` with `.cursor/skills/magic-assets/`.

```bash
python3 magic-assets/run.py fx --effects pulse,bob,flash,pop
python3 magic-assets/run.py grid --count 8 --names home,search,user,settings,bell,chart,folder,plus
python3 magic-assets/run.py pixel --count 4 --colors 12
python3 magic-assets/run.py pixel-anim --action idle --sprite 32
python3 magic-assets/run.py mixed --hero "handheld console front, original design" --small joystick,gamepad,cartridge
python3 magic-assets/run.py grid --skip-generate --sheet output/icon-sheet-8-xxx/sheet.png --count 8
python3 magic-assets/run.py test
python3 magic-assets/run.py pixel --brief example_web_design/briefs/puppy-icons.json
```

`--brief path.json` and `--prompt-file` override defaults. `--style` locks a family across jobs.

## Install into another project

Copy **this folder only**. Do not copy repo-root leftovers (`README.md`, `example_web_design/`).

1. Place it at `<app>/.cursor/skills/magic-assets/`.
2. `pip install -r .cursor/skills/magic-assets/requirements.txt`
3. Fill in `.cursor/skills/magic-assets/ma_settings.json` (`endpoint`, `apikey`, `model_name`).
4. Run `run.py` from `<app>/`. `output/` stays in the host app.

## After generate

Place files, update imports, and check the page. If edges are dirty, re-run `--skip-generate` before calling image2 again.

## Path details

- Script FX (no image2): [fx.md](references/fx.md)
- Equal-scale prompts and counts: [grid.md](references/grid.md)
- Pixel snap + rect SVG: [pixel.md](references/pixel.md)
- Pixel 4-frame cycles: [pixel-anim.md](references/pixel-anim.md)
- Mixed-scale prompts and split rules: [mixed.md](references/mixed.md)
