"""Script FX catalog: CSS/JS motion that must not call image2."""

from __future__ import annotations

from dataclasses import dataclass, field

LAYOUT_PROPS = ("width", "height", "top", "left", "right", "bottom", "margin", "padding", "inset")


@dataclass(frozen=True)
class Effect:
    id: str
    family: str
    title: str
    summary: str
    duration: str
    ease: str
    loop: bool
    default_trigger: str
    vars: dict[str, str] = field(default_factory=dict)
    keyframes: str = ""
    rest: str = ""


EFFECTS: dict[str, Effect] = {
    "pulse": Effect(
        id="pulse",
        family="scale",
        title="Pulse",
        summary="Breathe the scale. Use for idle attention, not a drawn squash cycle.",
        duration="1.2s",
        ease="ease-in-out",
        loop=True,
        default_trigger="loop",
        vars={"--ma-scale": "1.06"},
        keyframes="""0%, 100% { transform: scale(1); }
  50% { transform: scale(var(--ma-scale)); }""",
    ),
    "squash": Effect(
        id="squash",
        family="scale",
        title="Squash",
        summary="Width/height trade without redrawing frames. Pixel-friendly idle.",
        duration="1s",
        ease="ease-in-out",
        loop=True,
        default_trigger="loop",
        vars={"--ma-scale-x": "1.1", "--ma-scale-y": "0.9"},
        keyframes="""0%, 100% { transform: scale(1, 1); }
  50% { transform: scale(var(--ma-scale-x), var(--ma-scale-y)); }""",
    ),
    "bob": Effect(
        id="bob",
        family="position",
        title="Bob",
        summary="Vertical float. Wrap a static sprite or a pixel cycle.",
        duration="1.6s",
        ease="ease-in-out",
        loop=True,
        default_trigger="loop",
        vars={"--ma-distance": "8px"},
        keyframes="""0%, 100% { transform: translateY(0); }
  50% { transform: translateY(calc(var(--ma-distance) * -1)); }""",
    ),
    "shake": Effect(
        id="shake",
        family="position",
        title="Shake",
        summary="Horizontal hit jar. One-shot.",
        duration="420ms",
        ease="linear",
        loop=False,
        default_trigger="click",
        vars={"--ma-distance": "5px"},
        keyframes="""0%, 100% { transform: translateX(0); }
  20% { transform: translateX(var(--ma-distance)); }
  40% { transform: translateX(calc(var(--ma-distance) * -1)); }
  60% { transform: translateX(var(--ma-distance)); }
  80% { transform: translateX(calc(var(--ma-distance) * -1)); }""",
    ),
    "slide-up": Effect(
        id="slide-up",
        family="position",
        title="Slide up",
        summary="Enter from below. Keep opacity on transform only.",
        duration="520ms",
        ease="cubic-bezier(0.16, 1, 0.3, 1)",
        loop=False,
        default_trigger="mount",
        vars={"--ma-distance": "16px"},
        keyframes="""from {
    opacity: 0;
    transform: translateY(var(--ma-distance));
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }""",
        rest="opacity: 0; transform: translateY(var(--ma-distance));",
    ),
    "glow": Effect(
        id="glow",
        family="filter",
        title="Glow",
        summary="Brightness and saturate pulse. No extra bitmap.",
        duration="1.4s",
        ease="ease-in-out",
        loop=True,
        default_trigger="loop",
        vars={"--ma-flash": "1.35", "--ma-saturate": "1.25"},
        keyframes="""0%, 100% { filter: brightness(1) saturate(1); }
  50% { filter: brightness(var(--ma-flash)) saturate(var(--ma-saturate)); }""",
    ),
    "hue": Effect(
        id="hue",
        family="filter",
        title="Hue",
        summary="Hue rotate for status or rarity, not a new palette sheet.",
        duration="2.4s",
        ease="linear",
        loop=True,
        default_trigger="loop",
        vars={"--ma-hue": "40deg"},
        keyframes="""from { filter: hue-rotate(0deg); }
  to { filter: hue-rotate(var(--ma-hue)); }""",
    ),
    "wipe-right": Effect(
        id="wipe-right",
        family="mask",
        title="Wipe right",
        summary="Clip-path reveal. Use for cards, icons, not a generated transition plate.",
        duration="560ms",
        ease="cubic-bezier(0.16, 1, 0.3, 1)",
        loop=False,
        default_trigger="mount",
        keyframes="""from { clip-path: inset(0 100% 0 0); }
  to { clip-path: inset(0 0 0 0); }""",
        rest="clip-path: inset(0 100% 0 0);",
    ),
    "wipe-up": Effect(
        id="wipe-up",
        family="mask",
        title="Wipe up",
        summary="Clip-path reveal from the floor.",
        duration="560ms",
        ease="cubic-bezier(0.16, 1, 0.3, 1)",
        loop=False,
        default_trigger="mount",
        keyframes="""from { clip-path: inset(100% 0 0 0); }
  to { clip-path: inset(0 0 0 0); }""",
        rest="clip-path: inset(100% 0 0 0);",
    ),
    "reveal": Effect(
        id="reveal",
        family="mask",
        title="Reveal",
        summary="Circle iris. Good for spawn or map nodes.",
        duration="640ms",
        ease="cubic-bezier(0.16, 1, 0.3, 1)",
        loop=False,
        default_trigger="mount",
        vars={"--ma-iris": "80%"},
        keyframes="""from { clip-path: circle(0 at 50% 50%); }
  to { clip-path: circle(var(--ma-iris) at 50% 50%); }""",
        rest="clip-path: circle(0 at 50% 50%);",
    ),
    "flash": Effect(
        id="flash",
        family="flash",
        title="Flash",
        summary="White hit flash. Pair with a walk cycle later.",
        duration="280ms",
        ease="ease-out",
        loop=False,
        default_trigger="click",
        vars={"--ma-flash": "2.2"},
        keyframes="""0%, 100% { filter: brightness(1); }
  35% { filter: brightness(var(--ma-flash)); }""",
    ),
    "pop": Effect(
        id="pop",
        family="flash",
        title="Pop",
        summary="Scale-in spawn. The 闪出 default.",
        duration="480ms",
        ease="cubic-bezier(0.16, 1, 0.3, 1)",
        loop=False,
        default_trigger="mount",
        vars={"--ma-scale": "1.08"},
        keyframes="""0% {
    opacity: 0;
    transform: scale(0.45);
  }
  70% {
    opacity: 1;
    transform: scale(var(--ma-scale));
  }
  100% {
    opacity: 1;
    transform: scale(1);
  }""",
        rest="opacity: 0; transform: scale(0.45);",
    ),
    "fade-in": Effect(
        id="fade-in",
        family="flash",
        title="Fade in",
        summary="Opacity only. Quietest entrance.",
        duration="400ms",
        ease="ease-out",
        loop=False,
        default_trigger="mount",
        keyframes="""from { opacity: 0; }
  to { opacity: 1; }""",
        rest="opacity: 0;",
    ),
}

FAMILY_ORDER = ("scale", "position", "filter", "mask", "flash")
FAMILY_LABELS = {
    "scale": "大小",
    "position": "位置",
    "filter": "滤镜",
    "mask": "蒙版",
    "flash": "闪出",
}
TRIGGERS = ("loop", "mount", "click", "hover", "inview")


def effect_ids() -> list[str]:
    return list(EFFECTS.keys())


def resolve_effects(names: list[str]) -> list[Effect]:
    if not names:
        return [EFFECTS[key] for key in EFFECTS]
    resolved: list[Effect] = []
    seen: set[str] = set()
    for name in names:
        key = name.strip().lower()
        if key not in EFFECTS:
            known = ", ".join(effect_ids())
            raise ValueError(f"unknown fx '{name}'. known: {known}")
        if key not in seen:
            resolved.append(EFFECTS[key])
            seen.add(key)
    return resolved


def keyframes_name(effect: Effect) -> str:
    return f"ma-fx-{effect.id}"


def class_name(effect: Effect) -> str:
    return f"ma-fx--{effect.id}"


def uses_layout_property(effect: Effect) -> bool:
    blob = f"{effect.keyframes} {effect.rest}".lower()
    return any(f"{prop}:" in blob or f"{prop} :" in blob for prop in LAYOUT_PROPS)


def render_css(effects: list[Effect] | None = None) -> str:
    items = effects or list(EFFECTS.values())
    blocks = [
        "/* magic-assets script FX. No image2. Transform / opacity / filter / clip-path only. */",
        ".ma-fx {",
        "  --ma-duration: 600ms;",
        "  --ma-delay: 0ms;",
        "  --ma-ease: cubic-bezier(0.16, 1, 0.3, 1);",
        "  --ma-scale: 1.08;",
        "  --ma-scale-x: 1.1;",
        "  --ma-scale-y: 0.9;",
        "  --ma-distance: 8px;",
        "  --ma-flash: 2.2;",
        "  --ma-saturate: 1.25;",
        "  --ma-hue: 40deg;",
        "  --ma-iris: 80%;",
        "  display: inline-block;",
        "  transform-origin: center center;",
        "  will-change: transform, opacity, filter, clip-path;",
        "}",
        ".ma-fx > img,",
        ".ma-fx > svg {",
        "  display: block;",
        "}",
    ]
    for effect in items:
        cls = class_name(effect)
        var_lines = [f"  --ma-duration: {effect.duration};", f"  --ma-ease: {effect.ease};"]
        var_lines.extend(f"  {key}: {value};" for key, value in effect.vars.items())
        blocks.append(f".{cls} {{")
        blocks.extend(var_lines)
        blocks.append("}")
        if effect.rest:
            blocks.append(f".{cls}:not(.is-playing):not(.ma-fx-loop) {{")
            blocks.append(f"  {effect.rest}")
            blocks.append("}")
        animation = (
            f"  animation: {keyframes_name(effect)} var(--ma-duration) var(--ma-ease) "
            f"var(--ma-delay) {'infinite' if effect.loop else 'both'};"
        )
        if effect.loop:
            blocks.append(f".{cls}.ma-fx-loop {{")
            blocks.append(animation)
            blocks.append("}")
        blocks.append(f".{cls}.is-playing {{")
        blocks.append(animation)
        blocks.append("}")
        blocks.append(f"@keyframes {keyframes_name(effect)} {{")
        blocks.append(f"  {effect.keyframes}")
        blocks.append("}")

    reduced = ",\n  ".join(f".{class_name(effect)}" for effect in items)
    blocks.extend(
        [
            "@media (prefers-reduced-motion: reduce) {",
            "  .ma-fx {",
            "    animation: none !important;",
            "    filter: none !important;",
            "    clip-path: none !important;",
            "    transform: none !important;",
            "    opacity: 1 !important;",
            "  }",
            f"  {reduced} {{",
            "    animation: none !important;",
            "  }",
            "}",
        ]
    )
    return "\n".join(blocks) + "\n"


def render_js() -> str:
    return """(() => {
  const TRIGGERS = new Set(["loop", "mount", "click", "hover", "inview"]);

  function fxName(el) {
    return (el.getAttribute("data-ma-fx") || "").trim();
  }

  function triggerOf(el) {
    const value = (el.getAttribute("data-ma-trigger") || "").trim();
    return TRIGGERS.has(value) ? value : "";
  }

  function applyName(el) {
    const name = fxName(el);
    if (!name) return;
    el.classList.add("ma-fx");
    for (const cls of [...el.classList]) {
      if (cls.startsWith("ma-fx--")) el.classList.remove(cls);
    }
    el.classList.add(`ma-fx--${name}`);
  }

  function play(el) {
    const loop = el.classList.contains("ma-fx-loop");
    el.classList.remove("is-playing");
    if (loop) el.classList.remove("ma-fx-loop");
    void el.offsetWidth;
    if (loop) el.classList.add("ma-fx-loop");
    el.classList.add("is-playing");
  }

  function stop(el) {
    el.classList.remove("is-playing");
    el.classList.remove("ma-fx-loop");
  }

  function bindOne(el) {
    if (el.dataset.maBound === "1") return;
    el.dataset.maBound = "1";
    applyName(el);
    const trigger = triggerOf(el);
    if (trigger === "loop") {
      el.classList.add("ma-fx-loop");
      return;
    }
    if (trigger === "mount") {
      play(el);
      return;
    }
    if (trigger === "click") {
      el.addEventListener("click", () => play(el));
      return;
    }
    if (trigger === "hover") {
      el.addEventListener("pointerenter", () => play(el));
      return;
    }
    if (trigger === "inview" && "IntersectionObserver" in window) {
      const observer = new IntersectionObserver((entries) => {
        for (const entry of entries) {
          if (entry.isIntersecting) {
            play(el);
            observer.unobserve(el);
          }
        }
      }, { threshold: 0.4 });
      observer.observe(el);
    }
  }

  function bind(root = document) {
    root.querySelectorAll("[data-ma-fx]").forEach(bindOne);
  }

  const api = { bind, play, stop, applyName };
  if (typeof window !== "undefined") {
    window.MagicFx = api;
    if (document.readyState === "loading") {
      document.addEventListener("DOMContentLoaded", () => bind(document));
    } else {
      bind(document);
    }
  }
  if (typeof module === "object" && module.exports) module.exports = api;
})();
"""


SPRITE_SVG = """<svg class="ma-fx-sprite" viewBox="0 0 32 32" width="72" height="72" aria-hidden="true">
  <ellipse cx="16" cy="20" rx="10" ry="8" fill="#FFE4B0"/>
  <ellipse cx="16" cy="18" rx="9" ry="7" fill="#FFF1C9"/>
  <circle cx="12" cy="18" r="1.6" fill="#0B254A"/>
  <circle cx="20" cy="18" r="1.6" fill="#0B254A"/>
  <circle cx="12.5" cy="17.5" r="0.5" fill="#FFF6DC"/>
  <circle cx="20.5" cy="17.5" r="0.5" fill="#FFF6DC"/>
  <ellipse cx="12" cy="22" rx="1.6" ry="1" fill="#FA6754"/>
  <ellipse cx="20" cy="22" rx="1.6" ry="1" fill="#FA6754"/>
</svg>"""


def render_preview(effects: list[Effect] | None = None) -> str:
    items = effects or list(EFFECTS.values())
    families: dict[str, list[Effect]] = {key: [] for key in FAMILY_ORDER}
    for effect in items:
        families.setdefault(effect.family, []).append(effect)
    sections = []
    for family in FAMILY_ORDER:
        group = families.get(family) or []
        if not group:
            continue
        cards = []
        for effect in group:
            trigger = "loop" if effect.loop else "mount"
            hint = "循环" if effect.loop else "播完停住，可重放"
            cards.append(
                f"""        <figure class="stage" data-family="{effect.family}">
          <button type="button" class="replay" data-replay="{effect.id}">重放</button>
          <div class="stage-frame">
            <span class="ma-fx" data-ma-fx="{effect.id}" data-ma-trigger="{trigger}">{SPRITE_SVG}
            </span>
          </div>
          <figcaption>
            <code>{effect.id}</code>
            <span>{effect.title} · {hint}</span>
          </figcaption>
        </figure>"""
            )
        sections.append(
            f"""    <section class="family">
      <header>
        <p class="kicker">{FAMILY_LABELS[family]}</p>
        <h2>{family}</h2>
      </header>
      <div class="rail">
{chr(10).join(cards)}
      </div>
    </section>"""
        )

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>magic-assets script FX</title>
  <link rel="stylesheet" href="fx.css">
  <style>
    :root {{
      --ink: #2c2118;
      --paper: #f3e6cf;
      --mat: #7a4d32;
      --lamp: #e39b4b;
      --stage: #1f1813;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      color: var(--paper);
      background:
        radial-gradient(1200px 500px at 10% -10%, rgba(227, 155, 75, 0.18), transparent 50%),
        #15110e;
      font: 15px/1.45 "Iowan Old Style", "Palatino Linotype", Palatino, serif;
    }}
    main {{
      width: min(1080px, calc(100% - 40px));
      margin: 36px auto 80px;
    }}
    h1 {{
      font-size: 34px;
      letter-spacing: -0.03em;
      margin: 0 0 8px;
    }}
    .lead {{
      max-width: 46ch;
      color: color-mix(in srgb, var(--paper) 74%, #8a7460);
      margin: 0 0 36px;
    }}
    .family {{
      margin: 0 0 42px;
    }}
    .family h2 {{
      margin: 0 0 14px;
      font-size: 13px;
      font-weight: 600;
      letter-spacing: 0.16em;
      text-transform: uppercase;
      color: var(--lamp);
    }}
    .kicker {{
      margin: 0 0 4px;
      font-size: 20px;
    }}
    .rail {{
      display: flex;
      gap: 16px;
      overflow-x: auto;
      padding-bottom: 8px;
    }}
    .stage {{
      margin: 0;
      min-width: 168px;
      padding: 14px 14px 12px;
      background: color-mix(in srgb, var(--stage) 88%, var(--mat));
      border: 1px solid color-mix(in srgb, var(--lamp) 28%, #3a2a1c);
    }}
    .stage-frame {{
      height: 104px;
      display: grid;
      place-items: center;
      background:
        repeating-linear-gradient(
          45deg,
          #241910,
          #241910 8px,
          #1b140f 8px,
          #1b140f 16px
        );
    }}
    .replay {{
      display: block;
      width: 100%;
      margin-bottom: 10px;
      border: 1px solid color-mix(in srgb, var(--lamp) 55%, #3a2a1c);
      background: #2a1d14;
      color: var(--paper);
      font: inherit;
      font-size: 12px;
      letter-spacing: 0.08em;
      padding: 6px 8px;
    }}
    figcaption {{
      display: flex;
      flex-direction: column;
      gap: 2px;
      margin-top: 10px;
    }}
    figcaption code {{
      font: 12px/1.3 ui-monospace, SFMono-Regular, Menlo, monospace;
      color: var(--lamp);
    }}
    figcaption span {{
      color: color-mix(in srgb, var(--paper) 70%, #8a7460);
      font-size: 12px;
    }}
    @media (max-width: 640px) {{
      h1 {{ font-size: 28px; }}
    }}
  </style>
</head>
<body>
  <main>
    <h1>脚本特效台</h1>
    <p class="lead">这些运动只改 transform、opacity、filter、clip-path。身体要变形时，再走 pixel-anim。</p>
{chr(10).join(sections)}
  </main>
  <script src="fx.js"></script>
  <script>
    document.querySelectorAll("[data-replay]").forEach((button) => {{
      button.addEventListener("click", () => {{
        const stage = button.closest(".stage");
        const target = stage && stage.querySelector("[data-ma-fx]");
        if (target && window.MagicFx) window.MagicFx.play(target);
      }});
    }});
  </script>
</body>
</html>
"""


def effect_record(effect: Effect) -> dict:
    return {
        "id": effect.id,
        "family": effect.family,
        "title": effect.title,
        "summary": effect.summary,
        "duration": effect.duration,
        "ease": effect.ease,
        "loop": effect.loop,
        "default_trigger": effect.default_trigger,
        "class": class_name(effect),
        "keyframes": keyframes_name(effect),
        "vars": effect.vars,
        "triggers": list(TRIGGERS),
    }
