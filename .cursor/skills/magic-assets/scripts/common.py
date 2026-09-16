"""Shared image2 client and post-process for grid / mixed asset sheets."""

from __future__ import annotations

import base64
import colorsys
import json
import sys
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path

import requests
from PIL import Image, ImageFilter

SKILL_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = Path(__file__).resolve().parent


def resolve_project_root() -> Path:
    """Host app root. The skill folder can be copied into any project."""
    cwd = Path.cwd().resolve()
    for candidate in [cwd, *cwd.parents]:
        if candidate == Path.home():
            break
        if (candidate / ".git").exists():
            return candidate

    parts = SKILL_ROOT.parts
    if len(parts) >= 3 and parts[-2] == "skills" and parts[-3] == ".cursor":
        host = SKILL_ROOT.parents[2]
        if host != Path.home():
            return host
    return cwd


PROJECT_ROOT = resolve_project_root()
ROOT = PROJECT_ROOT
DEFAULT_CHROMA = "#FF00FF"
DEFAULT_GUIDE = "#00FFFF"
DEFAULT_STYLE = (
    "Soft 3D clay / chubby rounded product icons. Same perspective, corner radius, "
    "and top-left lighting. Palette: cream, coral, muted teal, navy, graphite. "
    "Never use magenta, fuchsia, hot pink, electric cyan, the chroma-key color, "
    "or the guide-box color on any object."
)
QUALITY_CHOICES = ("low", "medium", "high", "auto")
GRID_LAYOUTS = {
    4: (2, 2, "1024x1024"),
    8: (4, 2, "2048x1024"),
    16: (4, 4, "2048x2048"),
}

SETTINGS_PATH = SKILL_ROOT / "ma_settings.json"


def load_settings() -> tuple[str, str, str]:
    if not SETTINGS_PATH.exists():
        sys.exit(f"missing {SETTINGS_PATH.name} in the skill folder")
    try:
        data = json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        sys.exit(f"invalid {SETTINGS_PATH.name}: {error}")
    if not isinstance(data, dict):
        sys.exit(f"{SETTINGS_PATH.name} must be a JSON object")
    endpoint = str(data.get("endpoint") or "").strip().rstrip("/")
    api_key = str(data.get("apikey") or "").strip()
    model_name = str(data.get("model_name") or "").strip()
    missing = [
        name
        for name, value in (("endpoint", endpoint), ("apikey", api_key), ("model_name", model_name))
        if not value
    ]
    if missing:
        sys.exit(f"missing {', '.join(missing)} in {SETTINGS_PATH.name}")
    return api_key, endpoint, model_name


def load_brief(path: str) -> dict:
    if not path:
        return {}
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        sys.exit("brief must be a JSON object")
    return data


def parse_names(raw: str) -> list[str]:
    return [part.strip() for part in raw.split(",") if part.strip()]


def slug(value: str) -> str:
    cleaned = "".join(ch.lower() if ch.isalnum() else "-" for ch in value.strip())
    return "-".join(part for part in cleaned.split("-") if part) or "asset"


def parse_hex_color(value: str) -> tuple[int, int, int]:
    text = str(value).strip().lstrip("#")
    if len(text) != 6:
        raise ValueError(f"expected #RRGGBB, got {value!r}")
    return (int(text[0:2], 16), int(text[2:4], 16), int(text[4:6], 16))


GUIDE_RGB = parse_hex_color(DEFAULT_GUIDE)


def guide_box_rules(chroma: str, count: int, guide: str = DEFAULT_GUIDE) -> str:
    return f"""CUT MARKERS — required so a local script can crop without guessing:
- Around EVERY asset, draw one closed axis-aligned rectangle. Exactly {count} boxes. No box around the whole sheet.
- Stroke color is exactly {guide}. Never use {guide} on the object itself.
- Stroke width is exactly 2 canvas pixels (not 2 texels). Hard-edged, no anti-alias, no rounded corners, no gaps, no dashed lines.
- The box sits OUTSIDE the asset. Leave 6–10px of {chroma} padding between the object and the inner edge of the box.
- Boxes must not touch each other or the canvas edge. Leave at least 16px of {chroma} between boxes.
- Do not fill the box. Interior is {chroma} plus the single object.
- These {count} rectangles are the only frames allowed. No cards, captions, numbers, or extra borders."""


def generate_sheet(
    *,
    prompt: str,
    size: str,
    quality: str,
    api_key: str,
    base_url: str,
    model: str,
) -> tuple[bytes, dict]:
    url = f"{base_url}/images/generations"
    payload = {
        "model": model,
        "prompt": prompt,
        "n": 1,
        "size": size,
        "quality": quality,
        "output_format": "png",
        "background": "opaque",
    }
    print(f"requesting {url} size={size} quality={quality} model={model}")
    session = requests.Session()
    session.trust_env = False
    last_error: Exception | None = None
    response = None
    for attempt in range(1, 4):
        try:
            response = session.post(
                url,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
                timeout=300,
            )
            break
        except (
            requests.exceptions.ProxyError,
            requests.exceptions.ConnectionError,
            requests.exceptions.Timeout,
        ) as error:
            last_error = error
            print(f"image2 attempt {attempt} failed: {error.__class__.__name__}")
            if attempt == 3:
                sys.exit(f"image2 network failed after retries: {error}")
    if response is None:
        sys.exit(f"image2 network failed: {last_error}")
    if response.status_code >= 400:
        sys.exit(f"image2 HTTP {response.status_code}: {response.text[:800]}")

    body = response.json()
    items = body.get("data") or []
    if not items:
        sys.exit(f"image2 returned no data: {json.dumps(body)[:800]}")

    item = items[0]
    if item.get("b64_json"):
        return base64.b64decode(item["b64_json"]), body

    image_url = item.get("url")
    if not image_url:
        sys.exit(f"image2 missing b64_json/url: {json.dumps(body)[:800]}")
    image_response = session.get(image_url, timeout=120)
    image_response.raise_for_status()
    return image_response.content, body


def sample_chroma(image: Image.Image) -> tuple[int, int, int]:
    rgb = image.convert("RGB")
    width, height = rgb.size
    inset = max(2, min(width, height) // 40)
    points = (
        (inset, inset),
        (width - 1 - inset, inset),
        (inset, height - 1 - inset),
        (width - 1 - inset, height - 1 - inset),
    )
    samples = [rgb.getpixel(point) for point in points]
    return tuple(sum(channel) // len(samples) for channel in zip(*samples))


def chroma_alpha(r: int, g: int, b: int, key_h: float, hue_tol: float, sat_min: float) -> int:
    hue, sat, _ = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
    hue_delta = min(abs(hue - key_h), 1 - abs(hue - key_h))
    if sat < sat_min or hue_delta > hue_tol:
        return 255
    if hue_delta <= hue_tol * 0.55 and sat >= sat_min + 0.12:
        return 0
    fade = max(hue_delta / hue_tol, (sat_min + 0.25 - sat) / 0.25)
    return max(0, min(255, int(255 * fade)))


def remove_chroma(
    image: Image.Image,
    chroma: tuple[int, int, int],
    *,
    hue_tol: float = 0.09,
    sat_min: float = 0.32,
) -> Image.Image:
    rgba = image.convert("RGBA")
    key_h = colorsys.rgb_to_hsv(chroma[0] / 255, chroma[1] / 255, chroma[2] / 255)[0]
    keyed = [(r, g, b, chroma_alpha(r, g, b, key_h, hue_tol, sat_min)) for r, g, b, _a in rgba.getdata()]
    rgba.putdata(keyed)
    return rgba


def trim_alpha(image: Image.Image, padding: int = 8) -> Image.Image:
    bbox = image.getbbox()
    if not bbox:
        return image
    left, top, right, bottom = bbox
    left = max(0, left - padding)
    top = max(0, top - padding)
    right = min(image.width, right + padding)
    bottom = min(image.height, bottom + padding)
    return image.crop((left, top, right, bottom))


def is_guide_color(
    red: int,
    green: int,
    blue: int,
    guide: tuple[int, int, int] = GUIDE_RGB,
    *,
    max_dist: float = 70.0,
    max_red: int = 90,
    min_gb: int = 185,
) -> bool:
    """Match electric cyan guide strokes, not muted teal on the artwork."""
    if red > max_red or green < min_gb or blue < min_gb or abs(green - blue) > 55:
        return False
    dist = ((red - guide[0]) ** 2 + (green - guide[1]) ** 2 + (blue - guide[2]) ** 2) ** 0.5
    return dist <= max_dist


def guide_mask(image: Image.Image, guide: tuple[int, int, int] = GUIDE_RGB) -> Image.Image:
    rgb = image.convert("RGB")
    pixels = rgb.getdata()
    mask = Image.new("L", rgb.size, 0)
    mask.putdata([255 if is_guide_color(red, green, blue, guide) else 0 for red, green, blue in pixels])
    return mask


def close_mask(mask: Image.Image, radius: int = 2) -> Image.Image:
    size = max(3, radius * 2 + 1)
    if size % 2 == 0:
        size += 1
    return mask.filter(ImageFilter.MaxFilter(size)).filter(ImageFilter.MinFilter(size))


def _flood_exterior(guide_bytes: bytes, width: int, height: int) -> bytearray:
    exterior = bytearray(width * height)
    stack: list[int] = []

    def push(x: int, y: int) -> None:
        index = y * width + x
        if guide_bytes[index] or exterior[index]:
            return
        exterior[index] = 1
        stack.append(index)

    for x in range(width):
        push(x, 0)
        push(x, height - 1)
    for y in range(height):
        push(0, y)
        push(width - 1, y)
    while stack:
        index = stack.pop()
        x, y = index % width, index // width
        if x > 0:
            push(x - 1, y)
        if x + 1 < width:
            push(x + 1, y)
        if y > 0:
            push(x, y - 1)
        if y + 1 < height:
            push(x, y + 1)
    return exterior


def interiors_from_mask(
    mask: Image.Image,
    *,
    min_side: int = 16,
    min_fill: float = 0.72,
) -> list[dict]:
    width, height = mask.size
    guide_bytes = mask.tobytes()
    exterior = _flood_exterior(guide_bytes, width, height)
    visited = bytearray(width * height)
    boxes: list[dict] = []

    for start in range(width * height):
        if guide_bytes[start] or exterior[start] or visited[start]:
            continue
        stack = [start]
        visited[start] = 1
        xs: list[int] = []
        ys: list[int] = []
        while stack:
            index = stack.pop()
            x, y = index % width, index // width
            xs.append(x)
            ys.append(y)
            for nx, ny in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
                if 0 <= nx < width and 0 <= ny < height:
                    ni = ny * width + nx
                    if not guide_bytes[ni] and not exterior[ni] and not visited[ni]:
                        visited[ni] = 1
                        stack.append(ni)
        left, top, right, bottom = min(xs), min(ys), max(xs) + 1, max(ys) + 1
        width_box = right - left
        height_box = bottom - top
        if width_box < min_side or height_box < min_side:
            continue
        fill = len(xs) / (width_box * height_box)
        if fill < min_fill:
            continue
        boxes.append({"inner": (left, top, right, bottom), "area": len(xs), "fill": fill})
    return boxes


def order_guide_boxes(boxes: list[dict], *, hero_first: bool = False) -> list[dict]:
    reading = sorted(boxes, key=lambda item: (item["inner"][1], item["inner"][0]))
    if not hero_first or len(reading) < 2:
        return reading
    hero = max(
        reading,
        key=lambda item: (item["inner"][2] - item["inner"][0]) * (item["inner"][3] - item["inner"][1]),
    )
    rest = [item for item in reading if item is not hero]
    return [hero, *rest]


def find_guide_boxes(
    image: Image.Image,
    *,
    guide: tuple[int, int, int] = GUIDE_RGB,
    expected: int | None = None,
    min_side: int = 16,
    min_fill: float = 0.72,
    hero_first: bool = False,
) -> list[dict]:
    mask = close_mask(guide_mask(image, guide))
    boxes = order_guide_boxes(
        interiors_from_mask(mask, min_side=min_side, min_fill=min_fill),
        hero_first=hero_first,
    )
    if expected is not None and len(boxes) != expected:
        return []
    return boxes


def remove_guide(image: Image.Image, guide: tuple[int, int, int] = GUIDE_RGB) -> Image.Image:
    rgba = image.convert("RGBA")
    mask = close_mask(guide_mask(rgba, guide), radius=1)
    mask = mask.filter(ImageFilter.MaxFilter(3))
    mask_bytes = mask.tobytes()
    pixels = [
        (red, green, blue, 0) if mask_bytes[index] else (red, green, blue, alpha)
        for index, (red, green, blue, alpha) in enumerate(rgba.getdata())
    ]
    rgba.putdata(pixels)
    return rgba


def key_sheet(
    sheet: Image.Image,
    chroma: tuple[int, int, int],
    guide: tuple[int, int, int] = GUIDE_RGB,
) -> Image.Image:
    return remove_guide(remove_chroma(sheet, chroma), guide)


def sheet_cells(
    sheet: Image.Image,
    *,
    cols: int,
    rows: int,
    chroma: tuple[int, int, int],
    guide: tuple[int, int, int] = GUIDE_RGB,
    expected: int | None = None,
) -> tuple[list[Image.Image], dict]:
    want = cols * rows if expected is None else expected
    boxes = find_guide_boxes(sheet, guide=guide, expected=want)
    keyed = key_sheet(sheet, chroma, guide)
    if boxes:
        cells = [keyed.crop(box["inner"]) for box in boxes]
        print(f"cut {len(cells)} guide boxes")
        return cells, {"cut": "guide-box", "boxes": [list(box["inner"]) for box in boxes]}
    cell_w = sheet.width // cols
    cell_h = sheet.height // rows
    cells = [
        keyed.crop((col * cell_w, row * cell_h, (col + 1) * cell_w, (row + 1) * cell_h))
        for row in range(rows)
        for col in range(cols)
    ]
    return cells, {"cut": "cell"}


def neighbors8(x: int, y: int, width: int, height: int):
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            if dx == 0 and dy == 0:
                continue
            nx, ny = x + dx, y + dy
            if 0 <= nx < width and 0 <= ny < height:
                yield nx, ny


def find_blobs(alpha: Image.Image, *, min_area: int = 800, threshold: int = 40) -> list[dict]:
    width, height = alpha.size
    pixels = alpha.tobytes()
    visited = bytearray(width * height)
    blobs: list[dict] = []

    for start, value in enumerate(pixels):
        if value < threshold or visited[start]:
            continue
        stack = [start]
        visited[start] = 1
        xs: list[int] = []
        ys: list[int] = []
        while stack:
            index = stack.pop()
            x, y = index % width, index // width
            xs.append(x)
            ys.append(y)
            for nx, ny in neighbors8(x, y, width, height):
                ni = ny * width + nx
                if pixels[ni] >= threshold and not visited[ni]:
                    visited[ni] = 1
                    stack.append(ni)
        if len(xs) < min_area:
            continue
        blobs.append(
            {
                "area": len(xs),
                "bbox": (min(xs), min(ys), max(xs) + 1, max(ys) + 1),
                "pixels": list(zip(xs, ys)),
            }
        )
    blobs.sort(key=lambda item: item["area"], reverse=True)
    return blobs


def crop_blob(keyed: Image.Image, blob: dict, padding: int = 10) -> Image.Image:
    left, top, right, bottom = blob["bbox"]
    left = max(0, left - padding)
    top = max(0, top - padding)
    right = min(keyed.width, right + padding)
    bottom = min(keyed.height, bottom + padding)
    crop = keyed.crop((left, top, right, bottom))
    mask = Image.new("L", crop.size, 0)
    mask_px = mask.load()
    for x, y in blob["pixels"]:
        mask_px[x - left, y - top] = 255
    dilated = mask.copy()
    dilated_px = dilated.load()
    width, height = mask.size
    for y in range(height):
        for x in range(width):
            if mask_px[x, y]:
                continue
            for nx, ny in neighbors8(x, y, width, height):
                if mask_px[nx, ny]:
                    dilated_px[x, y] = 255
                    break
    out = Image.new("RGBA", crop.size, (0, 0, 0, 0))
    out.paste(crop, mask=dilated)
    return out


def split_grid(
    sheet: Image.Image,
    *,
    cols: int,
    rows: int,
    names: list[str],
    chroma: tuple[int, int, int],
    dest_dir: Path,
) -> tuple[list[Path], list[dict]]:
    dest_dir.mkdir(parents=True, exist_ok=True)
    cells, cut_meta = sheet_cells(sheet, cols=cols, rows=rows, chroma=chroma)
    written: list[Path] = []
    records: list[dict] = []
    for index, (cell, name) in enumerate(zip(cells, names)):
        cut = trim_alpha(cell)
        col, row = index % cols, index // cols
        path = dest_dir / f"{index + 1:02d}-{slug(name)}.png"
        cut.save(path)
        written.append(path)
        record = {
            "name": path.name,
            "size": [cut.width, cut.height],
            "cell": [col, row],
            "cut": cut_meta["cut"],
        }
        if cut_meta.get("boxes") and index < len(cut_meta["boxes"]):
            record["bbox"] = cut_meta["boxes"][index]
        records.append(record)
    return written, records


def split_blobs(
    sheet: Image.Image,
    *,
    names: list[str],
    chroma: tuple[int, int, int],
    dest_dir: Path,
) -> tuple[list[Path], list[dict]]:
    dest_dir.mkdir(parents=True, exist_ok=True)
    labels = [slug(name) for name in names]
    boxes = find_guide_boxes(sheet, expected=len(labels), hero_first=True)
    written: list[Path] = []
    records: list[dict] = []
    if boxes:
        keyed = key_sheet(sheet, chroma)
        print(f"cut {len(boxes)} guide boxes")
        for index, (box, name) in enumerate(zip(boxes, labels), start=1):
            left, top, right, bottom = box["inner"]
            cut = trim_alpha(keyed.crop((left, top, right, bottom)))
            path = dest_dir / f"{index:02d}-{name}.png"
            cut.save(path)
            written.append(path)
            records.append(
                {
                    "name": path.name,
                    "area": box["area"],
                    "bbox": [left, top, right, bottom],
                    "size": [cut.width, cut.height],
                    "cut": "guide-box",
                }
            )
        return written, records

    keyed = remove_chroma(sheet, chroma)
    blobs = find_blobs(keyed.getchannel("A"))
    if not blobs:
        sys.exit("no assets found after chroma key")

    hero, *rest = blobs
    rest.sort(key=lambda item: (item["bbox"][1], item["bbox"][0]))
    ordered = [hero, *rest]
    while len(labels) < len(ordered):
        labels.append(f"extra-{len(labels)}")

    for index, (blob, name) in enumerate(zip(ordered, labels), start=1):
        cut = crop_blob(keyed, blob)
        path = dest_dir / f"{index:02d}-{name}.png"
        cut.save(path)
        written.append(path)
        left, top, right, bottom = blob["bbox"]
        records.append(
            {
                "name": path.name,
                "area": blob["area"],
                "bbox": [left, top, right, bottom],
                "size": [cut.width, cut.height],
                "cut": "blob",
            }
        )
    return written, records


def execute_run(
    *,
    mode: str,
    prompt: str,
    size: str,
    quality: str,
    chroma: str,
    out_prefix: str,
    out_dir_flag: str,
    skip_generate: bool,
    sheet_path: str,
    extra_manifest: dict,
    split,
) -> Path:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    out_dir = ROOT / out_dir_flag / f"{out_prefix}-{stamp}"
    assets_dir = out_dir / "assets"
    out_dir.mkdir(parents=True, exist_ok=True)

    if skip_generate:
        if not sheet_path:
            sys.exit("--sheet is required with --skip-generate")
        source = Path(sheet_path)
        sheet = Image.open(source)
        sheet.save(out_dir / "sheet.png")
        body: dict = {"source": str(source)}
    else:
        api_key, base_url, model = load_settings()
        png_bytes, body = generate_sheet(
            prompt=prompt,
            size=size,
            quality=quality,
            api_key=api_key,
            base_url=base_url,
            model=model,
        )
        (out_dir / "sheet.png").write_bytes(png_bytes)
        sheet = Image.open(BytesIO(png_bytes))
        (out_dir / "prompt.txt").write_text(prompt, encoding="utf-8")
        print(f"saved sheet {out_dir / 'sheet.png'} ({sheet.width}x{sheet.height})")

    sampled = sample_chroma(sheet)
    print(f"chroma requested {chroma} sampled #{sampled[0]:02X}{sampled[1]:02X}{sampled[2]:02X}")
    paths, records = split(sheet, sampled, assets_dir)
    manifest = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "mode": mode,
        "count": len(records),
        "chroma": chroma,
        "sampled_chroma": f"#{sampled[0]:02X}{sampled[1]:02X}{sampled[2]:02X}",
        "quality": quality,
        "size": size,
        "assets": records,
        "revised_prompt": ((body.get("data") or [{}])[0].get("revised_prompt") if isinstance(body, dict) else None),
        **extra_manifest,
    }
    (out_dir / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"split {len(paths)} assets -> {assets_dir}")
    for path in paths:
        print(f"  {path.relative_to(ROOT)}")
    return out_dir
