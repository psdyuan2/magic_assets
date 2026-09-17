"""Assemble pixel frames into a strip, GIF, and CSS steps cycle."""

from __future__ import annotations

import json
from pathlib import Path

from PIL import Image

from common import slug as _slug
from pixelize import preview_nearest, write_pixel_svg

# Sprites are banned from magenta; GIF index 0 uses it so black outlines stay opaque.
GIF_TRANSPARENT = (255, 0, 255)


def write_strip(frames: list[Image.Image], dest: Path) -> Image.Image:
    if not frames:
        raise ValueError("no frames to strip")
    width, height = frames[0].size
    strip = Image.new("RGBA", (width * len(frames), height), (0, 0, 0, 0))
    for index, frame in enumerate(frames):
        if frame.size != (width, height):
            raise ValueError("animation frames must share one size")
        strip.paste(frame, (index * width, 0), frame)
    dest.parent.mkdir(parents=True, exist_ok=True)
    strip.save(dest)
    return strip


def _flatten_on_chroma(frame: Image.Image) -> Image.Image:
    rgb = Image.new("RGB", frame.size, GIF_TRANSPARENT)
    rgba = frame.convert("RGBA")
    rgb.paste(rgba.convert("RGB"), mask=rgba.getchannel("A"))
    return rgb


def _palette_index(palette: list[int], color: tuple[int, int, int]) -> int:
    best = 0
    best_dist = 10**9
    for index in range(len(palette) // 3):
        red, green, blue = palette[index * 3], palette[index * 3 + 1], palette[index * 3 + 2]
        dist = (red - color[0]) ** 2 + (green - color[1]) ** 2 + (blue - color[2]) ** 2
        if dist < best_dist:
            best_dist = dist
            best = index
            if dist == 0:
                break
    return best


def write_pixel_gif(
    frames: list[Image.Image],
    dest: Path,
    *,
    frame_ms: int = 140,
    loop: int = 0,
) -> None:
    if not frames:
        raise ValueError("no frames for gif")
    flats = [_flatten_on_chroma(frame) for frame in frames]
    width = sum(frame.width for frame in flats)
    height = max(frame.height for frame in flats)
    atlas = Image.new("RGB", (width, height), GIF_TRANSPARENT)
    left = 0
    for flat in flats:
        atlas.paste(flat, (left, 0))
        left += flat.width
    shared = atlas.quantize(colors=255, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
    palette = shared.getpalette() or []
    transparent = _palette_index(palette, GIF_TRANSPARENT)

    indexed: list[Image.Image] = []
    for flat in flats:
        page = flat.quantize(palette=shared, dither=Image.Dither.NONE)
        page.info["transparency"] = transparent
        indexed.append(page)

    dest.parent.mkdir(parents=True, exist_ok=True)
    indexed[0].save(
        dest,
        save_all=True,
        append_images=indexed[1:],
        duration=frame_ms,
        loop=loop,
        disposal=2,
        transparency=transparent,
        optimize=False,
    )


def auto_preview_scale(frame_size: tuple[int, int]) -> int:
    side = max(frame_size)
    if side <= 48:
        return 8
    if side <= 160:
        return 2
    return 1


def write_preview_gif(
    frames: list[Image.Image],
    dest: Path,
    *,
    scale: int = 8,
    frame_ms: int = 140,
    loop: int = 0,
) -> None:
    write_pixel_gif(
        [preview_nearest(frame, scale) for frame in frames],
        dest,
        frame_ms=frame_ms,
        loop=loop,
    )


def expand_holds(frames: list[Image.Image], holds: list[int] | None) -> list[Image.Image]:
    if not holds:
        return frames
    if len(holds) != len(frames):
        raise ValueError(f"holds length {len(holds)} != frames {len(frames)}")
    playable: list[Image.Image] = []
    for frame, hold in zip(frames, holds):
        playable.extend([frame] * max(1, hold))
    return playable


def parse_holds(raw: str, frame_count: int) -> list[int]:
    if not raw.strip():
        return [1] * frame_count
    holds = [int(part.strip()) for part in raw.split(",") if part.strip()]
    if len(holds) != frame_count:
        raise ValueError(f"holds expects {frame_count} ints, got {len(holds)}")
    if any(hold < 1 or hold > 8 for hold in holds):
        raise ValueError("each hold must be 1-8")
    return holds


def opaque_center_x(image: Image.Image) -> float:
    box = image.getbbox()
    if not box:
        return image.width / 2
    return (box[0] + box[2]) / 2


def stabilize_x(frames: list[Image.Image]) -> tuple[list[Image.Image], list[int]]:
    if not frames:
        return [], []
    centers = [opaque_center_x(frame) for frame in frames]
    target = sorted(centers)[len(centers) // 2]
    shifted: list[Image.Image] = []
    deltas: list[int] = []
    for frame, center in zip(frames, centers):
        delta = int(round(target - center))
        deltas.append(delta)
        if delta == 0:
            shifted.append(frame)
            continue
        moved = Image.new("RGBA", frame.size, (0, 0, 0, 0))
        moved.paste(frame, (delta, 0), frame)
        shifted.append(moved)
    return shifted, deltas


def jitter_report(frames: list[Image.Image]) -> dict:
    boxes = [frame.getbbox() for frame in frames]
    valid = [box for box in boxes if box]
    if not valid:
        return {"x_span": 0, "y_span": 0, "feet_span": 0}
    xs = [(box[0] + box[2]) / 2 for box in valid]
    ys = [(box[1] + box[3]) / 2 for box in valid]
    feet = [box[3] for box in valid]
    return {
        "x_span": round(max(xs) - min(xs), 2),
        "y_span": round(max(ys) - min(ys), 2),
        "feet_span": max(feet) - min(feet),
    }


def write_cycle_css(
    dest: Path,
    *,
    strip_name: str,
    frame_size: tuple[int, int],
    frames: int,
    frame_ms: int,
    class_name: str = "pixel-cycle",
) -> None:
    width, height = frame_size
    duration_ms = frame_ms * frames
    dest.write_text(
        f""".{class_name} {{
  width: {width}px;
  height: {height}px;
  background: url("{strip_name}") 0 0 no-repeat;
  background-size: {width * frames}px {height}px;
  image-rendering: pixelated;
  image-rendering: crisp-edges;
  animation: {class_name}-steps {duration_ms}ms steps({frames}) infinite;
}}
@keyframes {class_name}-steps {{
  to {{ background-position: -{width * frames}px 0; }}
}}
""",
        encoding="utf-8",
    )


def write_anim_json(dest: Path, payload: dict) -> None:
    dest.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def expand_loop(frames: list[Image.Image], mode: str) -> list[Image.Image]:
    if mode == "pingpong" and len(frames) > 2:
        return frames + frames[-2:0:-1]
    return frames


def write_frame_files(
    frames: list[Image.Image],
    dest_dir: Path,
    *,
    action: str,
    preview_scale: int = 8,
    write_svg: bool = False,
) -> tuple[list[Path], list[dict]]:
    dest_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    records: list[dict] = []
    stem = _slug(action)
    for index, frame in enumerate(frames, start=1):
        name = f"{index:02d}-{stem}"
        png_path = dest_dir / f"{name}.png"
        preview_path = dest_dir / f"{name}@{preview_scale}x.png"
        frame.save(png_path)
        written.append(png_path)
        record = {
            "name": name,
            "png": png_path.name,
            "preview": preview_path.name,
            "logical": [frame.width, frame.height],
            "index": index,
        }
        if write_svg:
            svg_path = dest_dir / f"{name}.svg"
            write_pixel_svg(frame, svg_path)
            written.append(svg_path)
            record["svg"] = svg_path.name
        if preview_scale > 1:
            preview_nearest(frame, preview_scale).save(preview_path)
            written.append(preview_path)
        else:
            record["preview"] = png_path.name
        records.append(record)
    return written, records


def render_cycle_preview(
    *,
    action: str,
    frame_size: tuple[int, int],
    playable_frames: int,
    frame_ms: int,
    preview_scale: int,
    records: list[dict],
    jitter: dict,
) -> str:
    width, height = frame_size
    duration_ms = frame_ms * playable_frames
    gif_name = f"cycle@{preview_scale}x.gif" if preview_scale > 1 else "cycle.gif"
    thumb_w = min(width, 180)
    thumb_h = max(1, int(height * thumb_w / width)) if width else height
    thumbs = "\n".join(
        f'        <img src="{item["preview"]}" width="{thumb_w}" height="{thumb_h}" alt="{item["name"]}">'
        for item in records
    )
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>pixel-anim {action}</title>
  <link rel="stylesheet" href="cycle.css">
  <style>
    :root {{ --paper: #f3e6cf; --lamp: #e39b4b; --stage: #1f1813; }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      color: var(--paper);
      background: #15110e;
      font: 15px/1.45 "Iowan Old Style", Palatino, serif;
    }}
    main {{ width: min(960px, calc(100% - 40px)); margin: 36px auto 80px; }}
    h1 {{ font-size: 32px; letter-spacing: -0.03em; margin: 0 0 8px; }}
    .lead {{ max-width: 48ch; color: color-mix(in srgb, var(--paper) 72%, #8a7460); }}
    .row {{ display: flex; flex-wrap: wrap; gap: 20px; margin: 28px 0; }}
    .stage {{
      padding: 14px;
      background: color-mix(in srgb, var(--stage) 88%, #7a4d32);
      border: 1px solid color-mix(in srgb, var(--lamp) 28%, #3a2a1c);
    }}
    .stage h2 {{
      margin: 0 0 12px;
      font-size: 12px;
      letter-spacing: 0.14em;
      text-transform: uppercase;
      color: var(--lamp);
    }}
    .zoom {{
      image-rendering: pixelated;
      image-rendering: crisp-edges;
    }}
    .css-box {{
      width: {width * preview_scale}px;
      height: {height * preview_scale}px;
    }}
    .css-box .pixel-cycle {{
      transform: scale({preview_scale});
      transform-origin: top left;
    }}
    .film {{ display: flex; gap: 8px; flex-wrap: wrap; }}
    .film img {{ image-rendering: pixelated; background: #241910; }}
    code {{ color: var(--lamp); }}
  </style>
</head>
<body>
  <main>
    <h1>{action} cycle</h1>
    <p class="lead">左边是原表切格后的 GIF，右边是同一条 strip 的 CSS steps。抖动 x={jitter.get("x_span", 0)} / 脚底={jitter.get("feet_span", 0)}。</p>
    <div class="row">
      <section class="stage">
        <h2>GIF @{preview_scale}x</h2>
        <img class="zoom" src="{gif_name}" width="{width * preview_scale}" height="{height * preview_scale}" alt="gif">
      </section>
      <section class="stage">
        <h2>CSS steps {duration_ms}ms</h2>
        <div class="css-box"><div class="pixel-cycle"></div></div>
      </section>
    </div>
    <section class="stage">
      <h2>frames</h2>
      <div class="film">
{thumbs}
      </div>
    </section>
    <p><a href="cycle.gif">cycle.gif</a> · <a href="strip.png">strip.png</a> · <a href="anim.json">anim.json</a></p>
  </main>
</body>
</html>
"""
