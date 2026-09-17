"""Snap raster icons to a logical pixel grid and emit crisp SVG rects."""

from __future__ import annotations

import json
import math
from collections import Counter
from pathlib import Path

from PIL import Image

from common import key_sheet, sheet_cells, slug

ALPHA_CUT = 40
TEXEL_MIN = 12
TEXEL_MAX = 32
MERGE_DISTANCE = 22


def pixel_key(pixel: tuple[int, ...], bucket: int = 10) -> tuple | None:
    red, green, blue, alpha = pixel
    if alpha < ALPHA_CUT:
        return None
    return (red // bucket, green // bucket, blue // bucket)


def rgb_distance(left: tuple[int, int, int], right: tuple[int, int, int]) -> float:
    return math.sqrt(sum((a - b) ** 2 for a, b in zip(left, right)))


def detect_texel(image: Image.Image) -> int:
    box = image.getbbox()
    if not box:
        return 16
    left, top, right, bottom = box
    sample = image.crop((left, top, min(right, left + 320), min(bottom, top + 320)))
    ranked: list[tuple[float, float, int]] = []
    for texel in range(TEXEL_MIN, TEXEL_MAX + 1):
        offset_x, offset_y = left % texel, top % texel
        uniform, unique = block_stats(sample, texel, offset_x, offset_y)
        ranked.append((uniform, -unique, texel))
    ranked.sort(reverse=True)
    best_uniform = ranked[0][0]
    good = [item for item in ranked if item[0] >= best_uniform * 0.9]
    good.sort(key=lambda item: (abs(item[2] - 16), -item[0], item[1]))
    return good[0][2] if good else 16


def block_stats(image: Image.Image, texel: int, offset_x: int, offset_y: int) -> tuple[float, float]:
    width, height = image.size
    pixels = image.load()
    unique_sum = 0.0
    uniform = 0
    blocks = 0
    stride = max(texel, texel * 2 if image.width > 200 else texel)
    sample = max(1, texel // 4)
    for top in range(offset_y, height - texel + 1, stride):
        for left in range(offset_x, width - texel + 1, stride):
            keys = []
            transparent = 0
            total = 0
            for y in range(top, top + texel, sample):
                for x in range(left, left + texel, sample):
                    key = pixel_key(pixels[x, y], bucket=8)
                    total += 1
                    if key is None:
                        transparent += 1
                    else:
                        keys.append(key)
            if not keys or transparent > total * 0.7:
                continue
            unique = len(set(keys))
            unique_sum += unique
            if unique == 1:
                uniform += 1
            blocks += 1
    if not blocks:
        return 0.0, 9.0
    return uniform / blocks, unique_sum / blocks


def detect_phase(image: Image.Image, texel: int) -> tuple[int, int]:
    box = image.getbbox()
    if not box:
        return 0, 0
    left, top, right, bottom = box
    sample = image.crop((left, top, min(right, left + 256), min(bottom, top + 256)))
    base_x, base_y = left % texel, top % texel
    best = (base_x, base_y)
    best_score = float("inf")
    for dx in range(-2, 3):
        for dy in range(-2, 3):
            offset_x = (base_x + dx) % texel
            offset_y = (base_y + dy) % texel
            _uniform, unique = block_stats(sample, texel, offset_x, offset_y)
            if unique < best_score:
                best_score = unique
                best = (offset_x, offset_y)
    return best


def detect_grid(image: Image.Image) -> tuple[int, int, int]:
    """Return (texel, phase_x, phase_y) for a chroma-keyed sheet or cell."""
    texel = detect_texel(image)
    phase_x, phase_y = detect_phase(image, texel)
    return texel, phase_x, phase_y


def align_box(
    box: tuple[int, int, int, int],
    *,
    texel: int,
    phase: tuple[int, int],
    origin: tuple[int, int],
    limits: tuple[int, int],
) -> tuple[int, int, int, int]:
    left, top, right, bottom = box
    phase_x, phase_y = phase
    origin_x, origin_y = origin
    sheet_left = origin_x + left
    sheet_top = origin_y + top
    sheet_right = origin_x + right
    sheet_bottom = origin_y + bottom
    aligned_left = phase_x + ((sheet_left - phase_x) // texel) * texel
    aligned_top = phase_y + ((sheet_top - phase_y) // texel) * texel
    aligned_right = phase_x + ((sheet_right - phase_x + texel - 1) // texel) * texel
    aligned_bottom = phase_y + ((sheet_bottom - phase_y + texel - 1) // texel) * texel
    local_left = max(0, aligned_left - origin_x)
    local_top = max(0, aligned_top - origin_y)
    local_right = min(limits[0], aligned_right - origin_x)
    local_bottom = min(limits[1], aligned_bottom - origin_y)
    local_right -= (local_right - local_left) % texel
    local_bottom -= (local_bottom - local_top) % texel
    if local_right - local_left < texel or local_bottom - local_top < texel:
        return box
    return local_left, local_top, local_right, local_bottom


def majority_downscale(image: Image.Image, out_w: int, out_h: int) -> Image.Image:
    source = image.convert("RGBA")
    width, height = source.size
    if width < 1 or height < 1 or out_w < 1 or out_h < 1:
        return Image.new("RGBA", (max(1, out_w), max(1, out_h)), (0, 0, 0, 0))

    src = source.load()
    out = Image.new("RGBA", (out_w, out_h), (0, 0, 0, 0))
    dst = out.load()
    for y in range(out_h):
        y0 = int(y * height / out_h)
        y1 = max(y0 + 1, int((y + 1) * height / out_h))
        for x in range(out_w):
            x0 = int(x * width / out_w)
            x1 = max(x0 + 1, int((x + 1) * width / out_w))
            votes: Counter[tuple[int, int, int]] = Counter()
            transparent = 0
            total = 0
            for yy in range(y0, y1):
                for xx in range(x0, x1):
                    red, green, blue, alpha = src[xx, yy]
                    total += 1
                    if alpha < ALPHA_CUT:
                        transparent += 1
                    else:
                        votes[(red, green, blue)] += 1
            if not votes or transparent > total * 0.55:
                continue
            color, _count = votes.most_common(1)[0]
            dst[x, y] = (*color, 255)
    return out


def snap_aligned(
    keyed: Image.Image,
    *,
    texel: int,
    phase: tuple[int, int],
    origin: tuple[int, int],
) -> Image.Image:
    box = keyed.getbbox()
    if not box:
        return Image.new("RGBA", (8, 8), (0, 0, 0, 0))
    left, top, right, bottom = align_box(
        box,
        texel=texel,
        phase=phase,
        origin=origin,
        limits=keyed.size,
    )
    crop = keyed.crop((left, top, right, bottom))
    if crop.width >= texel and crop.height >= texel and crop.width % texel == 0 and crop.height % texel == 0:
        return majority_downscale(crop, crop.width // texel, crop.height // texel)
    out_w = max(8, round(crop.width / texel))
    out_h = max(8, round(crop.height / texel))
    return majority_downscale(crop, out_w, out_h)


def collect_colors(image: Image.Image) -> Counter[tuple[int, int, int]]:
    counts: Counter[tuple[int, int, int]] = Counter()
    for red, green, blue, alpha in image.getdata():
        if alpha >= ALPHA_CUT:
            counts[(red, green, blue)] += 1
    return counts


def merge_palette(
    counts: Counter[tuple[int, int, int]],
    *,
    max_colors: int,
    min_distance: float = MERGE_DISTANCE,
) -> dict[tuple[int, int, int], tuple[int, int, int]]:
    if len(counts) > 40:
        colors = list(counts)
        chart = Image.new("RGB", (len(colors), 1))
        chart.putdata(colors)
        quantized = chart.quantize(colors=max_colors, method=Image.Quantize.MEDIANCUT).convert("RGB")
        first_pass = {color: quantized.getpixel((index, 0)) for index, color in enumerate(colors)}
        reduced_counts: Counter[tuple[int, int, int]] = Counter()
        for color, count in counts.items():
            reduced_counts[first_pass[color]] += count
        second_pass = merge_palette(reduced_counts, max_colors=max_colors, min_distance=min_distance)
        return {color: second_pass[first_pass[color]] for color in counts}

    entries = [[color, count] for color, count in counts.items()]
    mapping = {color: color for color in counts}

    def remap(source: tuple[int, int, int], dest: tuple[int, int, int]) -> None:
        for color, current in list(mapping.items()):
            if current == source:
                mapping[color] = dest

    while len(entries) > 1:
        best = float("inf")
        pair = None
        for i, (color_a, _count_a) in enumerate(entries):
            for j in range(i + 1, len(entries)):
                color_b, _count_b = entries[j]
                distance = rgb_distance(color_a, color_b)
                if distance < best:
                    best = distance
                    pair = (i, j)
        if pair is None:
            break
        if best > min_distance and len(entries) <= max_colors:
            break
        i, j = pair
        if entries[i][1] < entries[j][1]:
            i, j = j, i
        keep, drop = entries[i], entries[j]
        keep[1] += drop[1]
        remap(drop[0], keep[0])
        entries.pop(j)

    if len(entries) > max_colors:
        entries.sort(key=lambda item: item[1], reverse=True)
        kept = {color for color, _count in entries[:max_colors]}
        dropped = [color for color, _count in entries[max_colors:]]
        for color in dropped:
            nearest = min(kept, key=lambda other: rgb_distance(color, other))
            remap(color, nearest)
    return mapping


def apply_mapping(image: Image.Image, mapping: dict[tuple[int, int, int], tuple[int, int, int]]) -> Image.Image:
    out = Image.new("RGBA", image.size)
    mapped = []
    for red, green, blue, alpha in image.getdata():
        if alpha < ALPHA_CUT:
            mapped.append((0, 0, 0, 0))
        else:
            mapped.append((*mapping.get((red, green, blue), (red, green, blue)), 255))
    out.putdata(mapped)
    return out


def remove_specks(image: Image.Image) -> Image.Image:
    rgba = image.convert("RGBA")
    width, height = rgba.size
    src = list(rgba.getdata())

    def at(x: int, y: int) -> tuple[int, int, int, int]:
        return src[y * width + x]

    out = src[:]
    for y in range(height):
        for x in range(width):
            red, green, blue, alpha = at(x, y)
            if alpha < ALPHA_CUT:
                continue
            neighbors = []
            for nx, ny in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
                if 0 <= nx < width and 0 <= ny < height:
                    neighbors.append(at(nx, ny))
            same = sum(1 for nr, ng, nb, na in neighbors if na >= ALPHA_CUT and (nr, ng, nb) == (red, green, blue))
            if same:
                continue
            opaque = [(nr, ng, nb) for nr, ng, nb, na in neighbors if na >= ALPHA_CUT]
            if opaque:
                choice, _count = Counter(opaque).most_common(1)[0]
                out[y * width + x] = (*choice, 255)
            elif sum(1 for _n in neighbors if _n[3] < ALPHA_CUT) >= 3:
                out[y * width + x] = (0, 0, 0, 0)
    result = Image.new("RGBA", rgba.size)
    result.putdata(out)
    return result


def pad_square(image: Image.Image, side: int | None = None) -> Image.Image:
    target = side or max(image.width, image.height)
    if image.width == target and image.height == target:
        return image
    canvas = Image.new("RGBA", (target, target), (0, 0, 0, 0))
    canvas.paste(image, ((target - image.width) // 2, (target - image.height) // 2))
    return canvas


def snap_cell(cell: Image.Image, texel: int, phase: tuple[int, int]) -> Image.Image:
    """Downscale a whole cell so empty stage pixels stay in place."""
    phase_x, phase_y = phase
    width = ((cell.width - phase_x) // texel) * texel
    height = ((cell.height - phase_y) // texel) * texel
    if width < texel or height < texel:
        return snap_aligned(cell, texel=texel, phase=phase, origin=(0, 0))
    crop = cell.crop((phase_x, phase_y, phase_x + width, phase_y + height))
    return majority_downscale(crop, width // texel, height // texel)


def shared_trim(frames: list[Image.Image], margin: int = 1) -> list[Image.Image]:
    boxes = [frame.getbbox() for frame in frames]
    if not any(boxes):
        return frames
    left = min(box[0] for box in boxes if box)
    top = min(box[1] for box in boxes if box)
    right = max(box[2] for box in boxes if box)
    bottom = max(box[3] for box in boxes if box)
    left = max(0, left - margin)
    top = max(0, top - margin)
    right = min(frames[0].width, right + margin)
    bottom = min(frames[0].height, bottom + margin)
    return [frame.crop((left, top, right, bottom)) for frame in frames]


def pad_anchor(
    image: Image.Image,
    canvas: tuple[int, int],
    *,
    anchor: str = "bottom-center",
    margin: int = 1,
) -> Image.Image:
    canvas_w, canvas_h = canvas
    box = image.getbbox()
    out = Image.new("RGBA", (canvas_w, canvas_h), (0, 0, 0, 0))
    if not box:
        return out
    sprite = image.crop(box)
    width, height = sprite.size
    if anchor == "center":
        x = (canvas_w - width) // 2
        y = (canvas_h - height) // 2
    else:
        x = (canvas_w - width) // 2
        y = canvas_h - margin - height
    out.paste(sprite, (max(0, x), max(0, y)), sprite)
    return out


def align_frames(
    frames: list[Image.Image],
    *,
    register: str = "stage",
    margin: int = 1,
) -> tuple[list[Image.Image], tuple[int, int]]:
    if not frames:
        return [], (0, 0)
    if register == "stage":
        trimmed = shared_trim(frames, margin=margin)
        size = trimmed[0].size if trimmed else (0, 0)
        return trimmed, size
    boxes = [frame.getbbox() or (0, 0, 1, 1) for frame in frames]
    canvas = (
        max(box[2] - box[0] for box in boxes) + margin * 2,
        max(box[3] - box[1] for box in boxes) + margin * 2,
    )
    return [pad_anchor(frame, canvas, anchor=register, margin=margin) for frame in frames], canvas


def palette_hex(image: Image.Image) -> list[str]:
    colors = sorted(collect_colors(image))
    return [f"#{red:02X}{green:02X}{blue:02X}" for red, green, blue in colors]


def write_pixel_svg(image: Image.Image, dest: Path) -> None:
    width, height = image.size
    pixels = image.load()
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" height="{height}" shape-rendering="crispEdges">',
    ]
    for y in range(height):
        x = 0
        while x < width:
            red, green, blue, alpha = pixels[x, y]
            if alpha < ALPHA_CUT:
                x += 1
                continue
            end = x + 1
            while end < width and pixels[end, y] == (red, green, blue, alpha):
                end += 1
            parts.append(
                f'<rect x="{x}" y="{y}" width="{end - x}" height="1" fill="#{red:02X}{green:02X}{blue:02X}"/>'
            )
            x = end
    parts.append("</svg>\n")
    dest.write_text("\n".join(parts), encoding="utf-8")


def preview_nearest(image: Image.Image, scale: int = 8) -> Image.Image:
    return image.resize((image.width * scale, image.height * scale), Image.Resampling.NEAREST)


def pixelize_sheet_icons(
    sheet: Image.Image,
    *,
    cols: int,
    rows: int,
    chroma: tuple[int, int, int],
    logical: int,
    colors: int,
    texel: int = 0,
    merge_distance: float = MERGE_DISTANCE,
) -> tuple[list[Image.Image], dict]:
    keyed_sheet = key_sheet(sheet, chroma)
    detected_t, phase_x, phase_y = detect_grid(keyed_sheet)
    used_texel = texel or detected_t
    phase = (phase_x, phase_y)
    cells, cut_meta = sheet_cells(sheet, cols=cols, rows=rows, chroma=chroma)
    snapped: list[Image.Image] = []

    for cell in cells:
        if logical > 0:
            box = cell.getbbox() or (0, 0, cell.width, cell.height)
            icon = majority_downscale(cell.crop(box), logical, logical)
        else:
            local_phase = detect_phase(cell, used_texel)
            icon = snap_aligned(cell, texel=used_texel, phase=local_phase, origin=(0, 0))
        snapped.append(icon)

    combined = Counter()
    for icon in snapped:
        combined.update(collect_colors(icon))
    mapping = merge_palette(combined, max_colors=colors, min_distance=merge_distance)
    cleaned = [remove_specks(apply_mapping(icon, mapping)) for icon in snapped]
    family_side = max(max(icon.size) for icon in cleaned)
    padded = [pad_square(icon, family_side) for icon in cleaned]
    meta = {
        "detected_texel": detected_t,
        "texel": used_texel,
        "phase": [phase_x, phase_y],
        "logical_forced": logical,
        "family_size": [family_side, family_side],
        "palette": palette_hex(padded[0]) if padded else [],
        "palette_size": len(set().union(*[collect_colors(icon) for icon in padded])),
        "cut": cut_meta.get("cut", "cell"),
    }
    # Recompute palette from the whole family, not just the first icon.
    family_colors = Counter()
    for icon in padded:
        family_colors.update(collect_colors(icon))
    meta["palette"] = [f"#{r:02X}{g:02X}{b:02X}" for r, g, b in sorted(family_colors)]
    meta["palette_size"] = len(family_colors)
    return padded, meta


def pixelize_sheet_frames(
    sheet: Image.Image,
    *,
    cols: int,
    rows: int,
    chroma: tuple[int, int, int],
    colors: int,
    texel: int = 0,
    merge_distance: float = MERGE_DISTANCE,
    register: str = "stage",
) -> tuple[list[Image.Image], dict]:
    keyed_sheet = key_sheet(sheet, chroma)
    detected_t, phase_x, phase_y = detect_grid(keyed_sheet)
    used_texel = texel or detected_t
    cells, cut_meta = sheet_cells(sheet, cols=cols, rows=rows, chroma=chroma)
    snapped: list[Image.Image] = []

    for cell in cells:
        local_phase = detect_phase(cell, used_texel)
        snapped.append(snap_cell(cell, used_texel, local_phase))

    combined = Counter()
    for icon in snapped:
        combined.update(collect_colors(icon))
    mapping = merge_palette(combined, max_colors=colors, min_distance=merge_distance)
    cleaned = [remove_specks(apply_mapping(icon, mapping)) for icon in snapped]
    frames, family_size = align_frames(cleaned, register=register)
    family_colors = Counter()
    for frame in frames:
        family_colors.update(collect_colors(frame))
    meta = {
        "detected_texel": detected_t,
        "texel": used_texel,
        "phase": [phase_x, phase_y],
        "register": register,
        "family_size": list(family_size),
        "palette": [f"#{red:02X}{green:02X}{blue:02X}" for red, green, blue in sorted(family_colors)],
        "palette_size": len(family_colors),
        "cut": cut_meta.get("cut", "cell"),
    }
    return frames, meta


def cut_anim_frames(
    sheet: Image.Image,
    *,
    cols: int,
    rows: int,
    chroma: tuple[int, int, int],
    register: str = "stage",
) -> tuple[list[Image.Image], dict]:
    """Cut cells and drop chroma. Do not snap, quantize, or redraw."""
    cells, cut_meta = sheet_cells(sheet, cols=cols, rows=rows, chroma=chroma)
    frames, family_size = align_frames(cells, register=register)
    family_colors = Counter()
    for frame in frames:
        family_colors.update(collect_colors(frame))
    meta = {
        "mode": "cut",
        "cut": cut_meta.get("cut", "cell"),
        "register": register,
        "family_size": list(family_size),
        "palette_size": len(family_colors),
        "palette": [f"#{red:02X}{green:02X}{blue:02X}" for red, green, blue in sorted(family_colors)[:48]],
    }
    if cut_meta.get("boxes"):
        meta["boxes"] = cut_meta["boxes"]
    return frames, meta


def split_pixel_grid(
    sheet: Image.Image,
    *,
    cols: int,
    rows: int,
    names: list[str],
    chroma: tuple[int, int, int],
    dest_dir: Path,
    logical: int,
    colors: int,
    preview_scale: int = 8,
    texel: int = 0,
    merge_distance: float = MERGE_DISTANCE,
) -> tuple[list[Path], list[dict]]:
    dest_dir.mkdir(parents=True, exist_ok=True)
    icons, meta = pixelize_sheet_icons(
        sheet,
        cols=cols,
        rows=rows,
        chroma=chroma,
        logical=logical,
        colors=colors,
        texel=texel,
        merge_distance=merge_distance,
    )
    print(
        f"pixel grid texel={meta['texel']} (detected {meta['detected_texel']}) "
        f"phase={meta['phase']} palette={meta['palette_size']} family={meta['family_size']}"
    )
    (dest_dir / "palette.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

    written: list[Path] = []
    records: list[dict] = []
    for index, (icon, name) in enumerate(zip(icons, names), start=1):
        stem = f"{index:02d}-{slug(name)}"
        png_path = dest_dir / f"{stem}.png"
        svg_path = dest_dir / f"{stem}.svg"
        preview_path = dest_dir / f"{stem}@{preview_scale}x.png"
        icon.save(png_path)
        write_pixel_svg(icon, svg_path)
        preview_nearest(icon, preview_scale).save(preview_path)
        written.extend([png_path, svg_path, preview_path])
        records.append(
            {
                "name": stem,
                "png": png_path.name,
                "svg": svg_path.name,
                "preview": preview_path.name,
                "logical": [icon.width, icon.height],
                "colors": palette_hex(icon),
                "cell": [(index - 1) % cols, (index - 1) // cols],
            }
        )
    if records:
        records[0]["sheet"] = meta
    return written, records
