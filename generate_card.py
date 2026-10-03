#!/usr/bin/env python3
"""
Generate Neofetch-style GitHub Profile Card SVG
Reads neofetch.json and a profile image, then generates a sleek terminal card SVG.
"""

import html
import json
import os
import sys
from PIL import Image, ImageEnhance, ImageOps

# ==========================================
# CONFIGURATION
# ==========================================
USERNAME = "Mohitha-Gm"
JSON_PATH = "neofetch.json"
IMG_PATH = "pfp.jpg" if os.path.exists("pfp.jpg") else "pfp.png"
OUT_PATH = "profile-card.svg"

CARD_WIDTH = 985
MIN_CARD_HEIGHT = 530
LINE_HEIGHT = 20
TEXT_START_X = 390
GRID_PITCH = 5
IMG_TARGET_COLS = 72
IMG_TARGET_ROWS = 96
# ==========================================


def load_card_data(json_path: str, username: str) -> dict:
    """Load JSON content and substitute template variables."""
    if not os.path.exists(json_path):
        raise FileNotFoundError(f"Card content file '{json_path}' not found.")

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if "title" in data and isinstance(data["title"], str):
        data["title"] = data["title"].replace("{{username}}", username)

    return data


def generate_dot_art(img_path: str, offset_x: int, offset_y: int) -> list[str]:
    """
    Process photo with Pillow:
    1. Resize to 72x96
    2. Brighten by 1.3x
    3. Generate one SVG circle per pixel on a 5px grid with brightness-driven radius and opacity.
    """
    if not os.path.exists(img_path):
        raise FileNotFoundError(
            f"Profile image '{img_path}' not found. "
            f"Please place your headshot photo at '{img_path}' in the repository root."
        )

    img = Image.open(img_path).convert("RGB")
    # Preserve aspect ratio with center-crop fit to avoid squishing
    img = ImageOps.fit(img, (IMG_TARGET_COLS, IMG_TARGET_ROWS), method=Image.Resampling.LANCZOS, centering=(0.5, 0.4))

    # Brighten image by 1.3x
    enhancer = ImageEnhance.Brightness(img)
    img = enhancer.enhance(1.3)

    circles = []
    for r in range(IMG_TARGET_ROWS):
        for c in range(IMG_TARGET_COLS):
            r_px, g_px, b_px = img.getpixel((c, r))

            # Relative luminance (perceived brightness)
            lum = (0.299 * r_px + 0.587 * g_px + 0.114 * b_px) / 255.0
            lum = max(0.0, min(1.0, lum))

            # Radius from 0.5 to ~1.275
            radius = 0.5 + lum * (1.275 - 0.5)

            # Opacity from 0.5 to 1.0
            opacity = 0.5 + lum * (1.0 - 0.5)

            cx = offset_x + c * GRID_PITCH + 2.5
            cy = offset_y + r * GRID_PITCH + 2.5
            hex_color = f"#{r_px:02x}{g_px:02x}{b_px:02x}"

            circle_svg = (
                f'  <circle cx="{cx:.1f}" cy="{cy:.1f}" r="{radius:.3f}" '
                f'fill="{hex_color}" opacity="{opacity:.3f}" />'
            )
            circles.append(circle_svg)

    return circles


def format_section_header(title: str) -> tuple[str, str]:
    """Format section title into label and dashed line."""
    clean = title.strip()
    if clean.startswith("-"):
        clean = clean.lstrip("-").strip()
    if clean.endswith("-"):
        clean = clean.rstrip("-").strip()

    label = clean if clean else "Section"
    # Create dashes to reach ~50 characters
    remaining = max(6, 50 - len(label) - 3)
    dashes = "-" * remaining
    return label, dashes


def get_value_color(key: str) -> str:
    """Choose value color: #a5d6ff for links/status highlights, #c9d1d9 for tech specs."""
    highlight_keys = {"Email.Personal", "LinkedIn", "GitHub", "Focus"}
    if key in highlight_keys:
        return "#a5d6ff"
    return "#c9d1d9"


def generate_card():
    # Load content
    data = load_card_data(JSON_PATH, USERNAME)

    # Calculate padding for dot leaders based on longest key
    all_keys = [
        field["key"]
        for section in data.get("sections", [])
        for field in section.get("fields", [])
    ]
    max_key_len = max((len(k) for k in all_keys), default=12)

    # First pass: calculate total height needed for text
    y_cursor = 42
    title_text = data.get("title", f"{USERNAME}@github")
    y_cursor += LINE_HEIGHT  # Underline

    for section in data.get("sections", []):
        sec_title = section.get("title")
        if sec_title:
            y_cursor += LINE_HEIGHT + 6  # Spacing and line for section header
        for _ in section.get("fields", []):
            y_cursor += LINE_HEIGHT

    total_content_height = y_cursor + 35
    card_height = max(MIN_CARD_HEIGHT, total_content_height)

    # Calculate photo vertical offset
    photo_height = IMG_TARGET_ROWS * GRID_PITCH  # 96 * 5 = 480
    photo_offset_x = 15
    photo_offset_y = max(25, (card_height - photo_height) // 2)

    # Generate dot art circles from photo
    circle_elements = generate_dot_art(IMG_PATH, photo_offset_x, photo_offset_y)

    # Second pass: generate text SVG elements
    text_elements = []
    y = 42

    # Title
    esc_title = html.escape(title_text)
    text_elements.append(
        f'  <text x="{TEXT_START_X}" y="{y}" '
        f'font-family="\'Consolas\', \'Courier New\', monospace" '
        f'font-size="14px" font-weight="bold" fill="#a5d6ff">{esc_title}</text>'
    )
    y += LINE_HEIGHT

    # Grey dashed line under title matching title length
    dash_line = "-" * max(len(title_text), 17)
    text_elements.append(
        f'  <text x="{TEXT_START_X}" y="{y}" '
        f'font-family="\'Consolas\', \'Courier New\', monospace" '
        f'font-size="13px" fill="#616e7f">{dash_line}</text>'
    )

    for section in data.get("sections", []):
        sec_title = section.get("title")
        if sec_title:
            y += LINE_HEIGHT + 6
            label, dashes = format_section_header(sec_title)
            text_elements.append(
                f'  <text x="{TEXT_START_X}" y="{y}" '
                f'font-family="\'Consolas\', \'Courier New\', monospace" '
                f'font-size="13px" xml:space="preserve">'
                f'<tspan fill="#616e7f">- </tspan>'
                f'<tspan fill="#a5d6ff">{html.escape(label)} </tspan>'
                f'<tspan fill="#616e7f">{dashes}</tspan>'
                f'</text>'
            )

        for field in section.get("fields", []):
            y += LINE_HEIGHT
            key = field["key"]
            val = str(field["value"])

            dot_count = max_key_len - len(key) + 3
            dots = " " + ("." * dot_count) + " "
            val_color = get_value_color(key)

            esc_key = html.escape(key)
            esc_val = html.escape(val)

            text_elements.append(
                f'  <text x="{TEXT_START_X}" y="{y}" '
                f'font-family="\'Consolas\', \'Courier New\', monospace" '
                f'font-size="13px" xml:space="preserve">'
                f'<tspan fill="#ffa657">{esc_key}</tspan>'
                f'<tspan fill="#616e7f">{dots}</tspan>'
                f'<tspan fill="{val_color}">{esc_val}</tspan>'
                f'</text>'
            )

    # Assemble full SVG
    svg_lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {CARD_WIDTH} {card_height}" '
        f'width="{CARD_WIDTH}" height="{card_height}">',
        f'  <rect width="{CARD_WIDTH}" height="{card_height}" rx="12" fill="#161b22" stroke="#30363d" stroke-width="1" />',
        '  <!-- Dot Art Avatar -->',
        *circle_elements,
        '  <!-- Neofetch Terminal Text -->',
        *text_elements,
        '</svg>',
    ]

    # Write SVG joined by real newlines
    svg_content = "\n".join(svg_lines)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        f.write(svg_content)

    print(f"Successfully generated profile card: {OUT_PATH} ({CARD_WIDTH}x{card_height})")


if __name__ == "__main__":
    try:
        generate_card()
    except FileNotFoundError as e:
        print(f"\n[!] {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"\n[Error] {e}", file=sys.stderr)
        sys.exit(1)
