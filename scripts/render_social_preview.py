"""Optional Pillow renderer for the typography-only repository cover."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

root = Path(__file__).resolve().parents[1]
output = root / "assets/social-preview.png"
output.parent.mkdir(parents=True, exist_ok=True)
fonts = [Path("C:/Windows/Fonts/arial.ttf"), Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")]
font_path = next((path for path in fonts if path.exists()), None)

def font(size):
    return ImageFont.truetype(str(font_path), size) if font_path else ImageFont.load_default(size=size)

image = Image.new("RGB", (1280, 640), "#101b2c")
draw = ImageDraw.Draw(image)
draw.rounded_rectangle((850, 82, 1200, 554), radius=22, fill="#1a2a41", outline="#334c68", width=2)
draw.text((68, 82), "BSHL", font=font(80), fill="#8ee5ce")
draw.text((68, 203), "Evidence-first research", font=font(43), fill="white")
draw.text((68, 264), "& trade readiness", font=font(43), fill="white")
draw.text((68, 362), "CSV > Structure > Risk > Review", font=font(27), fill="#b8cadf")
draw.text((68, 422), "Offline demo  /  No-key start  /  MIT", font=font(25), fill="#b8cadf")
draw.text((68, 536), "Explain every decision. Preserve every blocker.", font=font(24), fill="#8ee5ce")
draw.text((884, 120), "RESEARCH CARD", font=font(24), fill="#8ee5ce")
for y, label, status in ((204, "Provenance", "Explicit"), (278, "Risk gates", "Required"),
                         (352, "Snapshots", "Immutable"), (426, "Orders", "None")):
    draw.text((884, y), label, font=font(24), fill="white")
    draw.text((884, y + 30), status, font=font(19), fill="#a8bcd4")
draw.text((884, 505), "Research preview", font=font(18), fill="#a8bcd4")
image.save(output, optimize=True)
print(str(output))
