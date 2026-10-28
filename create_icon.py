import math
from PIL import Image, ImageDraw, ImageFont

def create_iddaa_icon(output_path="icon.ico"):
    size = 256
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # 1. Dark Rounded Background with Neon Gradient look
    # Background rounded rectangle
    margin = 8
    draw.rounded_rectangle(
        [margin, margin, size - margin, size - margin],
        radius=48,
        fill=(11, 15, 25, 255),
        outline=(16, 185, 129, 255),  # Emerald border
        width=6
    )

    # Glowing inner accent
    draw.rounded_rectangle(
        [margin + 6, margin + 6, size - margin - 6, size - margin - 6],
        radius=42,
        outline=(59, 130, 246, 180),  # Electric blue inner glow
        width=3
    )

    # 2. Draw Football in the Center
    cx, cy = size // 2, size // 2 - 10
    r = 65

    # Ball background (White/light silver)
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(245, 248, 252, 255), outline=(30, 41, 59, 255), width=4)

    # Central black pentagon
    pent_r = 24
    pent_points = []
    for i in range(5):
        angle = math.radians(i * 72 - 90)
        px = cx + pent_r * math.cos(angle)
        py = cy + pent_r * math.sin(angle)
        pent_points.append((px, py))
    draw.polygon(pent_points, fill=(15, 23, 42, 255), outline=(16, 185, 129, 255))

    # Connecting seams from the vertices
    outer_angles = [-90, -18, 54, 126, 198]
    for i in range(5):
        p1 = pent_points[i]
        angle = math.radians(outer_angles[i])
        p2 = (cx + r * math.cos(angle), cy + r * math.sin(angle))
        draw.line([p1, p2], fill=(30, 41, 59, 255), width=4)

    # 3. AI / Tech Accent Lines (Neural nodes)
    nodes = [
        (42, 50), (214, 50),
        (35, 170), (221, 170)
    ]
    for nx, ny in nodes:
        draw.ellipse([nx - 6, ny - 6, nx + 6, ny + 6], fill=(16, 185, 129, 255))
        # Line towards center
        draw.line([nx, ny, cx, cy], fill=(16, 185, 129, 90), width=2)

    # 4. Banner Ribbon at bottom: "IDDAA AI"
    banner_y1 = size - 70
    banner_y2 = size - 22
    draw.rounded_rectangle(
        [24, banner_y1, size - 24, banner_y2],
        radius=14,
        fill=(16, 185, 129, 240),
        outline=(255, 255, 255, 200),
        width=2
    )

    # Text drawing
    # Fallback default font
    try:
        font = ImageFont.truetype("arialbd.ttf", 26)
    except Exception:
        font = ImageFont.load_default()

    text = "İDDAA AI"
    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    tx = (size - tw) // 2
    ty = banner_y1 + ((banner_y2 - banner_y1) - th) // 2 - 2

    draw.text((tx, ty), text, font=font, fill=(11, 15, 25, 255))

    # Save as ICO (multiple sizes)
    icon_sizes = [(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
    img.save(output_path, format="ICO", sizes=icon_sizes)
    img.save("static/favicon.png", format="PNG")
    print(f"Icon created successfully: {output_path}")

if __name__ == "__main__":
    create_iddaa_icon()
