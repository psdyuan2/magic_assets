# Script FX path

CSS and a tiny JS helper for motion that does **not** need new pixels. Scale, translate, filter, mask, flash. Never call image2 on this path.

## Use when

- Pulse, bob, shake, fade, pop-in, hit flash, hue shift, clip wipe
- A static PNG / SVG / pixel cycle already exists
- The body silhouette does not have to change

If limbs, squash drawings, or a walk must be redrawn, switch to [pixel-anim.md](pixel-anim.md).

## Do not generate

| Ask | Do this instead |
| --- | --- |
| Icon breathing | `pulse` or `squash` |
| Float / hover | `bob` |
| Hit jar | `shake` + optional `flash` |
| Spawn / 闪出 | `pop`, `fade-in`, or `reveal` |
| Card or icon unveil | `wipe-right` / `wipe-up` |
| Status tint | `hue` or `glow` |

One effect per element. Stack by wrapping:

```html
<span class="ma-fx" data-ma-fx="bob" data-ma-trigger="loop">
  <img class="pixel-cycle" alt="">
</span>
```

## Catalog

| Family | Ids |
| --- | --- |
| 大小 scale | `pulse`, `squash` |
| 位置 position | `bob`, `shake`, `slide-up` |
| 滤镜 filter | `glow`, `hue` |
| 蒙版 mask | `wipe-right`, `wipe-up`, `reveal` |
| 闪出 flash | `flash`, `pop`, `fade-in` |

Only `transform`, `opacity`, `filter`, and `clip-path` are animated. Layout properties are banned. `prefers-reduced-motion` kills the motion and shows the rest pose.

## Triggers

`data-ma-trigger`:

- `loop` — start immediately, infinite
- `mount` — play once on bind
- `click` / `hover` — replay from the start
- `inview` — first time 40% visible

Replay from JS: `MagicFx.play(el)`.

Tune with variables: `--ma-duration`, `--ma-delay`, `--ma-scale`, `--ma-distance`, `--ma-flash`.

## Pipeline

1. Confirm the motion is scriptable. If not, stop and use pixel-anim.
2. Pick ids from the catalog. Do not invent a new keyframe in the page.
3. Run the pack writer from the repo root.
4. Copy `fx.css` and `fx.js` into the app. Wire `data-ma-fx` on a wrapper, not on a layout box.
5. Open `preview.html` and replay each picked effect. Then check the real page, including reduced motion.

## Commands

```bash
python3 magic-assets/run.py fx
python3 magic-assets/run.py fx --effects pulse,bob,flash,pop
python3 magic-assets/run.py test fx
```

## Brief example

```json
{
  "effects": ["pop", "flash", "bob"]
}
```

## How to use the files

- `fx.css` / `fx.js` are the product
- `preview.html` is the bench, not an app page
- Keep `manifest.json` so later pages reuse the same ids and durations
