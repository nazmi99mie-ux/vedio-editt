"""Cinematic 9:16 da'wah edit renderer.

Usage: python3 render.py SRC.mp4 OUT_DIR [--preview a,b] [--workers N]
Renders video-only segments in parallel and concatenates them to OUT_DIR/video.mp4.
The timeline (shots, keywords, transitions) lives in timeline.py.
"""
import sys, os, json, math, subprocess, argparse, functools
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import timeline as TL

W, H, FPS = 1080, 1920, 30
SW, SH = 720, 1280
FONT_BLACK = "/usr/share/fonts/opentype/inter/InterDisplay-Black.otf"
FONT_BOLD = "/usr/share/fonts/opentype/inter/Inter-Bold.otf"
FONT_SEMI = "/usr/share/fonts/opentype/inter/Inter-SemiBold.otf"
FONT_SERIF = "/usr/share/fonts/truetype/crosextra/Caladea-Bold.ttf"
GOLD = (245, 197, 66)
GOLD_D = (120, 82, 18)
CREAM = (255, 246, 225)


def ease(p):  # smoothstep-ish ease in-out
    p = min(1.0, max(0.0, p))
    return p * p * (3 - 2 * p)


def ease_out(p):
    p = min(1.0, max(0.0, p))
    return 1 - (1 - p) ** 3


def ease_out_back(p, s=1.7):
    p = min(1.0, max(0.0, p)) - 1
    return 1 + (s + 1) * p ** 3 + s * p ** 2


# ---------------------------------------------------------------- source reader
class Reader:
    def __init__(self, path):
        self.path, self.proc, self.cur, self.frame = path, None, -1, None

    def _start(self, idx):
        if self.proc:
            self.proc.kill()
        self.proc = subprocess.Popen(
            ["ffmpeg", "-v", "error", "-ss", f"{idx / FPS:.4f}", "-i", self.path,
             "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE, bufsize=SW * SH * 3 * 4)
        self.cur = idx - 1

    def get(self, t):
        idx = max(0, int(round(t * FPS)))
        if self.proc is None or idx < self.cur or idx > self.cur + 60:
            self._start(idx)
        while self.cur < idx:
            buf = self.proc.stdout.read(SW * SH * 3)
            if len(buf) < SW * SH * 3:
                break  # past end: keep last frame
            self.frame = np.frombuffer(buf, np.uint8).reshape(SH, SW, 3)
            self.cur += 1
        return self.frame


# ---------------------------------------------------------------- face track
def load_face():
    pts = json.load(open(os.path.join(ROOT, "data", "face.json")))
    pts = [p for p in pts if p[3] > 0.12 and 0.15 < p[2] < 0.48]
    t = np.array([p[0] for p in pts]); x = np.array([p[1] for p in pts]); y = np.array([p[2] for p in pts])
    grid = np.arange(0, 80, 0.1)

    def smooth(v):
        g = np.interp(grid, t, v)
        med = np.array([np.median(g[max(0, i - 10):i + 11]) for i in range(len(g))])
        k = np.exp(-0.5 * (np.arange(-15, 16) / 6.0) ** 2); k /= k.sum()
        return np.convolve(np.pad(med, 15, mode="edge"), k, mode="valid")
    return grid, np.clip(smooth(x), 0.3, 0.7), np.clip(smooth(y), 0.24, 0.40)


FACE = load_face()


def face_at(src_t):
    g, x, y = FACE
    return float(np.interp(src_t, g, x)), float(np.interp(src_t, g, y))


# ---------------------------------------------------------------- photos
@functools.lru_cache(None)
def photo(name):
    im = cv2.cvtColor(cv2.imread(os.path.join(ROOT, "assets", "photos", name)), cv2.COLOR_BGR2RGB)
    return im


@functools.lru_cache(None)
def photo_blur(name):
    im = photo(name)
    s = max(W / im.shape[1], H / im.shape[0]) * 1.35
    small = cv2.resize(im, (int(im.shape[1] * s / 4), int(im.shape[0] * s / 4)), interpolation=cv2.INTER_AREA)
    small = cv2.GaussianBlur(small, (0, 0), 9)
    big = cv2.resize(small, (int(im.shape[1] * s), int(im.shape[0] * s)), interpolation=cv2.INTER_LINEAR)
    return (big.astype(np.float32) * 0.55).astype(np.uint8)


@functools.lru_cache(None)
def photo_card(name, width):
    """Photo with rounded corners + soft shadow, returned as RGBA float layer."""
    im = photo(name)
    s = width / im.shape[1]
    ch = int(im.shape[0] * s)
    card = cv2.resize(im, (width, ch), interpolation=cv2.INTER_AREA)
    pad = 60
    rgba = np.zeros((ch + 2 * pad, width + 2 * pad, 4), np.float32)
    mask = Image.new("L", (width, ch), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, width - 1, ch - 1], radius=36, fill=255)
    m = np.asarray(mask, np.float32) / 255
    sh = np.zeros((ch + 2 * pad, width + 2 * pad), np.float32)
    sh[pad + 18:pad + 18 + ch, pad:pad + width] = m * 0.7
    sh = cv2.GaussianBlur(sh, (0, 0), 22)
    rgba[..., 3] = sh
    a = m
    sl = (slice(pad, pad + ch), slice(pad, pad + width))
    rgba[sl[0], sl[1], :3] = card * a[..., None]
    rgba[sl[0], sl[1], 3] = a + sh[sl] * (1 - a)
    # gold hairline border
    border = np.zeros_like(m)
    bm = Image.new("L", (width, ch), 0)
    ImageDraw.Draw(bm).rounded_rectangle([1, 1, width - 2, ch - 2], radius=36, outline=255, width=3)
    border = np.asarray(bm, np.float32) / 255 * 0.8
    for c in range(3):
        rgba[sl[0], sl[1], c] = rgba[sl[0], sl[1], c] * (1 - border) + GOLD[c] * border
    return rgba  # premultiplied rgb, alpha


def warp(img, s, tx, ty, size=(W, H), border=cv2.BORDER_REFLECT):
    M = np.float32([[s, 0, tx], [0, s, ty]])
    return cv2.warpAffine(img, M, size, flags=cv2.INTER_LINEAR, borderMode=border)


def cover_xform(iw, ih, zoom, cx, cy, fx=0.5, fy=0.5):
    """Scale image to cover frame * zoom and put image point (cx,cy) at frame (fx,fy), clamped."""
    s = max(W / iw, H / ih) * zoom
    tx = W * fx - cx * iw * s
    ty = H * fy - cy * ih * s
    tx = min(0, max(W - iw * s, tx)); ty = min(0, max(H - ih * s, ty))
    return s, tx, ty


QC = {"on": False, "rec": False, "boxes": [], "base": None}


def over(base, rgba, x, y):
    """Composite premultiplied float RGBA layer onto float base at integer offset."""
    h, w = rgba.shape[:2]
    if QC["on"] and QC["rec"]:
        ys, xs = np.where(rgba[..., 3] > 0.35)
        if len(xs):
            QC["boxes"].append((x + xs.min(), y + ys.min(), x + xs.max(), y + ys.max()))
    x0, y0 = max(0, x), max(0, y)
    x1, y1 = min(base.shape[1], x + w), min(base.shape[0], y + h)
    if x1 <= x0 or y1 <= y0:
        return
    sub = rgba[y0 - y:y1 - y, x0 - x:x1 - x]
    a = sub[..., 3:4]
    base[y0:y1, x0:x1] = base[y0:y1, x0:x1] * (1 - a) + sub[..., :3]


# ---------------------------------------------------------------- atmosphere layers
RNG = np.random.default_rng(7)
PARTICLES = RNG.random((70, 5))  # x, y, size, speed, phase
BOKEH = RNG.random((9, 5))


def particle_layer(t, strength=1.0, warm=True, drift=(0.0, -1.0)):
    """Dust motes + large soft bokeh, rendered small and upscaled. Returns float additive layer."""
    lw, lh = W // 4, H // 4
    lay = np.zeros((lh, lw), np.float32)
    for x, y, s, sp, ph in PARTICLES:
        px = (x * lw + drift[0] * t * (6 + sp * 10) + 6 * math.sin(t * 0.7 + ph * 6)) % lw
        py = (y * lh + drift[1] * t * (5 + sp * 9)) % lh
        a = 0.35 + 0.65 * (0.5 + 0.5 * math.sin(t * 1.3 + ph * 9))
        cv2.circle(lay, (int(px), int(py)), 1 if s < 0.7 else 2, a, -1, lineType=cv2.LINE_AA)
    lay = cv2.GaussianBlur(lay, (0, 0), 0.8)
    big = np.zeros((lh, lw), np.float32)
    for x, y, s, sp, ph in BOKEH:  # foreground bokeh moves faster -> parallax depth
        px = (x * lw * 1.4 + drift[0] * t * (18 + sp * 14) + (1 - drift[0]) * 0) % (lw * 1.4) - lw * 0.2
        py = (y * lh * 1.4 + drift[1] * t * (14 + sp * 12)) % (lh * 1.4) - lh * 0.2
        cv2.circle(big, (int(px), int(py)), int(14 + s * 30), 0.10 + 0.08 * sp, -1, lineType=cv2.LINE_AA)
    big = cv2.GaussianBlur(big, (0, 0), 9)
    lay = cv2.resize(lay * 0.55 + big, (W, H), interpolation=cv2.INTER_LINEAR) * strength
    tint = np.array([1.0, 0.86, 0.6] if warm else [0.85, 0.92, 1.0], np.float32) * 255
    return lay[..., None] * tint


def light_sweep(img, p, width=260, strength=0.35, angle=0.35):
    """Diagonal soft light band crossing the frame as p goes 0->1."""
    if p <= 0 or p >= 1:
        return img
    yy, xx = np.mgrid[0:H // 8, 0:W // 8].astype(np.float32) * 8
    pos = -400 + p * (W + H * angle + 800)
    d = np.abs(xx + yy * angle - pos)
    band = np.clip(1 - d / width, 0, 1) ** 2 * strength * math.sin(math.pi * p)
    band = cv2.resize(band, (W, H))[..., None]
    return img + band * np.array([255, 236, 200], np.float32)


# ---------------------------------------------------------------- grading
def make_lut(lift, gamma, gain, contrast):
    x = np.linspace(0, 1, 256)
    out = []
    for c in range(3):
        v = np.clip(x * gain[c] + lift[c] * (1 - x), 0, 1) ** (1 / gamma[c])
        v = v + contrast * (v - 0.5) * (1 - np.abs(2 * v - 1)) * 1.2  # gentle S-curve
        out.append(np.clip(v * 255, 0, 255).astype(np.uint8))
    return np.stack(out, 1).reshape(256, 1, 3)


MOODS = {
    # lift, gamma, gain, contrast, saturation, vignette
    "warm":    (make_lut((0.030, 0.034, 0.040), (1.0, 0.98, 0.95), (1.03, 1.0, 0.94), 0.32), 1.06, 0.38),
    "neutral": (make_lut((0.020, 0.028, 0.034), (1.0, 1.0, 0.98), (1.0, 1.0, 0.97), 0.30), 1.02, 0.36),
    "somber":  (make_lut((0.030, 0.040, 0.052), (0.97, 0.98, 1.0), (0.97, 0.98, 1.0), 0.40), 0.80, 0.50),
    "golden":  (make_lut((0.050, 0.040, 0.030), (1.04, 1.0, 0.92), (1.05, 0.99, 0.88), 0.30), 1.0, 0.45),
}
_yy, _xx = np.mgrid[0:H, 0:W].astype(np.float32)
VIG = (((_xx - W / 2) / (W * 0.62)) ** 2 + ((_yy - H * 0.45) / (H * 0.62)) ** 2)
VIG = np.clip(VIG, 0, 1.6)[..., None]
del _xx, _yy
GRAIN = [cv2.resize(RNG.normal(0, 1, (H // 2, W // 2)).astype(np.float32), (W, H))[..., None] for _ in range(6)]


def grade(img_f, mood, frame_i, exposure=1.0):
    lut, sat, vig = MOODS[mood]
    u8 = np.clip(img_f * exposure, 0, 255).astype(np.uint8)
    u8 = cv2.LUT(u8, lut)
    f = u8.astype(np.float32)
    if abs(sat - 1) > 0.01:
        L = f @ np.array([0.299, 0.587, 0.114], np.float32)
        f = L[..., None] + (f - L[..., None]) * sat
    f *= (1 - vig * VIG * 0.55)
    f += GRAIN[frame_i % 6] * 4.5
    return f


# ---------------------------------------------------------------- text rendering
@functools.lru_cache(4096)
def font(path, size):
    return ImageFont.truetype(path, size)


@functools.lru_cache(2048)
def word_img(text, size, color, stroke=7, path=FONT_BLACK):
    f = font(path, size)
    l, t, r, b = f.getbbox(text, stroke_width=stroke)
    w, h = r - l + 24, b - t + 30
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    sh = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(sh).text((12 - l + 4, 12 - t + 7), text, font=f, fill=(0, 0, 0, 170), stroke_width=stroke, stroke_fill=(0, 0, 0, 170))
    sh = sh.filter(ImageFilter.GaussianBlur(5))
    im.alpha_composite(sh)
    ImageDraw.Draw(im).text((12 - l, 12 - t), text, font=f, fill=color + (255,), stroke_width=stroke, stroke_fill=(10, 10, 10, 255))
    a = np.asarray(im, np.float32) / 255
    a[..., :3] *= a[..., 3:4] * 255
    return a, (-l + 12, -t + 12)


def scaled(rgba, s):
    if abs(s - 1) < 0.01:
        return rgba
    h, w = rgba.shape[:2]
    return cv2.resize(rgba, (max(1, int(w * s)), max(1, int(h * s))), interpolation=cv2.INTER_LINEAR)


@functools.lru_cache(256)
def keyword_img(text, style):
    """Big kinetic keyword with subtle 3D extrusion + glow. Returns premultiplied RGBA float."""
    if style == "serif":
        f, face, ext, glow = font(FONT_SERIF, 150), GOLD, GOLD_D, (255, 210, 120)
    elif style == "whitesm":
        f, face, ext, glow = font(FONT_BLACK, 84), CREAM, (70, 60, 50), (255, 240, 210)
    elif style == "white":
        f, face, ext, glow = font(FONT_BLACK, 120), CREAM, (70, 60, 50), (255, 240, 210)
    elif style == "hook":
        f, face, ext, glow = font(FONT_BLACK, 112), CREAM, (60, 45, 20), (255, 220, 150)
    elif style == "hookgold":
        f, face, ext, glow = font(FONT_BLACK, 112), GOLD, GOLD_D, (255, 200, 90)
    else:  # gold
        f, face, ext, glow = font(FONT_BLACK, 130), GOLD, GOLD_D, (255, 200, 90)
    lines = text.split("\n")
    sizes = [f.getbbox(ln) for ln in lines]
    lh = int(f.size * 1.08)
    w = max(b[2] - b[0] for b in sizes) + 120
    h = lh * len(lines) + 120
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    gl = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    dr, dg = ImageDraw.Draw(im), ImageDraw.Draw(gl)
    depth = 9
    for i, ln in enumerate(lines):
        b = sizes[i]
        x = (w - (b[2] - b[0])) // 2 - b[0]
        y = 50 + i * lh - b[1] + (lh - (b[3] - b[1])) // 2
        dg.text((x, y), ln, font=f, fill=glow + (150,))
        dr.text((x + 5, y + depth + 8), ln, font=f, fill=(0, 0, 0, 140))  # drop shadow
        for d in range(depth, 0, -1):  # extrusion
            k = 0.55 + 0.45 * (1 - d / depth)
            dr.text((x + d * 0.5, y + d), ln, font=f, fill=tuple(int(c * k) for c in ext) + (255,))
        dr.text((x, y), ln, font=f, fill=face + (255,), stroke_width=2, stroke_fill=tuple(min(255, c + 20) for c in face) + (255,))
        # top highlight gradient on face
    gl = gl.filter(ImageFilter.GaussianBlur(22))
    out = Image.alpha_composite(gl, im)
    a = np.asarray(out, np.float32) / 255
    # vertical sheen on the face colour
    grad = np.linspace(1.12, 0.88, h, dtype=np.float32)[:, None, None]
    a[..., :3] = np.clip(a[..., :3] * grad, 0, 1)
    a[..., :3] *= a[..., 3:4] * 255
    return a


def draw_keyword(base, kw, t):
    t0, t1, text, style, yc, direction = kw
    if t < t0 - 0.01 or t > t1 + 0.35:
        return
    img = keyword_img(text, style)
    pin = (t - t0) / (0.45 if style != "serif" else 0.9)
    pout = (t - t1) / 0.35
    alpha = min(1.0, max(0.0, pin * 1.6)) * (1 - min(1.0, max(0.0, pout)))
    if alpha <= 0:
        return
    s = 1.0
    dx = dy = 0.0
    if style == "serif":  # respectful slow reveal: soft scale-down + fade, no shake
        s = 1.08 - 0.08 * ease_out(pin)
    else:
        e = ease_out_back(pin)
        dist = 260
        if direction == "L": dx = -(1 - e) * dist
        elif direction == "R": dx = (1 - e) * dist
        elif direction == "U": dy = -(1 - e) * dist * 0.6
        elif direction == "D": dy = (1 - e) * dist * 0.6
        else: s = 1.35 - 0.35 * ease_out_back(pin, 2.2)
        if style in ("hook", "hookgold") and 0.35 < pin < 0.7:  # minimal impact shake
            dx += math.sin(t * 90) * 4; dy += math.cos(t * 77) * 3
    s *= 1 + max(0.0, pout) * 0.12 + 0.025 * min(1.0, max(0.0, t - t0) / max(0.1, t1 - t0))
    im = scaled(img, s) * alpha
    h, w = im.shape[:2]
    over(base, im, int(W / 2 - w / 2 + dx), int(yc - h / 2 + dy))


# subtitle chunks --------------------------------------------------------------
WORDS = json.load(open(os.path.join(ROOT, "data", "words_final.json")))


def build_chunks():
    chunks, cur = [], []
    for w in WORDS:
        if cur and (w["seg"] != cur[-1]["seg"] or len(cur) >= 3 or sum(len(x["w"]) for x in cur) + len(w["w"]) > 20):
            chunks.append(cur); cur = []
        cur.append(w)
    chunks.append(cur)
    out = []
    for i, c in enumerate(chunks):
        nxt = chunks[i + 1][0]["s"] if i + 1 < len(chunks) else c[-1]["e"] + 1
        out.append((c[0]["s"] - 0.05, min(c[-1]["e"] + 0.5, nxt - 0.02), c))
    return out


CHUNKS = build_chunks()
SUB_SIZE = 70


def draw_subs(base, src_t, y_center):
    for a, b, c in CHUNKS:
        if a <= src_t <= b:
            break
    else:
        return
    items = []
    for w in c:
        if src_t < w["s"] - 0.04:
            continue
        txt = w["w"].upper()
        active = w["s"] - 0.04 <= src_t <= w["e"] + 0.05
        col = GOLD if active else (255, 255, 255)
        img, _ = word_img(txt, SUB_SIZE, col)
        p = (src_t - w["s"] + 0.04) / 0.16
        s = 0.7 + 0.3 * ease_out_back(p, 2.5)
        items.append((img, s, min(1.0, max(0.0, p * 2.5))))
    if not items:
        return
    # layout with full-size widths of the whole chunk (stable positions)
    full = [word_img(w["w"].upper(), SUB_SIZE, (255, 255, 255))[0] for w in c]
    gap = -6
    widths = [im.shape[1] for im in full]
    lines, cur, cw = [], [], 0
    for i, wd in enumerate(widths):
        if cur and cw + wd > 940:
            lines.append(cur); cur, cw = [], 0
        cur.append(i); cw += wd + gap
    lines.append(cur)
    lh = 86
    y0 = y_center - lh * len(lines) / 2
    for li, line in enumerate(lines):
        tw = sum(widths[i] for i in line) + gap * (len(line) - 1)
        x = W / 2 - tw / 2
        for i in line:
            if i < len(items):
                img, s, al = items[i]
                im = scaled(img, s) * al
                h, w = im.shape[:2]
                cx, cy = x + widths[i] / 2, y0 + li * lh + lh / 2
                over(base, im, int(cx - w / 2), int(cy - h / 2))
            x += widths[i] + gap


# lower-third pill ---------------------------------------------------------------
@functools.lru_cache(16)
def pill_img(line1, line2):
    f1, f2 = font(FONT_BOLD, 40), font(FONT_SEMI, 32)
    w = int(max(f1.getlength(line1), f2.getlength(line2))) + 150
    h = 128
    im = Image.new("RGBA", (w + 40, h + 40), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    sh = Image.new("RGBA", im.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle([20, 26, w + 20, h + 26], radius=30, fill=(0, 0, 0, 120))
    im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(10)))
    d.rounded_rectangle([20, 20, w + 20, h + 20], radius=30, fill=(12, 40, 30, 215), outline=GOLD + (230,), width=3)
    # pin icon
    cx, cy = 70, 20 + h // 2 - 6
    d.ellipse([cx - 18, cy - 22, cx + 18, cy + 14], fill=GOLD + (255,))
    d.polygon([(cx - 15, cy + 2), (cx + 15, cy + 2), (cx, cy + 30)], fill=GOLD + (255,))
    d.ellipse([cx - 7, cy - 11, cx + 7, cy + 3], fill=(12, 40, 30, 255))
    d.text((110, 34), line1, font=f1, fill=(255, 255, 255, 255))
    d.text((110, 84), line2, font=f2, fill=GOLD + (255,))
    a = np.asarray(im, np.float32) / 255
    a[..., :3] *= a[..., 3:4] * 255
    return a


def draw_pill(base, lt, t):
    t0, t1, l1, l2, y = lt
    if not (t0 <= t <= t1 + 0.4):
        return
    p = ease_out((t - t0) / 0.5)
    q = ease((t - t1) / 0.4) if t > t1 else 0
    img = pill_img(l1, l2)
    al = p * (1 - q)
    x = int(-img.shape[1] + (60 + img.shape[1]) * p - q * 80)
    over(base, img * al, x, y)


FONTS = {"bold": FONT_BOLD, "semi": FONT_SEMI, "serif": FONT_SERIF, "black": FONT_BLACK}
COLS = {"cream": CREAM, "gold": GOLD}


@functools.lru_cache(64)
def text_img(text, fk, size, ck):
    f = font(FONTS[fk], size)
    l, t, r, b = f.getbbox(text)
    w, h = r - l + 40, b - t + 40
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    sh = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(sh).text((20 - l + 2, 20 - t + 4), text, font=f, fill=(0, 0, 0, 200))
    im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(6)))
    ImageDraw.Draw(im).text((20 - l, 20 - t), text, font=f, fill=COLS[ck] + (255,))
    a = np.asarray(im, np.float32) / 255
    a[..., :3] *= a[..., 3:4] * 255
    return a


def draw_textcard(base, i, tc, t):
    t0, fk, size, ck, y, text = tc
    t1 = TL.TEXT_END.get(i, TL.TOTAL + 5)
    if t < t0 or t > t1 + 0.3:
        return
    p = ease_out((t - t0) / 0.6)
    al = p * (1 - min(1.0, max(0.0, (t - t1) / 0.3)))
    im = text_img(text, fk, size, ck) * al
    over(base, im, int(W / 2 - im.shape[1] / 2), int(y - im.shape[0] / 2 + (1 - p) * 30))


# ---------------------------------------------------------------- shot renderers
class Ctx:
    def __init__(self, src):
        self.main = Reader(src)
        self.hook = Reader(src)


def src_time(t):
    if t < TL.HOOK_DUR:
        return TL.HOOK_SRC + t
    return t - TL.MAIN_OFFSET


def speaker(ctx, t, z, drift=(0, 0), fy=0.33, oh=H):
    st = src_time(t)
    rd = ctx.hook if t < TL.HOOK_DUR else ctx.main
    fr = rd.get(min(max(st, 0), TL.SRC_END))
    cx, cy = face_at(st)
    s = 1.5 * z
    tx = W / 2 - cx * SW * s + drift[0]
    ty = oh * fy - cy * SH * s + drift[1]
    tx = min(0, max(W - SW * s, tx)); ty = min(0, max(oh - SH * s, ty))
    return warp(fr, s, tx, ty, size=(W, oh)).astype(np.float32)


def render_shot(ctx, sh, t):
    kind, t0, t1, prm = sh["kind"], sh["t0"], sh["t1"], sh
    p = (t - t0) / max(1e-6, t1 - t0)
    pe = ease(p)
    if kind == "spk":
        z0, z1 = prm.get("z", (1.0, 1.1))
        z = z0 + (z1 - z0) * pe
        if prm.get("punch"):
            z *= 1 + 0.10 * (1 - ease_out((t - t0) / 0.28)) if t >= t0 else 1.10
        d0, d1 = prm.get("drift", ((0, 0), (0, 0)))
        drift = (d0[0] + (d1[0] - d0[0]) * pe, d0[1] + (d1[1] - d0[1]) * pe)
        img = speaker(ctx, t, z, drift)
        if prm.get("parts", True):
            img += particle_layer(t, 0.5, True)
        return img
    if kind == "fill":
        name = prm["img"]; im = photo(name)
        (zx0, zx1), (c0, c1) = prm["zoom"], prm["path"]
        z = zx0 + (zx1 - zx0) * pe
        cx = c0[0] + (c1[0] - c0[0]) * pe; cy = c0[1] + (c1[1] - c0[1]) * pe
        s, tx, ty = cover_xform(im.shape[1], im.shape[0], z, cx, cy)
        img = warp(im, s, tx, ty).astype(np.float32)
        dirv = prm.get("pdrift", (0.0, -1.0))
        img += particle_layer(t, 0.9, True, dirv)
        return img
    if kind == "land":
        # whole aerial in a wide band (full extent visible) over a moving blurred copy;
        # gold boundary is traced around the complete empty land, then filled
        name = prm["img"]; im = photo(name); ih, iw = im.shape[:2]
        bg = photo_blur(name); bh, bw = bg.shape[:2]
        img = warp(bg, 1.0, (W - bw) / 2 - 120 * pe, -(bh - H) * (0.3 + 0.4 * pe)).astype(np.float32)
        (zx0, zx1), (c0, c1) = prm["zoom"], prm["path"]
        z = zx0 + (zx1 - zx0) * pe
        cx = c0[0] + (c1[0] - c0[0]) * pe
        y0 = prm.get("yc", 830)
        sc = W * z / iw
        tx = W / 2 - cx * iw * sc; ty = y0 - 0.5 * ih * sc
        band = warp(im, sc, tx, ty, border=cv2.BORDER_CONSTANT).astype(np.float32)
        msk = np.zeros((H, 1), np.float32)
        top, bot = max(0, ty), min(H, ty + ih * sc)
        yy = np.arange(H, dtype=np.float32)[:, None]
        msk = np.clip((yy - top) / 40, 0, 1) * np.clip((bot - yy) / 40, 0, 1)
        img = img * (1 - msk[..., None]) + band * msk[..., None]
        ds, dd = prm.get("draw", (0.3, 1.8))
        draw_outline(img, prm["poly"], sc, tx, ty, (t - t0 - ds) / dd, t)
        img += particle_layer(t, 0.6, True, (1.0, -0.3))
        return img
    if kind == "reveal":
        # before -> after: empty land wipes up into the development illustration
        A = render_shot(ctx, dict(prm["a"], t0=t0, t1=t1), t)
        B = render_shot(ctx, dict(prm["b"], t0=t0, t1=t1), t)
        ws, wd = prm["wipe"]
        q = ease((t - t0 - ws) / wd)
        if q <= 0:
            return A
        if q >= 1:
            return B
        edge = H * (1.08 - 1.16 * q)  # wipe line moves bottom -> top
        yy = np.arange(H, dtype=np.float32)[:, None, None]
        m = np.clip((yy - edge) / 90 + 0.5, 0, 1)
        img = A * (1 - m) + B * m
        glow = np.exp(-((yy - edge) / 26) ** 2) * 0.85
        img += glow * np.array([255, 225, 150], np.float32)
        return img
    if kind == "card":
        name = prm["img"]; im = photo(name)
        bg = photo_blur(name)
        bh, bw = bg.shape[:2]
        (b0, b1) = prm["bgpath"]  # bg moves slowly (vertical)
        by = b0 + (b1 - b0) * pe
        img = warp(bg, 1.0, (W - bw) / 2, -(bh - H) * by).astype(np.float32)
        cw = prm.get("cw", 980)
        card = photo_card(name, cw)
        (x0, x1), (y0, y1) = prm["cardx"], prm["cardy"]
        s = prm.get("cz", (1.0, 1.06)); sc = s[0] + (s[1] - s[0]) * pe
        c = scaled(card, sc)
        cx = W / 2 + x0 + (x1 - x0) * pe; cy = H * 0.42 + y0 + (y1 - y0) * pe
        over(img, c, int(cx - c.shape[1] / 2), int(cy - c.shape[0] / 2))
        img += particle_layer(t, prm.get("parts", 1.0), True, prm.get("pdrift", (-1.0, -0.3)))
        return img
    if kind == "split":
        # top: B-roll sliding horizontally, bottom: speaker. thin gold divider
        im = photo(prm["img"])
        top_h = int(H * 0.40)
        s = max(W / im.shape[1], top_h / im.shape[0]) * 1.25
        span = im.shape[1] * s - W
        tx = -span * (0.15 + 0.7 * pe)
        top = cv2.warpAffine(im, np.float32([[s, 0, tx], [0, s, -(im.shape[0] * s - top_h) * 0.5]]), (W, top_h), flags=cv2.INTER_LINEAR)
        img = np.zeros((H, W, 3), np.float32)
        img[top_h:] = speaker(ctx, t, prm.get("z", 1.35), fy=0.24, oh=H - top_h)
        slide = ease_out((t - t0) / 0.45)
        yoff = int(-top_h * (1 - slide))
        img[max(0, yoff):top_h + yoff] = top[max(0, -yoff):].astype(np.float32)
        if top_h + yoff > 0:
            img[max(0, top_h + yoff - 3):top_h + yoff + 3] = np.array(GOLD, np.float32)
        img += particle_layer(t, 0.5, True)
        return img
    if kind == "title":
        name = prm["img"]; bg = photo_blur(name)
        bh, bw = bg.shape[:2]
        img = warp(bg, 1.0, (W - bw) / 2, -(bh - H) * (0.6 - 0.3 * pe)).astype(np.float32) * 0.8
        img += particle_layer(t, 1.3, True, (0.0, -1.0))
        return img
    raise ValueError(kind)


def draw_outline(img, poly, sc, tx, ty, prog, t):
    if prog <= 0:
        return
    pts = np.array(poly, np.float32) * sc + np.float32([tx, ty])
    seg = np.r_[pts, pts[:1]]
    lens = np.linalg.norm(np.diff(seg, axis=0), axis=1)
    total = lens.sum(); target = min(1.0, prog) * total
    path = [seg[0]]; acc = 0.0
    for i, L in enumerate(lens):
        if acc + L >= target:
            path.append(seg[i] + (seg[i + 1] - seg[i]) * ((target - acc) / L)); break
        path.append(seg[i + 1]); acc += L
    path = np.array(path)
    lw, lh = W // 2, H // 2
    line = np.zeros((lh, lw), np.float32)
    cv2.polylines(line, [(path / 2).astype(np.int32)], False, 1.0, 3, cv2.LINE_AA)
    fill = np.zeros((lh, lw), np.float32)
    fa = min(1.0, max(0.0, (prog - 1.0) / 0.5))
    if fa > 0:
        cv2.fillPoly(fill, [(pts / 2).astype(np.int32)], 1.0, cv2.LINE_AA)
        fill *= fa * (0.28 + 0.07 * math.sin(t * 4))
    glow = cv2.GaussianBlur(line, (0, 0), 7) * 1.6
    lay = cv2.resize(np.clip(line + glow * 0.6, 0, 1.4), (W, H))[..., None]
    fl = cv2.resize(fill, (W, H))[..., None]
    gold = np.array(GOLD, np.float32)
    img[:] = img * (1 - fl) + gold * fl
    img[:] = img * (1 - np.clip(lay, 0, 1) * 0.6) + gold * lay * 0.75 + 255 * np.clip(line_full := cv2.resize(line, (W, H)), 0, 1)[..., None] * 0.35
    # pulsing pin on the leading point
    hx, hy = path[-1]
    if prog < 1.0:
        cv2.circle(img, (int(hx), int(hy)), 14, (255, 240, 200), -1, cv2.LINE_AA)
        cv2.circle(img, (int(hx), int(hy)), int(24 + 8 * math.sin(t * 12)), GOLD, 3, cv2.LINE_AA)


def motion_blur(img, length, horizontal=True):
    L = int(length)
    if L < 3:
        return img
    small = cv2.resize(img, (W // 2, H // 2))
    k = np.zeros((L // 2 * 2 + 1,) * 2, np.float32)
    if horizontal: k[k.shape[0] // 2, :] = 1
    else: k[:, k.shape[1] // 2] = 1
    k /= k.sum()
    small = cv2.filter2D(small, -1, k)
    return cv2.resize(small, (W, H))


def shift(img, dx, dy):
    return cv2.warpAffine(img, np.float32([[1, 0, dx], [0, 1, dy]]), (W, H), borderMode=cv2.BORDER_CONSTANT)


def compose(ctx, t, fi):
    shots = TL.SHOTS
    idx = next((i for i, s in enumerate(shots) if s["t0"] <= t < s["t1"]), len(shots) - 1)
    cur = shots[idx]
    img = None
    # transition with neighbour?
    for a, b in ((idx - 1, idx), (idx, idx + 1)):
        if a < 0 or b >= len(shots):
            continue
        B = shots[b]; tr = B.get("tr", "cut"); d = B.get("trd", 0.4)
        bnd = B["t0"]
        if tr in ("cut", "punch") or not (bnd - d / 2 <= t < bnd + d / 2):
            continue
        p = (t - (bnd - d / 2)) / d; e = ease(p)
        A_img = render_shot(ctx, shots[a], t); B_img = render_shot(ctx, B, t)
        bump = math.sin(math.pi * p)
        if tr in ("whipL", "whipR"):
            sg = -1 if tr == "whipL" else 1
            img = shift(A_img, sg * e * W, 0) + shift(B_img, -sg * (1 - e) * W, 0)
            img = motion_blur(img, bump * 110, True)
        elif tr in ("slideU", "slideD"):
            sg = -1 if tr == "slideU" else 1
            img = shift(A_img, 0, sg * e * H) + shift(B_img, 0, -sg * (1 - e) * H)
            img = motion_blur(img, bump * 110, False)
        elif tr == "zoom":
            za = 1 + 0.5 * e; zb = 0.82 + 0.18 * e
            Az = warp(A_img, za, W / 2 * (1 - za), H / 2 * (1 - za))
            Bz = warp(B_img, zb, W / 2 * (1 - zb), H / 2 * (1 - zb))
            img = Az * (1 - e) + Bz * e
            if bump > 0.2:
                k = int(bump * 14) * 2 + 1
                img = cv2.GaussianBlur(img, (k, k), 0)
        elif tr == "sweep":
            img = A_img * (1 - e) + B_img * e
            img = light_sweep(img, p, 300, 0.45)
        elif tr == "fade":
            img = A_img * (1 - e) + B_img * e
        break
    if img is None:
        img = render_shot(ctx, cur, t)
    mood = cur.get("mood", "warm")
    exp = 1.0
    for (a, b, e0, e1) in TL.EXPOSURE:
        if a <= t < b:
            exp = e0 + (e1 - e0) * ease((t - a) / (b - a))
    img = grade(img, mood, fi, exp)
    for ls in TL.SWEEPS:
        if ls[0] <= t <= ls[1]:
            img = light_sweep(img, (t - ls[0]) / (ls[1] - ls[0]), 340, 0.28)
    # overlays
    if QC["on"]:
        QC["base"] = np.clip(img, 0, 255).astype(np.uint8); QC["boxes"] = []; QC["rec"] = True
    for kw in TL.KEYWORDS:
        draw_keyword(img, kw, t)
    for lt in TL.PILLS:
        draw_pill(img, lt, t)
    for i, tc in enumerate(TL.TEXTCARDS):
        draw_textcard(img, i, tc, t)
    if TL.BODY_T0 <= t < TL.MAIN_OFFSET + TL.SRC_END + 0.4:
        st = src_time(t)
        draw_subs(img, st, TL.sub_y(t))
    QC["rec"] = False
    # fade from/to black
    if t < 0.12:
        img *= t / 0.12
    if t > TL.TOTAL - 1.2:
        img *= max(0.0, (TL.TOTAL - t) / 1.2)
    return np.clip(img, 0, 255).astype(np.uint8)


def render_range(src, f0, f1, out):
    ctx = Ctx(src)
    enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                            "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "17", "-pix_fmt", "yuv420p", out], stdin=subprocess.PIPE)
    for fi in range(f0, f1):
        enc.stdin.write(compose(ctx, fi / FPS, fi).tobytes())
        if (fi - f0) % 150 == 0:
            print(f"[{os.path.basename(out)}] {fi - f0}/{f1 - f0}", flush=True)
    enc.stdin.close(); enc.wait()


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("src"); ap.add_argument("outdir")
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--range", default=None, help="t0,t1 seconds (preview)")
    ap.add_argument("--stills", default=None, help="comma separated times -> png")
    a = ap.parse_args()
    os.makedirs(a.outdir, exist_ok=True)
    if a.stills:
        ctx = Ctx(a.src)
        for s in a.stills.split(","):
            t = float(s)
            cv2.imwrite(os.path.join(a.outdir, f"still_{t:06.2f}.jpg"), cv2.cvtColor(compose(ctx, t, int(t * FPS)), cv2.COLOR_RGB2BGR), [cv2.IMWRITE_JPEG_QUALITY, 85])
        sys.exit()
    t0, t1 = (0, TL.TOTAL) if not a.range else map(float, a.range.split(","))
    F0, F1 = int(t0 * FPS), int(t1 * FPS)
    n = a.workers
    bounds = [F0 + (F1 - F0) * i // n for i in range(n + 1)]
    from multiprocessing import Process
    parts = [os.path.join(a.outdir, f"part{i}.mp4") for i in range(n)]
    ps = [Process(target=render_range, args=(a.src, bounds[i], bounds[i + 1], parts[i])) for i in range(n)]
    [p.start() for p in ps]; [p.join() for p in ps]
    with open(os.path.join(a.outdir, "parts.txt"), "w") as f:
        f.writelines(f"file '{p}'\n" for p in parts)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", os.path.join(a.outdir, "parts.txt"), "-c", "copy",
                    os.path.join(a.outdir, "video.mp4")], check=True)
    print("done", os.path.join(a.outdir, "video.mp4"))
