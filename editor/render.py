#!/usr/bin/env python3
"""
Cinematic 9:16 renderer for the Zawiyah An-Nur da'wah / waqf appeal.

  python3 render.py                 # full render -> out/final.mp4
  python3 render.py --preview 40    # quick low-res check of first 40 s
  python3 render.py --stills        # dump one still per shot to out/stills

Everything (backgrounds, parallax layers, motion graphics, kinetic type, sound
design) is generated procedurally here, so there are no third-party clips and
nothing that depicts the sacred.  The speaker's face/voice are never altered:
only graded, re-framed, and pauses shortened.
"""
import argparse, json, math, os, subprocess, sys, functools
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter

import plan as P

HERE = os.path.dirname(os.path.abspath(__file__))
os.chdir(HERE)
W, H, FPS = 1080, 1920, 30
SR = 48000
FONT_DIR = os.path.join(HERE, "fonts")
F_BLACK = os.path.join(FONT_DIR, "montserrat-latin-900-normal.woff2")
F_BOLD = os.path.join(FONT_DIR, "montserrat-latin-800-normal.woff2")
F_MED = os.path.join(FONT_DIR, "montserrat-latin-500-normal.woff2")
F_SERIF = os.path.join(FONT_DIR, "playfair-display-latin-700-normal.woff2")
F_SERIF_I = os.path.join(FONT_DIR, "playfair-display-latin-700-italic.woff2")

GOLD = (255, 201, 92)      # RGB
CREAM = (255, 240, 214)
WHITE = (255, 255, 255)

# ============================================================== utilities
def clamp01(x): return max(0.0, min(1.0, x))
def ease(x):  # smooth in-out
    x = clamp01(x); return x * x * (3 - 2 * x)
def ease_out(x):
    x = clamp01(x); return 1 - (1 - x) ** 3
def ease_in(x):
    x = clamp01(x); return x ** 3
def lerp(a, b, x): return a + (b - a) * x
def hex2bgr(h):
    h = h.lstrip("#"); return np.array([int(h[4:6], 16), int(h[2:4], 16), int(h[0:2], 16)], np.float32)

@functools.lru_cache(None)
def font(path, size): return ImageFont.truetype(path, size)

def blend_rgba(dst, spr, x, y, alpha=1.0):
    """Alpha-blend BGRA uint8/float sprite onto BGR uint8 dst at top-left (x,y)."""
    if alpha <= 0.003: return
    sh, sw = spr.shape[:2]
    x0, y0 = int(round(x)), int(round(y))
    dx0, dy0 = max(0, x0), max(0, y0)
    dx1, dy1 = min(dst.shape[1], x0 + sw), min(dst.shape[0], y0 + sh)
    if dx1 <= dx0 or dy1 <= dy0: return
    s = spr[dy0 - y0:dy1 - y0, dx0 - x0:dx1 - x0]
    a = s[..., 3:4].astype(np.float32) * (alpha / 255.0)
    d = dst[dy0:dy1, dx0:dx1].astype(np.float32)
    dst[dy0:dy1, dx0:dx1] = (d + (s[..., :3].astype(np.float32) - d) * a).astype(np.uint8)

def add_light(dst, layer_f, gain=1.0):
    """Screen-like additive light (layer float 0..255, same size as dst)."""
    d = dst.astype(np.float32)
    d = 255 - (255 - d) * (1 - np.clip(layer_f * gain, 0, 255) / 255.0)
    dst[:] = d.astype(np.uint8)

def fbm(h, w, seed, octaves=5, base=4, persistence=0.55, wrap_x=False):
    rng = np.random.default_rng(seed)
    out = np.zeros((h, w), np.float32); amp = 1.0; tot = 0
    for o in range(octaves):
        gh, gw = base * 2 ** o, base * 2 ** o * max(1, w // max(h, 1))
        g = rng.random((gh + 1, gw + 1)).astype(np.float32)
        if wrap_x: g[:, -1] = g[:, 0]
        out += cv2.resize(g, (w, h), interpolation=cv2.INTER_CUBIC) * amp
        tot += amp; amp *= persistence
    out /= tot
    out = (out - out.min()) / (out.max() - out.min() + 1e-6)
    return out

def wrap_cols(img, ox, width):
    """Take `width` columns of img starting at ox with horizontal wrap."""
    lw = img.shape[1]; ox = int(ox) % lw
    if ox + width <= lw: return img[:, ox:ox + width]
    return np.concatenate([img[:, ox:], img[:, :ox + width - lw]], axis=1)

def vgrad(h, w, stops):
    """stops: list of (pos 0..1, '#hex')"""
    ys = np.linspace(0, 1, h)
    cols = np.zeros((h, 3), np.float32)
    ps = [p for p, _ in stops]; cs = [hex2bgr(c) for _, c in stops]
    for ch in range(3):
        cols[:, ch] = np.interp(ys, ps, [c[ch] for c in cs])
    return np.repeat(cols[:, None, :], w, axis=1)

def rounded_mask(w, h, r):
    m = Image.new("L", (w * 2, h * 2), 0)
    ImageDraw.Draw(m).rounded_rectangle([0, 0, w * 2 - 1, h * 2 - 1], r * 2, fill=255)
    return np.array(m.resize((w, h), Image.LANCZOS))

# ============================================================== text sprites
@functools.lru_cache(4096)
def text_sprite(text, fpath, size, fill=WHITE, stroke=8, stroke_fill=(10, 10, 14),
                shadow=True, glow=None, extrude=0, tracking=0):
    """Return BGRA uint8 sprite of `text` (cached)."""
    f = font(fpath, size)
    if tracking:
        widths = [f.getlength(c) for c in text]
        tw = int(sum(widths) + tracking * (len(text) - 1))
    else:
        tw = int(f.getlength(text))
    asc, desc = f.getmetrics()
    pad = stroke + 40 + extrude
    Wd, Hd = tw + pad * 2, asc + desc + pad * 2
    def draw_text(dr, xy, **kw):
        if tracking:
            x = xy[0]
            for c, cw in zip(text, widths):
                dr.text((x, xy[1]), c, font=f, **kw); x += cw + tracking
        else:
            dr.text(xy, text, font=f, **kw)
    layers = []
    if shadow:
        sh = Image.new("RGBA", (Wd, Hd), (0, 0, 0, 0))
        draw_text(ImageDraw.Draw(sh), (pad + 4, pad + 10), fill=(0, 0, 0, 170),
                  stroke_width=stroke + 4, stroke_fill=(0, 0, 0, 170))
        layers.append(sh.filter(ImageFilter.GaussianBlur(12)))
    if glow:
        gl = Image.new("RGBA", (Wd, Hd), (0, 0, 0, 0))
        draw_text(ImageDraw.Draw(gl), (pad, pad), fill=glow + (200,), stroke_width=stroke + 6,
                  stroke_fill=glow + (200,))
        layers.append(gl.filter(ImageFilter.GaussianBlur(22)))
    if extrude:
        ex = Image.new("RGBA", (Wd, Hd), (0, 0, 0, 0)); de = ImageDraw.Draw(ex)
        dark = tuple(int(c * 0.35) for c in fill)
        for k in range(extrude, 0, -1):
            draw_text(de, (pad + k * 0.6, pad + k), fill=dark + (255,), stroke_width=stroke,
                      stroke_fill=stroke_fill + (255,))
        layers.append(ex)
    tx = Image.new("RGBA", (Wd, Hd), (0, 0, 0, 0))
    draw_text(ImageDraw.Draw(tx), (pad, pad), fill=fill + (255,), stroke_width=stroke,
              stroke_fill=stroke_fill + (255,))
    layers.append(tx)
    out = layers[0]
    for l in layers[1:]: out = Image.alpha_composite(out, l)
    a = np.array(out)
    bb = Image.fromarray(a[..., 3]).getbbox()
    if bb: a = a[max(0, bb[1] - 4):bb[3] + 4, max(0, bb[0] - 4):bb[2] + 4]
    return cv2.cvtColor(a, cv2.COLOR_RGBA2BGRA)

def scale_sprite(spr, s):
    if abs(s - 1) < 0.01: return spr
    h, w = spr.shape[:2]
    return cv2.resize(spr, (max(1, int(w * s)), max(1, int(h * s))), interpolation=cv2.INTER_LINEAR)

def sweep_sprite(spr, p, width=0.18, strength=120):
    """Add a moving diagonal light band (p in 0..1) to a sprite."""
    if p <= 0 or p >= 1: return spr
    h, w = spr.shape[:2]
    xs = np.arange(w)[None, :] + np.arange(h)[:, None] * 0.35
    c = lerp(-0.3 * w, 1.3 * w + h * 0.35, p)
    band = np.exp(-((xs - c) / (width * w + 1)) ** 2)[..., None] * strength
    out = spr.copy().astype(np.float32)
    out[..., :3] = np.minimum(255, out[..., :3] + band)
    return out.astype(np.uint8)

# ============================================================== silhouettes
def _poly(d, pts, s=2): d.polygon([(x * s, y * s) for x, y in pts], fill=255)

def draw_palm(d, x, base, h, lean, rng, s=2):
    # trunk: quadratic curve
    n = 40; pts = []
    for i in range(n + 1):
        t = i / n
        px = x + lean * h * t * t; py = base - h * t
        pts.append((px, py))
    for i, (px, py) in enumerate(pts):
        r = lerp(h * 0.035, h * 0.018, i / n)
        d.ellipse([(px - r) * s, (py - r) * s, (px + r) * s, (py + r) * s], fill=255)
    tx, ty = pts[-1]
    for k in range(9):
        ang = -math.pi / 2 + (k - 4) * 0.42 + rng.uniform(-0.12, 0.12)
        L = h * rng.uniform(0.38, 0.52); droop = rng.uniform(0.5, 0.9)
        left, right = [], []
        for i in range(21):
            t = i / 20
            a = ang + droop * t * t * (1 if math.cos(ang) >= 0 else -1) * 1.2
            cx_ = tx + math.cos(ang) * L * t
            cy_ = ty + math.sin(ang) * L * t + droop * L * 0.55 * t * t
            wdt = h * 0.035 * math.sin(math.pi * min(1, t * 1.1)) + 1
            nx, ny = -math.sin(a), math.cos(a)
            left.append((cx_ + nx * wdt, cy_ + ny * wdt)); right.append((cx_ - nx * wdt, cy_ - ny * wdt))
        _poly(d, left + right[::-1], s)

def draw_house(d, x, base, w, h, s=2):
    stilt = h * 0.28; body_h = h * 0.38
    for k in range(5):
        sx = x + w * 0.06 + k * (w * 0.88 / 4)
        d.rectangle([(sx - 4) * s, (base - stilt) * s, (sx + 4) * s, base * s], fill=255)
    top = base - stilt - body_h
    d.rectangle([x * s, top * s, (x + w) * s, (base - stilt) * s], fill=255)
    _poly(d, [(x - w * 0.12, top + 6), (x + w * 0.5, top - h * 0.36), (x + w * 1.12, top + 6)], s)
    # stairs
    _poly(d, [(x + w * 0.75, base - stilt), (x + w * 0.95, base), (x + w * 0.88, base), (x + w * 0.70, base - stilt)], s)
    # windows (cut out)
    for k in range(3):
        wx = x + w * (0.12 + k * 0.28)
        d.rectangle([wx * s, (top + body_h * 0.25) * s, (wx + w * 0.12) * s, (top + body_h * 0.7) * s], fill=0)

def draw_mosque(d, cx, base, sc, s=2):
    hw, hh = 210 * sc, 170 * sc
    d.rectangle([(cx - hw) * s, (base - hh) * s, (cx + hw) * s, base * s], fill=255)
    # drum
    dw = 110 * sc; dt = base - hh - 50 * sc
    d.rectangle([(cx - dw) * s, dt * s, (cx + dw) * s, (base - hh + 2) * s], fill=255)
    # onion dome
    pts = []
    for i in range(61):
        t = i / 60; ang = math.pi * t
        r = 135 * sc * (math.sin(ang) ** 0.9)
        y = dt - 230 * sc * t ** 1.15
        bulge = 1 + 0.25 * math.sin(math.pi * min(1, t * 1.6))
        pts.append((cx - r * bulge * (1 - t) ** 0.35, y))
    pts = pts + [(2 * cx - px, py) for px, py in pts[::-1]]
    _poly(d, pts, s)
    tip = dt - 230 * sc
    d.rectangle([(cx - 3 * sc) * s, (tip - 60 * sc) * s, (cx + 3 * sc) * s, tip * s], fill=255)
    # crescent finial
    r = 18 * sc; cy_ = tip - 70 * sc
    d.ellipse([(cx - r) * s, (cy_ - r) * s, (cx + r) * s, (cy_ + r) * s], fill=255)
    d.ellipse([(cx - r + 9 * sc) * s, (cy_ - r - 5 * sc) * s, (cx + r + 9 * sc) * s, (cy_ + r - 5 * sc) * s], fill=0)
    # side domes
    for sx in (-1, 1):
        x0 = cx + sx * 150 * sc; r = 52 * sc
        d.ellipse([(x0 - r) * s, (base - hh - r * 1.1) * s, (x0 + r) * s, (base - hh + r * 0.9) * s], fill=255)
    # arches cut
    for k in range(-3, 4):
        ax = cx + k * 56 * sc
        d.rounded_rectangle([(ax - 17 * sc) * s, (base - 120 * sc) * s, (ax + 17 * sc) * s, (base - 10 * sc) * s],
                            int(16 * sc * s), fill=0)
    # minarets
    for sx in (-1, 1):
        mx = cx + sx * 300 * sc; mt = base - 560 * sc
        d.rectangle([(mx - 20 * sc) * s, mt * s, (mx + 20 * sc) * s, base * s], fill=255)
        d.rectangle([(mx - 32 * sc) * s, (mt + 120 * sc) * s, (mx + 32 * sc) * s, (mt + 140 * sc) * s], fill=255)
        d.rectangle([(mx - 30 * sc) * s, (mt + 300 * sc) * s, (mx + 30 * sc) * s, (mt + 316 * sc) * s], fill=255)
        _poly(d, [(mx - 24 * sc, mt), (mx, mt - 90 * sc), (mx + 24 * sc, mt)], s)

def hills_poly(d, LW, base, amp, seed, s=2, LH=0):
    rng = np.random.default_rng(seed)
    xs = np.linspace(0, LW, 200)
    y = np.zeros_like(xs)
    for f in range(1, 5):
        ph = rng.uniform(0, 2 * np.pi)
        y += np.sin(xs / LW * 2 * np.pi * f + ph) / f
    y = base - amp * (y - y.min()) / (np.ptp(y) + 1e-6)
    pts = list(zip(xs, y)) + [(LW, LH + 10), (0, LH + 10)]
    _poly(d, pts, s)

def make_layer(LW, LH, painter):
    S = 2
    im = Image.new("L", (LW * S, LH * S), 0)
    painter(ImageDraw.Draw(im), S)
    return np.array(im.resize((LW, LH), Image.LANCZOS))

# ============================================================== scenes
GROUND_EXTRA = 420   # layer pixels below the screen bottom (for vertical moves)

PALETTES = {
    "dawn":  dict(sky=[(0, "#0d1b3d"), (0.38, "#34477a"), (0.62, "#b9786a"), (0.78, "#f0b77c"), (1, "#f7d9a0")],
                  sun=(0.5, 0.60), suncol="#ffd9a0", far="#7a6a86", mid="#2e2a44", fg="#0e0d18", cloud="#f3c6a0"),
    "dusk":  dict(sky=[(0, "#050815"), (0.35, "#161c42"), (0.62, "#5a3358"), (0.80, "#c9654f"), (1, "#f2a560")],
                  sun=(0.5, 0.66), suncol="#ffb070", far="#4c2f4e", mid="#1d1428", fg="#07060c", cloud="#c77a72"),
    "gold":  dict(sky=[(0, "#1d3552"), (0.40, "#55789a"), (0.70, "#e1bf8a"), (1, "#fbe6b8")],
                  sun=(0.62, 0.42), suncol="#fff1c8", far="#8d8a8e", mid="#3c4048", fg="#15171d", cloud="#fff3df"),
    "night": dict(sky=[(0, "#02040b"), (0.5, "#0b1633"), (1, "#22305e")],
                  sun=(0.7, 0.25), suncol="#c9d8ff", far="#1c2546", mid="#0d1328", fg="#04060c", cloud="#3a4a7a"),
}

class Particles:
    def __init__(self, n, seed, size=(1.5, 4.5), speed=(15, 45), color=(200, 225, 255), alpha=(0.25, 0.8)):
        r = np.random.default_rng(seed)
        self.x0 = r.uniform(0, W, n); self.y0 = r.uniform(0, H, n)
        self.sz = r.uniform(*size, n); self.vy = r.uniform(*speed, n)
        self.ph = r.uniform(0, 6.28, n); self.al = r.uniform(*alpha, n)
        self.col = color
    def draw(self, frame, t, rise=1.0, cam_y=0.0, scale=0.5):
        h2, w2 = int(H * scale), int(W * scale)
        lay = np.zeros((h2, w2, 3), np.float32)
        x = (self.x0 + 18 * np.sin(t * 0.6 + self.ph)) % W
        y = (self.y0 - rise * self.vy * t + cam_y * 0.8 * (self.sz / 4.5)) % H
        fl = 0.6 + 0.4 * np.sin(t * 2.2 + self.ph * 3)
        for i in range(len(x)):
            c = tuple(float(v) * self.al[i] * fl[i] for v in self.col)
            cv2.circle(lay, (int(x[i] * scale), int(y[i] * scale)), max(1, int(self.sz[i] * scale)), c, -1, cv2.LINE_AA)
        lay = cv2.GaussianBlur(lay, (0, 0), 1.6)
        lay = cv2.resize(lay, (W, H))
        add_light(frame, lay, 1.0)

class SkyScene:
    """Layered parallax landscape: sky, sun glow, god-rays, clouds, far hills,
    mid layer (village/mosque/trees), foreground, dust."""
    def __init__(self, palette, kind, seed=1):
        pal = PALETTES[palette]; self.pal = pal; self.kind = kind
        self.sky = vgrad(H + 700, W, pal["sky"])
        self.sun = pal["sun"]; self.suncol = hex2bgr(pal["suncol"])
        LW = W * 2
        r = np.random.default_rng(seed)
        self.cloud = [fbm(H // 2, LW // 2, seed + k, octaves=6, base=3, wrap_x=True) for k in range(2)]
        self.cloudcol = hex2bgr(pal["cloud"])
        LH = 1000 + GROUND_EXTRA; base = 1000
        self.layers = []
        # far hills
        far = make_layer(LW, LH, lambda d, s: hills_poly(d, LW, base - 330, 160, seed + 3, s, LH))
        self.layers.append((far, hex2bgr(pal["far"]), 0.25, 0.35))
        # mid
        def mid_p(d, s):
            hills_poly(d, LW, base - 150, 70, seed + 5, s, LH)
            rr = np.random.default_rng(seed + 9)
            if kind in ("village",):
                for k in range(5):
                    draw_house(d, 120 + k * 430 + rr.uniform(-40, 40), base - 140, rr.uniform(170, 230), rr.uniform(180, 230), s)
                for k in range(9):
                    draw_palm(d, rr.uniform(0, LW), base - 135, rr.uniform(260, 420), rr.uniform(-0.25, 0.25), rr, s)
            if kind in ("mosque", "dusk", "endcard"):
                draw_mosque(d, LW * 0.25, base - 145, 0.95 if kind == "mosque" else 0.62, s)
                draw_mosque(d, LW * 0.75, base - 145, 0.95 if kind == "mosque" else 0.62, s)
                for k in range(6):
                    xx = LW * 0.25 + (k - 2.5) * 260 if k % 2 else LW * 0.75 + (k - 2.5) * 240
                    draw_palm(d, xx % LW, base - 140, rr.uniform(240, 360), rr.uniform(-0.2, 0.2), rr, s)
            if kind in ("rays", "gold", "dawn", "bokeh"):
                for k in range(7):
                    draw_palm(d, rr.uniform(0, LW), base - 140, rr.uniform(200, 340), rr.uniform(-0.2, 0.2), rr, s)
        mid = make_layer(LW, LH, mid_p)
        self.layers.append((mid, hex2bgr(pal["mid"]), 0.6, 0.12))
        # foreground: big palms at edges + grass
        def fg_p(d, s):
            hills_poly(d, LW, base - 40, 40, seed + 11, s, LH)
            rr = np.random.default_rng(seed + 21)
            for xx in (60, LW * 0.5 - 80, LW * 0.5 + 120, LW - 80):
                draw_palm(d, xx, base - 30, rr.uniform(700, 900), rr.uniform(-0.3, 0.3), rr, s)
        self.fg = make_layer(LW, LH, fg_p)
        self.fgcol = hex2bgr(pal["fg"])
        self.LH, self.LW = LH, LW
        self.dust = Particles(60, seed + 31, color=(150, 200, 255) if palette != "night" else (255, 255, 255))
        self.stars = None
        if palette in ("night", "dusk"):
            rs = np.random.default_rng(seed + 41)
            st = np.zeros((H // 2 + 350, W // 2, 3), np.float32)
            for _ in range(260):
                x, y = rs.integers(0, W // 2), rs.integers(0, int((H // 2 + 350) * 0.55))
                v = rs.uniform(80, 255); cv2.circle(st, (int(x), int(y)), 0 if v < 200 else 1, (v, v, v), -1, cv2.LINE_AA)
            self.stars = st

    def render(self, t, cam_x=0.0, cam_y=0.0, slide=0.0, ray_gain=1.0, fg=True):
        # sky (moves least)
        sy = int(np.clip(350 - cam_y * 0.25, 0, 700))
        f = self.sky[sy:sy + H].copy()
        # sun glow
        sx, syy = self.sun[0] * W, self.sun[1] * H + cam_y * 0.3
        yy, xx = np.ogrid[0:H // 4, 0:W // 4]
        dist = np.sqrt((xx * 4 - sx) ** 2 + (yy * 4 - syy) ** 2)
        glow = (np.exp(-dist / 240) * 0.7 + np.exp(-dist / 55) * 0.45).astype(np.float32)
        # god rays
        ang = np.arctan2(yy * 4 - syy, xx * 4 - sx)
        rot = t * 0.05
        rays = (0.5 + 0.5 * np.cos(ang * 9 + rot + np.sin(ang * 3 - rot * 2) * 0.8)) ** 5 * np.exp(-dist / 900)
        lightmap = cv2.resize((glow + rays * 0.45 * ray_gain).astype(np.float32), (W, H))
        f = f + lightmap[..., None] * self.suncol[None, None, :] * 0.6
        if self.stars is not None:
            sty = int(np.clip(175 - cam_y * 0.12, 0, 350))
            st = cv2.resize(self.stars[sty:sty + H // 2], (W, H)) * (0.6 + 0.4 * math.sin(t * 1.3))
            f = f + st * 0.8
        # clouds (2 depths, horizontal drift)
        for k, cl in enumerate(self.cloud):
            spd = (14 + 16 * k) + slide * 0.2
            ox = (t * spd + cam_x * (0.15 + 0.1 * k)) / 2
            c = wrap_cols(cl, ox, W // 2)
            a = np.clip((c - 0.52) * 3.2, 0, 1) * (0.35 + 0.2 * k)
            a = cv2.resize(a, (W, H))
            yshift = int(cam_y * (0.3 + 0.1 * k)) - 250 + k * 120
            a = np.roll(a, yshift, axis=0)
            if yshift > 0: a[:yshift] = 0
            f = f * (1 - a[..., None]) + self.cloudcol[None, None, :] * a[..., None]
        f = np.clip(f, 0, 255)
        # silhouettes
        for lay, col, par, haze in self.layers + ([(self.fg, self.fgcol, 1.0, 0.0)] if fg else []):
            ox = (cam_x + slide * t) * par
            y_top = H - (self.LH - GROUND_EXTRA) + cam_y * par
            a = wrap_cols(lay, ox, W)
            y0 = int(y_top); ys0, ys1 = max(0, y0), min(H, y0 + self.LH)
            if ys1 <= ys0: continue
            aa = a[ys0 - y0:ys1 - y0].astype(np.float32)[..., None] / 255.0
            seg = f[ys0:ys1]
            c = col * (1 - haze) + seg * haze
            f[ys0:ys1] = seg * (1 - aa) + c * aa
        out = f.astype(np.uint8)
        self.dust.draw(out, t, rise=0.6, cam_y=cam_y)
        return out

class BlueprintScene:
    """Architect's elevation of the pondok being drawn; grid slides (parallax)."""
    def __init__(self, rooms=False):
        self.bg = vgrad(H, W, [(0, "#06101f"), (0.5, "#0b2140"), (1, "#081428")]).astype(np.uint8)
        self.rooms = rooms
        self.dust = Particles(40, 77, color=(255, 210, 140), alpha=(0.15, 0.5))
    def grid(self, f, t, ox, oy, step, col, th):
        for x in np.arange(-step + (ox % step), W + step, step):
            cv2.line(f, (int(x), 0), (int(x), H), col, th, cv2.LINE_AA)
        for y in np.arange(-step + (oy % step), H + step, step):
            cv2.line(f, (0, int(y)), (W, int(y)), col, th, cv2.LINE_AA)
    def render(self, t, count=None, dur=8.0):
        f = self.bg.copy()
        self.grid(f, t, -t * 18, t * 6, 36, (70, 45, 22), 1)
        self.grid(f, t, -t * 40, t * 14, 180, (120, 80, 40), 1)
        # building elevation, camera dolly
        z = 1.0 + 0.06 * ease(t / dur)
        cx, base = W / 2 - 40 * ease(t / dur), 1250
        bw, fl = 860 * z, 230 * z
        p = ease(t / 2.4)
        gold = (92, 201, 255); line = (255, 225, 180)
        segs = [((cx - bw / 2, base), (cx + bw / 2, base)),
                ((cx - bw / 2, base), (cx - bw / 2, base - 2 * fl)),
                ((cx + bw / 2, base), (cx + bw / 2, base - 2 * fl)),
                ((cx - bw / 2, base - fl), (cx + bw / 2, base - fl)),
                ((cx - bw / 2 - 40 * z, base - 2 * fl), (cx + bw / 2 + 40 * z, base - 2 * fl)),
                ((cx - bw / 2 - 40 * z, base - 2 * fl), (cx, base - 2 * fl - 170 * z)),
                ((cx + bw / 2 + 40 * z, base - 2 * fl), (cx, base - 2 * fl - 170 * z))]
        total = len(segs)
        for i, (a, b) in enumerate(segs):
            q = clamp01(p * total - i)
            if q <= 0: break
            e = (a[0] + (b[0] - a[0]) * q, a[1] + (b[1] - a[1]) * q)
            cv2.line(f, (int(a[0]), int(a[1])), (int(e[0]), int(e[1])), line, 3, cv2.LINE_AA)
        # doors: 15 per floor
        n_show = 30 if not self.rooms else (0 if count is None else count)
        if not self.rooms: n_show = int(30 * ease((t - 1.6) / 2.5))
        dw = bw / 15
        for k in range(min(30, n_show)):
            fl_i, j = divmod(k, 15)
            x0 = cx - bw / 2 + j * dw + dw * 0.22; x1 = x0 + dw * 0.56
            y1 = base - fl_i * fl - 8; y0 = y1 - fl * 0.62
            cv2.rectangle(f, (int(x0), int(y0)), (int(x1), int(y1)), gold, 2, cv2.LINE_AA)
            cv2.circle(f, (int(x1 - dw * 0.1), int((y0 + y1) / 2)), 3, gold, -1, cv2.LINE_AA)
        # dimension line
        if p >= 1:
            yy = base + 50
            cv2.line(f, (int(cx - bw / 2), yy), (int(cx + bw / 2), yy), (200, 160, 110), 1, cv2.LINE_AA)
            for xx in (cx - bw / 2, cx + bw / 2):
                cv2.line(f, (int(xx), yy - 12), (int(xx), yy + 12), (200, 160, 110), 1, cv2.LINE_AA)
        self.dust.draw(f, t, rise=0.4)
        return f

class LandScene:
    """Perspective ground grid; a 1-acre plot boundary traces itself in gold."""
    def __init__(self):
        self.sky = SkyScene("dusk", "rays", seed=5)
    def render(self, t, dur=5.0):
        f = self.sky.render(t, cam_y=-100 + 60 * t, fg=False, ray_gain=0.6)
        hor = 860; cx = W / 2
        ov = np.zeros_like(f)
        def proj(X, Z):
            Z = Z - t * 0.9
            if Z < 0.4: Z = 0.4
            return (cx + X * 700 / Z, hor + 600 / Z)
        # ground fill
        pts = np.array([[0, hor], [W, hor], [W, H], [0, H]], np.int32)
        g = f.copy(); cv2.fillPoly(g, [pts], (40, 22, 18)); f[:] = cv2.addWeighted(f, 0.25, g, 0.75, 0)
        for X in np.arange(-12, 13, 1.0):
            a, b = proj(X, 1.0), proj(X, 40)
            cv2.line(ov, (int(a[0]), int(a[1])), (int(b[0]), int(b[1])), (120, 90, 60), 1, cv2.LINE_AA)
        for Z in np.arange(1, 40, 1.0):
            Zr = Z + (t * 0.9) % 1.0
            a, b = proj(-12, Zr), proj(12, Zr)
            cv2.line(ov, (int(a[0]), int(a[1])), (int(b[0]), int(b[1])), (120, 90, 60), 1, cv2.LINE_AA)
        # plot boundary
        corners = [(-2.4, 3.2), (2.4, 3.2), (2.4, 8.5), (-2.4, 8.5), (-2.4, 3.2)]
        p = ease((t - 0.3) / 2.6)
        segs = len(corners) - 1
        for i in range(segs):
            q = clamp01(p * segs - i)
            if q <= 0: break
            (x0, z0), (x1, z1) = corners[i], corners[i + 1]
            pts = [proj(lerp(x0, x1, k / 20 * q), lerp(z0, z1, k / 20 * q)) for k in range(21)]
            cv2.polylines(ov, [np.array(pts, np.int32)], False, (92, 201, 255), 5, cv2.LINE_AA)
        if p >= 1:
            fillp = np.array([proj(x, z) for x, z in corners[:-1]], np.int32)
            g2 = np.zeros_like(f); cv2.fillPoly(g2, [fillp], (60, 150, 230))
            ov = cv2.add(ov, (g2 * (0.18 + 0.06 * math.sin(t * 4))).astype(np.uint8))
        glow = cv2.GaussianBlur(ov, (0, 0), 8)
        f = cv2.add(f, ov); f = cv2.add(f, glow)
        return f

class TilesScene:
    """Square-foot tiles light up in a wave; RM50 counter rolls in."""
    def __init__(self):
        self.bg = vgrad(H, W, [(0, "#071612"), (0.55, "#0e2a22"), (1, "#06100d")]).astype(np.uint8)
        self.dust = Particles(50, 91, color=(140, 220, 255), alpha=(0.2, 0.6))
    def render(self, t, dur=10.0):
        f = self.bg.copy()
        # isometric-ish tile field sliding upward (vertical movement)
        step = 92; oy = -t * 22; ox = t * 10
        cx, cy = W / 2, 1180
        for i in range(-9, 10):
            for j in range(-4, 16):
                X, Y = i * step + ox % step, j * step * 0.55 + oy % (step * 0.55)
                # skew to fake perspective
                k = 1 + (Y / 900)
                px, py = cx + X * k, cy + Y * k
                if py < 700 or py > H + 60: continue
                d = math.hypot(i, j - 4)
                wave = clamp01((t * 5.0 - d) / 3.0)
                s = step * 0.42 * k
                pts = np.array([[px, py - s * 0.55], [px + s, py], [px, py + s * 0.55], [px - s, py]], np.int32)
                col = (int(lerp(40, 92, wave)), int(lerp(60, 201, wave)), int(lerp(50, 255, wave)))
                cv2.polylines(f, [pts], True, col, 2, cv2.LINE_AA)
                if wave > 0.95 and (i + j) % 3 == 0:
                    g = f.copy(); cv2.fillPoly(g, [pts], (60, 150, 230))
                    f = cv2.addWeighted(f, 0.85, g, 0.15, 0)
        glow = cv2.GaussianBlur(f, (0, 0), 10); f = cv2.add(f, (glow * 0.6).astype(np.uint8))
        self.dust.draw(f, t, rise=0.5)
        return f

class BokehScene:
    """Warm golden light, soft bokeh rising (light of knowledge)."""
    def __init__(self):
        self.sky = SkyScene("gold", "bokeh", seed=13)
        r = np.random.default_rng(5); n = 34
        self.x = r.uniform(0, W, n); self.y = r.uniform(0, H, n); self.rad = r.uniform(18, 70, n)
        self.v = r.uniform(20, 70, n); self.ph = r.uniform(0, 6.28, n)
    def render(self, t, cam_y=0.0):
        f = self.sky.render(t, cam_y=cam_y, fg=True, ray_gain=0.9)
        lay = np.zeros((H // 2, W // 2, 3), np.float32)
        for i in range(len(self.x)):
            x = (self.x[i] + 30 * math.sin(t * 0.4 + self.ph[i])) % W
            y = (self.y[i] - self.v[i] * t) % (H + 200) - 100
            a = 0.25 + 0.2 * math.sin(t * 1.5 + self.ph[i])
            cv2.circle(lay, (int(x / 2), int(y / 2)), int(self.rad[i] / 2), (120 * a, 200 * a, 255 * a), -1, cv2.LINE_AA)
        lay = cv2.GaussianBlur(lay, (0, 0), 3)
        add_light(f, cv2.resize(lay, (W, H)), 1.0)
        return f

class PhotoScene:
    """Real event photo with a slow Ken Burns move (faces never covered)."""
    def __init__(self, spec):
        im = cv2.imread(spec["path"]); h, w = im.shape[:2]
        s = max(W / w, H / h)
        im = cv2.resize(im, (int(w * s) + 2, int(h * s) + 2), interpolation=cv2.INTER_AREA)
        b, g, r = cv2.split(im)
        x = np.arange(256) / 255.0
        curve = np.clip(x + 0.06 * np.sin(2 * np.pi * x) * -0.5, 0, 1)
        im = cv2.merge([cv2.LUT(b, (curve * 248).astype(np.uint8)), cv2.LUT(g, (curve * 252).astype(np.uint8)),
                        cv2.LUT(r, (np.clip(curve * 1.03, 0, 1) * 255).astype(np.uint8))])
        self.img = im; self.spec = spec
        self.dust = Particles(35, 61, color=(150, 210, 255), alpha=(0.1, 0.4))
    def xform(self, u):
        sp = self.spec; ih, iw = self.img.shape[:2]
        z = lerp(sp["z"][0], sp["z"][1], u)
        fx, fy = sp["focus"]; px, py = sp["pan"]
        tx = W / 2 - z * fx * iw + px * u; ty = H / 2 - z * fy * ih + py * u
        tx = min(0, max(W - z * iw, tx)); ty = min(0, max(H - z * ih, ty))
        return z, tx, ty
    def face_band(self, u):
        z, tx, ty = self.xform(u); ih = self.img.shape[0]
        a, b = self.spec["face_band"]
        return ty + z * a * ih, ty + z * b * ih
    def render(self, t, dur):
        u = ease(t / max(dur, 0.1))
        z, tx, ty = self.xform(u)
        M = np.float32([[z, 0, tx], [0, z, ty]])
        f = cv2.warpAffine(self.img, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
        self.dust.draw(f, t, rise=0.4)
        return f

@functools.lru_cache(4)
def qr_card(width):
    q = cv2.imread(P.QR_IMAGE)
    x0, y0, x1, y1 = P.QR_CROP
    q = q[y0:y1, x0:x1]
    h = int(q.shape[0] * width / q.shape[1])
    q = cv2.resize(q, (width, h), interpolation=cv2.INTER_AREA)
    pad = 26
    card = np.full((h + pad * 2, width + pad * 2, 3), 255, np.uint8)
    card[pad:pad + h, pad:pad + width] = q
    m = rounded_mask(card.shape[1], card.shape[0], 34)
    return np.dstack([card, m])

def draw_qr(f, tr, y0, title=True):
    """QR + account number, drawn AFTER grain/vignette so it stays scannable."""
    a = ease_out(tr / 0.5)
    if a <= 0: return
    card = qr_card(600)
    ch, cw = card.shape[:2]
    x = W / 2 - cw / 2; y = y0 + (1 - a) * 60
    sh = np.zeros((ch + 120, cw + 120), np.uint8); sh[60:-60, 60:-60] = 255
    sh = cv2.GaussianBlur(sh, (0, 0), 24)
    blend_rgba(f, np.dstack([np.zeros((*sh.shape, 3), np.uint8), (sh * 0.7).astype(np.uint8)]), x - 60, y - 40, a)
    ring = rounded_mask(cw + 12, ch + 12, 38)
    blend_rgba(f, np.dstack([np.full_like(ring, 70), np.full_like(ring, 196), np.full_like(ring, 255), ring]), x - 6, y - 6, a)
    blend_rgba(f, card, x, y, a)
    if title:
        t1 = text_sprite("IMBAS QR UNTUK WAKAF", F_BLACK, 56, fill=WHITE, stroke=6)
        blend_rgba(f, t1, W / 2 - t1.shape[1] / 2, y0 - 110 + (1 - a) * 30, a)
    # account box
    b = ease_out((tr - 0.35) / 0.5)
    if b <= 0: return
    by = y0 + ch + 40
    lab = text_sprite("NO. AKAUN", F_BOLD, 38, fill=CREAM, stroke=0, shadow=False, tracking=6)
    num = text_sprite(P.ACCOUNT_NO, F_BLACK, 92, fill=GOLD, stroke=0, shadow=False, tracking=4)
    bw, bh = max(num.shape[1], lab.shape[1]) + 90, num.shape[0] + lab.shape[0] + 50
    box = np.zeros((bh, bw, 4), np.uint8); box[..., 0], box[..., 1], box[..., 2] = 34, 20, 10
    box[..., 3] = (rounded_mask(bw, bh, 26) * 0.88).astype(np.uint8)
    bx = W / 2 - bw / 2
    blend_rgba(f, box, bx, by, b)
    ring = cv2.subtract(rounded_mask(bw, bh, 26), cv2.erode(rounded_mask(bw, bh, 26), np.ones((5, 5), np.uint8)))
    blend_rgba(f, np.dstack([np.full_like(ring, 70), np.full_like(ring, 196), np.full_like(ring, 255), ring]), bx, by, b)
    blend_rgba(f, lab, W / 2 - lab.shape[1] / 2, by + 18, b)
    blend_rgba(f, sweep_sprite(num, clamp01((tr - 0.6) / 1.2)), W / 2 - num.shape[1] / 2, by + 24 + lab.shape[0], b)

# ============================================================== speaker
class Speaker:
    def __init__(self, path):
        self.cap = cv2.VideoCapture(path)
        self.n = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.idx = -10; self.cur = None
        x = np.arange(256) / 255.0
        s = x + 0.10 * np.sin(2 * np.pi * x) * -0.5          # gentle S-curve
        s = np.clip((s - 0.02) / 0.98, 0, 1)
        self.lut_b = np.clip((s * 0.97 + 0.025 * (1 - x)) * 255, 0, 255).astype(np.uint8)
        self.lut_g = np.clip(s * 0.99 * 255, 0, 255).astype(np.uint8)
        self.lut_r = np.clip((s * 1.02 + 0.01) * 255, 0, 255).astype(np.uint8)
        self.bright = 1.0
    def _read(self, n):
        if n == self.idx: return self.cur
        if n < self.idx or n > self.idx + 90:
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, n); ok, fr = self.cap.read()
        else:
            for _ in range(n - self.idx - 1): self.cap.grab()
            ok, fr = self.cap.read()
        if not ok: return self.cur
        self.idx = n; self.cur = self._grade(fr); return self.cur
    def _grade(self, fr):
        hsv = cv2.cvtColor(fr, cv2.COLOR_BGR2HSV)
        h, s, v = cv2.split(hsv)
        green = ((h > 28) & (h < 95)).astype(np.float32)
        s = (s.astype(np.float32) * (1 - 0.45 * green)).astype(np.uint8)  # tame the mint wall
        fr = cv2.cvtColor(cv2.merge([h, s, v]), cv2.COLOR_HSV2BGR)
        b, g, r = cv2.split(fr)
        fr = cv2.merge([cv2.LUT(b, self.lut_b), cv2.LUT(g, self.lut_g), cv2.LUT(r, self.lut_r)])
        fr = cv2.resize(fr, (W, H), interpolation=cv2.INTER_CUBIC)
        bl = cv2.GaussianBlur(fr, (0, 0), 2.0)
        return cv2.addWeighted(fr, 1.35, bl, -0.35, 0)
    def get(self, src_t):
        return self._read(int(np.clip(round(src_t * FPS), 0, self.n - 1)))

FACE = (0.50, 0.40)   # normalised face centre in the source frame

def frame_full(img, z, dx=0, dy=0):
    ax, ay = FACE[0] * W, FACE[1] * H
    M = np.float32([[z, 0, (1 - z) * ax + dx], [0, z, (1 - z) * ay + dy]])
    return cv2.warpAffine(img, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)

@functools.lru_cache(16)
def card_assets(w, h):
    m = rounded_mask(w, h, 38)
    pad = 90
    sh = np.zeros((h + pad * 2, w + pad * 2), np.uint8)
    sh[pad + 24:pad + 24 + h, pad:pad + w] = 255
    sh = cv2.GaussianBlur(sh, (0, 0), 30)
    border = np.zeros((h, w), np.uint8)
    cv2.rectangle(border, (0, 0), (w - 1, h - 1), 255, 3)
    border = cv2.bitwise_and(border, m)
    inner = rounded_mask(w - 6, h - 6, 35); ring = m.copy(); ring[3:-3, 3:-3] = cv2.subtract(ring[3:-3, 3:-3], inner)
    return m, sh, ring

def draw_card(dst, img, w, h, cx, cy, scale=1.0, crop_w=0.92, alpha=1.0):
    w2, h2 = int(w * scale) // 2 * 2, int(h * scale) // 2 * 2
    if w2 < 20: return
    m, sh, ring = card_assets(w2, h2)
    # source crop around the face
    cw = W * crop_w; ch = cw * h2 / w2
    x0 = W / 2 - cw / 2; y0 = np.clip(FACE[1] * H - ch * 0.40, 0, H - ch)
    k = w2 / cw
    M = np.float32([[k, 0, -x0 * k], [0, k, -y0 * k]])
    face = cv2.warpAffine(img, M, (w2, h2), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    X, Y = int(cx - w2 / 2), int(cy - h2 / 2)
    shs = np.dstack([np.zeros_like(sh)] * 3 + [(sh * 0.75).astype(np.uint8)])
    blend_rgba(dst, shs, X - 90, Y - 90, alpha)
    blend_rgba(dst, np.dstack([face, m]), X, Y, alpha)
    gold = np.dstack([np.full_like(ring, 120), np.full_like(ring, 205), np.full_like(ring, 255), ring])
    blend_rgba(dst, gold, X, Y, 0.55 * alpha)

# ============================================================== timeline
def load_voice():
    """Return processed mono voice at SR (cached to out/voice.wav)."""
    os.makedirs("out", exist_ok=True)
    wav = "out/voice.wav"
    if not os.path.exists(wav):
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", P.SOURCE, "-ac", "1", "-ar", str(SR), "-af",
                        "highpass=f=75,afftdn=nf=-28,acompressor=threshold=-21dB:ratio=2.5:attack=8:release=120,"
                        "loudnorm=I=-15:TP=-1.5:LRA=8", wav], check=True)
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", wav, "-f", "f32le", "-"], capture_output=True).stdout
    return np.frombuffer(raw, np.float32).copy()

def find_silences(voice, thr_db=-38, min_len=0.30):
    hop = SR // 100
    n = len(voice) // hop
    rms = np.sqrt(np.mean(voice[:n * hop].reshape(n, hop) ** 2, axis=1) + 1e-12)
    db = 20 * np.log10(rms)
    sil = db < thr_db
    out = []; i = 0
    while i < n:
        if sil[i]:
            j = i
            while j < n and sil[j]: j += 1
            if (j - i) / 100 >= min_len: out.append((i / 100, j / 100))
            i = j
        else: i += 1
    return out

def build_edl(voice):
    """List of (src_start, src_end) segments composing the output, plus hook."""
    sil = find_silences(voice)
    segs = [P.HOOK]
    for b0, b1 in P.BODY:
        cur = b0
        for a, b in sil:
            if b <= b0 or a >= b1: continue
            a, b = max(a, b0), min(b, b1)
            keep = P.MAX_PAUSE
            if P.PEAK_PAUSE[0] <= a <= P.PEAK_PAUSE[1]: keep = P.PEAK_PAUSE[2]
            if b - a > keep + 0.05:
                cut0, cut1 = a + keep * 0.5, b - keep * 0.5
                if cut0 > cur + 0.02: segs.append((cur, cut0))
                cur = cut1
        segs.append((cur, b1))
    return segs

class Timeline:
    def __init__(self, segs):
        self.segs = []
        t = 0.0
        for i, (a, b) in enumerate(segs):
            self.segs.append((t, a, b)); t += b - a
            if i == 0: t += P.HOOK_TAIL
        self.speech_end = t
        self.total = t + P.END_CARD
        self.body_start = self.segs[1][0]
    def src(self, t):
        """output time -> source time (None if in a gap)"""
        for t0, a, b in self.segs:
            if t0 <= t < t0 + (b - a): return a + (t - t0)
        if t < self.body_start: return self.segs[0][2]  # hook tail: hold last hook frame
        return self.segs[-1][2]
    def tl(self, src_t, prefer_hook=False):
        """source time -> output time (first body occurrence unless prefer_hook)"""
        cands = self.segs if prefer_hook else self.segs[1:]
        best = None
        for t0, a, b in cands:
            if a <= src_t <= b: return t0 + src_t - a
            if src_t < a and best is None: best = t0
        return best if best is not None else self.speech_end

# ============================================================== subtitles
def norm(w): return "".join(c for c in w.lower() if c.isalnum())

class Subs:
    def __init__(self, words, tl):
        self.items = []  # (t_start, t_end, word, kind, is_hook)
        hook = P.HOOK
        imp = set()
        for t_imp, n in P.IMPORTANT:
            for i, w in enumerate(words):
                if abs(w["s"] - t_imp) < 0.02:
                    for k in range(n): imp.add(round(words[i + k]["s"], 3))
        self.imp_times = []
        for w in words:
            important = round(w["s"], 3) in imp
            k = norm(w["w"])
            kind = "allah" if k in P.KEY_ALLAH else ("gold" if k in P.KEY_GOLD else "n")
            if hook[0] - 0.05 <= w["s"] < hook[1] - 0.08:
                t0 = tl.segs[0][0] + w["s"] - hook[0]
                self.items.append([max(0, t0), t0 + (w["e"] - w["s"]), w["w"], kind, True, important])
            if any(a <= w["s"] < b for a, b in P.BODY):
                t0 = tl.tl(w["s"]); t1 = tl.tl(min(w["e"], w["s"] + 1.2))
                self.items.append([t0, max(t1, t0 + 0.12), w["w"], kind, False, important])
        self.imp_times = [it[0] for it in self.items if it[5]]
        self.items.sort(key=lambda x: x[0])
        # chunk
        self.chunks = []
        cur = []
        for it in self.items:
            if cur:
                prev = cur[-1]
                text_len = sum(len(c[2]) for c in cur) + len(it[2])
                brk = (len(cur) >= (2 if it[4] else 4) or text_len > (16 if it[4] else 22)
                       or it[0] - prev[1] > 0.55 or prev[2].endswith((".", ",", "...")) or it[4] != prev[4])
                if brk: self.chunks.append(cur); cur = []
            cur.append(it)
        if cur: self.chunks.append(cur)
        self.spans = []
        for i, c in enumerate(self.chunks):
            s = c[0][0] - 0.06
            e = c[-1][1] + 0.35
            if i + 1 < len(self.chunks): e = min(e, self.chunks[i + 1][0][0] - 0.06)
            self.spans.append((s, max(e, c[-1][0] + 0.25)))

    def sprite(self, word, kind, active, big):
        size = 104 if big else 74
        if kind == "allah":
            return text_sprite(word.upper(), F_BLACK, int(size * 1.08), fill=CREAM, stroke=7, glow=(255, 200, 120))
        if kind == "gold":
            return text_sprite(word.upper(), F_BLACK, int(size * 1.12), fill=GOLD, stroke=8,
                               extrude=6 if big else 4, glow=(255, 170, 60) if active else None)
        return text_sprite(word.upper(), F_BLACK if big else F_BOLD, size,
                           fill=(255, 236, 160) if active else WHITE, stroke=8)

    def draw(self, f, t, y_center=1520, big_override=None):
        for (s, e), ch in zip(self.spans, self.chunks):
            if not (s <= t < e): continue
            big = ch[0][4] if big_override is None else big_override
            fade = clamp01((e - t) / 0.12)
            sprs = []
            for it in ch:
                active = it[0] <= t < it[1]
                sp = self.sprite(it[2], it[3], active, big)
                sprs.append(sp)
            # layout (wrap at 960)
            gap = 6
            lines, curl, wsum = [], [], 0
            for i, sp in enumerate(sprs):
                w = sp.shape[1] - 30
                if curl and wsum + w > 960: lines.append(curl); curl, wsum = [], 0
                curl.append(i); wsum += w + gap
            if curl: lines.append(curl)
            lh = (118 if big else 92)
            y = y_center - lh * (len(lines) - 1) / 2
            for ln in lines:
                tw = sum(sprs[i].shape[1] - 30 for i in ln) + gap * (len(ln) - 1)
                x = W / 2 - tw / 2
                for i in ln:
                    it = ch[i]; sp = sprs[i]
                    w = sp.shape[1] - 30
                    if t < it[0] - 0.02:
                        blend_rgba(f, sp, x + w / 2 - sp.shape[1] / 2, y - sp.shape[0] / 2 + 6, 0.32 * fade)
                    else:
                        a = clamp01((t - it[0] + 0.02) / 0.10)
                        pop = 1 + 0.14 * math.sin(math.pi * clamp01((t - it[0]) / 0.22)) if it[3] != "allah" else 1.0
                        sc = (0.78 + 0.22 * ease_out(a)) * pop
                        oy = (1 - ease_out(a)) * 26
                        if it[5]:   # marker highlight for the most important words
                            dk = text_sprite(it[2].upper(), F_BLACK, int((104 if big else 74) * 1.12),
                                             fill=(26, 18, 8), stroke=0, shadow=False)
                            m = clamp01((t - it[0]) / 0.16)
                            bw, bh = int((dk.shape[1] + 22) * sc), int((dk.shape[0] + 10) * sc)
                            box = np.zeros((bh, bw, 4), np.uint8)
                            box[..., 0], box[..., 1], box[..., 2] = 70, 196, 255
                            box[..., 3] = rounded_mask(bw, bh, 14)
                            box[:, int(bw * ease_out(m)):, 3] = 0
                            blend_rgba(f, box, x + w / 2 - bw / 2, y - bh / 2 + oy, min(1, a * 1.5) * fade)
                            sp = dk
                        sp2 = scale_sprite(sp, sc)
                        if it[3] == "allah":   # respectful soft light reveal
                            sp2 = sweep_sprite(sp2, clamp01((t - it[0]) / 0.9), strength=70)
                        shake = 0
                        if norm(it[2]) == "kubur" and it[0] <= t < it[0] + 0.25:
                            shake = 3 * math.sin((t - it[0]) * 90)
                        blend_rgba(f, sp2, x + w / 2 - sp2.shape[1] / 2 + shake,
                                   y - sp2.shape[0] / 2 + oy, min(1, a * 1.5) * fade)
                    x += w + gap
                y += lh

# ============================================================== overlays
def draw_title(f, ov, t_rel, tl_dur):
    a_in = ease_out(t_rel / 0.5); a_out = clamp01((tl_dur - t_rel) / 0.35)
    if a_in <= 0 or a_out <= 0: return
    col = {"gold": GOLD, "white": WHITE, "allah": CREAM}[ov["color"]]
    if ov["color"] == "allah":
        sp = text_sprite(ov["text"], F_SERIF, ov["size"], fill=CREAM, stroke=0, glow=(255, 205, 130), shadow=True)
    else:
        sp = text_sprite(ov["text"], F_BLACK, ov["size"], fill=col, stroke=6, extrude=8 if ov["color"] == "gold" else 0,
                         tracking=6 if ov["anim"] == "track" else 0)
    anim = ov["anim"]; sc, dx, dy = 1.0, 0, 0
    if anim == "zoom": sc = lerp(1.35, 1.0, ease_out(t_rel / 0.7)) * (1 + 0.03 * t_rel / tl_dur)
    elif anim == "rise": dy = (1 - a_in) * 60
    elif anim == "track": sc = lerp(0.9, 1.0, ease_out(t_rel / 1.2)) + 0.02 * t_rel / tl_dur
    elif anim == "glow": sc = lerp(0.92, 1.0, ease_out(t_rel / 1.6))
    sp = scale_sprite(sp, sc)
    sp = sweep_sprite(sp, clamp01((t_rel - 0.35) / 1.0))
    blend_rgba(f, sp, W / 2 - sp.shape[1] / 2 + dx, ov["y"] - sp.shape[0] / 2 + dy, a_in * a_out)

def draw_lower3(f, ov, t_rel, dur):
    p = ease_out(t_rel / 0.7); q = clamp01((dur - t_rel) / 0.4)
    if p <= 0 or q <= 0: return
    x0, y0 = 70, ov.get("y", 1130)
    barw = int(8 + 520 * p)
    g = f[y0 - 20:y0 + 150, x0:x0 + 640].astype(np.float32)
    f[y0 - 20:y0 + 150, x0:x0 + 640] = (g * (1 - 0.35 * p * q)).astype(np.uint8)
    cv2.line(f, (x0 + 76, y0 + 66), (x0 + 76 + barw, y0 + 66), (92, 201, 255), 2, cv2.LINE_AA)
    s1 = text_sprite(ov["l1"], F_BLACK, 46, fill=WHITE, stroke=4)
    s2 = text_sprite(ov["l2"], F_MED, 38, fill=CREAM, stroke=3)
    blend_rgba(f, s1, x0 + 70 - (1 - p) * 60, y0 - 12, p * q)
    blend_rgba(f, s2, x0 + 74 - (1 - p) * 90, y0 + 66, p * q)
    # map pin
    px, py = x0 + 42, y0 + 22
    cv2.circle(f, (int(px), int(py)), 18, (92, 201, 255), -1, cv2.LINE_AA)
    cv2.fillConvexPoly(f, np.array([[px - 14, py + 10], [px + 14, py + 10], [px, py + 44]], np.int32), (92, 201, 255), cv2.LINE_AA)
    cv2.circle(f, (int(px), int(py)), 7, (30, 20, 10), -1, cv2.LINE_AA)

def draw_chip(f, ov, t_rel, dur):
    p = ease_out(t_rel / 0.45); q = clamp01((dur - t_rel) / 0.35)
    if p <= 0 or q <= 0: return
    sp = text_sprite(ov["text"], F_BLACK, 50, fill=WHITE, stroke=0, shadow=False)
    w, h = sp.shape[1] + 70, 92
    x = W / 2 - w / 2 + (1 - p) * 300; y = ov["y"] - h / 2
    box = np.zeros((h, w, 4), np.uint8)
    m = rounded_mask(w, h, 46)
    box[..., 0], box[..., 1], box[..., 2] = 20, 40, 70
    box[..., 3] = (m * 0.72).astype(np.uint8)
    blend_rgba(f, box, x, y, p * q)
    ring = cv2.subtract(m, cv2.erode(m, np.ones((5, 5), np.uint8)))
    blend_rgba(f, np.dstack([np.full_like(ring, 92), np.full_like(ring, 201), np.full_like(ring, 255), ring]), x, y, p * q)
    blend_rgba(f, sp, x + w / 2 - sp.shape[1] / 2, y + h / 2 - sp.shape[0] / 2, p * q)

def info_lines():
    i = P.INFO
    out = [(i["title"], F_BLACK, 50, GOLD)]
    for l in i["lines"]: out.append((l, F_BOLD, 44, WHITE))
    if i.get("account"): out.append((i["account"], F_BLACK, 48, GOLD))
    if i.get("account_name"): out.append((i["account_name"], F_MED, 38, CREAM))
    if i.get("contact"): out.append((i["contact"], F_MED, 38, CREAM))
    return out

def draw_panel(f, ov, t_rel, dur, y=None):
    p = ease_out(t_rel / 0.6); q = clamp01((dur - t_rel) / 0.4)
    if p <= 0 or q <= 0: return
    lines = info_lines()
    h = 40 + sum(int(s * 1.45) for _, _, s, _ in lines); w = 900
    x0 = int(W / 2 - w / 2); y0 = int((y or ov["y"]) + (1 - p) * 80)
    y0 = min(y0, H - h - 10)
    reg = f[y0:y0 + h, x0:x0 + w]
    bl = cv2.GaussianBlur(reg, (0, 0), 18)
    bl = (bl.astype(np.float32) * 0.45 + np.array([40, 22, 8], np.float32)).clip(0, 255).astype(np.uint8)
    m = rounded_mask(w, h, 30)
    blend_rgba(f, np.dstack([bl, m]), x0, y0, p * q)
    ring = cv2.subtract(m, cv2.erode(m, np.ones((5, 5), np.uint8)))
    blend_rgba(f, np.dstack([np.full_like(ring, 92), np.full_like(ring, 201), np.full_like(ring, 255), ring]), x0, y0, 0.8 * p * q)
    yy = y0 + 26
    for k, (txt, fp, s, col) in enumerate(lines):
        sp = text_sprite(txt, fp, s, fill=col, stroke=0, shadow=False)
        a = clamp01((t_rel - 0.25 - k * 0.12) / 0.35)
        blend_rgba(f, sp, W / 2 - sp.shape[1] / 2 + (1 - ease_out(a)) * 40, yy, a * q)
        yy += int(s * 1.45)

# ============================================================== renderer
class Renderer:
    def __init__(self, preview=False):
        self.preview = preview
        voice = load_voice()
        self.edl = build_edl(voice)
        self.tl = Timeline(self.edl)
        words = json.load(open(P.WORDS))
        self.subs = Subs(words, self.tl)
        self.spk = Speaker(P.SOURCE)
        self.scenes = {}
        # shots on the output timeline
        self.shots = []
        for sh in P.SHOTS:
            sh = dict(sh)
            if sh["at"] == "hook": sh["t0"] = 0.0
            elif sh["at"] == "end": sh["t0"] = self.tl.speech_end - 0.2
            else: sh["t0"] = self.tl.tl(sh["at"])
            self.shots.append(sh)
        for i, sh in enumerate(self.shots):
            sh["t1"] = self.shots[i + 1]["t0"] if i + 1 < len(self.shots) else self.tl.total
            for ov in sh.get("overlays", []):
                ov["tt"] = self.tl.tl(ov["t"])
        self.total = self.tl.total
        yy, xx = np.ogrid[0:H, 0:W]
        d = np.sqrt(((xx - W / 2) / (W * 0.62)) ** 2 + ((yy - H * 0.45) / (H * 0.62)) ** 2)
        self.vig = np.clip(1 - 0.55 * np.clip(d - 0.45, 0, 1) ** 1.6, 0, 1).astype(np.float32)[..., None]
        self.vig_peak = np.clip(1 - 0.85 * np.clip(d - 0.30, 0, 1) ** 1.4, 0, 1).astype(np.float32)[..., None]
        bot = np.clip((np.arange(H) - 1180) / 600, 0, 1) ** 1.3 * 0.55
        self.botshade = (1 - bot).astype(np.float32)[:, None, None]
        rg = np.random.default_rng(3)
        self.grain = [cv2.resize(rg.normal(0, 7, (H // 2, W // 2)).astype(np.float32), (W, H),
                                 interpolation=cv2.INTER_NEAREST)[..., None] for _ in range(6)]

    def scene(self, name):
        if name.startswith("photo:") and name not in self.scenes:
            self.scenes[name] = PhotoScene(P.PHOTOS[name[6:]])
        if name not in self.scenes:
            self.scenes[name] = {
                "dawn": lambda: SkyScene("dawn", "dawn", 2), "dusk": lambda: SkyScene("dusk", "dusk", 4),
                "gold": lambda: SkyScene("gold", "gold", 6), "village": lambda: SkyScene("dawn", "village", 8),
                "mosque": lambda: SkyScene("dawn", "mosque", 10), "rays": lambda: SkyScene("gold", "rays", 12),
                "endcard": lambda: SkyScene("dusk", "endcard", 14),
                "blueprint": lambda: BlueprintScene(False), "rooms": lambda: BlueprintScene(True),
                "land": LandScene, "tiles": TilesScene, "bokeh": BokehScene,
            }[name]()
        return self.scenes[name]

    # ---------------------------------------------------------- one shot
    def render_shot(self, sh, t):
        tr = t - sh["t0"]; dur = sh["t1"] - sh["t0"]; u = clamp01(tr / max(dur, 0.01))
        mode = sh["mode"]
        src_t = self.tl.src(t)
        if mode == "full":
            img = self.spk.get(src_t)
            z0, z1 = sh.get("zoom", (1.05, 1.15))
            z = lerp(z0, z1, ease(u))
            for pt, dz in sh.get("punches", []):
                pt_tl = self.tl.tl(pt)
                if t >= pt_tl: z += dz * ease_out((t - pt_tl) / 0.12)
            dx, dy = sh.get("drift", (0, 0))
            f = frame_full(img, z, dx * ease(u), dy * ease(u))
            if sh.get("peak"):
                # light dims a touch as he reaches "alam kubur", then lifts
                ab = self.tl.tl(160.2); lift = 1 - 0.10 * math.exp(-((t - ab) / 1.2) ** 2)
                f = (f.astype(np.float32) * self.vig_peak * lift).clip(0, 255).astype(np.uint8)
            return f
        if mode == "photo":
            return self.scene("photo:" + sh["photo"]).render(tr, dur)
        name = sh.get("scene")
        sc = self.scene(name)
        cam = sh.get("cam", (0, 0))
        cam_y = lerp(cam[0], cam[1], ease(u))
        if isinstance(sc, SkyScene):
            f = sc.render(tr, cam_x=tr * 12, cam_y=cam_y, slide=sh.get("slide", 0))
        elif isinstance(sc, BlueprintScene):
            cnt = None
            if "count" in sh:
                c = sh["count"]; c0 = self.tl.tl(c["t"]) - sh["t0"]; c2 = self.tl.tl(c["t2"]) - sh["t0"]
                cnt = int(30 * ease_out((tr - c0 + 0.6) / (c2 - c0 + 0.8)))
            f = sc.render(tr, cnt, dur)
            if "count" in sh: self.draw_count(f, tr, cnt or 0, sh)
        elif isinstance(sc, LandScene): f = sc.render(tr, dur)
        elif isinstance(sc, TilesScene):
            f = sc.render(tr, dur); self.draw_rm(f, tr, sh)
        elif isinstance(sc, BokehScene): f = sc.render(tr, cam_y)
        if mode == "card":
            c = sh["card"]
            push = sh.get("push")
            s = 1.0
            if push: s = lerp(push[0], push[1], ease_out(tr / 0.6))
            s *= 1 + 0.025 * ease(u)
            fy = 10 * math.sin(tr * 0.9)
            draw_card(f, self.spk.get(src_t), c["w"], c["h"], W / 2 + 6 * math.sin(tr * 0.6), c["cy"] + fy, s)
        if name == "endcard": self.draw_end(f, tr, dur)
        return f

    def draw_count(self, f, tr, n, sh):
        if n <= 0: return
        sp = text_sprite(str(n), F_BLACK, 260, fill=GOLD, stroke=8, extrude=10, glow=(255, 170, 60))
        blend_rgba(f, sp, W / 2 - sp.shape[1] / 2, 380 - sp.shape[0] / 2, 1)
        l2 = text_sprite("PINTU PENGINAPAN", F_BLACK, 56, fill=WHITE, stroke=5)
        blend_rgba(f, l2, W / 2 - l2.shape[1] / 2, 540, clamp01(n / 30 * 2))
        if n >= 30:
            l3 = text_sprite("UNTUK WARGA EMAS", F_BOLD, 44, fill=CREAM, stroke=4)
            blend_rgba(f, l3, W / 2 - l3.shape[1] / 2, 615, 1)

    def draw_rm(self, f, tr, sh):
        r = sh["rm"]; tw = self.tl.tl(r["t_wakaf"]) - sh["t0"]; t0 = self.tl.tl(r["t"]) - sh["t0"]
        if tr >= tw - 0.1:
            a = ease_out((tr - tw + 0.1) / 0.5)
            sp = text_sprite("WAKAF", F_BLACK, 130, fill=WHITE, stroke=6, extrude=8)
            sp = sweep_sprite(scale_sprite(sp, lerp(1.3, 1.0, a)), clamp01((tr - tw) / 1.2))
            blend_rgba(f, sp, W / 2 - sp.shape[1] / 2, 330 - sp.shape[0] / 2, a)
        if tr >= t0 - 0.2:
            a = ease_out((tr - t0 + 0.2) / 0.6)
            val = int(round(50 * ease_out((tr - t0 + 0.2) / 1.6)))
            sp = text_sprite(f"RM{val}", F_BLACK, 210, fill=GOLD, stroke=8, extrude=12, glow=(255, 170, 60))
            sp = scale_sprite(sp, lerp(1.4, 1.0, a))
            blend_rgba(f, sp, W / 2 - sp.shape[1] / 2, 560 - sp.shape[0] / 2, a)
            l2 = text_sprite("SEKAKI", F_BLACK, 70, fill=WHITE, stroke=5, tracking=14)
            blend_rgba(f, l2, W / 2 - l2.shape[1] / 2, 700, clamp01((tr - t0) / 0.5))

    def draw_end(self, f, tr, dur):
        items = [("WAKAF SEKAKI", F_BLACK, 66, WHITE, 150), ("RM50", F_BLACK, 150, GOLD, 270)]
        for k, (txt, fp, sz, col, y) in enumerate(items):
            a = ease_out((tr - 0.1 - k * 0.2) / 0.5)
            if a <= 0: continue
            sp = text_sprite(txt, fp, sz, fill=col, stroke=6, extrude=10 if txt == "RM50" else 0,
                             glow=(255, 170, 60) if txt == "RM50" else None)
            sp = sweep_sprite(scale_sprite(sp, lerp(1.15, 1.0, a)), clamp01((tr - 0.8 - k * 0.2) / 1.2))
            blend_rgba(f, sp, W / 2 - sp.shape[1] / 2, y - sp.shape[0] / 2 + (1 - a) * 30, a)
        a = ease_out((tr - 1.2) / 0.8)
        if a > 0:
            sp = text_sprite("“...sedekah jariah kita yang berkekalan...”", F_SERIF_I, 44, fill=CREAM, stroke=0)
            blend_rgba(f, sp, W / 2 - sp.shape[1] / 2, 1640, a)
            sp = text_sprite("PONDOK ZAWIYAH AN-NUR  ·  GERIK, PERAK", F_BOLD, 32, fill=WHITE, stroke=4)
            blend_rgba(f, sp, W / 2 - sp.shape[1] / 2, 1730, a)

    # ---------------------------------------------------------- transitions
    def shot_index(self, t):
        for i, sh in enumerate(self.shots):
            if sh["t0"] <= t < sh["t1"]: return i
        return len(self.shots) - 1

    def frame(self, t):
        i = self.shot_index(t)
        sh = self.shots[i]
        TD = 0.45 if sh["trans"] not in ("fade",) else 0.7
        tr = t - sh["t0"]
        f = None
        if i > 0 and sh["trans"] != "cut" and tr < TD / 2 and sh["t0"] - TD / 2 >= 0:
            p = (tr + TD / 2) / TD     # 0.5..1
        elif i + 1 < len(self.shots) and self.shots[i + 1]["trans"] != "cut" and t >= self.shots[i + 1]["t0"] - (
                (0.45 if self.shots[i + 1]["trans"] != "fade" else 0.7) / 2):
            sh2 = self.shots[i + 1]; TD = 0.45 if sh2["trans"] != "fade" else 0.7
            p = (t - (sh2["t0"] - TD / 2)) / TD  # 0..0.5
            i = i + 1; sh = sh2
        else:
            p = None
        if p is None:
            f = self.render_shot(sh, t)
        else:
            A = self.render_shot(self.shots[i - 1], t); B = self.render_shot(sh, t)
            f = self.transition(A, B, ease(p), sh["trans"])
        f = self.finish(f, t, sh)
        if sh.get("qr") and not (t > self.total - 1.0):
            tr = t - sh["t0"]
            if sh["at"] == "end": draw_qr(f, tr - 0.4, 450, title=False)
            else: draw_qr(f, tr, 330)
        if sh["at"] == "end" and t > self.total - 1.0:
            draw_qr(f, 9, 450, title=False)
            f[:] = (f.astype(np.float32) * clamp01((self.total - t) / 1.0)).astype(np.uint8)
        return f

    def transition(self, A, B, p, kind):
        if kind in ("whip_l", "whip_r"):
            d = -1 if kind == "whip_l" else 1
            off = int(p * W) * d
            out = np.empty_like(A)
            sA = np.roll(A, off, axis=1); sB = np.roll(B, off - d * W, axis=1)
            mask = np.zeros(W, bool)
            if d < 0: mask[W + off:] = True
            else: mask[:off] = True
            out[:] = sA; out[:, mask] = sB[:, mask]
            k = int(1 + 140 * math.sin(math.pi * p))
            return cv2.blur(out, (k, 1)) if k > 2 else out
        if kind in ("slide_up", "slide_down"):
            d = -1 if kind == "slide_up" else 1
            off = int(p * H) * d
            sA = np.roll(A, off, axis=0); sB = np.roll(B, off - d * H, axis=0)
            out = sA.copy()
            if d < 0: out[H + off:] = sB[H + off:]
            else: out[:off] = sB[:off]
            k = int(1 + 120 * math.sin(math.pi * p))
            return cv2.blur(out, (1, k)) if k > 2 else out
        if kind == "zoom":
            za = 1 + 0.9 * p; zb = 0.75 + 0.25 * p
            MA = np.float32([[za, 0, (1 - za) * W / 2], [0, za, (1 - za) * H / 2]])
            MB = np.float32([[zb, 0, (1 - zb) * W / 2], [0, zb, (1 - zb) * H / 2]])
            a2 = cv2.warpAffine(A, MA, (W, H), borderMode=cv2.BORDER_REFLECT)
            b2 = cv2.warpAffine(B, MB, (W, H), borderMode=cv2.BORDER_REFLECT)
            k = int(1 + 25 * math.sin(math.pi * p))
            out = cv2.addWeighted(a2, 1 - p, b2, p, 0)
            return cv2.GaussianBlur(out, (0, 0), k / 6) if k > 3 else out
        if kind == "light":
            out = cv2.addWeighted(A, 1 - p, B, p, 0).astype(np.float32)
            xs = np.arange(W)[None, :] + np.arange(H)[:, None] * 0.4
            c = lerp(-600, W + H * 0.4 + 600, p)
            band = np.exp(-((xs - c) / 260) ** 2)[..., None] * np.array([150, 215, 255], np.float32)
            flash = math.sin(math.pi * p) * 0.9
            return np.clip(out + band * flash, 0, 255).astype(np.uint8)
        # fade / dissolve
        return cv2.addWeighted(A, 1 - p, B, p, 0)

    def finish(self, f, t, sh):
        # subtitles
        big = (sh["at"] == "hook")
        if sh["at"] != "end":
            fl = f.astype(np.float32) * self.botshade
            f = fl.astype(np.uint8)
            self.subs.draw(f, t, y_center=sh.get("sub_y", 1660 if sh.get("qr") else (1540 if sh["mode"] != "card" else 1560)))
        for s in self.shots:
            for ov in s.get("overlays", []):
                tr = t - ov["tt"]
                if 0 <= tr < ov["dur"] + 0.01:
                    {"title": draw_title, "lower3": draw_lower3, "chip": draw_chip,
                     "panel": draw_panel}[ov["kind"]](f, ov, tr, ov["dur"])
        # hook flash
        g = self.grain[int(t * FPS) % 6]
        out = f.astype(np.float32) * self.vig + g
        if t < 0.25: out = out + 255 * (1 - t / 0.25) ** 2 * 0.6
        if t > self.total - 1.0: out *= clamp01((self.total - t) / 1.0)
        return np.clip(out, 0, 255).astype(np.uint8)

# ============================================================== audio design
def midi_hz(n): return 440.0 * 2 ** ((n - 69) / 12)

def piano_note(f, L, vel, rng):
    n = int((L + 2.2) * SR); t = np.arange(n) / SR
    out = np.zeros(n, np.float32)
    for k in range(1, 8):
        fk = f * k * (1 + 0.0004 * k * k)
        if fk > 9000: break
        out += (np.sin(2 * np.pi * fk * t + rng.uniform(0, 6.28)) / k ** 1.4 *
                np.exp(-t * (0.9 + 0.55 * k + f / 1400))).astype(np.float32)
    out *= np.clip(t / 0.004, 0, 1)
    rel = np.clip(1 - (t - L - 0.15) / 0.9, 0, 1); out *= rel.astype(np.float32)
    return out * vel

def strings_chord(notes, L, rng):
    n = int((L + 2.5) * SR); t = np.arange(n) / SR
    env = (np.clip(t / 1.6, 0, 1) * np.clip((L + 2.5 - t) / 2.0, 0, 1)).astype(np.float32)
    st = np.zeros((n, 2), np.float32)
    for m in notes:
        f0 = midi_hz(m)
        for side, det in ((0, -0.0025), (1, 0.0025)):
            vib = 1 + 0.003 * np.sin(2 * np.pi * 5.2 * t + rng.uniform(0, 6))
            ph = 2 * np.pi * np.cumsum(f0 * (1 + det) * vib) / SR
            w = sum(np.sin(k * ph) / k for k in range(1, 7))
            st[:, side] += (w * env).astype(np.float32)
    return st

def sad_music(T, R, rng):
    """Original emotional piano + strings bed in A minor, 68 bpm."""
    from scipy.signal import butter, sosfilt, fftconvolve
    N = int(T * SR) + SR
    beat = 60 / 68; bar = 4 * beat
    # Am  F  C  G | Am  F  Dm  E
    prog = [(45, [57, 60, 64]), (41, [53, 57, 60]), (48, [55, 60, 64]), (43, [55, 59, 62]),
            (45, [57, 60, 64]), (41, [53, 57, 60]), (38, [53, 57, 62]), (40, [56, 59, 64])]
    mel = [[(0, 76, 2), (2, 74, 1), (3, 72, 1)], [(0, 72, 2), (2, 69, 2)],
           [(0, 67, 1.5), (1.5, 72, .5), (2, 76, 2)], [(0, 74, 3), (3, 71, 1)],
           [(0, 69, 2), (2, 72, 1), (3, 76, 1)], [(0, 77, 2), (2, 76, 1), (3, 72, 1)],
           [(0, 74, 2), (2, 72, 1), (3, 69, 1)], [(0, 71, 3), (3, 68, 1)]]
    piano = np.zeros(N, np.float32); strings = np.zeros((N, 2), np.float32)
    hook_end = R.tl.body_start
    nbars = int(T / bar) + 2
    for b in range(nbars):
        t0 = b * bar
        bass, tri = prog[b % 8]
        arp = [bass - 12 + 12, tri[1], tri[2], tri[0] + 12, tri[2], tri[1] + 12, tri[2], tri[1]]
        for e, m in enumerate(arp):
            ts = t0 + e * beat / 2
            if ts >= T: break
            nt = piano_note(midi_hz(m), beat / 2, 0.16 if e else 0.24, rng)
            i = int(ts * SR); j = min(N, i + len(nt)); piano[i:j] += nt[:j - i]
        if t0 >= hook_end - 0.5:        # melody enters after the hook
            for pos, m, L in mel[b % 8]:
                ts = t0 + pos * beat
                if ts >= T: break
                nt = piano_note(midi_hz(m), L * beat, 0.30, rng)
                i = int(ts * SR); j = min(N, i + len(nt)); piano[i:j] += nt[:j - i]
        stc = strings_chord([bass, tri[0], tri[1], tri[2]], bar, rng)
        i = int(max(0, t0 - 0.6) * SR); j = min(N, i + len(stc)); strings[i:j] += stc[:j - i] * 0.035
    strings = sosfilt(butter(2, 2200, "low", fs=SR, output="sos"), strings, axis=0).astype(np.float32)
    strings = sosfilt(butter(1, 90, "high", fs=SR, output="sos"), strings, axis=0).astype(np.float32)
    mus = np.stack([piano * 0.95, piano * 1.0], 1) + strings
    for c in range(2):
        ir = (rng.normal(0, 1, int(3.2 * SR)) * np.exp(-np.arange(int(3.2 * SR)) / (0.85 * SR))).astype(np.float32)
        ir /= np.sqrt((ir ** 2).sum())
        mus[:, c] = 0.62 * mus[:, c] + 0.38 * fftconvolve(mus[:, c], ir)[:N]
    rms = np.sqrt(np.mean(mus[:int(T * SR)] ** 2)) + 1e-9
    return mus * (0.06 / rms)

def synth_audio(R):
    from scipy.signal import butter, sosfilt
    voice = load_voice()
    T = R.total; N = int(T * SR) + SR
    vo = np.zeros(N, np.float32)
    for t0, a, b in R.tl.segs:
        seg = voice[int(a * SR):int(b * SR)].copy()
        fl = int(0.012 * SR); ramp = np.linspace(0, 1, fl, dtype=np.float32)
        seg[:fl] *= ramp; seg[-fl:] *= ramp[::-1]
        i0 = int(t0 * SR); vo[i0:i0 + len(seg)] += seg
    rng = np.random.default_rng(7)
    mus = sad_music(T, R, rng)
    # duck under the voice, swell at the end card
    hop = SR // 50
    e = np.convolve(np.abs(vo), np.ones(hop * 12) / (hop * 12), "same")
    duck = 1 - 0.45 * np.clip(e / (np.percentile(e[e > 1e-4], 85) + 1e-6), 0, 1)
    dyn = np.ones(N, np.float32)
    ie = int(R.tl.speech_end * SR); dyn[ie:] = np.linspace(1.0, 1.9, N - ie)
    dyn[:int(0.6 * SR)] = np.linspace(0.3, 1.0, int(0.6 * SR))
    mus *= (duck * dyn)[:, None]
    fo = int(2.0 * SR); mus[int(T * SR) - fo:int(T * SR)] *= np.linspace(1, 0, fo)[:, None]
    # ---- whoosh-only sound effects
    sfx = np.zeros((N, 2), np.float32)
    last = [-9.0]
    def whoosh(d=0.55, bright=1.0):
        n = int(d * SR); x = np.linspace(0, 1, n)
        nz = rng.normal(0, 1, n)
        lo = sosfilt(butter(2, [250, 2000], "band", fs=SR, output="sos"), nz)
        hi = sosfilt(butter(2, [1200, 5500 * bright], "band", fs=SR, output="sos"), nz)
        env = np.sin(np.pi * x ** 0.75) ** 2
        mix = lo * (1 - x) + hi * x * 0.7
        return np.stack([mix * env * (1 - 0.5 * x), mix * env * (0.5 + 0.5 * x)], 1).astype(np.float32)
    def put(sig, t, g, gap=0.5):
        if t - last[0] < gap: return
        last[0] = t
        i = int(t * SR); j = min(N, i + len(sig))
        if i < 0 or i >= N: return
        sfx[i:j] += sig[:j - i] * g
    events = [(0.0, "big")]
    for sh in R.shots[1:]:
        if sh["trans"] != "cut": events.append((sh["t0"] - 0.3, "trans"))
    for sh in R.shots:
        for ov in sh.get("overlays", []):
            if ov.get("sfx"): events.append((ov["tt"] - 0.15, "hi"))
        if "count" in sh: events.append((R.tl.tl(sh["count"]["t"]) - 0.15, "hi"))
        if "rm" in sh: events.append((R.tl.tl(sh["rm"]["t"]) - 0.15, "hi"))
        if sh.get("qr") and sh["at"] != "end": events.append((sh["t0"] + 0.05, "hi"))
    for tt in R.subs.imp_times: events.append((tt - 0.12, "word"))
    for tt, kind in sorted(events):
        if kind == "big": put(whoosh(0.9, 0.8), tt, 0.40, 0)
        elif kind == "trans": put(whoosh(0.6), tt, 0.30)
        elif kind == "hi": put(whoosh(0.5, 1.1), tt, 0.26)
        else: put(whoosh(0.35, 1.2), tt, 0.15, 0.9)
    mix = np.stack([vo, vo], 1) + mus + sfx
    mix = mix[:int(T * SR)]
    mix[-int(0.4 * SR):] *= np.linspace(1, 0, int(0.4 * SR))[:, None]
    peak = np.abs(mix).max()
    if peak > 0.98: mix *= 0.98 / peak
    out = "out/mix.wav"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(SR), "-ac", "2", "-i", "-",
                    "-af", "alimiter=limit=0.95", "-c:a", "pcm_s16le", out], input=mix.astype(np.float32).tobytes(), check=True)
    return out

# ============================================================== main
def render_range(args):
    a, b, path, preview = args
    R = Renderer(preview)
    scale = 0.5 if preview else 1.0
    ow, oh = int(W * scale) // 2 * 2, int(H * scale) // 2 * 2
    enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{ow}x{oh}",
                            "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "veryfast" if preview else "medium",
                            "-crf", "26" if preview else "18", "-pix_fmt", "yuv420p", path], stdin=subprocess.PIPE)
    for n in range(a, b):
        f = R.frame(n / FPS)
        if preview: f = cv2.resize(f, (ow, oh), interpolation=cv2.INTER_AREA)
        enc.stdin.write(f.tobytes())
        if (n - a) % 150 == 0: print(f"[{path}] {n - a}/{b - a}", flush=True)
    enc.stdin.close(); enc.wait()
    return path

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--preview", type=float, default=0, help="render first N seconds at half res")
    ap.add_argument("--stills", action="store_true")
    ap.add_argument("--at", type=float, nargs="*", help="still frames at these output times")
    ap.add_argument("--still-dir", default="out/stills")
    ap.add_argument("--workers", type=int, default=os.cpu_count())
    a = ap.parse_args()
    os.makedirs("out", exist_ok=True)
    R = Renderer()
    print(f"output duration {R.total:.2f}s  ({len(R.tl.segs)} segments)")
    for sh in R.shots:
        print(f"  {sh['t0']:7.2f}-{sh['t1']:7.2f}  {sh['mode']:5s} {sh.get('scene', ''):9s} <{sh['trans']}>")
    if a.stills or a.at:
        os.makedirs(a.still_dir, exist_ok=True)
        ts = a.at or [sh["t0"] + min(1.8, (sh["t1"] - sh["t0"]) * 0.6) for sh in R.shots]
        for t in ts:
            cv2.imwrite(f"{a.still_dir}/t{t:07.2f}.jpg", R.frame(t), [cv2.IMWRITE_JPEG_QUALITY, 88])
        print("stills written"); return
    total = int((a.preview or R.total) * FPS)
    k = max(1, a.workers)
    bounds = [int(total * i / k) for i in range(k + 1)]
    parts = [(bounds[i], bounds[i + 1], f"out/part{i}.mp4", bool(a.preview)) for i in range(k)]
    from multiprocessing import Pool
    with Pool(k) as pool: pool.map(render_range, parts)
    with open("out/parts.txt", "w") as fh:
        for p in parts: fh.write(f"file '{os.path.basename(p[2])}'\n")
    mix = synth_audio(R)
    name = "out/preview.mp4" if a.preview else "out/final.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", "out/parts.txt", "-i", mix,
                    "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest",
                    "-movflags", "+faststart", name], check=True)
    print("wrote", name)

if __name__ == "__main__":
    main()
