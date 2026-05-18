"""Generate ShutStart icons (multi-resolution ICO) for each theme.

Produces:
  shutstart/resources/icon-claude.ico  (warm orange, Claude theme)
  shutstart/resources/icon-mac.ico     (Apple blue gradient, Mac theme)
  shutstart/resources/icon.ico         (= icon-claude.ico — PyInstaller default)

Run:
  pip install Pillow
  python tools/make_icons.py
"""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFilter
except ImportError:
    sys.stderr.write("Pillow not installed. Run: pip install Pillow\n")
    sys.exit(1)


REPO_ROOT = Path(__file__).resolve().parent.parent
RESOURCES = REPO_ROOT / "shutstart" / "resources"

# Render once at this size then let Pillow downsample for the other ICO entries.
BASE_SIZE = 512
ICO_SIZES = [(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]


def _power_glyph(draw: ImageDraw.ImageDraw, size: int, fg: tuple[int, int, int, int]) -> None:
    """Draw a white 'power' glyph (universal IEC 60417-5009) centered on the canvas."""
    cx, cy = size // 2, int(size * 0.54)  # nudged slightly down to balance the top stem
    arc_radius = int(size * 0.24)
    stroke = max(2, int(size * 0.075))

    arc_box = (cx - arc_radius, cy - arc_radius, cx + arc_radius, cy + arc_radius)
    # Arc with a gap at the top (gap centered on 270° in PIL coordinates; PIL angles
    # start at 3-o'clock and run clockwise). Draw 130° → 50° = 280° sweep, gap at top.
    draw.arc(arc_box, start=130, end=50, fill=fg, width=stroke)

    # Vertical stem from above the arc down toward the center.
    stem_top = cy - int(size * 0.36)
    stem_bottom = cy - int(size * 0.05)
    half = stroke // 2
    draw.rounded_rectangle(
        (cx - half, stem_top, cx + half, stem_bottom),
        radius=half,
        fill=fg,
    )


def _make_claude(size: int = BASE_SIZE) -> Image.Image:
    """Warm orange rounded square + cream power glyph."""
    bg = (217, 119, 87, 255)         # #d97757
    glow = (224, 138, 105, 255)      # slightly lighter for soft inner highlight
    fg = (254, 250, 245, 255)        # #fefaf5

    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    radius = int(size * 0.22)
    inset = int(size * 0.03)
    draw.rounded_rectangle(
        (inset, inset, size - inset, size - inset),
        radius=radius,
        fill=bg,
    )

    # Soft top inner highlight: a slightly smaller, slightly lighter rounded rect with low opacity.
    highlight = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    hd = ImageDraw.Draw(highlight)
    hd.rounded_rectangle(
        (inset + 6, inset + 6, size - inset - 6, int(size * 0.55)),
        radius=radius - 6,
        fill=(glow[0], glow[1], glow[2], 90),
    )
    highlight = highlight.filter(ImageFilter.GaussianBlur(8))
    img.alpha_composite(highlight)

    _power_glyph(draw, size, fg)
    return img


def _make_mac(size: int = BASE_SIZE) -> Image.Image:
    """Apple-blue rounded square with vertical gradient + white power glyph."""
    top = (10, 132, 255)             # #0a84ff
    bottom = (0, 88, 192)            # #0058c0
    fg = (255, 255, 255, 255)

    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))

    # Build a vertical gradient inside a mask shaped like a rounded square.
    grad = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    gd = ImageDraw.Draw(grad)
    for y in range(size):
        t = y / max(1, size - 1)
        r = int(top[0] + (bottom[0] - top[0]) * t)
        g = int(top[1] + (bottom[1] - top[1]) * t)
        b = int(top[2] + (bottom[2] - top[2]) * t)
        gd.line([(0, y), (size, y)], fill=(r, g, b, 255))

    mask = Image.new("L", (size, size), 0)
    md = ImageDraw.Draw(mask)
    radius = int(size * 0.22)
    inset = int(size * 0.03)
    md.rounded_rectangle(
        (inset, inset, size - inset, size - inset),
        radius=radius,
        fill=255,
    )
    img.paste(grad, (0, 0), mask)

    # Subtle specular highlight near the top edge.
    spec = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    sd = ImageDraw.Draw(spec)
    sd.rounded_rectangle(
        (inset + 8, inset + 8, size - inset - 8, int(size * 0.40)),
        radius=radius - 6,
        fill=(255, 255, 255, 70),
    )
    spec = spec.filter(ImageFilter.GaussianBlur(10))
    # Clip the highlight to the rounded square shape too.
    spec_clipped = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    spec_clipped.paste(spec, (0, 0), mask)
    img.alpha_composite(spec_clipped)

    _power_glyph(ImageDraw.Draw(img), size, fg)
    return img


def _save_ico(img: Image.Image, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    img.save(path, format="ICO", sizes=ICO_SIZES)


def _make_check(size: int = 32, color: tuple[int, int, int, int] = (255, 255, 255, 255)) -> Image.Image:
    """White checkmark on transparent background, used inside filled checkboxes."""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    stroke = max(2, int(size * 0.15))
    p1 = (int(size * 0.22), int(size * 0.52))
    p2 = (int(size * 0.43), int(size * 0.72))
    p3 = (int(size * 0.78), int(size * 0.30))
    # joint='curve' rounds the corner; falls back to None on very old Pillow.
    try:
        draw.line([p1, p2, p3], fill=color, width=stroke, joint="curve")
    except TypeError:
        draw.line([p1, p2], fill=color, width=stroke)
        draw.line([p2, p3], fill=color, width=stroke)
    return img


def main() -> int:
    RESOURCES.mkdir(parents=True, exist_ok=True)

    claude = _make_claude()
    mac = _make_mac()

    claude_path = RESOURCES / "icon-claude.ico"
    mac_path = RESOURCES / "icon-mac.ico"
    default_path = RESOURCES / "icon.ico"
    check_path = RESOURCES / "check-white.png"

    _save_ico(claude, claude_path)
    _save_ico(mac, mac_path)
    shutil.copyfile(claude_path, default_path)

    # Render the check glyph at a high resolution and downsample for crisp 16-px display.
    check = _make_check(64).resize((24, 24), Image.LANCZOS)
    check.save(check_path, format="PNG")

    print(f"Generated {claude_path.relative_to(REPO_ROOT)}")
    print(f"Generated {mac_path.relative_to(REPO_ROOT)}")
    print(f"Generated {default_path.relative_to(REPO_ROOT)} (= icon-claude.ico)")
    print(f"Generated {check_path.relative_to(REPO_ROOT)}")

    # Also dump a PNG preview at 256 per theme for quick visual check.
    claude.resize((256, 256), Image.LANCZOS).save(RESOURCES / "icon-claude.preview.png")
    mac.resize((256, 256), Image.LANCZOS).save(RESOURCES / "icon-mac.preview.png")
    print("Preview PNGs saved alongside.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
