# Pixel animation path

One character, one looping cycle, one 1024 sheet. Trust the painted sheet. Local scripts crop the 2px cyan boxes, drop magenta, align, and assemble GIF / strip / CSS.

Do **not** reuse the pixel-icon path. Icons snap to a texel grid. This path is consecutive frames of the same sprite.

## Use when

- Retro / pixel characters need idle, walk-in-place, or squash bounce
- The cycle can be told in **4 frames**
- The character can be painted at about **32×32 texels** on the sheet

If the motion is only scale, fade, flash, shake, or a mask, do not call image2. Use [fx.md](fx.md).

## v1 limits

| Lock | Value | Why |
| --- | --- | --- |
| Frames | 4 | Write it in the prompt. image2 must paint four cells |
| Layout | 2×2 on 1024×1024 | One sheet, one generate |
| Sprite | 16–48 texels, default 32 | Size lives in the prompt, not in a later resample |
| Cycle | In-place | Jump / travel / turnaround later |

Do not generate 8 or 16 animation frames on one sheet yet.

## Two animation layers

1. **Script FX** — [fx.md](fx.md). CSS: pulse, bob, shake, flash, fade, mask wipe. No image2.
2. **Drawn cycles** — image2 must redraw the body. This path.

## Pipeline

Default is **light cut**. The sheet is the final art.

1. Write frames, sprite size, beats, and 2px `#00FFFF` boxes into the prompt so image2 paints them
2. image2 returns one chroma-key sheet with one closed box per frame
3. Local script: crop box interiors, drop cyan + magenta, shared crop (`stage`) or pin feet. Equal cells only if the boxes are missing.
4. Optional `--stabilize-x` (default on) only slides X
5. Optional `--holds 2,1,1,1`
6. Write PNG frames, `strip.png`, `cycle.gif`, `cycle.css`, `preview.html`, `anim.json`

Do **not** snap, majority-vote, merge the palette, or emit rect SVG unless the user asks for `--snap`. `--snap` is the old hard-pixel path and will lose eyes and blush.

## Prompt must include

- “This sheet is the final art / will not redraw”
- Exactly N frames, one character, in-betweens
- Sprite size in texels (`32×32`)
- Identical costume, colors, facing, camera, baseline
- Frame N reads back into frame 1
- Hard pixels, no smear
- One closed 2px `#00FFFF` box around each frame (2 canvas pixels, not 2 texels)
- No labels

## How to use the files

- Preview with `preview.html` or `cycle.gif`
- In a page, `strip.png` + `cycle.css` (`steps(N)` + `image-rendering: pixelated`)
- PNG frames are the fidelity source. GIF may quantize only if the cut has more than 255 colors
- Keep `anim.json` so later cycles can lock the same character paragraph

## Commands

```bash
python3 magic-assets/run.py pixel-anim --action idle
python3 magic-assets/run.py pixel-anim --action idle --holds 2,1,1,1 --frame-ms 120
python3 magic-assets/run.py pixel-anim --skip-generate --sheet output/pixel-anim-idle-4-xxx/sheet.png
python3 magic-assets/run.py pixel-anim --snap --sheet output/pixel-anim-idle-4-xxx/sheet.png --skip-generate
python3 magic-assets/run.py test pixel-anim
```

## Brief example

```json
{
  "frames": 4,
  "sprite": 32,
  "action": "idle",
  "character": "One small round slime: cream body, coral blush, two navy dot eyes.",
  "beats": [
    "rest pose",
    "squash wider",
    "stretch taller",
    "settle toward rest"
  ],
  "register": "stage",
  "frame_ms": 140,
  "loop": "cycle"
}
```
