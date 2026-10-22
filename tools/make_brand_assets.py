#!/usr/bin/env python3
"""One-off: builds favicon, app icons and the 1200x630 social-sharing image from the official crest
(assets-src/crest.png). The crest is only resized, never recoloured, cropped or redrawn.
Outputs go to assets/ and are committed, so deployments do not need fonts or Pillow."""
import pathlib
from PIL import Image, ImageDraw, ImageFont
R = pathlib.Path(__file__).resolve().parent.parent
crest = Image.open(R/'assets-src/crest.png').convert('RGB')
A = R/'assets'; A.mkdir(exist_ok=True)
for n, s in (('icon-192.png', 192), ('icon-512.png', 512), ('apple-touch-icon.png', 180)):
    crest.resize((s, s), Image.LANCZOS).quantize(colors=192, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE).save(A/n, optimize=True)
crest.resize((64, 64), Image.LANCZOS).save(A/'favicon.ico', sizes=[(16, 16), (32, 32), (48, 48)])
NAVY, GOLD, WHITE = (6, 43, 91), (245, 181, 27), (255, 255, 255)
img = Image.new('RGB', (1200, 630), NAVY); d = ImageDraw.Draw(img)
d.rectangle([0, 600, 1200, 630], fill=GOLD)
d.rounded_rectangle([60, 105, 480, 525], radius=24, fill=WHITE)
img.paste(crest.resize((380, 380), Image.LANCZOS), (80, 125))
F = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
def fit(text, size, maxw):
    while True:
        f = ImageFont.truetype(F, size)
        if d.textlength(text, font=f) <= maxw or size < 20: return f
        size -= 2
x, w = 530, 610
d.text((x, 120), 'MTeC', font=fit('MTeC', 130, w), fill=WHITE)
y = 285
for line in ('Makeni Technical College', 'of Innovation & Technology'):
    f = fit(line, 42, w); d.text((x, y), line, font=f, fill=WHITE); y += 58
d.rectangle([x, y + 18, x + 110, y + 24], fill=GOLD)
d.text((x, y + 48), 'SKILLS FOR INNOVATION.', font=fit('SKILLS FOR INNOVATION.', 38, w), fill=GOLD)
img.save(A/'og-image.jpg', quality=88, optimize=True, progressive=True)
print('written:', sorted(p.name for p in A.iterdir()))
