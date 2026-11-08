"""Cinematic dakwah edit renderer.

Reads the edit decision list in edl.py, the graded A-roll, AI b-roll stills,
word-level transcript and synthesized audio, and renders a 1080x1920 30fps MP4.

usage: python3 render.py WORKDIR OUT.mp4 [start_s end_s]   (optional preview range)
"""
import json, math, os, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

WORK = sys.argv[1]
os.environ["EDIT_WORK"] = WORK
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import edl as E

W, H, FPS = 1080, 1920, 30
SR = 48000
OUT = sys.argv[2]
RANGE = (float(sys.argv[3]), float(sys.argv[4])) if len(sys.argv) > 4 else None
FONTS = f"{WORK}/fonts"
GOLD = (255, 201, 74)
WHITE = (255, 255, 255)

# ---------------------------------------------------------------- fonts
_fc = {}
def font(name, size, var=None):
    k = (name, size, var)
    if k not in _fc:
        f = ImageFont.truetype(f"{FONTS}/{name}", size,
                               layout_engine=ImageFont.Layout.RAQM)
        if var: f.set_variation_by_name(var)
        _fc[k] = f
    return _fc[k]

def ease_out(x): x = min(max(x, 0), 1); return 1 - (1 - x) ** 3
def ease_io(x): x = min(max(x, 0), 1); return x * x * (3 - 2 * x)
def back_out(x, s=1.9):
    x = min(max(x, 0), 1); x -= 1; return x * x * ((s + 1) * x + s) + 1

# ---------------------------------------------------------------- timeline
clips = []          # dicts with out_start/out_end
t = 0.0
for c in E.TIMELINE:
    c = dict(c)
    d = (c["src"][1] - c["src"][0]) if c["kind"] == "speech" else c["dur"]
    c["out_start"], c["out_end"], c["dur_"] = t, t + d, d
    clips.append(c); t += d
TOTAL = t
NFR = int(round(TOTAL * FPS))
print(f"total {TOTAL:.2f}s, {NFR} frames", flush=True)

def src_to_out(ts):
    """Map a source timestamp to output time (first speech clip containing it)."""
    for c in clips:
        if c["kind"] == "speech" and c["src"][0] <= ts < c["src"][1] and not c.get("hook"):
            return c["out_start"] + ts - c["src"][0]
    return None

# ---------------------------------------------------------------- words / captions
words = json.load(open(f"{WORK}/words.json"))   # [{w,s,e}] cleaned, source time
for w in words:   # whisper puts a word's start at the previous word's end after a pause
    w["s"] = min(max(w["s"], E.word_onset(w["s"])), w["e"] - 0.08)
cap_words = []   # output-time words per clip
for ci, c in enumerate(clips):
    if c["kind"] != "speech": continue
    a, b = c["src"]
    for w in words:
        if w["s"] >= a - 0.05 and w["e"] <= b + 0.1 and w["s"] < b:
            s = c["out_start"] + max(w["s"], a) - a
            e = c["out_start"] + min(w["e"], b) - a
            cap_words.append(dict(text=w["w"], s=s, e=e, clip=ci,
                                  emph=w["w"].upper().strip(",.?!") in E.EMPHASIS))

def chunk_words(ws):
    chunks, cur = [], []
    for w in ws:
        cur.append(w)
        brk = len(cur) >= 3 or w["text"].endswith((",", ".", "?", "!")) or w["emph"] and len(cur) >= 2
        if brk: chunks.append(cur); cur = []
    if cur: chunks.append(cur)
    return chunks

chunks = []
for ci in sorted(set(w["clip"] for w in cap_words)):
    for ch in chunk_words([w for w in cap_words if w["clip"] == ci]):
        chunks.append(dict(words=ch, s=ch[0]["s"], e=max(ch[-1]["e"], ch[0]["s"] + 0.4), clip=ci))
for i in range(len(chunks) - 1):        # hold each chunk until the next starts (same clip)
    if chunks[i + 1]["clip"] == chunks[i]["clip"]:
        chunks[i]["e"] = chunks[i + 1]["s"]
    else:
        chunks[i]["e"] = min(clips[chunks[i]["clip"]]["out_end"], chunks[i]["e"] + 0.3)

_wc = {}
def word_img(text, size, color, glow):
    k = (text, size, color, glow)
    if k in _wc: return _wc[k]
    f = font("Montserrat.ttf", size, "ExtraBold")
    bb = f.getbbox(text, stroke_width=max(3, size // 14))
    pad = 30
    im = Image.new("RGBA", (bb[2] - bb[0] + pad * 2, bb[3] - bb[1] + pad * 2), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    org = (pad - bb[0], pad - bb[1])
    # soft drop shadow
    sh = Image.new("RGBA", im.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).text((org[0] + 4, org[1] + 7), text, font=f, fill=(0, 0, 0, 170),
                            stroke_width=max(3, size // 14), stroke_fill=(0, 0, 0, 170))
    sh = sh.filter(ImageFilter.GaussianBlur(7))
    if glow:
        gl = Image.new("RGBA", im.size, (0, 0, 0, 0))
        ImageDraw.Draw(gl).text(org, text, font=f, fill=color + (255,))
        gl = gl.filter(ImageFilter.GaussianBlur(14))
        sh = Image.alpha_composite(sh, gl)
    d = ImageDraw.Draw(sh)
    d.text(org, text, font=f, fill=color + (255,), stroke_width=max(3, size // 14),
           stroke_fill=(20, 14, 6, 255))
    _wc[k] = sh
    return sh

CAP_Y = 1360
BASE = 76
def draw_captions(frame, tt):
    ch = next((c for c in chunks if c["s"] <= tt < c["e"]), None)
    if ch is None: return
    ws = ch["words"]
    texts = [w["text"].upper() for w in ws]
    sizes = [int(BASE * (1.18 if w["emph"] else 1.0)) for w in ws]
    imgs = [word_img(tx, sz, WHITE, False) for tx, sz in zip(texts, sizes)]
    gap = 4
    # line layout (max width 960)
    lines, cur, cw = [], [], 0
    for i, im in enumerate(imgs):
        wdt = im.width - 60
        if cur and cw + wdt + 22 > 960:
            lines.append(cur); cur, cw = [], 0
        cur.append(i); cw += wdt + (22 if len(cur) > 1 else 0)
    if cur: lines.append(cur)
    age = tt - ch["s"]
    chunk_a = ease_out(age / 0.12)
    y0 = CAP_Y - (len(lines) - 1) * 50 + (1 - chunk_a) * 25
    for li, ln in enumerate(lines):
        total_w = sum(imgs[i].width - 60 for i in ln) + 26 * (len(ln) - 1)
        x = W / 2 - total_w / 2
        cy = y0 + li * 104
        for i in ln:
            w = ws[i]; base_w = imgs[i].width - 60
            cx = x + base_w / 2
            active = w["s"] <= tt < max(w["e"], w["s"] + 0.15) or (tt >= w["e"] and (i == len(ws) - 1 or tt < ws[i + 1]["s"]))
            spoken = tt >= w["s"]
            if active:
                p = (tt - w["s"]) / 0.18
                sc = 1.0 + (0.18 if w["emph"] else 0.10) * (1 - ease_out(p))
                im = word_img(texts[i], int(sizes[i] * sc), GOLD, w["emph"])
            else:
                im = word_img(texts[i], sizes[i], WHITE if spoken or True else WHITE, False)
            if not spoken:
                im = im.copy(); im.putalpha(im.getchannel("A").point(lambda v: v * 0.55))
            a = chunk_a
            if a < 1:
                im = im.copy(); im.putalpha(im.getchannel("A").point(lambda v, a=a: v * a))
            frame.alpha_composite(im, (int(cx - im.width / 2), int(cy - im.height / 2)))
            x += base_w + 26

# ---------------------------------------------------------------- b-roll images
_bc = {}
def broll_base(name):
    if name in _bc: return _bc[name]
    im = Image.open(f"{WORK}/broll/{name}.png").convert("RGB")
    im = im.resize((int(W * 1.22), int(H * 1.22)), Image.LANCZOS)
    im = im.filter(ImageFilter.UnsharpMask(2, 60, 2))
    a = np.asarray(im).astype(np.float32) / 255
    # cinematic grade: lift blacks a touch, warm highlights, teal shadows
    lum = a.mean(2, keepdims=True)
    a = a * 0.96 + 0.02
    a = a + (np.array([0.035, 0.012, -0.03]) * lum) + (np.array([-0.02, 0.005, 0.03]) * (1 - lum))
    a = np.clip((a - 0.5) * 1.06 + 0.5, 0, 1)
    _bc[name] = Image.fromarray((a * 255).astype(np.uint8))
    return _bc[name]

def kenburns(name, p, motion):
    base = broll_base(name)
    bw, bh = base.size
    z0, z1, dx, dy = {"in": (1.0, 1.14, 0, 0), "out": (1.14, 1.0, 0, 0),
                      "left": (1.08, 1.12, 1, 0), "right": (1.08, 1.12, -1, 0),
                      "up": (1.06, 1.12, 0, 1), "down": (1.06, 1.12, 0, -1)}[motion]
    pe = ease_io(p)
    z = z0 + (z1 - z0) * pe
    cw, chh = bw / 1.22 / z * 1.0, bh / 1.22 / z
    cx = bw / 2 + dx * (pe - 0.5) * (bw - cw) * 0.8
    cy = bh / 2 + dy * (pe - 0.5) * (bh - chh) * 0.8
    box = (cx - cw / 2, cy - chh / 2, cx + cw / 2, cy + chh / 2)
    return base.resize((W, H), Image.BILINEAR, box=box)

# ---------------------------------------------------------------- overlays
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
r = np.sqrt(((xx - W / 2) / (W * 0.62)) ** 2 + ((yy - H * 0.47) / (H * 0.6)) ** 2)
VIG = Image.fromarray((np.clip(1 - 0.62 * np.clip(r - 0.45, 0, 1) ** 1.5, 0, 1) * 255).astype(np.uint8), "L")
VIG_RGB = Image.merge("RGB", (VIG, VIG, VIG))
rng = np.random.default_rng(3)
GRAIN = [Image.fromarray(np.clip(128 + rng.normal(0, 9, (H // 2, W // 2)), 0, 255).astype(np.uint8), "L")
         .resize((W, H), Image.BILINEAR) for _ in range(6)]
LEAK = Image.fromarray((np.clip(1 - np.sqrt(((xx - W * 0.1) / (W * 0.9)) ** 2 + ((yy - H * 0.25) / (H * 0.55)) ** 2), 0, 1) ** 2 * 255).astype(np.uint8), "L")
LEAK_COL = Image.new("RGB", (W, H), (255, 150, 60))

PART = rng.uniform(0, 1, (55, 5))
def particles(frame, tt, strength=1.0):
    d = ImageDraw.Draw(frame)
    for i, (px, py, sp, sz, ph) in enumerate(PART):
        x = (px * W + math.sin(tt * 0.4 + ph * 6) * 40) % W
        y = (py * H - tt * (20 + sp * 45)) % H
        a = int((0.35 + 0.65 * (0.5 + 0.5 * math.sin(tt * 2 + ph * 9))) * 150 * strength)
        s = 1.5 + sz * 3.5
        d.ellipse((x - s, y - s, x + s, y + s), fill=(255, 214, 140, a))

def label_ai(frame, a):
    im = word_small("ILUSTRASI AI", 24)
    im = im.copy(); im.putalpha(im.getchannel("A").point(lambda v: v * a * 0.75))
    frame.alpha_composite(im, (W - im.width - 36, 64))

_sc = {}
def word_small(text, size, var="SemiBold", color=WHITE):
    k = (text, size, var, color)
    if k not in _sc:
        f = font("Montserrat.ttf", size, var)
        bb = f.getbbox(text)
        im = Image.new("RGBA", (bb[2] - bb[0] + 20, bb[3] - bb[1] + 20), (0, 0, 0, 0))
        ImageDraw.Draw(im).text((10 - bb[0], 10 - bb[1]), text, font=f, fill=color + (255,))
        sh = im.filter(ImageFilter.GaussianBlur(4))
        out = Image.new("RGBA", im.size, (0, 0, 0, 0))
        out.alpha_composite(Image.merge("RGBA", (*[Image.new("L", im.size, 0)] * 3, sh.getchannel("A"))))
        out.alpha_composite(im)
        _sc[k] = out
    return _sc[k]

def text_block(text, fnt, color, width, align="center", spacing=14, shadow=True):
    """Render wrapped text block to RGBA."""
    d0 = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    words_ = text.split(" "); lines = []; cur = ""
    for w in words_:
        tst = (cur + " " + w).strip()
        if d0.textlength(tst, font=fnt) > width and cur:
            lines.append(cur); cur = w
        else: cur = tst
    if cur: lines.append(cur)
    asc, desc = fnt.getmetrics(); lh = asc + desc + spacing
    im = Image.new("RGBA", (width + 60, lh * len(lines) + 60), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    for i, ln in enumerate(lines):
        lw = d.textlength(ln, font=fnt)
        x = 30 + (width - lw) / 2 if align == "center" else 30
        d.text((x, 30 + i * lh), ln, font=fnt, fill=color + (255,))
    if shadow:
        sh = Image.new("RGBA", im.size, (0, 0, 0, 0))
        sh.putalpha(im.getchannel("A").filter(ImageFilter.GaussianBlur(8)).point(lambda v: min(255, v * 2)))
        out = Image.new("RGBA", im.size, (0, 0, 0, 0)); out.alpha_composite(sh); out.alpha_composite(im)
        return out
    return im

def fade_paste(frame, im, xy, a, dy=0):
    if a <= 0: return
    if a < 1:
        im = im.copy(); im.putalpha(im.getchannel("A").point(lambda v: v * a))
    frame.alpha_composite(im, (int(xy[0]), int(xy[1] + dy)))

_tb = {}
def cached_block(key, fn):
    if key not in _tb: _tb[key] = fn()
    return _tb[key]

# ---------------------------------------------------------------- cards
def dark_bg(name, p, motion="in", dim=0.45, blur=0):
    im = kenburns(name, p, motion)
    if blur: im = im.filter(ImageFilter.GaussianBlur(blur))
    return Image.blend(Image.new("RGB", (W, H), (6, 8, 14)), im, dim)

def card_title(c, lt):
    p = lt / c["dur_"]
    fr = dark_bg(c["bg"], p, "in", 0.42, 3).convert("RGBA")
    particles(fr, lt + 10, 1.0)
    big = cached_block("t1", lambda: text_block(c["line1"], font("Anton-Regular.ttf.ttf", 230), GOLD, 1000))
    mid = cached_block("t2", lambda: text_block(c["line2"], font("Anton-Regular.ttf.ttf", 104), WHITE, 1000))
    sub = cached_block("t3", lambda: text_block(c["line3"], font("Montserrat.ttf", 38, "SemiBold"), (230, 230, 230), 1000))
    s = 1.0 + 0.25 * (1 - ease_out(lt / 0.35))
    bi = big.resize((int(big.width * s), int(big.height * s)), Image.LANCZOS) if s != 1 else big
    fade_paste(fr, bi, (W / 2 - bi.width / 2, 700 - bi.height / 2), ease_out(lt / 0.2))
    fade_paste(fr, mid, (W / 2 - mid.width / 2, 860), ease_out((lt - 0.35) / 0.4), 30 * (1 - ease_out((lt - 0.35) / 0.4)))
    # gold rule
    a = ease_out((lt - 0.7) / 0.5)
    d = ImageDraw.Draw(fr); half = 160 * a
    d.rectangle((W / 2 - half, 1012, W / 2 + half, 1016), fill=GOLD + (int(255 * a),))
    fade_paste(fr, sub, (W / 2 - sub.width / 2, 1040), ease_out((lt - 0.9) / 0.5))
    out_a = ease_io((c["dur_"] - lt) / 0.35)
    return fr, out_a

def card_hadith(c, lt):
    p = lt / c["dur_"]
    fr = dark_bg(c["bg"], p, c.get("motion", "in"), 0.38, 4).convert("RGBA")
    particles(fr, lt + 30, 0.9)
    k = c["key"]
    hd = cached_block(k + "h", lambda: text_block(c["head"], font("Montserrat.ttf", 34, "Bold"), GOLD, 900))
    ar = cached_block(k + "a", lambda: text_block(c["arabic"], font("Amiri-Regular.ttf.ttf", 64), (255, 236, 190), 940, spacing=30))
    ms = cached_block(k + "m", lambda: text_block(c["malay"], font("PlayfairDisplay.ttf", 54), WHITE, 920, spacing=18))
    src = cached_block(k + "s", lambda: text_block(c["source"], font("Montserrat.ttf", 32, "Medium"), (210, 210, 210), 900))
    total_h = hd.height + ar.height + ms.height + src.height - 40
    y = H / 2 - total_h / 2 - 60
    seq = [(hd, 0.2), (ar, 0.6), (ms, 1.6), (src, 2.6)]
    for im, t0 in seq:
        a = ease_out((lt - t0) / 0.7)
        fade_paste(fr, im, (W / 2 - im.width / 2, y), a, 26 * (1 - a))
        if im is ar:
            d = ImageDraw.Draw(fr); aa = ease_out((lt - 1.2) / 0.6)
            yy_ = y + im.height + 2
            d.rectangle((W / 2 - 120 * aa, yy_, W / 2 + 120 * aa, yy_ + 3), fill=GOLD + (int(230 * aa),))
            y += 24
        y += im.height - 10
    out_a = ease_io((c["dur_"] - lt) / 0.5)
    return fr, out_a

def card_end(c, lt):
    p = lt / c["dur_"]
    fr = dark_bg(c["bg"], p, "out", 0.5, 2).convert("RGBA")
    particles(fr, lt + 50, 1.0)
    l1 = cached_block("e1", lambda: text_block(c["line1"], font("Anton-Regular.ttf.ttf", 120), GOLD, 1000))
    l2 = cached_block("e2", lambda: text_block(c["line2"], font("Montserrat.ttf", 44, "SemiBold"), WHITE, 900))
    l3 = cached_block("e3", lambda: text_block(c["line3"], font("Montserrat.ttf", 40, "Medium"), (235, 235, 235), 900))
    l4 = cached_block("e4", lambda: text_block(c["line4"], font("Montserrat.ttf", 36, "Bold"), GOLD, 900))
    y = 680
    for im, t0 in [(l1, 0.1), (l2, 0.5), (l3, 0.9), (l4, 1.3)]:
        a = ease_out((lt - t0) / 0.6)
        fade_paste(fr, im, (W / 2 - im.width / 2, y), a, 24 * (1 - a))
        y += im.height + (30 if im is l1 else 10)
    out_a = min(1, (c["dur_"] - lt) / 1.2)
    return fr, max(0, out_a)

CARDS = {"title": card_title, "hadith": card_hadith, "end": card_end}

# ---------------------------------------------------------------- A-roll readers
class Reader:
    def __init__(self, a, b):
        self.p = subprocess.Popen(["ffmpeg", "-v", "error", "-ss", f"{a:.3f}", "-i", f"{WORK}/aroll.mp4",
                                   "-t", f"{b - a + 0.2:.3f}", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                                  stdout=subprocess.PIPE)
        self.n = 0; self.last = None
    def get(self, idx):
        while self.n <= idx:
            buf = self.p.stdout.read(W * H * 3)
            if len(buf) < W * H * 3: break
            self.last = buf; self.n += 1
        return Image.frombuffer("RGB", (W, H), self.last, "raw", "RGB", 0, 1)
    def close(self):
        self.p.stdout.close(); self.p.kill(); self.p.wait()

def aroll_frame(c, reader, lt, ci):
    im = reader.get(int(lt * FPS + 0.5))
    zs = c.get("zoom", (1.0, 1.06))
    z = zs[0] + (zs[1] - zs[0]) * ease_io(lt / c["dur_"])
    # punch-in at given moments (local source time)
    for pt in c.get("punch", []):
        lp = c["src"][0]
        dt = (c["src"][0] + lt) - pt
        if 0 <= dt:
            z *= 1 + 0.12 * ease_out(dt / 0.12)
    if abs(z - 1) < 1e-3: return im
    fx, fy = c.get("focus", (0.5, 0.36))
    cw, chh = W / z, H / z
    x0 = min(max(fx * W - cw / 2, 0), W - cw); y0 = min(max(fy * H - chh / 2, 0), H - chh)
    return im.resize((W, H), Image.BILINEAR, box=(x0, y0, x0 + cw, y0 + chh))

# ---------------------------------------------------------------- main loop
ff = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
                       "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium",
                       "-crf", "17", "-pix_fmt", "yuv420p", "-tune", "film", f"{OUT}.video.mp4"],
                      stdin=subprocess.PIPE)
f0, f1 = (int(RANGE[0] * FPS), int(RANGE[1] * FPS)) if RANGE else (0, NFR)
readers = {}
TRANS = set(round(c["out_start"], 3) for c in clips if c.get("flash"))
for fi in range(f0, f1):
    tt = fi / FPS
    ci = next(i for i, c in enumerate(clips) if c["out_start"] <= tt < c["out_end"] or i == len(clips) - 1)
    c = clips[ci]; lt = tt - c["out_start"]
    for k in list(readers):
        if k != ci: readers.pop(k).close()
    if c["kind"] == "speech":
        if ci not in readers: readers[ci] = Reader(*c["src"])
        frame = aroll_frame(c, readers[ci], lt, ci).convert("RGBA")
        # b-roll overlays
        for br in c.get("broll", []):
            bs, be = br["at"][0] - c["src"][0], br["at"][1] - c["src"][0]
            if bs - 0.01 <= lt < be:
                p = (lt - bs) / (be - bs)
                a = min(ease_io((lt - bs) / 0.25) if bs > 0.05 else 1, ease_io((be - lt) / 0.25) if be < c["dur_"] - 0.05 else 1)
                bim = kenburns(br["img"], p, br.get("motion", "in")).convert("RGBA")
                if br.get("particles"): particles(bim, tt, 1.0)
                if a < 1: bim.putalpha(int(255 * a))
                frame.alpha_composite(bim)
                label_ai(frame, a)
        rgb = frame.convert("RGB")
    else:
        fr, a = CARDS[c["kind"]](c, lt)
        label_ai(fr, 1.0)
        rgb = fr.convert("RGB")
        if a < 1: rgb = Image.blend(Image.new("RGB", (W, H), (0, 0, 0)), rgb, max(a, 0))
        if c["kind"] == "end" or c.get("fade_in"):
            ia = ease_io(lt / 0.5)
            if ia < 1: rgb = Image.blend(Image.new("RGB", (W, H), (0, 0, 0)), rgb, ia)
    # vignette, light leak, grain
    rgb = Image.composite(rgb, Image.new("RGB", (W, H), (0, 0, 0)), VIG)
    for ts in TRANS:
        dt = tt - ts
        if -0.12 <= dt < 0.45:
            a = (1 - abs(dt) / 0.12) if dt < 0 else (1 - dt / 0.45) ** 2
            if a > 0:
                rgb = Image.composite(Image.blend(rgb, LEAK_COL, min(0.75, a)), rgb, LEAK)
    g = GRAIN[fi % len(GRAIN)]
    rgb = Image.blend(rgb, Image.merge("RGB", (g, g, g)), 0.045)
    # overlays drawn after grain: lower third, captions, fade from black at start
    ov = rgb.convert("RGBA")
    if c["kind"] == "speech":
        lo = c.get("lower")
        if lo:
            a = min(ease_out((lt - 0.4) / 0.5), ease_io((c["dur_"] - 0.3 - lt) / 0.4))
            if a > 0:
                l1 = cached_block("lo1", lambda: text_block(lo[0], font("Montserrat.ttf", 44, "ExtraBold"), WHITE, 900, "left"))
                l2 = cached_block("lo2", lambda: text_block(lo[1], font("Montserrat.ttf", 32, "Medium"), GOLD, 900, "left"))
                d = ImageDraw.Draw(ov)
                d.rectangle((64, 236, 64 + 8, 236 + 120 * a), fill=GOLD + (255,))
                fade_paste(ov, l1, (60 + 40 * a - 20, 216), a)
                fade_paste(ov, l2, (60 + 40 * a - 20, 284), a)
        draw_captions(ov, tt)
        top = c.get("badge")
        if top:
            a = min(ease_out((lt - top[1]) / 0.4), 1)
            if a > 0:
                b = cached_block("badge" + top[0], lambda: text_block(top[0], font("Montserrat.ttf", 40, "ExtraBold"), WHITE, 900))
                d = ImageDraw.Draw(ov); bw = b.width - 40
                y = 1080
                d.rounded_rectangle((W / 2 - bw / 2 - 10, y + 10 + 20 * (1 - a), W / 2 + bw / 2 + 10, y + b.height - 10 + 20 * (1 - a)), 30,
                                    fill=(12, 12, 12, int(170 * a)), outline=GOLD + (int(255 * a),), width=3)
                fade_paste(ov, b, (W / 2 - b.width / 2, y), a, 20 * (1 - a))
    if tt < 0.25:
        ov = Image.blend(Image.new("RGBA", (W, H), (0, 0, 0, 255)), ov, tt / 0.25)
    ff.stdin.write(ov.convert("RGB").tobytes())
    if fi % 150 == 0: print(f"frame {fi}/{NFR}", flush=True)
for r_ in readers.values(): r_.close()
ff.stdin.close(); ff.wait()

# ---------------------------------------------------------------- audio mix
import wave
def rd(path):
    with wave.open(path) as w:
        x = np.frombuffer(w.readframes(w.getnframes()), "<i2").astype(np.float32) / 32768
        return x.reshape(-1, w.getnchannels())
voice_src = rd(f"{WORK}/voice.wav")
if voice_src.shape[1] == 1: voice_src = np.repeat(voice_src, 2, 1)
N = int(TOTAL * SR) + SR
voice = np.zeros((N, 2), np.float32); speech_mask = np.zeros(N, np.float32)
for c in clips:
    if c["kind"] != "speech": continue
    a, b = int(c["src"][0] * SR), int(c["src"][1] * SR)
    seg = voice_src[a:b].copy(); fl = int(0.012 * SR)
    seg[:fl] *= np.linspace(0, 1, fl)[:, None]; seg[-fl:] *= np.linspace(1, 0, fl)[:, None]
    o = int(c["out_start"] * SR); voice[o:o + len(seg)] += seg; speech_mask[o:o + len(seg)] = 1
# smooth ducking envelope
k = int(0.35 * SR); ker = np.ones(k) / k
duck = np.convolve(speech_mask, ker, "same")
music = rd(f"{WORK}/sfx/pad.wav")
music = np.concatenate([music, np.zeros((max(0, N - len(music)), 2), np.float32)])[:N]
gain = 10 ** ((-23 * duck + -11 * (1 - duck)) / 20)
mix = voice * 1.0 + music * gain[:, None]
for name, at, db in E.SFX:
    s = rd(f"{WORK}/sfx/{name}.wav")
    o = int(at * SR)
    if o < 0: s = s[-o:]; o = 0
    e = min(N, o + len(s)); mix[o:e] += s[:e - o] * 10 ** (db / 20)
mix = mix[:int(TOTAL * SR)]
mix /= max(1.0, np.abs(mix).max() / 0.97)
with wave.open(f"{OUT}.audio.wav", "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((np.clip(mix, -1, 1) * 32767).astype("<i2").tobytes())
ss = f"-ss {RANGE[0]} -t {RANGE[1]-RANGE[0]}" if RANGE else ""
subprocess.run(f"ffmpeg -v error -y -i {OUT}.video.mp4 {ss} -i {OUT}.audio.wav "
               f"-af loudnorm=I=-14:TP=-1.5:LRA=11 -c:v copy -c:a aac -b:a 192k -ar 48000 -shortest -movflags +faststart {OUT}",
               shell=True, check=True)
print("wrote", OUT)
