"""Stage 2: render 1080x1920 frames from plan.json.
Usage: python render.py <workdir> <frames_dir> <out.mp4> [workers]"""
import sys, os, json, math, subprocess, functools
from multiprocessing import Pool
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance

HERE = os.path.dirname(os.path.abspath(__file__))
W, H, FPS = 1080, 1920, 30
SRC_W, SRC_H = 1080, 1974
FACE_Y = 0.47

F_BLACK = "/usr/share/fonts/opentype/inter/InterDisplay-Black.otf"
F_XB = "/usr/share/fonts/opentype/inter/InterDisplay-ExtraBold.otf"
F_SEMI = "/usr/share/fonts/opentype/inter/Inter-SemiBold.otf"
F_SERIF = "/usr/share/fonts/truetype/crosextra/Caladea-Bold.ttf"
F_SERIF_I = "/usr/share/fonts/truetype/crosextra/Caladea-BoldItalic.ttf"
GOLD = (255, 201, 60)
GOLD_L = (255, 226, 140)
GOLD_D = (214, 150, 30)


@functools.lru_cache(None)
def font(path, size):
    return ImageFont.truetype(path, size)


def ease(x):
    x = min(1, max(0, x))
    return x * x * (3 - 2 * x)


def ease_out(x):
    x = min(1, max(0, x))
    return 1 - (1 - x) ** 3


def back_out(x, s=1.6):
    x = min(1, max(0, x)) - 1
    return x * x * ((s + 1) * x + s) + 1


# ----------------------------------------------------------------- assets ---
def grade(im, warm=True):
    im = ImageEnhance.Contrast(im).enhance(1.06)
    im = ImageEnhance.Color(im).enhance(1.08)
    if warm:
        a = np.asarray(im).astype(np.float32)
        a[..., 0] *= 1.03
        a[..., 2] *= 0.95
        im = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
    return im


@functools.lru_cache(None)
def asset(name):
    im = Image.open(os.path.join(HERE, "assets", name + ".jpg")).convert("RGB")
    im = im.resize((im.width * 2, im.height * 2), Image.LANCZOS).filter(ImageFilter.UnsharpMask(2, 60, 2))
    return grade(im)


@functools.lru_cache(None)
def asset_bg(name):
    im = asset(name)
    s = max(W / im.width, H / im.height) * 1.1
    im = im.resize((int(im.width * s), int(im.height * s)), Image.BILINEAR)
    x0, y0 = (im.width - W) // 2, (im.height - H) // 2
    im = im.crop((x0, y0, x0 + W, y0 + H)).filter(ImageFilter.GaussianBlur(40))
    return ImageEnhance.Brightness(im).enhance(0.42)


@functools.lru_cache(maxsize=6)
def src_frame(idx):
    idx = max(0, min(idx, NFRAMES - 1))
    return Image.open(os.path.join(FRAMES, f"{idx:05d}.jpg")).convert("RGB")


def make_maps():
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    d = np.sqrt(((xx - W / 2) / (W * 0.62)) ** 2 + ((yy - H * 0.48) / (H * 0.62)) ** 2)
    vig = 1 - 0.42 * np.clip(d - 0.45, 0, 1) ** 1.6
    top = 1 - 0.30 * np.clip(1 - yy / 330, 0, 1) ** 2
    bot = 1 - 0.55 * np.clip((yy - 1150) / 770, 0, 1) ** 1.3
    m = (vig * top * bot)[..., None]
    rng = np.random.default_rng(3)
    grain = [rng.normal(0, 4.2, (H // 2, W // 2, 1)).astype(np.float32).repeat(2, 0).repeat(2, 1) for _ in range(6)]
    leak = np.zeros((H, W, 3), np.float32)
    d2 = np.sqrt(((xx - W * 0.85) / W) ** 2 + ((yy - H * 0.15) / H) ** 2)
    g = np.exp(-(d2 / 0.45) ** 2)
    leak[..., 0], leak[..., 1], leak[..., 2] = 255 * g, 170 * g, 70 * g
    return m.astype(np.float32), grain, leak


# --------------------------------------------------------------- shots ------
def src_time(out_t):
    for s in PLAN["segs"]:
        if s["src0"] is not None and s["out0"] - 1e-6 <= out_t < s["out1"]:
            return s["src0"] + (out_t - s["out0"])
    # breath gap / beyond: hold the last frame of the previous segment
    prev = [s for s in PLAN["segs"] if s["src0"] is not None and s["out1"] <= out_t + 1e-6]
    if prev:
        s = prev[-1]
        return s["src0"] + (s["out1"] - s["out0"]) - 0.02
    return PLAN["segs"][0]["src0"] or 0


def r_spk(spec, p, t):
    z = spec["z"][0] + (spec["z"][1] - spec["z"][0]) * ease(p)
    im = src_frame(int(round(src_time(t) * FPS)))
    cw, ch = W / z, H / z
    cx, cy = SRC_W / 2, SRC_H * FACE_Y
    x0 = min(max(cx - cw / 2, 0), SRC_W - cw)
    y0 = min(max(cy - ch / 2, 0), SRC_H - ch)
    return im.resize((W, H), Image.BICUBIC, box=(x0, y0, x0 + cw, y0 + ch))


def r_img(spec, p, t):
    im = asset(spec["img"])
    e = ease(p)
    a, b = spec["a"], spec["b"]
    cx, cy, sc = (a[i] + (b[i] - a[i]) * e for i in range(3))
    maxh = min(im.height, im.width * H / W)
    ch = maxh * sc
    cw = ch * W / H
    x0 = min(max(cx * im.width - cw / 2, 0), im.width - cw)
    y0 = min(max(cy * im.height - ch / 2, 0), im.height - ch)
    return im.resize((W, H), Image.BICUBIC, box=(x0, y0, x0 + cw, y0 + ch))


FG_H, FG_Y = 1060, 300


@functools.lru_cache(None)
def fg_mask():
    m = np.ones((FG_H, W), np.float32)
    f = 70
    ramp = np.linspace(0, 1, f)
    m[:f] *= ramp[:, None]
    m[-f:] *= ramp[::-1][:, None]
    return Image.fromarray((m * 255).astype(np.uint8))


def r_wide(spec, p, t):
    im = asset(spec["img"])
    bg = asset_bg(spec["img"]).copy()
    ch = im.height
    cw = ch * W / FG_H
    if cw > im.width:
        cw = im.width
        ch = cw * FG_H / W
    e = ease(p)
    pos = spec["a"] + (spec["b"] - spec["a"]) * e
    x0 = pos * (im.width - cw)
    y0 = (im.height - ch) / 2
    fg = im.resize((W, FG_H), Image.BICUBIC, box=(x0, y0, x0 + cw, y0 + ch))
    bg.paste(fg, (0, FG_Y), fg_mask())
    d = ImageDraw.Draw(bg)
    for yy in (FG_Y + 8, FG_Y + FG_H - 9):
        d.line([(80, yy), (W - 80, yy)], fill=GOLD_D, width=2)
    return bg


# ----------------------------------------------------------------- text -----
def text_size(fnt, s, sp=0):
    b = fnt.getbbox(s)
    return b[2] - b[0] + sp * max(0, len(s) - 1), b


def draw_spaced(d, xy, s, fnt, fill, sp):
    x, y = xy
    for ch in s:
        d.text((x, y), ch, font=fnt, fill=fill)
        x += fnt.getlength(ch) + sp


def shadowed(layer, blur=12, strength=200, offset=(0, 6)):
    a = layer.split()[3]
    sh = Image.new("RGBA", layer.size, (0, 0, 0, 0))
    sh.putalpha(a.point(lambda v: v * strength // 255).filter(ImageFilter.GaussianBlur(blur)))
    out = Image.new("RGBA", layer.size, (0, 0, 0, 0))
    out.alpha_composite(sh, offset)
    out.alpha_composite(layer)
    return out


def gold_fill(mask):
    w, h = mask.size
    g = np.zeros((h, w, 4), np.uint8)
    y = np.linspace(0, 1, h)[:, None]
    for c, (a, b) in enumerate(zip(GOLD_L, GOLD_D)):
        g[..., c] = (a + (b - a) * y).astype(np.uint8)
    g[..., 3] = np.asarray(mask)
    return Image.fromarray(g, "RGBA")


def norm_word(w):
    return "".join(ch for ch in w.lower() if ch.isalnum() or ch in "-'")


KEY = {"akhirat", "kebajikan", "sumbangan", "wakaf", "diwakafkan", "hektar", "warga", "emas", "warga-warga",
       "pondok", "pondok-pondok", "ilmu", "sebarkan", "hari", "raya", "allah", "madrasah", "alhamdulillah",
       "syukur", "asrama", "kompleks", "berkelamin", "single", "bismillahirrahmanirrahim"}

CAP_Y = 1395
CAP_MAXW = 960


@functools.lru_cache(maxsize=64)
def caption_bitmap(gi, active):
    g = GROUPS[gi]
    size = 76
    while True:
        f, fk = font(F_BLACK, size), font(F_BLACK, int(size * 1.12))
        parts = []
        for i, w in enumerate(g["words"]):
            txt = w["w"].upper()
            k = norm_word(w["w"]) in KEY
            fn = fk if (k or i == active) else f
            parts.append((txt, fn, k))
        sp = int(size * 0.28)
        tw = sum(fn.getlength(t) for t, fn, _ in parts) + sp * (len(parts) - 1)
        if tw <= CAP_MAXW or size <= 48:
            break
        size -= 4
    hgt = int(size * 1.9)
    pad = 30
    lay = Image.new("RGBA", (int(tw) + pad * 2, hgt + pad * 2), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    x = pad
    base = pad + hgt * 0.78
    for i, (t, fn, k) in enumerate(parts):
        asc = fn.getmetrics()[0]
        y = base - asc
        if i == active:
            col = GOLD
        elif k:
            col = GOLD_L
        elif active >= 0 and i > active:
            col = (255, 255, 255, 150)
        else:
            col = (255, 255, 255)
        d.text((x, y), t, font=fn, fill=col, stroke_width=max(3, size // 14), stroke_fill=(10, 8, 5, 235))
        x += fn.getlength(t) + sp
    return shadowed(lay, 14, 210, (0, 8))


@functools.lru_cache(maxsize=32)
def hook_bitmap(i):
    w = HOOK[i]
    txt = w["w"].upper().rstrip(".,")
    last = i == len(HOOK) - 1
    k = norm_word(w["w"]) in KEY or last
    size = 210 if last else (170 if k else 150)
    f = font(F_BLACK, size)
    while f.getlength(txt) > 980:
        size -= 6
        f = font(F_BLACK, size)
    tw = int(f.getlength(txt))
    lay = Image.new("RGBA", (tw + 80, int(size * 1.6)), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    m = Image.new("L", lay.size, 0)
    ImageDraw.Draw(m).text((40, size * 0.2), txt, font=f, fill=255)
    if k:
        lay = gold_fill(m)
    else:
        d.text((40, size * 0.2), txt, font=f, fill=(255, 255, 255))
    return shadowed(lay, 18, 230, (0, 10))


@functools.lru_cache(maxsize=16)
def slam_bitmap(i):
    s = SLAMS[i]
    size = 150
    f = font(F_BLACK, size)
    while f.getlength(s["txt"]) > 960:
        size -= 6
        f = font(F_BLACK, size)
    tw = int(f.getlength(s["txt"]))
    sub = s["sub"].upper()
    fs = font(F_SEMI, 36)
    sw, _ = text_size(fs, sub, 6)
    w = max(tw, sw) + 120
    h = int(size * 1.35) + 110
    m = Image.new("L", (w, h), 0)
    ImageDraw.Draw(m).text(((w - tw) // 2, 70 + size * 0.05), s["txt"], font=f, fill=255)
    lay = gold_fill(m)
    d = ImageDraw.Draw(lay)
    if sub:
        draw_spaced(d, ((w - sw) // 2, 14), sub, fs, (255, 255, 255, 235), 6)
    return shadowed(lay, 20, 235, (0, 10)), tw


@functools.lru_cache(maxsize=8)
def tag_bitmap(txt):
    f = font(F_SEMI, 34)
    tw = int(f.getlength(txt))
    lay = Image.new("RGBA", (tw + 100, 76), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    d.rounded_rectangle((0, 0, tw + 98, 74), 37, fill=(12, 10, 6, 150), outline=GOLD_D, width=2)
    # map-pin dot
    d.ellipse((24, 24, 50, 50), fill=GOLD)
    d.ellipse((32, 32, 42, 42), fill=(12, 10, 6))
    d.text((66, 15), txt, font=f, fill=(255, 255, 255))
    return lay


def paste(base, lay, cx, cy, alpha=1.0, scale=1.0):
    if alpha <= 0.01:
        return
    if abs(scale - 1) > 0.003:
        lay = lay.resize((max(1, int(lay.width * scale)), max(1, int(lay.height * scale))), Image.BILINEAR)
    if alpha < 0.999:
        a = lay.split()[3].point(lambda v: int(v * alpha))
        lay = lay.copy()
        lay.putalpha(a)
    base.alpha_composite(lay, (int(cx - lay.width / 2), int(cy - lay.height / 2)))


# ----------------------------------------------------------------- cards ----
def r_title(p, t):
    bg = asset_bg("konsep_kompleks")
    z = 1.0 + 0.05 * p
    cw, ch = W / z, H / z
    im = bg.resize((W, H), Image.BICUBIC, box=((W - cw) / 2, (H - ch) / 2, (W + cw) / 2, (H + ch) / 2))
    im = ImageEnhance.Brightness(im).enhance(0.75).convert("RGBA")
    lt = p * PLAN["title"][1] + 0 - PLAN["title"][0] * 0
    T = p * (PLAN["title"][1] - PLAN["title"][0])
    # particles
    d = ImageDraw.Draw(im)
    rng = np.random.default_rng(11)
    for _ in range(70):
        x, y0, sp, r = rng.uniform(0, W), rng.uniform(0, H), rng.uniform(20, 70), rng.uniform(1.5, 4)
        y = (y0 - sp * T) % H
        a = int(120 + 100 * math.sin(T * 2 + x))
        d.ellipse((x - r, y - r, x + r, y + r), fill=(255, 210, 120, max(0, min(255, a))))
    cy = 860
    paste(im, title_layer("top"), W / 2, cy - 190, ease((T - 0.15) / 0.5), 1.0)
    l = ease_out((T - 0.25) / 0.7)
    if l > 0:
        d.line([(W / 2 - 330 * l, cy - 130), (W / 2 + 330 * l, cy - 130)], fill=GOLD, width=3)
    paste(im, title_layer("main"), W / 2, cy - 15 + 30 * (1 - ease_out((T - 0.35) / 0.6)), ease((T - 0.35) / 0.5),
          1.08 - 0.08 * ease_out((T - 0.35) / 1.2))
    paste(im, title_layer("sub"), W / 2, cy + 120 + 20 * (1 - ease_out((T - 0.9) / 0.6)), ease((T - 0.9) / 0.5))
    return im.convert("RGB")


@functools.lru_cache(None)
def title_layer(which):
    if which == "top":
        f = font(F_SEMI, 34)
        s = "MADRASAH ZAWIYAH AN NUR  ·  GERIK"
        w, _ = text_size(f, s, 7)
        lay = Image.new("RGBA", (w + 40, 70), (0, 0, 0, 0))
        draw_spaced(ImageDraw.Draw(lay), (20, 12), s, f, GOLD_L, 7)
        return shadowed(lay, 8, 200, (0, 3))
    if which == "main":
        f = font(F_SERIF, 116)
        lines = ["SEBIDANG", "TANAH WAKAF"]
        lay = Image.new("RGBA", (1040, 290), (0, 0, 0, 0))
        d = ImageDraw.Draw(lay)
        for i, s in enumerate(lines):
            d.text(((1040 - f.getlength(s)) / 2, 8 + i * 128), s, font=f, fill=(255, 255, 255))
        return shadowed(lay, 16, 230, (0, 8))
    f = font(F_SERIF_I, 64)
    s = "untuk Pondok Warga Emas"
    m = Image.new("L", (int(f.getlength(s)) + 40, 100), 0)
    ImageDraw.Draw(m).text((20, 10), s, font=f, fill=255)
    return shadowed(gold_fill(m), 12, 220, (0, 6))


@functools.lru_cache(None)
def end_layer():
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    a = np.zeros((H, W, 4), np.float32)
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    top, bot = np.array([10, 46, 34]), np.array([2, 14, 10])
    g = (yy / H)[..., None]
    a[..., :3] = top * (1 - g) + bot * g
    glow = np.exp(-(((xx - W / 2) / 520) ** 2 + ((yy - 820) / 520) ** 2))[..., None]
    a[..., :3] += glow * np.array([70, 55, 20])
    a[..., 3] = 255
    lay = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGBA")
    d = ImageDraw.Draw(lay)
    # thin geometric frame
    d.rounded_rectangle((70, 380, W - 70, 1290), 28, outline=(214, 150, 30, 160), width=2)
    # 8-point star ornament
    cx, cy, r = W / 2, 500, 34
    pts = []
    for k in range(16):
        rr = r if k % 2 == 0 else r * 0.45
        ang = math.pi / 8 * k - math.pi / 2
        pts.append((cx + rr * math.cos(ang), cy + rr * math.sin(ang)))
    d.polygon(pts, fill=GOLD)
    f1 = font(F_SERIF, 92)
    m = Image.new("L", (W, 240), 0)
    md = ImageDraw.Draw(m)
    for i, s in enumerate(["PONDOK", "WARGA EMAS"]):
        md.text(((W - f1.getlength(s)) / 2, 10 + i * 104), s, font=f1, fill=255)
    lay.alpha_composite(shadowed(gold_fill(m), 10, 200, (0, 5)), (0, 570))
    f2 = font(F_SEMI, 40)
    s = "Madrasah Zawiyah An Nur, Gerik"
    d.text(((W - f2.getlength(s)) / 2, 826), s, font=f2, fill=(255, 255, 255, 235))
    d.line([(W / 2 - 160, 906), (W / 2 + 160, 906)], fill=GOLD_D, width=2)
    f3 = font(F_SERIF_I, 54)
    for i, s in enumerate(["“Mudah-mudahan sumbangan", "tuan-tuan sekalian menjadi", "kebajikan hingga ke akhirat.”"]):
        d.text(((W - f3.getlength(s)) / 2, 945 + i * 70), s, font=f3, fill=(255, 255, 255))
    f4 = font(F_BLACK, 40)
    s = "SEBARKAN BERITA INI"
    tw = f4.getlength(s)
    d.rounded_rectangle((W / 2 - tw / 2 - 44, 1172, W / 2 + tw / 2 + 44, 1252), 40, fill=GOLD)
    d.text(((W - tw) / 2, 1188), s, font=f4, fill=(20, 30, 20))
    return lay


# --------------------------------------------------------------- compose ----
SHOT_FN = dict(spk=r_spk, img=r_img, wide=r_wide)
XF = 0.32  # crossfade length for spk<->broll


def shot_frame(sh, t):
    dur = sh["o1"] - sh["o0"]
    p = (t - sh["o0"]) / max(dur, 1e-3)
    if sh["spec"]["k"] == "card":
        if sh["spec"]["card"] == "title":
            return r_title(min(max(p, 0), 1), t)
        return Image.new("RGB", (W, H))
    im = SHOT_FN[sh["spec"]["k"]](sh["spec"], p, t)
    if sh["pid"] == "hook":
        im = ImageEnhance.Brightness(im).enhance(0.62)
        im = ImageEnhance.Color(im).enhance(0.75)
    return im


def frame(fi):
    t = fi / FPS
    shots = PLAN["shots"]
    i = max(k for k, s in enumerate(shots) if s["o0"] <= t + 1e-6) if t >= shots[0]["o0"] else 0
    sh = shots[i]
    im = shot_frame(sh, t)
    leak_a = 0.0
    # crossfade with previous shot
    if i > 0:
        pr = shots[i - 1]
        soft = not (pr["spec"]["k"] == "spk" and sh["spec"]["k"] == "spk")
        dt = t - sh["o0"]
        if soft and dt < XF:
            a = ease(dt / XF)
            prev = shot_frame(pr, t)
            if sh["spec"]["k"] != "card" and pr["spec"]["k"] != "card":
                z = 1 + 0.06 * (1 - a)
                im = im.resize((W, H), Image.BICUBIC, box=(W * (1 - 1 / z) / 2, H * (1 - 1 / z) / 2, W * (1 + 1 / z) / 2, H * (1 + 1 / z) / 2))
                leak_a = 0.55 * math.sin(math.pi * a)
            im = Image.blend(prev, im, a)
    # end card cross-dissolve
    ec = PLAN["endcard_at"]
    if t >= ec:
        a = ease((t - ec) / 0.9)
        card = end_layer()
        base = im.convert("RGBA")
        if a < 1:
            c2 = card.copy()
            c2.putalpha(int(255 * a))
            base.alpha_composite(c2)
        else:
            base = card.copy()
        im = base.convert("RGB")
    # hook kinetic intro: fade in from black
    arr = np.asarray(im).astype(np.float32)
    arr *= MAP
    arr += GRAIN[fi % len(GRAIN)]
    if leak_a > 0:
        arr += LEAK * leak_a
    if t < 0.35:
        arr *= ease(t / 0.35)
    tot = PLAN["total"]
    if t > tot - 0.8:
        arr *= ease((tot - t) / 0.8)
    im = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).convert("RGBA")
    overlays(im, t, sh)
    return im.convert("RGB")


def overlays(im, t, sh):
    # tags
    tag = sh["spec"].get("tag")
    if tag:
        a = ease((t - sh["o0"] - 0.3) / 0.4) * ease((sh["o1"] - t) / 0.3)
        lay = tag_bitmap(tag)
        paste(im, lay, 70 + lay.width / 2 - 20 * (1 - a), 260, a)
    # hook words
    if HOOK and t < PLAN["title"][0]:
        cur = [k for k, w in enumerate(HOOK) if w["s"] - 0.04 <= t]
        if cur:
            k = cur[-1]
            w = HOOK[k]
            last = k == len(HOOK) - 1
            dt = t - (w["s"] - 0.04)
            sc = 0.82 + 0.18 * back_out(dt / 0.18) if not last else 1.25 - 0.25 * ease_out(dt / 0.35)
            if last:
                sc += 0.04 * min(1, max(0, t - w["s"] - 0.35))
            a = 1.0
            if last:
                a = ease((PLAN["title"][0] - t) / 0.25)
            shake = (math.sin(t * 90) * 8 * max(0, 1 - dt / 0.25)) if last else 0
            paste(im, hook_bitmap(k), W / 2 + shake, 900, a, sc)
        return
    # slams
    for j, s in enumerate(SLAMS):
        dt = t - s["o"]
        if 0 <= dt <= s["d"]:
            lay, _ = slam_bitmap(j)
            sc = 1.45 - 0.45 * back_out(dt / 0.26, 1.2)
            a = ease(dt / 0.14) * ease((s["d"] - dt) / 0.3)
            shake = math.sin(dt * 80) * 7 * max(0, 1 - (dt - 0.22) / 0.2) if dt > 0.22 else 0
            paste(im, lay, W / 2 + shake, 560, a, sc)
    # captions
    if t >= PLAN["endcard_at"] + 0.4 and t > LAST_WORD_E + 0.4:
        return
    for gi, g in enumerate(GROUPS):
        if g["s"] <= t < g["end"]:
            act = -1
            for k, w in enumerate(g["words"]):
                if w["s"] - 0.03 <= t:
                    act = k
            lay = caption_bitmap(gi, act)
            dt = t - g["s"]
            a = ease(dt / 0.12) * ease((g["end"] - t) / 0.1)
            aw = g["words"][act]["s"] if act >= 0 else g["s"]
            pop = 1 + 0.06 * (1 - ease_out((t - aw) / 0.14))
            paste(im, lay, W / 2, CAP_Y + 26 * (1 - ease_out(dt / 0.18)), a, pop)
            break


def make_groups(words):
    groups = []
    cur = []
    for w in words:
        if w["hook"]:
            continue
        if cur:
            prev = cur[-1]
            text = " ".join(x["w"] for x in cur + [w])
            if (len(cur) >= 3 or len(text) > 22 or prev["w"][-1] in ".,?!" or w["s"] - prev["e"] > 0.55
                    or w["piece"] != prev["piece"]):
                groups.append(cur)
                cur = []
        cur.append(w)
    if cur:
        groups.append(cur)
    out = []
    for i, g in enumerate(groups):
        nxt = groups[i + 1][0]["s"] if i + 1 < len(groups) else 1e9
        end = min(nxt - 0.02, g[-1]["e"] + 0.45)
        out.append(dict(words=g, s=g[0]["s"] - 0.05, end=end))
    return out


def init(work, frames):
    global PLAN, GROUPS, HOOK, SLAMS, MAP, GRAIN, LEAK, FRAMES, NFRAMES, LAST_WORD_E
    PLAN = json.load(open(os.path.join(work, "plan.json")))
    FRAMES = frames
    NFRAMES = len(os.listdir(frames))
    GROUPS = make_groups(PLAN["words"])
    HOOK = [w for w in PLAN["words"] if w["hook"]]
    SLAMS = PLAN["slams"]
    LAST_WORD_E = PLAN["words"][-1]["e"]
    MAP, GRAIN, LEAK = make_maps()


def render_chunk(args):
    work, frames, a, b, path = args
    init(work, frames)
    cmd = ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
           "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "16", "-pix_fmt", "yuv420p",
           "-x264-params", "keyint=60", path]
    pr = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for fi in range(a, b):
        pr.stdin.write(frame(fi).tobytes())
        if (fi - a) % 150 == 0:
            print(f"  chunk {a}: {fi - a}/{b - a}", flush=True)
    pr.stdin.close()
    pr.wait()
    return path


if __name__ == "__main__":
    work, frames, out = sys.argv[1:4]
    nw = int(sys.argv[4]) if len(sys.argv) > 4 else 4
    plan = json.load(open(os.path.join(work, "plan.json")))
    N = int(round(plan["total"] * FPS))
    if os.environ.get("ONLY"):
        init(work, frames)
        for t in map(float, os.environ["ONLY"].split(",")):
            frame(int(t * FPS)).save(os.path.join(work, f"still_{t:07.2f}.jpg"), quality=90)
        sys.exit()
    cuts = [N * k // nw for k in range(nw + 1)]
    jobs = [(work, frames, cuts[k], cuts[k + 1], os.path.join(work, f"chunk{k}.mp4")) for k in range(nw)]
    with Pool(nw) as pool:
        parts = pool.map(render_chunk, jobs)
    with open(os.path.join(work, "chunks.txt"), "w") as f:
        for p_ in parts:
            f.write(f"file '{p_}'\n")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", os.path.join(work, "chunks.txt"),
                    "-c", "copy", os.path.join(work, "video_only.mp4")], check=True)
    print("done", N, "frames")
