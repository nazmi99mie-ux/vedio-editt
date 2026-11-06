"""High-impact motion-graphics renderer (v2). Reuses shot rendering from render.py.
Usage: python render2.py <workdir> <frames_dir> x [workers]   (reads plan2.json)"""
import sys, os, json, math, subprocess, functools
from multiprocessing import Pool
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance, ImageChops
import render as R
from render import W, H, FPS, ease, ease_out, back_out, font, shadowed

HERE = os.path.dirname(os.path.abspath(__file__))
FD = os.path.join(HERE, "fonts")
P_BLACK = os.path.join(FD, "Poppins-Black.ttf")
P_XB = os.path.join(FD, "Poppins-ExtraBold.ttf")
AMIRI = os.path.join(FD, "Amiri-Bold.ttf")

STYLES = {
    "gold": ((255, 240, 160), (236, 160, 26), (118, 66, 6)),
    "green": ((190, 255, 215), (26, 196, 112), (6, 78, 44)),
    "white": ((255, 255, 255), (206, 218, 232), (52, 62, 84)),
    "coral": ((255, 214, 186), (255, 104, 74), (120, 36, 22)),
    "sky": ((214, 244, 255), (50, 168, 255), (14, 56, 120)),
}

CAT = {}
for w in "akhirat kebajikan sumbangan allah alhamdulillah syukur ilmu bismillahirrahmanirrahim ta'ala insya-allah".split():
    CAT[w] = "gold"
for w in "wakaf diwakafkan hektar tanah pondok pondok-pondok kompleks asrama madrasah hari raya projek pembinaan".split():
    CAT[w] = "green"
for w in "warga emas warga-warga single berkelamin".split():
    CAT[w] = "coral"
for w in "sebarkan berita rayuan respons menginap".split():
    CAT[w] = "sky"


def easeb(x):  # bounce out
    x = min(1, max(0, x))
    n1, d1 = 7.5625, 2.75
    if x < 1 / d1:
        return n1 * x * x
    if x < 2 / d1:
        x -= 1.5 / d1
        return n1 * x * x + 0.75
    if x < 2.5 / d1:
        x -= 2.25 / d1
        return n1 * x * x + 0.9375
    x -= 2.625 / d1
    return n1 * x * x + 0.984375


# ---------------------------------------------------------------- sprites ---
def grad_fill(mask, top, bot, gloss=True):
    w, h = mask.size
    y = np.linspace(0, 1, h)[:, None, None]
    a = np.array(top, np.float32) * (1 - y) + np.array(bot, np.float32) * y
    a = np.repeat(a, w, 1)
    if gloss:
        a[: int(h * 0.48)] = a[: int(h * 0.48)] * 0.78 + 255 * 0.22
    out = np.zeros((h, w, 4), np.uint8)
    out[..., :3] = np.clip(a, 0, 255)
    out[..., 3] = np.asarray(mask)
    return Image.fromarray(out, "RGBA")


@functools.lru_cache(maxsize=256)
def text3d(txt, size, style="gold", depth=10, fpath=P_BLACK, maxw=980, rtl=False):
    f = ImageFont.truetype(fpath, size)
    kw = dict(direction="rtl", language="ar") if rtl else {}
    bb = f.getbbox(txt, **kw)
    if bb[2] - bb[0] > maxw:
        return text3d(txt, int(size * maxw / (bb[2] - bb[0])), style, depth, fpath, maxw, rtl)
    top, bot, side = STYLES[style]
    stroke = max(3, size // 18)
    pad = depth + stroke + 30
    w, h = bb[2] - bb[0] + pad * 2, bb[3] - bb[1] + pad * 2
    org = (pad - bb[0], pad - bb[1])
    m = Image.new("L", (w, h), 0)
    ImageDraw.Draw(m).text(org, txt, font=f, fill=255, **kw)
    ms = Image.new("L", (w, h), 0)
    ImageDraw.Draw(ms).text(org, txt, font=f, fill=255, stroke_width=stroke, stroke_fill=255, **kw)
    lay = Image.new("RGBA", (w + depth, h + depth), (0, 0, 0, 0))
    for d in range(depth, 0, -1):
        k = 0.55 + 0.45 * (1 - d / depth)
        col = tuple(int(c * k) for c in side) + (255,)
        lay.paste(Image.new("RGBA", (w, h), col), (int(d * 0.55), d), ms)
    lay.paste(Image.new("RGBA", (w, h), (18, 12, 6, 255)), (0, 0), ms)
    lay.alpha_composite(grad_fill(m, top, bot), (0, 0))
    return shadowed(lay, max(8, size // 9), 220, (4, depth + 6))


@functools.lru_cache(maxsize=64)
def icon(name, size):
    im = Image.open(os.path.join(HERE, "icons", name + ".png")).convert("RGBA").resize((size, size), Image.LANCZOS)
    pad = size // 4
    out = Image.new("RGBA", (size + pad * 2, size + pad * 2), (0, 0, 0, 0))
    a = im.split()[3]
    glow = Image.new("RGBA", out.size, (255, 230, 150, 0))
    ga = Image.new("L", out.size, 0)
    ga.paste(a, (pad, pad))
    glow.putalpha(ga.filter(ImageFilter.GaussianBlur(size // 10)).point(lambda v: v * 120 // 255))
    out.alpha_composite(glow)
    sh = Image.new("RGBA", out.size, (0, 0, 0, 0))
    sa = Image.new("L", out.size, 0)
    sa.paste(a, (pad + size // 30, pad + size // 14))
    sh.putalpha(sa.filter(ImageFilter.GaussianBlur(size // 18)).point(lambda v: v * 150 // 255))
    out.alpha_composite(sh)
    out.alpha_composite(im, (pad, pad))
    return out


@functools.lru_cache(maxsize=64)
def chip(txt, icon_name, style):
    top, bot, side = STYLES[style]
    f = ImageFont.truetype(P_BLACK, 52)
    tw = int(f.getlength(txt))
    isz = 96
    w, h = tw + isz + 80, 112
    lay = Image.new("RGBA", (w + 20, h + 30), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    d.rounded_rectangle((6, 14, w + 6, h + 14), 56, fill=tuple(int(c * 0.6) for c in side) + (255,))
    body = Image.new("L", (w, h), 0)
    ImageDraw.Draw(body).rounded_rectangle((0, 0, w - 1, h - 1), 56, fill=255)
    lay.alpha_composite(grad_fill(body, tuple(int(c * 0.55) for c in top), tuple(int(c * 0.45) for c in bot), True), (0, 0))
    ImageDraw.Draw(lay).rounded_rectangle((0, 0, w - 1, h - 1), 56, outline=(255, 255, 255, 120), width=3)
    ic = Image.open(os.path.join(HERE, "icons", icon_name + ".png")).convert("RGBA").resize((isz, isz), Image.LANCZOS)
    lay.alpha_composite(ic, (18, (h - isz) // 2))
    d = ImageDraw.Draw(lay)
    d.text((isz + 40, h / 2 - 2), txt, font=f, fill=(255, 255, 255), anchor="lm", stroke_width=3, stroke_fill=(0, 0, 0, 160))
    return shadowed(lay, 14, 200, (0, 10))


@functools.lru_cache(maxsize=32)
def glow_dot(r, color):
    s = int(r * 6)
    yy, xx = np.mgrid[0:s, 0:s].astype(np.float32) - s / 2
    d = np.sqrt(xx ** 2 + yy ** 2) / r
    a = np.clip(np.exp(-d ** 2 * 0.9) + 0.6 * np.exp(-d ** 2 * 6), 0, 1)
    out = np.zeros((s, s, 4), np.uint8)
    c = {"gold": (255, 214, 110), "white": (255, 255, 255), "green": (140, 255, 190)}[color]
    out[..., 0], out[..., 1], out[..., 2] = c
    out[..., 3] = (a * 255).astype(np.uint8)
    return Image.fromarray(out, "RGBA")


@functools.lru_cache(maxsize=16)
def star4(r):
    s = int(r * 4)
    yy, xx = np.mgrid[0:s, 0:s].astype(np.float32) - s / 2
    ax, ay = np.abs(xx) / r, np.abs(yy) / r
    a = np.clip(np.exp(-(ax * 9) ** 2) * np.exp(-ay ** 2 * 1.5) + np.exp(-(ay * 9) ** 2) * np.exp(-ax ** 2 * 1.5)
                + np.exp(-(ax ** 2 + ay ** 2) * 6), 0, 1)
    out = np.zeros((s, s, 4), np.uint8)
    out[..., :3] = (255, 246, 210)
    out[..., 3] = (a * 255).astype(np.uint8)
    return Image.fromarray(out, "RGBA")


@functools.lru_cache(None)
def rays_img():
    s = 1800
    yy, xx = np.mgrid[0:s, 0:s].astype(np.float32) - s / 2
    ang = np.arctan2(yy, xx)
    r = np.sqrt(xx ** 2 + yy ** 2) / (s / 2)
    band = (np.cos(ang * 14) * 0.5 + 0.5) ** 6 + 0.5 * (np.cos(ang * 9 + 1) * 0.5 + 0.5) ** 8
    a = band * np.exp(-r * 2.4) + np.exp(-r * 5) * 0.8
    img = np.zeros((s, s, 3), np.float32)
    img[..., 0], img[..., 1], img[..., 2] = 255 * a, 205 * a, 120 * a
    return Image.fromarray(np.clip(img, 0, 255).astype(np.uint8))


def paste(base, lay, cx, cy, alpha=1.0, scale=1.0, rot=0.0):
    if alpha <= 0.01 or scale <= 0.02:
        return
    if abs(scale - 1) > 0.004:
        lay = lay.resize((max(1, int(lay.width * scale)), max(1, int(lay.height * scale))), Image.BILINEAR)
    if abs(rot) > 0.3:
        lay = lay.rotate(rot, Image.BILINEAR, expand=True)
    if alpha < 0.995:
        lay = lay.copy()
        lay.putalpha(lay.split()[3].point(lambda v: int(v * alpha)))
    x, y = int(cx - lay.width / 2), int(cy - lay.height / 2)
    # clip to canvas
    if x >= W or y >= H or x + lay.width <= 0 or y + lay.height <= 0:
        return
    cx0, cy0 = max(0, -x), max(0, -y)
    cx1, cy1 = min(lay.width, W - x), min(lay.height, H - y)
    if (cx0, cy0, cx1, cy1) != (0, 0, lay.width, lay.height):
        lay = lay.crop((cx0, cy0, cx1, cy1))
    base.alpha_composite(lay, (x + cx0, y + cy0))


def shine(lay, p):
    """diagonal light sweep across a sprite, p in 0..1"""
    if p <= 0 or p >= 1:
        return lay
    w, h = lay.size
    a = np.asarray(lay.split()[3]).astype(np.float32) / 255
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    pos = -0.3 * w + p * 1.6 * w
    band = np.clip(1 - np.abs(xx + yy * 0.6 - pos) / (w * 0.06 + 20), 0, 1) ** 2
    arr = np.asarray(lay).astype(np.float32)
    arr[..., :3] += (band * a * 200)[..., None]
    out = np.clip(arr, 0, 255).astype(np.uint8)
    return Image.fromarray(out, "RGBA")


# ------------------------------------------------------------- event draw ---
def anim_in_out(dt, dur, tin=0.3, tout=0.25):
    return min(1, dt / tin), max(0, min(1, (dur - dt) / tout))


def draw_t3d(im, e, dt):
    d = e["dur"]
    rtl = e["type"] == "arabic"
    if rtl:
        lay = text3d(e["txt"], e["size"], "gold", 7, AMIRI, 980, True)
    else:
        lay = text3d(e["txt"], e["size"], e["style"], max(8, e["size"] // 11))
    pin, pout = anim_in_out(dt, d, 0.3, 0.28)
    x, y, sc, a, rot = W / 2, e["y"], 1.0, 1.0, 0.0
    an = e.get("anim", "grow")
    if an == "slam":
        sc = 2.3 - 1.3 * ease_out(dt / 0.17)
        a = ease(dt / 0.08)
        rot = -7 * (1 - ease_out(dt / 0.2))
    elif an == "fly_l":
        x = W / 2 - 900 * (1 - back_out(dt / 0.32, 1.2))
        rot = 8 * (1 - ease_out(dt / 0.32))
    elif an == "fly_r":
        x = W / 2 + 900 * (1 - back_out(dt / 0.32, 1.2))
        rot = -8 * (1 - ease_out(dt / 0.32))
    elif an == "fly_b":
        y = e["y"] + 260 * (1 - back_out(dt / 0.34, 1.4))
        a = ease(dt / 0.18)
    elif an == "drop":
        y = e["y"] - 600 * (1 - easeb(dt / 0.55))
    else:  # grow
        sc = 0.15 + 0.85 * back_out(dt / 0.38, 2.0)
        a = ease(dt / 0.15)
    if pout < 1:
        sc *= 1 + 0.15 * (1 - pout)
        a *= pout
    sc *= 1 + 0.015 * math.sin(dt * 5)  # breathing
    lay = shine(lay, (dt - 0.3) / 0.6)
    if "rays" in e.get("fx", []) and rtl:
        pass
    paste(im, lay, x, y, a, sc, rot)
    if e.get("sub"):
        s = text3d(e["sub"].upper(), 40, "white", 3, P_XB)
        paste(im, s, W / 2, y - lay.height * sc / 2 - 10, a * ease((dt - 0.15) / 0.2))
    # twinkles around the text
    rng = np.random.default_rng(int(e["t"] * 100))
    for k in range(5):
        ox, oy = rng.uniform(-0.5, 0.5) * lay.width * sc, rng.uniform(-0.5, 0.5) * lay.height * sc
        ph = rng.uniform(0, 6)
        tw = max(0, math.sin(dt * 7 + ph)) ** 3
        if tw > 0.05 and dt > 0.2:
            paste(im, star4(18), x + ox, y + oy, a * tw, 0.6 + tw)


def draw_icon(im, e, dt):
    d = e["dur"]
    lay = icon(e["icon"], e["size"])
    x, y = e["x"], e["y"]
    pin, pout = anim_in_out(dt, d, 0.3, 0.22)
    sc, a, rot = 1.0, 1.0, 0.0
    an = e["anim"]
    if an == "pop":
        sc = back_out(dt / 0.32, 2.6)
        rot = 14 * (1 - ease_out(dt / 0.4))
    elif an == "drop":
        y = e["y"] - 700 * (1 - easeb(dt / 0.6))
    elif an == "fly_l":
        x = e["x"] - 800 * (1 - back_out(dt / 0.35, 1.3))
        rot = 20 * (1 - ease_out(dt / 0.35))
    elif an == "fly_r":
        x = e["x"] + 800 * (1 - back_out(dt / 0.35, 1.3))
        rot = -20 * (1 - ease_out(dt / 0.35))
    sc *= pout if pout < 1 else 1
    y += 10 * math.sin(dt * 4.2 + e["x"])
    rot += 4 * math.sin(dt * 3.1 + e["y"]) if dt > 0.4 else 0
    if e.get("ring") and dt > 0.2:
        rd = ImageDraw.Draw(im)
        for k in range(3):
            q = ((dt - 0.2) * 1.1 + k / 3) % 1
            r = e["size"] * (0.4 + 1.1 * q)
            al = int(200 * (1 - q) * pout)
            rd.ellipse((x - r, y - r * 0.5 + e["size"] * 0.42, x + r, y + r * 0.5 + e["size"] * 0.42),
                       outline=(255, 210, 90, al), width=5)
    paste(im, lay, x, y, a, sc, rot)


def draw_chip(im, e, dt):
    lay = chip(e["txt"], e["icon"], e["style"])
    pin, pout = anim_in_out(dt, e["dur"], 0.35, 0.25)
    sgn = -1 if e["side"] == "left" else 1
    x = W / 2 + sgn * 1000 * (1 - back_out(dt / 0.36, 1.3)) + sgn * 1000 * (1 - pout) ** 2
    sc = 1 + 0.08 * (1 - ease_out(dt / 0.4))
    paste(im, lay, x, e["y"], 1.0, sc)


def draw_iconrow(im, e, dt):
    n = len(e["icons"])
    for k, nm in enumerate(e["icons"]):
        x = W / 2 + (k - (n - 1) / 2) * e["size"] * 1.45
        sub = dict(icon=nm, size=e["size"], x=x, y=e["y"], anim="pop", dur=e["dur"] - k * e["gap"], ring=False)
        ddt = dt - k * e["gap"]
        if ddt > 0:
            draw_icon(im, sub, ddt)


def draw_burst(im, e, dt):
    if dt > 1.3:
        return
    rng = np.random.default_rng(int(e["t"] * 1000) % 2 ** 31)
    n = e.get("n", 50)
    ang = rng.uniform(0, 2 * np.pi, n)
    sp = rng.uniform(300, 1500, n)
    sz = rng.uniform(4, 13, n)
    kind = rng.uniform(0, 1, n)
    for k in range(n):
        tt = dt
        drag = (1 - math.exp(-tt * 3.2)) / 3.2
        x = e["x"] + math.cos(ang[k]) * sp[k] * drag
        y = e["y"] + math.sin(ang[k]) * sp[k] * drag + 380 * tt * tt
        life = max(0, 1 - tt / (0.8 + 0.4 * kind[k]))
        if life <= 0:
            continue
        if kind[k] > 0.82:
            paste(im, star4(int(sz[k] * 2.2)), x, y, life, 1.0)
        else:
            paste(im, glow_dot(int(sz[k]), e.get("color", "gold")), x, y, life * 0.95, 1.0)


def draw_boundary(im, e, dt):
    p = ease_out(dt / 0.9)
    a = ease((e["dur"] - dt) / 0.4)
    d = ImageDraw.Draw(im)
    pts = [(120, 640), (720, 600), (760, 1290), (120, 1320)]
    per = list(zip(pts, pts[1:] + pts[:1]))
    total = p * 4
    for k, (p0, p1) in enumerate(per):
        f = min(1, max(0, total - k))
        if f <= 0:
            break
        x1, y1 = p0[0] + (p1[0] - p0[0]) * f, p0[1] + (p1[1] - p0[1]) * f
        L = math.hypot(x1 - p0[0], y1 - p0[1])
        nseg = int(L / 34) + 1
        for s in range(nseg):
            q0, q1 = s / nseg, min(1, (s + 0.6) / nseg)
            d.line([(p0[0] + (x1 - p0[0]) * q0, p0[1] + (y1 - p0[1]) * q0), (p0[0] + (x1 - p0[0]) * q1, p0[1] + (y1 - p0[1]) * q1)],
                   fill=(120, 255, 170, int(230 * a)), width=7)
    if p > 0.95:
        poly = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ImageDraw.Draw(poly).polygon(pts, fill=(60, 230, 140, int(55 * a * (0.6 + 0.4 * math.sin(dt * 6)))))
        im.alpha_composite(poly)


DRAW = dict(t3d=draw_t3d, arabic=draw_t3d, icon=draw_icon, chip=draw_chip, iconrow=draw_iconrow, burst=draw_burst,
            boundary=draw_boundary)


# --------------------------------------------------------------- captions ---
def cap_style(w):
    k = R.norm_word(w)
    return CAT.get(k)


@functools.lru_cache(maxsize=512)
def cap_word(txt, style, size):
    if style:
        return text3d(txt, int(size * 1.14), style, 8, P_BLACK, 2000)
    return text3d(txt, size, "white", 4, P_BLACK, 2000)


GROUP_LAYOUT = {}


def group_layout(gi):
    if gi in GROUP_LAYOUT:
        return GROUP_LAYOUT[gi]
    g = R.GROUPS[gi]
    size = 84
    while True:
        sprites = [cap_word(w["w"].upper(), cap_style(w["w"]), size) for w in g["words"]]
        boxes = [s.split()[3].point(lambda v: 255 if v > 140 else 0).getbbox() or (0, 0, s.width, s.height) for s in sprites]
        gap = int(size * 0.26)
        tw = sum(b[2] - b[0] for b in boxes) + gap * (len(sprites) - 1)
        if tw <= 1000 or size <= 48:
            break
        size -= 4
    xs, x = [], W / 2 - tw / 2
    for s, b in zip(sprites, boxes):
        vis_c = (b[0] + b[2]) / 2
        xs.append(x + (b[2] - b[0]) / 2 + (s.width / 2 - vis_c))
        x += b[2] - b[0] + gap
    GROUP_LAYOUT[gi] = (sprites, xs)
    return GROUP_LAYOUT[gi]


def draw_captions(im, t):
    for gi, g in enumerate(R.GROUPS):
        if g["s"] <= t < g["end"]:
            sprites, xs = group_layout(gi)
            fade = ease((g["end"] - t) / 0.1)
            for k, w in enumerate(g["words"]):
                dt = t - (w["s"] - 0.04)
                if dt < 0:
                    break
                sc = 0.55 + 0.45 * back_out(dt / 0.2, 2.4)
                yy = R.CAP_Y - 30 * (1 - ease_out(dt / 0.2))
                paste(im, sprites[k], xs[k], yy, ease(dt / 0.06) * fade, sc)
            return


def draw_hook(im, t):
    hook = R.HOOK
    cur = [k for k, w in enumerate(hook) if w["s"] - 0.04 <= t]
    if not cur:
        return
    k = cur[-1]
    w = hook[k]
    last = k == len(hook) - 1
    dt = t - (w["s"] - 0.04)
    txt = w["w"].upper().rstrip(".,")
    st = cap_style(w["w"]) or ("gold" if last else "white")
    lay = text3d(txt, 230 if last else 160, st, 18 if last else 12, P_BLACK, 1000)
    a = ease((PLAN["title"][0] - t) / 0.25)
    dirs = ["fly_l", "fly_r", "grow", "fly_b"]
    an = "slam" if last else dirs[k % 4]
    e = dict(dur=99, y=900, anim=an, txt=txt, style=st, size=1, t=w["s"])
    # reuse t3d anim math by temporarily drawing via a stub sprite
    x, y, sc, rot = W / 2, 900, 1.0, 0.0
    if an == "slam":
        sc = 2.4 - 1.4 * ease_out(dt / 0.16)
        rot = -8 * (1 - ease_out(dt / 0.2))
        sc *= 1 + 0.03 * min(1, max(0, dt - 0.3))
    elif an == "fly_l":
        x = W / 2 - 900 * (1 - back_out(dt / 0.26, 1.2))
    elif an == "fly_r":
        x = W / 2 + 900 * (1 - back_out(dt / 0.26, 1.2))
    elif an == "fly_b":
        y = 900 + 300 * (1 - back_out(dt / 0.26, 1.4))
    else:
        sc = 0.2 + 0.8 * back_out(dt / 0.3, 2.2)
    paste(im, shine(lay, (dt - 0.2) / 0.5), x, y, a, sc, rot)


# ---------------------------------------------------------------- title -----
def title2(t):
    T0, T1 = PLAN["title"]
    T = t - T0
    im = R.asset_bg("konsep_kompleks")
    z = 1.0 + 0.06 * T / (T1 - T0)
    cw, ch = W / z, H / z
    im = im.resize((W, H), Image.BICUBIC, box=((W - cw) / 2, (H - ch) / 2, (W + cw) / 2, (H + ch) / 2)).convert("RGBA")
    arr = np.asarray(im).astype(np.float32)
    rr = ROT_RAYS[int(T * 6) % len(ROT_RAYS)]
    arr[20:1420, :, :3] += rr[:, 160:160 + W] * 0.55 * ease(T / 0.4)
    im = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGBA")
    top = R.title_layer("top")
    paste(im, top, W / 2, 470, ease((T - 0.1) / 0.4))
    l1 = text3d("SEBIDANG", 120, "white", 10)
    l2 = text3d("TANAH WAKAF", 150, "gold", 14)
    paste(im, l1, W / 2 - 900 * (1 - back_out(T / 0.3, 1.2)), 610, 1)
    dt2 = T - 0.25
    if dt2 > 0:
        paste(im, shine(l2, (dt2 - 0.3) / 0.7), W / 2, 780, ease(dt2 / 0.06), 2.2 - 1.2 * ease_out(dt2 / 0.18), -6 * (1 - ease_out(dt2 / 0.2)))
    dt3 = T - 0.8
    if dt3 > 0:
        c = chip("untuk Pondok Warga Emas", "house", "coral")
        paste(im, c, W / 2, 960 + 200 * (1 - back_out(dt3 / 0.35, 1.3)), ease(dt3 / 0.15))
    for k, (nm, x) in enumerate((("seedling", 240), ("oldman", 440), ("oldwoman", 640), ("mosque", 840))):
        dd = T - 1.2 - k * 0.15
        if dd > 0:
            paste(im, icon(nm, 150), x, 1200 + 8 * math.sin(T * 4 + k), 1, back_out(dd / 0.3, 2.4))
    return im.convert("RGB")


# --------------------------------------------------------------- frame ------
TR_KINDS = ["whip", "zoom", "flash", "whip_up"]
TR = 0.30


def shot_img(sh, t):
    if sh["spec"]["k"] == "card" and sh["spec"]["card"] == "title":
        return title2(t)
    return R.shot_frame(sh, t)


def zoom_img(im, z):
    if abs(z - 1) < 0.002:
        return im
    if z > 1:
        cw, ch = W / z, H / z
        return im.resize((W, H), Image.BICUBIC, box=((W - cw) / 2, (H - ch) / 2, (W + cw) / 2, (H + ch) / 2))
    small = im.resize((int(W * z), int(H * z)), Image.BICUBIC)
    out = Image.new("RGB", (W, H))
    out.paste(small, ((W - small.width) // 2, (H - small.height) // 2))
    return out


def base_frame(t):
    shots = PLAN["shots"]
    i = max(k for k, s in enumerate(shots) if s["o0"] <= t + 1e-6) if t >= shots[0]["o0"] else 0
    sh = shots[i]
    im = shot_img(sh, t)
    flash = 0.0
    if i > 0:
        pr = shots[i - 1]
        dt = t - sh["o0"]
        both_spk = pr["spec"]["k"] == "spk" and sh["spec"]["k"] == "spk"
        if both_spk and dt < 0.22:
            im = zoom_img(im, 1.10 - 0.10 * ease_out(dt / 0.22))
        elif not both_spk and dt < TR:
            kind = TR_KINDS[i % len(TR_KINDS)]
            a = ease(dt / TR)
            prev = shot_img(pr, t)
            if kind in ("whip", "whip_up"):
                c = Image.new("RGB", (W, H))
                if kind == "whip":
                    c.paste(prev, (int(-a * W), 0))
                    c.paste(im, (int((1 - a) * W), 0))
                    bl = c.resize((W // 14, H), Image.BILINEAR).resize((W, H), Image.BILINEAR)
                else:
                    c.paste(prev, (0, int(-a * H)))
                    c.paste(im, (0, int((1 - a) * H)))
                    bl = c.resize((W, H // 14), Image.BILINEAR).resize((W, H), Image.BILINEAR)
                im = Image.blend(c, bl, min(1, math.sin(math.pi * a) * 1.3))
            elif kind == "zoom":
                p2 = zoom_img(prev, 1 + 0.7 * a)
                n2 = zoom_img(im, 1.35 - 0.35 * a)
                im = Image.blend(p2, n2, a)
            else:
                im = prev if a < 0.5 else im
                flash = max(flash, 0.9 * (1 - abs(a - 0.5) * 2))
    ec = PLAN["endcard_at"]
    if t >= ec:
        a = ease((t - ec) / 0.5)
        card = R.end_layer()
        base = im.convert("RGBA")
        c2 = card.copy()
        c2.putalpha(int(255 * a))
        base.alpha_composite(c2)
        im = base.convert("RGB")
    return im, flash, sh


def frame(fi):
    t = fi / FPS
    im, flash, sh = base_frame(t)
    arr = np.asarray(im).astype(np.float32)
    arr *= R.MAP
    arr += R.GRAIN[fi % len(R.GRAIN)]
    shake = [0.0, 0.0, 0.0]
    for e in EVENTS:
        dt = t - e["o"]
        if dt < 0 or dt > 3.0:
            continue
        typ = e["type"]
        fx = e.get("fx", [])
        if typ == "flash" or "flash" in fx:
            if dt < 0.3:
                flash = max(flash, e.get("a", 0.7) * (1 - dt / 0.3) ** 1.5)
        if typ == "shake" or "shake" in fx:
            amp, dur = (e["amp"], e["dur"]) if typ == "shake" else (14, 0.35)
            if dt < dur:
                k = (1 - dt / dur) ** 2
                shake[0] += amp * k * math.sin(dt * 71)
                shake[1] += amp * k * math.cos(dt * 53)
                shake[2] += amp * 0.08 * k * math.sin(dt * 40)
        if typ == "rays" or "rays" in fx:
            dur = e.get("dur", 2.2 if typ != "rays" else 1.5)
            if dt < dur:
                ra = 0.5 * ease(dt / 0.3) * ease((dur - dt) / 0.5)
                rr = ROT_RAYS[int(t * 6) % len(ROT_RAYS)]
                cy = int(e.get("y", 560))
                y0 = max(0, cy - 700)
                y1 = min(H, cy + 700)
                arr[y0:y1, :, :] += rr[y0 - (cy - 700): y1 - (cy - 700), 160:160 + W] * ra
    if flash > 0:
        arr += 255 * flash
    if t < 0.3:
        arr *= ease(t / 0.3)
    tot = PLAN["total"]
    if t > tot - 0.8:
        arr *= ease((tot - t) / 0.8)
    im = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).convert("RGBA")
    # ambient bokeh dust
    for k in range(16):
        r = DUST[k]
        x = (r[0] + r[2] * t) % (W + 200) - 100
        y = (r[1] - r[3] * t) % (H + 200) - 100
        paste(im, glow_dot(int(r[4]), "gold"), x, y, r[5] * (0.6 + 0.4 * math.sin(t * r[6] + k)))
    # tag pill
    tag = sh["spec"].get("tag")
    if tag:
        a = ease((t - sh["o0"] - 0.3) / 0.4) * ease((sh["o1"] - t) / 0.3)
        lay = R.tag_bitmap(tag)
        paste(im, lay, 70 + lay.width / 2 - 20 * (1 - a), 250, a)
    for e in EVENTS:
        dt = t - e["o"]
        if "burst" in e.get("fx", []) and 0 <= dt <= 1.3:
            draw_burst(im, dict(t=e["t"], x=W / 2, y=e["y"], n=55), dt)
        if e["type"] in DRAW and 0 <= dt <= e.get("dur", 1.4):
            DRAW[e["type"]](im, e, dt)
    if R.HOOK and t < PLAN["title"][0]:
        draw_hook(im, t)
    elif not (t >= PLAN["endcard_at"] + 0.4 and t > R.LAST_WORD_E + 0.4):
        draw_captions(im, t)
    if t >= PLAN["endcard_at"]:
        dt = t - PLAN["endcard_at"]
        for k, (nm, x, y) in enumerate((("heart", 190, 300), ("palms", 890, 300))):
            dd = dt - 0.5 - k * 0.2
            if dd > 0:
                paste(im, icon(nm, 150), x, y + 8 * math.sin(t * 3 + k), 1, back_out(dd / 0.3, 2.4))
    im = im.convert("RGB")
    if shake[0] or shake[1]:
        z = 1.04
        cx, cy = W / 2 + shake[0], H / 2 + shake[1]
        im = im.rotate(shake[2], Image.BILINEAR, center=(cx, cy), translate=(shake[0], shake[1]))
        im = zoom_img(im, z)
    return im


def init(work, frames):
    global PLAN, EVENTS, ROT_RAYS, DUST
    R.init(work, frames)
    R.PLAN = PLAN = json.load(open(os.path.join(work, "plan2.json")))
    R.GROUPS = R.make_groups(PLAN["words"])
    EVENTS = PLAN["events_fx"]
    R.HOOK = [w for w in PLAN["words"] if w["hook"]]
    R.LAST_WORD_E = PLAN["words"][-1]["e"]
    base = rays_img().resize((1400, 1400))
    ROT_RAYS = [np.asarray(base.rotate(k * 3, Image.BILINEAR)).astype(np.float32) for k in range(12)]
    rng = np.random.default_rng(5)
    DUST = [(rng.uniform(0, W), rng.uniform(0, H), rng.uniform(-12, 12), rng.uniform(15, 45), rng.uniform(3, 9),
             rng.uniform(0.25, 0.6), rng.uniform(0.5, 2)) for _ in range(16)]


def render_chunk(args):
    work, frames, a, b, path = args
    init(work, frames)
    cmd = ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
           "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "17", "-pix_fmt", "yuv420p", path]
    pr = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for fi in range(a, b):
        pr.stdin.write(frame(fi).tobytes())
    pr.stdin.close()
    pr.wait()
    return path


if __name__ == "__main__":
    work, frames = sys.argv[1:3]
    nw = int(sys.argv[4]) if len(sys.argv) > 4 else 4
    plan = json.load(open(os.path.join(work, "plan2.json")))
    N = int(round(plan["total"] * FPS))
    if os.environ.get("ONLY"):
        init(work, frames)
        for t in map(float, os.environ["ONLY"].split(",")):
            frame(int(round(t * FPS))).save(os.path.join(work, f"v2_{t:07.2f}.jpg"), quality=88)
        sys.exit()
    # interleave chunk sizes evenly
    nch = nw * 3
    cuts = [N * k // nch for k in range(nch + 1)]
    jobs = [(work, frames, cuts[k], cuts[k + 1], os.path.join(work, f"v2chunk{k:02d}.mp4")) for k in range(nch)]
    with Pool(nw) as pool:
        parts = pool.map(render_chunk, jobs, chunksize=1)
    with open(os.path.join(work, "v2chunks.txt"), "w") as f:
        for p_ in parts:
            f.write(f"file '{p_}'\n")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", os.path.join(work, "v2chunks.txt"),
                    "-c", "copy", os.path.join(work, "v2_video_only.mp4")], check=True)
    print("done", N, "frames")
