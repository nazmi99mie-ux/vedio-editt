"""Render the cinematic 9:16 1080p dakwah video (video track only).

usage: python3 render.py SOURCE.mp4 OUT_video.mp4 [--preview START END]
"""
import os, sys, math, subprocess, random
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import edit_plan as P

HERE = P.HERE
W, H, FPS = 1080, 1920, P.FPS
ASSET = os.path.join(HERE, "assets")
F_INTER_BLACK = "/usr/share/fonts/opentype/inter/Inter-Black.otf"
F_INTER_BOLD = "/usr/share/fonts/opentype/inter/Inter-Bold.otf"
F_INTER_SEMI = "/usr/share/fonts/opentype/inter/Inter-SemiBold.otf"
F_CINZEL = os.path.join(ASSET, "fonts", "Cinzel.ttf")

GOLD = (66, 197, 245)        # BGR of #F5C542
GOLD_RGB = (245, 197, 66)
EMERALD_RGB = (12, 122, 76)
CREAM_RGB = (250, 244, 228)

SFX = []  # (time, kind) collected for the audio mixer


def ease_out(x):
    x = min(max(x, 0.0), 1.0)
    return 1 - (1 - x) ** 3


def ease_io(x):
    x = min(max(x, 0.0), 1.0)
    return x * x * (3 - 2 * x)


def back_out(x, s=1.7):
    x = min(max(x, 0.0), 1.0) - 1
    return x * x * ((s + 1) * x + s) + 1


def font(path, size, wght=None):
    f = ImageFont.truetype(path, size)
    if wght is not None:
        try:
            f.set_variation_by_axes([wght])
        except Exception:
            pass
    return f


# ---------------------------------------------------------------- compositing
def blend(dst, rgba, x, y, alpha=1.0):
    """Alpha-blend an RGBA (numpy, BGR+A uint8) sprite onto dst at (x, y)."""
    h, w = rgba.shape[:2]
    x0, y0 = max(x, 0), max(y, 0)
    x1, y1 = min(x + w, dst.shape[1]), min(y + h, dst.shape[0])
    if x1 <= x0 or y1 <= y0 or alpha <= 0.003:
        return
    s = rgba[y0 - y:y1 - y, x0 - x:x1 - x]
    a = s[:, :, 3:4].astype(np.float32) * (alpha / 255.0)
    d = dst[y0:y1, x0:x1, :3].astype(np.float32)
    dst[y0:y1, x0:x1, :3] = (d + (s[:, :, :3].astype(np.float32) - d) * a).astype(np.uint8)


def pil_to_rgba(im):
    a = np.array(im.convert("RGBA"))
    return np.dstack([a[:, :, 2], a[:, :, 1], a[:, :, 0], a[:, :, 3]])


def scale_sprite(sp, s):
    if abs(s - 1) < 0.01:
        return sp
    h, w = sp.shape[:2]
    return cv2.resize(sp, (max(1, int(w * s)), max(1, int(h * s))), interpolation=cv2.INTER_LINEAR)


_text_cache = {}


def text_sprite(text, size, fill=(255, 255, 255), fpath=F_INTER_BLACK, stroke=0, glow=0,
                glow_col=(0, 0, 0), shadow=10, track=0, wght=None, grad=None):
    key = (text, size, fill, fpath, stroke, glow, glow_col, shadow, track, wght, grad)
    if key in _text_cache:
        return _text_cache[key]
    f = font(fpath, size, wght)
    # measure with tracking
    widths = [f.getlength(c) for c in text]
    tw = int(sum(widths) + track * max(len(text) - 1, 0))
    asc, desc = f.getmetrics()
    pad = max(stroke, glow, shadow) * 2 + 16
    Wd, Hd = tw + 2 * pad, asc + desc + 2 * pad
    mask = Image.new("L", (Wd, Hd), 0)
    d = ImageDraw.Draw(mask)
    x = pad
    for c, cw in zip(text, widths):
        d.text((x, pad), c, font=f, fill=255)
        x += cw + track
    out = Image.new("RGBA", (Wd, Hd), (0, 0, 0, 0))
    if shadow:
        sh = mask.filter(ImageFilter.GaussianBlur(shadow))
        sh = sh.point(lambda v: int(v * 0.75))
        shadow_img = Image.new("RGBA", (Wd, Hd), (0, 0, 0, 255))
        shadow_img.putalpha(sh)
        out.alpha_composite(shadow_img, (0, int(shadow * 0.4)))
    if glow:
        g = mask.filter(ImageFilter.GaussianBlur(glow))
        gi = Image.new("RGBA", (Wd, Hd), glow_col + (255,))
        gi.putalpha(g.point(lambda v: min(255, int(v * 1.6))))
        out.alpha_composite(gi)
    if stroke:
        sm = Image.new("L", (Wd, Hd), 0)
        sd = ImageDraw.Draw(sm)
        x = pad
        for c, cw in zip(text, widths):
            sd.text((x, pad), c, font=f, fill=255, stroke_width=stroke, stroke_fill=255)
            x += cw + track
        si = Image.new("RGBA", (Wd, Hd), (10, 10, 10, 255))
        si.putalpha(sm.point(lambda v: int(v * 0.85)))
        out.alpha_composite(si)
    if grad:
        top, bot = grad
        g = np.zeros((Hd, Wd, 4), np.uint8)
        ys = np.linspace(0, 1, Hd)[:, None]
        for i in range(3):
            g[:, :, i] = (top[i] * (1 - ys) + bot[i] * ys).astype(np.uint8)
        g[:, :, 3] = np.array(mask)
        out.alpha_composite(Image.fromarray(g, "RGBA"))
    else:
        fi = Image.new("RGBA", (Wd, Hd), fill + (255,))
        fi.putalpha(mask)
        out.alpha_composite(fi)
    sp = pil_to_rgba(out)
    _text_cache[key] = (sp, pad)
    return sp, pad


def rounded_mask(w, h, r):
    m = Image.new("L", (w, h), 0)
    ImageDraw.Draw(m).rounded_rectangle([0, 0, w - 1, h - 1], r, fill=255)
    return m


# ---------------------------------------------------------------- global looks
YY, XX = np.mgrid[0:H, 0:W].astype(np.float32)
_r = np.sqrt(((XX - W / 2) / (W * 0.62)) ** 2 + ((YY - H * 0.45) / (H * 0.62)) ** 2)
VIGNETTE = np.clip(1.0 - 0.55 * np.clip(_r - 0.45, 0, 1) ** 1.4, 0, 1)[:, :, None].astype(np.float32)
# readability gradient behind subtitles
_g = np.clip((YY - H * 0.60) / (H * 0.18), 0, 1) * np.clip((H * 0.95 - YY) / (H * 0.10), 0, 1)
SUBSHADE = (1 - 0.42 * _g)[:, :, None].astype(np.float32)
del _r, _g


def make_lut():
    x = np.arange(256) / 255.0
    s = x + 0.10 * np.sin((x - 0.5) * 2 * np.pi) * -1 * 0.55      # gentle S
    s = np.clip(0.02 + s * 0.97, 0, 1)
    b = np.clip(s * 0.96 + 0.015 * (1 - x), 0, 1)                  # cool shadows a touch
    g = np.clip(s * 0.995, 0, 1)
    r = np.clip(s * 1.03 + 0.01, 0, 1)                             # warm highlights
    return [np.clip(c * 255, 0, 255).astype(np.uint8) for c in (b, g, r)]


LUT = make_lut()
rng = np.random.default_rng(7)
GRAIN = [rng.normal(0, 4.0, (H // 2, W // 2)).astype(np.float32) for _ in range(6)]


def grade(img, sat=1.08):
    b, g, r = cv2.split(img)
    img = cv2.merge([cv2.LUT(b, LUT[0]), cv2.LUT(g, LUT[1]), cv2.LUT(r, LUT[2])])
    if sat != 1.0:
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        hsv[:, :, 1] = cv2.convertScaleAbs(hsv[:, :, 1], alpha=sat)
        img = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)
    return img


def finish(img, fi, sub_active):
    f = img.astype(np.float32) * VIGNETTE
    if sub_active:
        f *= SUBSHADE
    n = cv2.resize(GRAIN[fi % len(GRAIN)], (W, H), interpolation=cv2.INTER_NEAREST)
    f += n[:, :, None]
    return np.clip(f, 0, 255).astype(np.uint8)


# ---------------------------------------------------------------- particles / light
class Dust:
    def __init__(self, n=46, seed=3):
        r = np.random.default_rng(seed)
        self.p = r.random((n, 2)) * [W, H]
        self.v = (r.random((n, 2)) - [0.5, 0.9]) * [14, 26]
        self.s = r.random(n) * 4 + 2
        self.ph = r.random(n) * 6.28

    def draw(self, img, t, strength=1.0):
        if strength <= 0:
            return
        ov = np.zeros((H // 2, W // 2), np.float32)
        pos = (self.p + self.v * t) % [W, H]
        for (x, y), s, ph in zip(pos, self.s, self.ph):
            a = (0.5 + 0.5 * math.sin(t * 1.7 + ph)) * strength
            cv2.circle(ov, (int(x / 2), int(y / 2)), int(s / 2) + 1, a, -1, cv2.LINE_AA)
        ov = cv2.GaussianBlur(ov, (0, 0), 2.2)
        ov = cv2.resize(ov, (W, H))
        add = np.dstack([ov * 120, ov * 200, ov * 255])
        cv2.add(img, np.clip(add, 0, 255).astype(np.uint8), dst=img)


DUST = Dust()


def light_leak(img, k, seed=0, gain=1.0):
    """Warm additive light sweep, k in [0,1] progress."""
    if k <= 0 or k >= 1:
        return img
    a = math.sin(k * math.pi)
    r = np.random.default_rng(seed)
    sw, sh = W // 6, H // 6
    yy, xx = np.mgrid[0:sh, 0:sw].astype(np.float32)
    ov = np.zeros((sh, sw, 3), np.float32)
    for i in range(3):
        cx = (-0.3 + 1.6 * k + r.uniform(-0.25, 0.25)) * sw
        cy = r.uniform(0.1, 0.9) * sh
        rad = r.uniform(0.35, 0.6) * sw
        d = np.exp(-(((xx - cx) ** 2 + ((yy - cy) * 0.6) ** 2) / (2 * rad ** 2)))
        col = [(60, 150, 255), (90, 200, 255), (40, 110, 240)][i]
        for c in range(3):
            ov[:, :, c] += d * col[c]
    ov = cv2.resize(ov, (W, H)) * (a * 0.85 * gain)
    return np.clip(img.astype(np.float32) + ov, 0, 255).astype(np.uint8)


# ---------------------------------------------------------------- sources
class SpeakerReader:
    """Sequential frame reader for one source piece (1080x1920 upscale done later)."""

    def __init__(self, src, s, nframes):
        self.n = nframes
        self.p = subprocess.Popen(
            ["ffmpeg", "-v", "error", "-ss", f"{s:.3f}", "-i", src, "-frames:v", str(nframes),
             "-f", "rawvideo", "-pix_fmt", "bgr24", "-"], stdout=subprocess.PIPE)
        self.last = None

    def read(self):
        b = self.p.stdout.read(720 * 1280 * 3)
        if len(b) == 720 * 1280 * 3:
            self.last = np.frombuffer(b, np.uint8).reshape(1280, 720, 3)
        return self.last


def speaker_frame(fr, z, ay=430, dim=1.0):
    """Zoom into source 720x1280 frame around (360, ay) and fill 1080x1920."""
    s = 1.5 * z
    cw, ch = W / s, H / s
    cx = 360.0
    cy = min(max(ay, ch / 2), 1280 - ch / 2)
    x0, y0 = cx - cw / 2, cy - ch / 2
    M = np.float32([[s, 0, -x0 * s], [0, s, -y0 * s]])
    out = cv2.warpAffine(fr, M, (W, H), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT)
    if dim != 1.0:
        out = cv2.convertScaleAbs(out, alpha=dim)
    return out


_img_cache = {}


def load_img(name):
    if name in _img_cache:
        return _img_cache[name]
    p = [f for f in os.listdir(os.path.join(ASSET, "img")) if f.split(".")[0] == name][0]
    im = cv2.imread(os.path.join(ASSET, "img", p))
    crops = {"nightmajlis": (554, 1366), "tasmik": (554, 1366), "crowd": (554, 1366),
             "ustaz": (239, 1681), "class": (242, 1678)}
    if name in crops:
        a, b = crops[name]
        im = im[a:b]
    if name == "elec":   # hide the utility account number / barcode
        x0, y0, x1, y1 = 250, 600, 560, 725
        im[y0:y1, x0:x1] = cv2.GaussianBlur(im[y0:y1, x0:x1], (0, 0), 14)
    # gentle sharpening for upscaled phone photos
    bl = cv2.GaussianBlur(im, (0, 0), 1.6)
    im = cv2.addWeighted(im, 1.35, bl, -0.35, 0)
    _img_cache[name] = im
    return im


def kenburns(im, z, fx, fy, ow=W, oh=H):
    h, w = im.shape[:2]
    s = max(ow / w, oh / h) * z
    cw, ch = ow / s, oh / s
    cx = min(max(fx * w, cw / 2), w - cw / 2)
    cy = min(max(fy * h, ch / 2), h - ch / 2)
    M = np.float32([[s, 0, -(cx - cw / 2) * s], [0, s, -(cy - ch / 2) * s]])
    return cv2.warpAffine(im, M, (ow, oh), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT)


_bg_cache = {}


def blurred_bg(name, dark=0.42):
    k = (name, dark)
    if k not in _bg_cache:
        im = load_img(name)
        b = kenburns(im, 1.15, 0.5, 0.5, W // 4, H // 4)
        b = cv2.GaussianBlur(b, (0, 0), 9)
        b = cv2.resize(b, (W, H), interpolation=cv2.INTER_CUBIC)
        _bg_cache[k] = cv2.convertScaleAbs(b, alpha=dark)
    return _bg_cache[k].copy()


_card_mask = {}


def card_frame(name, z, fx, fy, t):
    out = blurred_bg(name)
    im = load_img(name)
    cw = 980
    ch = int(cw * im.shape[0] / im.shape[1])
    ch = min(ch, 1180)
    inner = kenburns(im, z, fx, fy, cw, ch)
    if (cw, ch) not in _card_mask:
        m = np.array(rounded_mask(cw, ch, 30))
        sh = Image.new("L", (cw + 120, ch + 120), 0)
        ImageDraw.Draw(sh).rounded_rectangle([60, 70, 60 + cw, 70 + ch], 30, fill=200)
        sh = np.array(sh.filter(ImageFilter.GaussianBlur(26)))
        _card_mask[(cw, ch)] = (m, sh)
    m, sh = _card_mask[(cw, ch)]
    float_y = int(6 * math.sin(t * 0.9))
    x, y = (W - cw) // 2, 820 - ch // 2 + float_y
    shadow = np.zeros((sh.shape[0], sh.shape[1], 4), np.uint8)
    shadow[:, :, 3] = sh
    blend(out, shadow, x - 60, y - 60)
    blend(out, np.dstack([inner, m]), x, y)
    # thin gold frame
    cv2.rectangle(out, (x + 2, y + 2), (x + cw - 3, y + ch - 3), (90, 180, 230), 2, cv2.LINE_AA)
    return out


# ---------------------------------------------------------------- subtitles
def build_groups(words):
    groups, cur = [], []
    for w in words:
        if cur:
            prev = cur[-1]
            chars = sum(len(x["text"]) + 1 for x in cur) + len(w["text"])
            if (w["t0"] - prev["t1"] > 0.32 or len(cur) >= 4 or chars > 24
                    or prev["text"][-1] in ".?!" or (prev["text"][-1] == "," and len(cur) >= 2)
                    or w["hook"] != prev["hook"]):
                groups.append(cur)
                cur = []
        cur.append(w)
    if cur:
        groups.append(cur)
    for i, g in enumerate(groups):
        nxt = groups[i + 1][0]["t0"] if i + 1 < len(groups) else 1e9
        g_end = min(g[-1]["t1"] + 0.45, nxt - 0.02)
        for w in g:
            w["g_end"] = g_end
            w["g_start"] = g[0]["t0"] - 0.04
    return groups


def word_style(w):
    k = w["text"].lower().strip(".,?!")
    key = k in P.KEYWORDS
    size = 92 if not w["hook"] else 104
    if key:
        size = int(size * 1.12)
    return key, size


def layout_group(g):
    """Return per-word (x_center, y_center) positions, wrapping to two lines."""
    maxw = 940
    items = []
    for w in g:
        key, size = word_style(w)
        f = font(F_INTER_BLACK, size)
        txt = w["text"].upper() if key else w["text"]
        items.append((txt, f.getlength(txt), size, key))
    space = 44
    lines, cur, cw = [], [], 0
    for i, (txt, tw, size, key) in enumerate(items):
        add = tw + (space if cur else 0)
        if cur and cw + add > maxw:
            lines.append(cur)
            cur, cw = [], 0
            add = tw
        cur.append(i)
        cw += add
    lines.append(cur)
    pos = [None] * len(items)
    lh = 118
    base_y = (1420 if not g[0]["hook"] else 1300) - (len(lines) - 1) * lh / 2
    for li, line in enumerate(lines):
        tot = sum(items[i][1] for i in line) + space * (len(line) - 1)
        x = (W - tot) / 2
        for i in line:
            pos[i] = (x + items[i][1] / 2, base_y + li * lh)
            x += items[i][1] + space
    return items, pos


class Subtitles:
    def __init__(self, words, hidden):
        self.words = [w for w in words]
        for w in self.words:
            w["hidden"] = id(w) in hidden
        self.groups = build_groups(self.words)
        self.layouts = {}
        for gi, g in enumerate(self.groups):
            vis = [w for w in g if not w["hidden"]]
            if vis:
                self.layouts[gi] = (vis, layout_group(vis))

    def active(self, t):
        for gi, (vis, _) in self.layouts.items():
            if vis[0]["g_start"] <= t < vis[0]["g_end"]:
                return True
        return False

    def draw(self, img, t):
        for gi, (vis, (items, pos)) in self.layouts.items():
            g0, g1 = vis[0]["g_start"], vis[0]["g_end"]
            if not (g0 <= t < g1):
                continue
            fade = min(1.0, (g1 - t) / 0.12)
            for w, (txt, tw, size, key), (cx, cy) in zip(vis, items, pos):
                if t < w["t0"] - 0.03:
                    continue
                k = (t - (w["t0"] - 0.03)) / 0.2
                sc = 0.55 + 0.45 * back_out(k, 2.2)
                speaking = w["t0"] - 0.03 <= t <= w["t1"] + 0.05
                col = GOLD_RGB if key else (255, 255, 255)
                sp, pad = text_sprite(txt, size, fill=col, stroke=7, shadow=12,
                                      glow=(16 if key else 0), glow_col=(120, 70, 0))
                if speaking and not key:
                    # emerald highlight capsule behind the spoken word
                    hw = int(tw / 2 + 18)
                    hh = int(size * 0.62)
                    a = min(1, k * 2)
                    ov = img[int(cy - hh + 6):int(cy + hh + 6), int(cx - hw):int(cx + hw)]
                    if ov.size:
                        cap = np.zeros((ov.shape[0], ov.shape[1], 4), np.uint8)
                        cap[:, :, :3] = (60, 128, 14)
                        cap[:, :, 3] = np.array(rounded_mask(ov.shape[1], ov.shape[0], 22)) * 0.92
                        blend(img, cap, int(cx - hw), int(cy - hh + 6), a * fade)
                if speaking:
                    sc *= 1.08
                s2 = scale_sprite(sp, sc)
                rise = int((1 - ease_out(k)) * 26)
                x = int(cx - s2.shape[1] / 2)
                y = int(cy - s2.shape[0] / 2 + rise)
                blend(img, s2, x, y, min(1.0, k * 3) * fade)


# ---------------------------------------------------------------- overlays
def draw_pill(img, text, t, t0, t1):
    if not (t0 <= t < t1):
        return
    k_in = ease_out((t - t0) / 0.3)
    k_out = min(1.0, (t1 - t) / 0.15)
    sp, pad = text_sprite(text, 44, fill=(30, 22, 8), fpath=F_INTER_BLACK, shadow=0, track=3)
    tw = sp.shape[1] - 2 * pad
    pw, ph = tw + 76, 84
    pill = Image.new("RGBA", (pw + 40, ph + 40), (0, 0, 0, 0))
    d = ImageDraw.Draw(pill)
    d.rounded_rectangle([20, 26, pw + 20, ph + 26], ph // 2, fill=(0, 0, 0, 120))
    pill = pill.filter(ImageFilter.GaussianBlur(8))
    d = ImageDraw.Draw(pill)
    d.rounded_rectangle([20, 20, pw + 20, ph + 20], ph // 2, fill=GOLD_RGB + (255,))
    d.ellipse([44, 20 + ph // 2 - 8, 60, 20 + ph // 2 + 8], fill=EMERALD_RGB + (255,))
    ps = pil_to_rgba(pill)
    blend(ps, sp, 20 + 54 - pad + 12, 20 + (ph - sp.shape[0]) // 2 + 2)
    w_vis = int(ps.shape[1] * k_in)
    if w_vis < 10:
        return
    x = (W - ps.shape[1]) // 2
    y = 250 + int((1 - k_in) * -30)
    blend(img, ps[:, :w_vis], x, y, k_out)


def draw_big(img, t, ev, words):
    s0, s1, lines = ev
    t0, t1 = P.m(s0), P.m(s1)
    if not (t0 <= t < t1 + 0.25):
        return
    fade = min(1.0, (t1 + 0.25 - t) / 0.25)
    n = len(lines)
    big = n <= 2 and len(lines[0][0]) <= 9
    sizes = []
    for i, (txt, _) in enumerate(lines):
        if txt.startswith("RM"):
            sizes.append(250)
        elif n == 3:
            sizes.append(170 if i else 150)
        elif i == 0:
            sizes.append(180 if len(txt) <= 7 else 150)
        else:
            sizes.append(84)
    total_h = sum(int(s * 1.12) for s in sizes)
    y = 900 - total_h // 2
    for (txt, trig), size in zip(lines, sizes):
        tt = next((w["t0"] for w in words if w["text"] == trig and t0 - 0.4 <= w["t0"] <= t1 + 0.1), t0)
        if t >= tt - 0.04:
            k = (t - tt + 0.04) / 0.28
            sc = 0.4 + 0.6 * back_out(k, 2.6)
            if size >= 150:
                sp, pad = text_sprite(txt, size, fpath=F_INTER_BLACK, stroke=0, shadow=18, glow=28,
                                      glow_col=(150, 90, 0), grad=((255, 236, 170), (222, 160, 40)))
            else:
                sp, pad = text_sprite(txt, size, fill=(255, 255, 255), fpath=F_INTER_BLACK, shadow=14,
                                      track=10)
            s2 = scale_sprite(sp, sc)
            shake = int(10 * math.exp(-k * 6) * math.sin(k * 40)) if size >= 150 else 0
            blend(img, s2, (W - s2.shape[1]) // 2 + shake, y + int(size * 0.56) - s2.shape[0] // 2,
                  min(1, k * 4) * fade)
        y += int(size * 1.12)


def gold_rule(img, cx, y, w, a=1.0):
    ov = np.zeros((10, w, 4), np.uint8)
    ov[3:7, :, :3] = GOLD
    ramp = np.minimum(np.linspace(0, 2, w), np.linspace(2, 0, w)).clip(0, 1)
    ov[3:7, :, 3] = (ramp * 255).astype(np.uint8)[None, :]
    blend(img, ov, cx - w // 2, y, a)


_logo = None


def logo_plate(width):
    global _logo
    if _logo is None or _logo.shape[1] != width:
        im = Image.open(os.path.join(ASSET, "img", "logo.jpg")).convert("RGB")
        im = im.crop((40, 110, 1240, 860))
        h = int(width * im.height / im.width)
        im = im.resize((width, h), Image.LANCZOS)
        pw, ph = width + 60, h + 60
        plate = Image.new("RGBA", (pw + 80, ph + 80), (0, 0, 0, 0))
        d = ImageDraw.Draw(plate)
        d.rounded_rectangle([40, 52, pw + 40, ph + 52], 36, fill=(0, 0, 0, 150))
        plate = plate.filter(ImageFilter.GaussianBlur(20))
        d = ImageDraw.Draw(plate)
        d.rounded_rectangle([40, 40, pw + 40, ph + 40], 36, fill=(255, 255, 255, 255),
                            outline=GOLD_RGB + (255,), width=5)
        plate.paste(im, (70, 70))
        _logo = pil_to_rgba(plate)
    return _logo


def bg_emerald(t):
    g = np.zeros((H, W, 3), np.float32)
    yy = YY / H
    g[:, :, 0] = 22 + 30 * yy
    g[:, :, 1] = 40 + 46 * (1 - yy)
    g[:, :, 2] = 8 + 8 * yy
    # soft moving halo
    cx, cy = W / 2 + 80 * math.sin(t * 0.6), H * 0.42
    d = np.exp(-(((XX - cx) / 520) ** 2 + ((YY - cy) / 620) ** 2))
    g += d[:, :, None] * np.array([40, 120, 150], np.float32)
    return np.clip(g, 0, 255).astype(np.uint8)


_star = None


def star_pattern():
    """Faint 8-point star lattice (rub el hizb motif) in gold."""
    global _star
    if _star is None:
        im = Image.new("L", (W, H), 0)
        d = ImageDraw.Draw(im)
        step = 180
        for yy in range(-step, H + step, step):
            for xx in range(-step, W + step, step):
                ox = xx + (step // 2 if (yy // step) % 2 else 0)
                for rot in (0, 45):
                    pts = []
                    for c in range(4):
                        ang = math.radians(rot + c * 90 + 45)
                        pts.append((ox + 46 * math.cos(ang), yy + 46 * math.sin(ang)))
                    d.polygon(pts, outline=255)
        im = np.array(im.filter(ImageFilter.GaussianBlur(0.6))).astype(np.float32) / 255
        _star = im
    return _star


def title_card(t, d):
    img = bg_emerald(t)
    pat = star_pattern() * (0.16 * ease_out(t / 0.6))
    img = np.clip(img + pat[:, :, None] * np.array([90, 190, 245]), 0, 255).astype(np.uint8)
    k = ease_out(t / 0.5)
    lp = logo_plate(820)
    s2 = scale_sprite(lp, 0.86 + 0.14 * back_out(t / 0.55, 1.4) + 0.02 * t)
    blend(img, s2, (W - s2.shape[1]) // 2, 760 - s2.shape[0] // 2, k)
    gold_rule(img, W // 2, 1170, int(640 * ease_out((t - 0.3) / 0.6)))
    sp, _ = text_sprite("TARBIYAH  ·  ILMU  ·  AMAL", 46, fill=CREAM_RGB, fpath=F_CINZEL, wght=700,
                        shadow=8, track=6)
    blend(img, sp, (W - sp.shape[1]) // 2, 1210, ease_out((t - 0.45) / 0.5))
    DUST.draw(img, t + 10, 1.0)
    fade = min(1.0, (d - t) / 0.18)
    return cv2.convertScaleAbs(img, alpha=fade * 0.6 + 0.4)


def end_card(t, d):
    img = bg_emerald(t + 3)
    pat = star_pattern() * 0.14
    img = np.clip(img + pat[:, :, None] * np.array([90, 190, 245]), 0, 255).astype(np.uint8)
    lp = logo_plate(700)
    s2 = scale_sprite(lp, 0.94 + 0.06 * ease_out(t / 0.8))
    blend(img, s2, (W - s2.shape[1]) // 2, 300, ease_out(t / 0.5))
    y = 300 + lp.shape[0] + 40
    lines = [("JADI PENGINFAK", 92, True), ("TETAP BULANAN", 92, True)]
    for i, (txt, sz, g) in enumerate(lines):
        kk = (t - 0.35 - i * 0.15) / 0.35
        if kk > 0:
            sp, _ = text_sprite(txt, sz, fpath=F_INTER_BLACK, shadow=14, glow=22, glow_col=(150, 90, 0),
                                grad=((255, 236, 170), (222, 160, 40)))
            s2 = scale_sprite(sp, 0.6 + 0.4 * back_out(kk))
            blend(img, s2, (W - s2.shape[1]) // 2, y - s2.shape[0] // 2 + 50, min(1, kk * 3))
        y += 112
    gold_rule(img, W // 2, y + 30, int(560 * ease_out((t - 0.8) / 0.5)))
    info = ["Tekan pautan yang disediakan", "Pilih InfakPay  ·  Daftar sebagai", "penginfak tetap bulanan"]
    y += 80
    for i, txt in enumerate(info):
        kk = ease_out((t - 1.0 - i * 0.15) / 0.4)
        sp, _ = text_sprite(txt, 50, fill=CREAM_RGB, fpath=F_INTER_SEMI, shadow=8)
        blend(img, sp, (W - sp.shape[1]) // 2, y + int((1 - kk) * 20), kk)
        y += 70
    kk = ease_out((t - 1.7) / 0.6)
    sp, _ = text_sprite("Berapa pun kita mampu — ikhlas & istiqamah", 40, fill=GOLD_RGB,
                        fpath=F_INTER_BOLD, shadow=6)
    blend(img, sp, (W - sp.shape[1]) // 2, y + 40, kk)
    DUST.draw(img, t + 30, 1.0)
    fade = min(1.0, (d - t) / 0.6)
    return cv2.convertScaleAbs(img, alpha=fade)


def yaman_card(t, tl, words):
    """'3 pelajar ... sedang menyambung pengajian agama dekat Yaman'"""
    img = blurred_bg("podium", 0.32)
    img = cv2.addWeighted(img, 1.0, bg_emerald(tl), 0.35, 0)
    pat = star_pattern() * 0.10
    img = np.clip(img + pat[:, :, None] * np.array([90, 190, 245]), 0, 255).astype(np.uint8)
    def wt(txt):
        return next((w["t0"] for w in words if w["text"] == txt and abs(w["t0"] - t + tl) < 6), t - tl)
    t3, tp, ty = wt("tiga"), wt("pelajar"), wt("Yaman.")
    k = (t - t3 + 0.05) / 0.35
    if k > 0:
        sp, _ = text_sprite("3", 420, fpath=F_INTER_BLACK, shadow=22, glow=40, glow_col=(150, 90, 0),
                            grad=((255, 236, 170), (222, 160, 40)))
        s2 = scale_sprite(sp, 0.3 + 0.7 * back_out(k, 2.4))
        blend(img, s2, (W - s2.shape[1]) // 2, 560 - s2.shape[0] // 2, min(1, k * 3))
    k = ease_out((t - tp) / 0.3)
    sp, _ = text_sprite("ORANG PELAJAR", 70, fill=(255, 255, 255), fpath=F_INTER_BLACK, shadow=10, track=12)
    blend(img, sp, (W - sp.shape[1]) // 2, 790 + int((1 - k) * 30), k)
    k = ease_out((t - tp - 0.6) / 0.4)
    gold_rule(img, W // 2, 900, int(520 * k))
    k = (t - ty + 0.05) / 0.3
    if k > 0:
        sp, _ = text_sprite("YAMAN", 170, fpath=F_CINZEL, wght=900, shadow=18, glow=30,
                            glow_col=(150, 90, 0), grad=((255, 236, 170), (222, 160, 40)), track=8)
        s2 = scale_sprite(sp, 0.5 + 0.5 * back_out(k, 2))
        blend(img, s2, (W - s2.shape[1]) // 2, 1010 - s2.shape[0] // 2 + 60, min(1, k * 3))
    DUST.draw(img, t, 0.8)
    return img


def steps_card(t, tl, fr, words):
    img = bg_emerald(tl)
    pat = star_pattern() * 0.08
    img = np.clip(img + pat[:, :, None] * np.array([90, 190, 245]), 0, 255).astype(np.uint8)
    # speaker in a circle at top
    sp = speaker_frame(fr, 1.0, ay=430)
    r = 190
    cx, cy = W // 2, 320
    R = 270
    crop = cv2.resize(sp[450 - R:450 + R, W // 2 - R:W // 2 + R], (2 * r, 2 * r), interpolation=cv2.INTER_AREA)
    mask = np.zeros((2 * r, 2 * r), np.uint8)
    cv2.circle(mask, (r, r), r - 2, 255, -1, cv2.LINE_AA)
    k = ease_out(tl / 0.4)
    blend(img, np.dstack([crop, mask]), cx - r, cy - r, k)
    cv2.circle(img, (cx, cy), r + 2, GOLD, 6, cv2.LINE_AA)
    # steps
    def wt(txt):
        return next((w["t0"] for w in words if w["text"] == txt and abs(w["t0"] - t + tl) < 9), t - tl)
    steps = [("1", "Tekan pautan", "yang disediakan", wt("Tekan")),
             ("2", "Pilih sumbangan", "melalui InfakPay", wt("pilih")),
             ("3", "Daftar", "penginfak tetap bulanan", wt("daftar"))]
    y = 600
    for num, a, b, tt in steps:
        kk = (t - tt + 0.05) / 0.35
        if kk > 0:
            e = ease_out(kk)
            box = Image.new("RGBA", (900, 170), (0, 0, 0, 0))
            d = ImageDraw.Draw(box)
            d.rounded_rectangle([0, 0, 899, 169], 34, fill=(250, 244, 228, 238))
            d.ellipse([28, 28, 142, 142], fill=EMERALD_RGB + (255,))
            fn = font(F_INTER_BLACK, 70)
            d.text((85, 86), num, font=fn, fill=GOLD_RGB, anchor="mm")
            d.text((172, 52), a, font=font(F_INTER_BLACK, 60), fill=(20, 40, 28), anchor="lm")
            d.text((172, 118), b, font=font(F_INTER_SEMI, 40), fill=(70, 90, 75), anchor="lm")
            bx = pil_to_rgba(box)
            x = (W - 900) // 2 + int((1 - e) * 160)
            blend(img, bx, x, y, min(1, kk * 2.5))
        y += 200
    return img


# ---------------------------------------------------------------- main
def main():
    src = sys.argv[1]
    out = sys.argv[2]
    pv = None
    if "--preview" in sys.argv:
        i = sys.argv.index("--preview")
        pv = (float(sys.argv[i + 1]), float(sys.argv[i + 2]))

    words = P.out_words()
    # words hidden from subtitles during big kinetic words
    hidden = set()
    for s0, s1, lines in P.BIG:
        t0, t1 = P.m(s0), P.m(s1)
        trig = {x[1] for x in lines}
        for w in words:
            if not w["hook"] and t0 - 0.3 <= w["t0"] <= t1 and w["text"] in trig:
                hidden.add(id(w))
        if lines[-1][0] == "TIAP-TIAP BULAN":
            for w in words:
                if not w["hook"] and t0 <= w["t0"] <= t1 + 0.1 and w["text"] == "bulan.":
                    hidden.add(id(w))
    for w in words:
        if w["text"] == "Yaman." and not w["hook"]:
            hidden.add(id(w))
    subs = Subtitles(words, hidden)

    # shots on output timeline
    shots = []
    hook = P.LAID[0]
    shots.append(dict(t0=0, kind="spk", z0=1.30, z1=1.16, hook=True))
    for i, (s, kind, prm) in enumerate(P.SHOTS):
        sh = dict(t0=P.m(s), kind=kind, **prm)
        shots.append(sh)
    shots.sort(key=lambda x: x["t0"])
    for i, sh in enumerate(shots):
        sh["t1"] = shots[i + 1]["t0"] if i + 1 < len(shots) else P.TOTAL
    # hook shot ends at title card
    shots[0]["t1"] = P.LAID[1]["o"]

    # SFX cues
    SFX.append((0.0, "riser_short"))
    SFX.append((P.LAID[1]["o"], "impact"))
    SFX.append((P.LAID[1]["o"] + 0.05, "shimmer"))
    prev = None
    for sh in shots[1:]:
        if sh["kind"] in ("img", "yaman", "steps") and (prev is None or prev != sh.get("img", sh["kind"])):
            SFX.append((sh["t0"] - 0.18, "whoosh"))
        elif sh["kind"] == "spk" and prev not in (None, "spk"):
            SFX.append((sh["t0"] - 0.12, "whoosh_soft"))
        prev = sh.get("img", sh["kind"])
    for s0, s1, lines in P.BIG:
        for txt, trig in lines:
            tt = next((w["t0"] for w in words if w["text"] == trig and P.m(s0) - 0.4 <= w["t0"] <= P.m(s1)), None)
            if tt is not None:
                SFX.append((tt - 0.02, "impact" if txt in ("RM150", "PENGINFAK", "ISTIQAMAH") else "hit"))
    for s0, s1, txt in P.PILLS:
        SFX.append((P.m(s0), "tick"))
    for w in words:
        if w["text"] in ("tiga", "Yaman.") and 40 < w["t0"] < 50:
            SFX.append((w["t0"] - 0.02, "impact" if w["text"] == "Yaman." else "hit"))
        if w["text"] in ("Tekan", "pilih", "daftar") and w["t0"] > 90:
            SFX.append((w["t0"], "tick"))
    SFX.append((P.LAID[-1]["o"], "impact_soft"))
    SFX.append((P.LAID[-1]["o"] + 0.1, "shimmer"))
    leaks = [P.m(s) for s in P.LEAKS] + [P.LAID[1]["o"], P.LAID[-1]["o"]]

    with open(os.path.join(os.path.dirname(out) or ".", "sfx_cues.txt"), "w") as f:
        for t, k in sorted(SFX):
            f.write(f"{t:.3f} {k}\n")

    nframes = P.LAID[-1]["f1"]
    f_start, f_end = 0, nframes
    frames = range(f_start, f_end)
    if "--stills" in sys.argv:
        ts = [float(x) for x in sys.argv[sys.argv.index("--stills") + 1].split(",")]
        frames = [int(x * FPS) for x in ts]
    if pv:
        f_start, f_end = int(pv[0] * FPS), int(pv[1] * FPS)
        frames = range(f_start, f_end)

    enc = subprocess.Popen(
        ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{W}x{H}",
         "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "slow", "-crf", "19",
         "-pix_fmt", "yuv420p", "-movflags", "+faststart", out], stdin=subprocess.PIPE)

    reader, reader_piece = None, None
    stills = "--stills" in sys.argv
    for fi in frames:
        t = fi / FPS
        piece = next(L for L in P.LAID if L["f0"] <= fi < L["f1"])
        fr = None
        if piece["kind"] == "src":
            if reader_piece is not piece or stills:
                local0 = fi - piece["f0"]
                reader = SpeakerReader(src, piece["s"] + local0 / FPS, piece["f1"] - fi)
                reader_piece = piece
            fr = reader.read()
            sh = [s for s in shots if s["t0"] <= t + 0.034][-1]
            tl = t - sh["t0"]
            dur = max(sh["t1"] - sh["t0"], 1e-3)
            u = tl / dur
            if sh["kind"] == "spk":
                z = sh["z0"] + (sh["z1"] - sh["z0"]) * ease_io(u)
                settle = 1 + 0.05 * (1 - ease_out(tl / 0.3))
                img = speaker_frame(fr, z * settle, ay=430, dim=sh.get("dim", 1.0))
                img = grade(img, 1.06)
                if sh.get("hook"):
                    img = cv2.convertScaleAbs(img, alpha=0.82)
                if sh.get("glow"):
                    img = light_leak(img, 0.15 + 0.7 * u, seed=11, gain=0.28)
            elif sh["kind"] == "img":
                z = sh["z0"] + (sh["z1"] - sh["z0"]) * ease_io(u)
                fx = sh["f0"][0] + (sh["f1"][0] - sh["f0"][0]) * ease_io(u)
                fy = sh["f0"][1] + (sh["f1"][1] - sh["f0"][1]) * ease_io(u)
                settle = 1 + 0.06 * (1 - ease_out(tl / 0.35))
                if sh.get("mode") == "card":
                    img = card_frame(sh["img"], z * settle, fx, fy, tl)
                else:
                    img = kenburns(load_img(sh["img"]), z * settle, fx, fy)
                img = grade(img, 1.10)
                DUST.draw(img, t, 0.35)
            elif sh["kind"] == "yaman":
                img = yaman_card(t, tl, words)
            elif sh["kind"] == "steps":
                img = steps_card(t, tl, fr, words)
            # quick flash-in on cuts
            if tl < 0.1 and sh["kind"] != "spk":
                img = cv2.addWeighted(img, 1.0, np.full_like(img, 255), 0.35 * (1 - tl / 0.1), 0)
        else:
            tl = t - piece["o"]
            img = title_card(tl, piece["d"]) if piece["name"] == "title" else end_card(tl, piece["d"])

        for lt in leaks:
            if lt - 0.25 <= t < lt + 0.45:
                img = light_leak(img, (t - lt + 0.25) / 0.7, seed=int(lt * 10))
        if piece["kind"] == "src":
            for s0, s1, txt in P.PILLS:
                draw_pill(img, txt, t, P.m(s0), P.m(s1))
            bigs_on = False
            for ev in P.BIG:
                if P.m(ev[0]) <= t < P.m(ev[1]) + 0.25:
                    bigs_on = True
                draw_big(img, t, ev, words)
            sub_on = subs.active(t)
            img = finish(img, fi, sub_on)
            subs.draw(img, t)
        else:
            img = finish(img, fi, False)
        # fade from black at start
        if t < 0.25:
            img = cv2.convertScaleAbs(img, alpha=t / 0.25)
        enc.stdin.write(img.tobytes())
        if fi % 150 == 0:
            print(f"frame {fi}/{f_end}", flush=True)
    enc.stdin.close()
    enc.wait()


if __name__ == "__main__":
    main()
