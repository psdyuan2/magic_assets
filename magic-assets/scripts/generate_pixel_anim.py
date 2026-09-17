#!/usr/bin/env python3
"""Pixel animation cycle: one character, consecutive frames, then GIF/strip."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from animate import (
    auto_preview_scale,
    expand_holds,
    expand_loop,
    jitter_report,
    parse_holds,
    render_cycle_preview,
    stabilize_x,
    write_anim_json,
    write_cycle_css,
    write_frame_files,
    write_pixel_gif,
    write_preview_gif,
    write_strip,
)
from common import DEFAULT_CHROMA, DEFAULT_GUIDE, QUALITY_CHOICES, execute_run, guide_box_rules, load_brief
from pixelize import cut_anim_frames, pixelize_sheet_frames

ANIM_LAYOUTS = {
    4: (2, 2, "1024x1024"),
}

PIXEL_ANIM_STYLE = (
    "True pixel art sprites, not a filtered photo. Hard nearest-neighbor squares only. "
    "No anti-aliasing, no blur, no gradients, no motion blur, no smear frames. "
    "Limited shared palette: cream, coral, muted teal, navy, graphite. "
    "Never use magenta, electric cyan, the chroma-key color, or the guide-box color."
)

DEFAULT_CHARACTER = (
    "One small round slime: cream body, coral blush, two navy dot eyes, no limbs, no face change."
)

DEFAULT_ACTIONS = {
    "idle": [
        "rest pose, compact and centered",
        "squash down a little, wider and shorter",
        "stretch up a little, taller and narrower",
        "settle back toward the rest pose so the loop can restart",
    ],
    "walk": [
        "in-place walk, left contact, body lowest",
        "passing pose, body highest, legs together",
        "in-place walk, right contact, body lowest",
        "passing pose, body highest, legs together, ready to loop",
    ],
    "bounce": [
        "crouch, ready to hop, feet on the floor",
        "compress, much wider",
        "extend upward but feet still near the same floor",
        "land and recover toward the crouch so the loop restarts",
    ],
}


def resolve_beats(action: str, beats: list[str], frames: int) -> list[str]:
    if beats:
        if len(beats) != frames:
            sys.exit(f"pixel-anim expects {frames} beats, got {len(beats)}")
        return beats
    preset = DEFAULT_ACTIONS.get(action)
    if not preset:
        sys.exit("unknown --action; pass --beats or use idle / walk / bounce")
    return list(preset)


def build_prompt(
    *,
    chroma: str,
    character: str,
    action: str,
    beats: list[str],
    style: str,
    sprite: int,
    cols: int,
    rows: int,
) -> str:
    frames = len(beats)
    labeled = "\n".join(f"{index}. {beat}" for index, beat in enumerate(beats, start=1))
    return f"""Create ONE pixel-art animation sprite sheet.

THIS SHEET IS THE FINAL ART. A local script will crop inside the {frames} {DEFAULT_GUIDE} boxes, then remove those strokes and {chroma}.
It will not redraw, sharpen, shrink, or quantize the sprites. Paint the finished look here.

THIS IS A CONTINUOUS ANIMATION, NOT A SET OF ICONS.
Exactly {frames} frames. All cells are consecutive in-betweens of ONE looping cycle of ONE character.

CHARACTER — identical in every frame:
{character}
Do not change costume, colors, body proportions, facing, or camera.

ACTION:
{action} as a seamless loop. Frame {frames} must read back into frame 1.

SIZE — paint this in the artwork, do not leave it for later:
- Each sprite is a {sprite}×{sprite} texel character.
- Enlarge those texels with nearest-neighbor so each texel is a clearly visible square.
- Same scale in every cell. The character should fill most of the cell, about 70%.

LAYOUT — follow exactly:
- Entire canvas is a perfectly flat, even fill of {chroma}. No scene, no paper, no desk.
- Strict {cols} columns × {rows} rows. Every cell is the same size.
- 16px even gutter of the same {chroma} between cells. No captions, no numbers.
- Each cell contains exactly the same character.
- Plant the feet on the SAME invisible baseline in every cell (same distance from the cell bottom).
- Keep the same horizontal center. Only the described motion changes.

{guide_box_rules(chroma, frames, DEFAULT_GUIDE)}

PIXEL RULES:
- Every edge is a hard pixel stair. No anti-aliasing, no blur, no gradients, no motion blur, no smear frames.
- One shared integer pixel grid and one shared palette for all {frames} frames.
- {style}

TEMPORAL ORDER, left-to-right, top-to-bottom:
{labeled}

Background must stay a single flat {chroma}.
"""


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Pixel animation cycle via image2")
    parser.add_argument("--frames", type=int, choices=sorted(ANIM_LAYOUTS), default=4)
    parser.add_argument("--character", default="")
    parser.add_argument("--action", default="idle")
    parser.add_argument("--beats", default="", help="comma-separated per-frame motion notes")
    parser.add_argument("--style", default="")
    parser.add_argument("--sprite", type=int, default=32, help="prompt size lock in texels")
    parser.add_argument("--snap", action="store_true", help="optional hard texel snap; default only cuts the sheet")
    parser.add_argument("--texel", type=int, default=0)
    parser.add_argument("--colors", type=int, default=12)
    parser.add_argument("--merge-distance", type=float, default=22)
    parser.add_argument("--register", choices=("stage", "bottom-center", "center"), default="stage")
    parser.add_argument("--frame-ms", type=int, default=140)
    parser.add_argument("--holds", default="", help="per-source-frame repeats, e.g. 2,1,1,1")
    parser.add_argument("--loop", choices=("cycle", "pingpong"), default="cycle")
    parser.add_argument("--stabilize-x", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--preview-scale", type=int, default=0, help="0 = auto from frame size")
    parser.add_argument("--quality", choices=QUALITY_CHOICES, default="medium")
    parser.add_argument("--size", default="")
    parser.add_argument("--chroma", default=DEFAULT_CHROMA)
    parser.add_argument("--brief", default="")
    parser.add_argument("--prompt-file", default="")
    parser.add_argument("--out-dir", default="output")
    parser.add_argument("--skip-generate", action="store_true")
    parser.add_argument("--sheet", default="")
    args = parser.parse_args(argv)

    brief = load_brief(args.brief)
    frames = int(brief.get("frames") or args.frames)
    if frames not in ANIM_LAYOUTS:
        sys.exit("pixel-anim v1 only supports 4 frames on one 1024 sheet")
    sprite = int(brief.get("sprite") or args.sprite)
    texel = int(brief.get("texel") or args.texel)
    colors = int(brief.get("colors") or args.colors)
    merge_distance = float(brief.get("merge_distance") or args.merge_distance)
    register = str(brief.get("register") or args.register)
    frame_ms = int(brief.get("frame_ms") or args.frame_ms)
    loop = str(brief.get("loop") or args.loop)
    stabilize = bool(brief["stabilize_x"]) if "stabilize_x" in brief else args.stabilize_x
    snap = bool(brief.get("snap")) if "snap" in brief else args.snap
    preview_scale_flag = int(brief.get("preview_scale") if brief.get("preview_scale") is not None else args.preview_scale)
    if sprite < 16 or sprite > 48:
        sys.exit("--sprite must be 16-48 so one 1024 sheet can hold 4 readable frames")
    if texel < 0 or texel > 64:
        sys.exit("--texel must be 0 (auto) or 4-64")
    if colors < 2 or colors > 32:
        sys.exit("--colors must be between 2 and 32")
    if frame_ms < 40 or frame_ms > 1000:
        sys.exit("--frame-ms must be 40-1000")
    if preview_scale_flag < 0 or preview_scale_flag > 16:
        sys.exit("--preview-scale must be 0 (auto) or 1-16")
    try:
        holds = parse_holds(str(brief.get("holds") or args.holds), frames)
    except ValueError as error:
        sys.exit(str(error))

    character = args.character or brief.get("character") or DEFAULT_CHARACTER
    action = args.action or brief.get("action") or "idle"
    raw_beats = [part.strip() for part in args.beats.split(",") if part.strip()]
    beats = raw_beats or [str(item) for item in brief.get("beats") or []]
    beats = resolve_beats(action, beats, frames)
    style = args.style or brief.get("style") or PIXEL_ANIM_STYLE
    chroma = args.chroma if args.chroma != DEFAULT_CHROMA else brief.get("chroma") or args.chroma
    quality = brief.get("quality") or args.quality
    cols, rows, default_size = ANIM_LAYOUTS[frames]
    size = args.size or brief.get("size") or default_size
    prompt = (
        Path(args.prompt_file).read_text(encoding="utf-8")
        if args.prompt_file
        else build_prompt(
            chroma=chroma,
            character=character,
            action=action,
            beats=beats,
            style=style,
            sprite=sprite,
            cols=cols,
            rows=rows,
        )
    )

    def split(sheet, sampled, dest_dir):
        if snap:
            frames, meta = pixelize_sheet_frames(
                sheet,
                cols=cols,
                rows=rows,
                chroma=sampled,
                colors=colors,
                texel=texel,
                merge_distance=merge_distance,
                register=register,
            )
        else:
            frames, meta = cut_anim_frames(
                sheet,
                cols=cols,
                rows=rows,
                chroma=sampled,
                register=register,
            )
        shifts: list[int] = []
        if stabilize:
            frames, shifts = stabilize_x(frames)
        jitter = jitter_report(frames)
        playable = expand_loop(expand_holds(frames, holds), loop)
        preview_scale = preview_scale_flag or auto_preview_scale(playable[0].size)
        written, records = write_frame_files(
            frames,
            dest_dir,
            action=action,
            preview_scale=preview_scale,
            write_svg=snap,
        )
        strip_path = dest_dir / "strip.png"
        gif_path = dest_dir / "cycle.gif"
        css_path = dest_dir / "cycle.css"
        anim_path = dest_dir / "anim.json"
        preview_path = dest_dir / "preview.html"
        write_strip(playable, strip_path)
        write_pixel_gif(playable, gif_path, frame_ms=frame_ms)
        extra_gif: list = []
        preview_gif_name = gif_path.name
        if preview_scale > 1:
            preview_gif = dest_dir / f"cycle@{preview_scale}x.gif"
            write_preview_gif(playable, preview_gif, scale=preview_scale, frame_ms=frame_ms)
            extra_gif.append(preview_gif)
            preview_gif_name = preview_gif.name
        write_cycle_css(
            css_path,
            strip_name=strip_path.name,
            frame_size=playable[0].size,
            frames=len(playable),
            frame_ms=frame_ms,
        )
        preview_path.write_text(
            render_cycle_preview(
                action=action,
                frame_size=playable[0].size,
                playable_frames=len(playable),
                frame_ms=frame_ms,
                preview_scale=preview_scale,
                records=records,
                jitter=jitter,
            ),
            encoding="utf-8",
        )
        payload = {
            **meta,
            "kind": "pixel-cycle",
            "cut": "snap" if snap else meta.get("cut", "light"),
            "refine": "snap" if snap else "light",
            "character": character,
            "action": action,
            "beats": beats,
            "frames": len(frames),
            "playable_frames": len(playable),
            "frame_ms": frame_ms,
            "holds": holds,
            "loop": loop,
            "stabilize_x": shifts,
            "jitter": jitter,
            "sprite": sprite,
            "strip": strip_path.name,
            "gif": gif_path.name,
            "preview_gif": preview_gif_name,
            "css": css_path.name,
            "preview": preview_path.name,
        }
        write_anim_json(anim_path, payload)
        written.extend([strip_path, gif_path, *extra_gif, css_path, anim_path, preview_path])
        if records:
            records[0]["sheet"] = payload
        if jitter["x_span"] > 2:
            print(f"warning: horizontal jitter {jitter['x_span']}px; try --register bottom-center")
        print(
            f"pixel-anim cut={'snap' if snap else 'light'} register={register} "
            f"size={meta['family_size']} gif={gif_path.name} {frame_ms}ms {loop} "
            f"jitter_x={jitter['x_span']} feet={jitter['feet_span']}"
        )
        return written, records

    execute_run(
        mode="pixel-anim",
        prompt=prompt,
        size=size,
        quality=quality,
        chroma=chroma,
        out_prefix=f"pixel-anim-{action}-{frames}",
        out_dir_flag=args.out_dir,
        skip_generate=args.skip_generate,
        sheet_path=args.sheet,
        extra_manifest={
            "grid": {"cols": cols, "rows": rows, "size": size},
            "character": character,
            "action": action,
            "beats": beats,
            "style": style,
            "sprite": sprite,
            "texel": texel,
            "colors": colors,
            "register": register,
            "snap": snap,
            "frame_ms": frame_ms,
            "holds": holds,
            "loop": loop,
            "stabilize_x": stabilize,
        },
        split=split,
    )


if __name__ == "__main__":
    main()
