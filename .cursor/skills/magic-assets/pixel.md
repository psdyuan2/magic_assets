# Pixel path

Equal-scale pixel-art family. Generate a grid sheet, snap each cell onto a detected texel grid, share one palette, then write a 1:1 PNG and a rect SVG.

Do **not** potrace / autotrace the raw model image. That smooths stairs into curves and kills the pixel look. The crisp vector is `shape-rendering="crispEdges"` plus one `<rect>` per horizontal texel run.

## Use when

- Retro UI, game HUD, 8-bit / 16-bit icons
- Edges must stay stair-stepped at any display size
- Every icon can share one cell size and one palette

If the icons should look clay / smooth / glossy, use the grid path.

## Pipeline

image2 still paints anti-aliased “fake pixels”. Post-process is mandatory:

1. Crop each 2px `#00FFFF` box (or equal cells if boxes are missing)
2. Shared chroma-key of the sheet, then drop leftover cyan
3. Detect texel size from block uniformity (prefer ~16px; ignore 8px AA crumbs)
4. Detect phase **per cell** (model grids are not globally aligned)
5. Align each sprite to that grid and majority-vote each texel
6. Build one family palette: merge near-duplicate colors, cap with `--colors`
7. Remove 1px specks
8. Pad every icon to the same square
9. Write `{name}.png`, `{name}.svg`, `{name}@8x.png`, and `palette.json`

`--logical 0` (default) keeps the detected aspect. `--logical 32` forces a square resample and usually crushes detail. `--texel 16` overrides detection if a sheet is unusually chunky.

## Prompt must include

- Flat chroma fill, exact grid
- One closed 2px `#00FFFF` box around each sprite (2 canvas pixels, not 2 texels)
- True pixel art, nearest-neighbor squares, no anti-aliasing, no gradients
- One shared integer grid and one shared palette
- No labels

## How to use the files

- Prefer the SVG in web/app UI. It scales without blur.
- If you use the PNG, set `image-rendering: pixelated` and scale by integers only.
- Never bilinear-scale the logical PNG.

## Commands

```bash
python3 .cursor/skills/magic-assets/run.py pixel --count 4 --colors 12
python3 .cursor/skills/magic-assets/run.py pixel --skip-generate --sheet output/pixel-sheet-4-xxx/sheet.png --count 4
python3 .cursor/skills/magic-assets/run.py test pixel
```

## Brief example

```json
{
  "count": 4,
  "names": ["heart", "star", "coin", "potion"],
  "logical": 0,
  "colors": 12,
  "quality": "medium"
}
```
