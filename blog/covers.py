"""Generative cover plates.

Every article gets a two-ink print instead of a stock photo: paper stock,
a couple of geometric forms, deliberate misregistration between the plates,
and grain over the whole thing. The composition is derived from the slug, so
the same post always gets the same cover.
"""

import hashlib
import math
import random

from PIL import Image, ImageChops, ImageDraw, ImageEnhance, ImageFilter

SIZE = (1400, 875)

PAPERS = [
    (243, 236, 222),
    (240, 233, 217),
    (238, 231, 216),
    (245, 238, 226),
]

INKS = [
    (138, 47, 34),    # oxblood
    (36, 31, 26),     # press black
    (43, 58, 85),     # navy
    (150, 110, 42),   # mustard
    (86, 96, 74),     # sage
    (120, 62, 48),    # brick
]


def _seed(slug):
    digest = hashlib.md5(slug.encode('utf-8')).hexdigest()
    return random.Random(int(digest[:12], 16))


def _blank(size):
    """A plate starts white so multiplying it leaves the paper untouched."""
    return Image.new('RGB', size, (255, 255, 255))


# --- compositions -------------------------------------------------------
# Each one draws a single ink plate. dx/dy is the misregistration offset.

def _rings(draw, size, ink, rnd, dx, dy):
    w, h = size
    cx = w * rnd.uniform(0.28, 0.72) + dx
    cy = h * rnd.uniform(0.3, 0.7) + dy
    step = rnd.randint(52, 78)
    width = rnd.randint(9, 16)
    for i in range(rnd.randint(4, 8)):
        r = step * (i + 1) + rnd.randint(0, 14)
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], outline=ink, width=width)
    r = rnd.randint(26, 48)
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=ink)


def _halftone(draw, size, ink, rnd, dx, dy):
    w, h = size
    step = rnd.randint(46, 66)
    phase = rnd.uniform(0, math.pi)
    tilt = rnd.uniform(-0.4, 0.4)
    for y in range(-step, h + step, step):
        for x in range(-step, w + step, step):
            falloff = (math.sin(x / w * 3.1 + phase) + math.sin(y / h * 2.2 + tilt) + 2) / 4
            r = (step * 0.46) * falloff
            if r < 2:
                continue
            draw.ellipse([x + dx - r, y + dy - r, x + dx + r, y + dy + r], fill=ink)


def _rules(draw, size, ink, rnd, dx, dy):
    w, h = size
    y = rnd.randint(60, 220)
    while y < h - 60:
        thickness = rnd.choice([6, 10, 14, 22, 34, 54])
        inset = rnd.choice([0, 0, w * 0.12, w * 0.3])
        draw.rectangle([inset + dx, y + dy, w - inset + dx, y + thickness + dy], fill=ink)
        y += thickness + rnd.randint(26, 90)


def _arch(draw, size, ink, rnd, dx, dy):
    w, h = size
    span = rnd.uniform(0.42, 0.66) * w
    cx = w * rnd.uniform(0.35, 0.65) + dx
    base = h * rnd.uniform(0.62, 0.84) + dy
    box = [cx - span / 2, base - span / 2, cx + span / 2, base + span / 2]
    if rnd.random() < 0.5:
        draw.pieslice(box, 180, 360, fill=ink)
    else:
        draw.pieslice(box, 180, 360, outline=ink, width=rnd.randint(16, 30))
    draw.rectangle([w * 0.08 + dx, base + 26, w * 0.92 + dx, base + 26 + rnd.randint(8, 18)], fill=ink)


def _stack(draw, size, ink, rnd, dx, dy):
    w, h = size
    for _ in range(rnd.randint(3, 6)):
        bw = rnd.uniform(0.18, 0.44) * w
        bh = rnd.uniform(0.16, 0.5) * h
        x = rnd.uniform(0.02, 0.78) * w + dx
        y = rnd.uniform(0.05, 0.6) * h + dy
        box = [x, y, x + bw, y + bh]
        if rnd.random() < 0.45:
            draw.rectangle(box, fill=ink)
        else:
            draw.rectangle(box, outline=ink, width=rnd.randint(10, 20))


def _wave(draw, size, ink, rnd, dx, dy):
    w, h = size
    rows = rnd.randint(5, 9)
    amp = rnd.uniform(30, 90)
    freq = rnd.uniform(1.4, 3.2)
    for row in range(rows):
        base_y = (h / (rows + 1)) * (row + 1)
        r = rnd.uniform(5, 13)
        for x in range(40, w - 20, int(r * 3.4)):
            y = base_y + math.sin(x / w * math.pi * freq + row * 0.7) * amp
            draw.ellipse([x + dx - r, y + dy - r, x + dx + r, y + dy + r], fill=ink)


COMPOSITIONS = [_rings, _halftone, _rules, _arch, _stack, _wave]


# --- finishing ----------------------------------------------------------

def _grain(img, rnd, strength=0.085):
    noise = Image.effect_noise(img.size, rnd.uniform(14, 22)).convert('L')
    noise = noise.filter(ImageFilter.GaussianBlur(0.4))
    return Image.blend(img, Image.merge('RGB', (noise, noise, noise)), strength)


def _vignette(img):
    w, h = img.size
    small = (w // 8, h // 8)
    mask = Image.new('L', small, 0)
    ImageDraw.Draw(mask).ellipse(
        [-small[0] * 0.08, -small[1] * 0.12, small[0] * 1.08, small[1] * 1.12], fill=255
    )
    mask = mask.filter(ImageFilter.GaussianBlur(10)).resize(img.size, Image.BICUBIC)
    darker = ImageEnhance.Brightness(img).enhance(0.9)
    return Image.composite(img, darker, mask)


def make_cover(slug, size=SIZE):
    """Return a PIL image: a two-ink plate printed on aged paper."""
    rnd = _seed(slug)
    img = Image.new('RGB', size, rnd.choice(PAPERS))

    inks = rnd.sample(INKS, 2)
    plates = rnd.sample(COMPOSITIONS, 2)

    for index, (draw_plate, ink) in enumerate(zip(plates, inks)):
        layer = _blank(size)
        # the second plate lands slightly off register, like a real two-pass print
        offset = 0 if index == 0 else rnd.randint(6, 22)
        draw_plate(ImageDraw.Draw(layer), size, ink, rnd, offset, -offset // 2)
        layer = layer.filter(ImageFilter.GaussianBlur(rnd.uniform(0.5, 1.4)))
        img = ImageChops.multiply(img, layer)

    img = _vignette(_grain(img, rnd))
    return img
