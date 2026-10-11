# Grid path

Equal-scale icon family. One sheet, one cell size, then cut by cell.

## Use when

- Nav, toolbar, settings, empty-state glyphs
- Every asset should be the same pixel budget
- You can name 4, 8, or 16 items

If one item must be a large product shot, switch to the mixed path.

## Counts

| Count | Grid | Size |
| --- | --- | --- |
| 4 | 2×2 | 1024×1024 |
| 8 | 4×2 | 2048×1024 |
| 16 | 4×4 | 2048×2048 |

`--names` length must match `--count`. Quality default is `medium`.

## Prompt must include

- Flat chroma fill, no scene
- Exact `cols × rows`, equal cells, ~12px chroma gutter
- One centered icon per cell, ~70% of the cell
- One closed 2px `#00FFFF` box around each icon, outside the artwork
- One style paragraph for the whole family
- Named icons in reading order
- No labels on the artwork

The script writes this. Override with `--style` or `--prompt-file` when the UI has a different look.

## Split

Shared post-process looks for the cyan boxes first and crops their interiors. If the count does not match, it falls back to equal cells. Then it samples the real background (often `#F803E4`, not exact `#FF00FF`), keys magenta and leftover cyan, and trims alpha.

## Brief example

```json
{
  "count": 8,
  "names": ["home", "search", "user", "settings", "bell", "chart", "folder", "plus"],
  "style": "Soft 3D clay SaaS icons. Cream, coral, teal, navy.",
  "quality": "medium"
}
```
