# Mixed path

One hero plus smaller matching objects on a single sheet. Cut by cyan guide boxes first; fall back to connected blobs if the boxes are missing.

## Use when

- A large product / character / device must sit next to smaller glyphs
- Pixel budgets differ (hero ~2.5×–3× the satellites)
- Equal cells would waste the hero or crush the small icons

If every item can share one cell size, use the grid path instead.

## Defaults

- Size `2048×2048`, quality `high`
- `--hero` is the large object
- `--small` is a comma list, stacked on the right

## Prompt must include

- "This is NOT a scene" — no desk, shelf, room, hands, or shared platform
- Hero on the left (~58%), small column on the right (~42%)
- ≥90px chroma gap between every object
- One closed 2px `#00FFFF` box around every object, including the hero
- Objects never touch or share a shadow
- One style family; small objects stay chunky, not tiny copies of the hero
- No labels on the artwork

Brand lookalikes are a known failure. Say "invent the design, do not copy [brands]" when that matters.

## Split

Prefer the cyan boxes: largest interior is the hero, remaining boxes keep reading order. If the expected count is missing, fall back to chroma key plus 8-connected blobs. Thin bridges (mic boom, joystick shaft) can still snap on the blob path — inspect those first.

If only the cut is wrong, re-run:

```bash
python3 .cursor/skills/magic-assets/run.py mixed --skip-generate --sheet output/mixed-sheet-xxx/sheet.png --hero console-front --small joystick,gamepad,cartridge,dpad,headset
```

## Brief example

```json
{
  "hero": "original handheld console, front view, no real-world brand",
  "small": ["joystick", "gamepad", "cartridge", "dpad", "headset"],
  "style": "Soft 3D clay collectible render. Cream, coral, teal, navy, graphite.",
  "quality": "high",
  "size": "2048x2048"
}
```
