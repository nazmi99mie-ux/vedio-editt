"""Renders the picture (no text): grade, face-anchored zooms, transitions, cards, particles."""
import subprocess, sys, numpy as np, cv2
import plan

W, H, FPS = plan.W, plan.H, plan.FPS
SW, SH = 694, 1280
NF = 1608
src = np.memmap(f"{plan.S}/frames.rgb", np.uint8, "r", shape=(NF, SH, SW, 3))
segs, TOTAL = plan.timeline()
CUES = plan.cues()
rng = np.random.default_rng(3)


def ease(x):
    x = np.clip(x, 0, 1); return x * x * (3 - 2 * x)


def back(x):  # ease-out with overshoot
    x = np.clip(x, 0, 1); c = 1.7
    return 1 + (c + 1) * (x - 1) ** 3 + c * (x - 1) ** 2


def get(ts, crop=None):
    f = ts * FPS
    i = int(np.clip(np.floor(f), 0, NF - 1)); j = min(i + 1, NF - 1); a = f - np.floor(f)
    im = src[i] if a < 0.02 else cv2.addWeighted(src[i], 1 - a, src[j], a, 0)
    if crop is not None and 16.9 <= ts <= 23.2:
        x, y, w, h = crop; im = im[y:y + h, x:x + w]
    return np.ascontiguousarray(im)


def grade(im, kind):
    x = im.astype(np.float32) / 255
    x = x ** 1.07                                       # tame the over-bright phone exposure
    l = (x @ np.array([0.299, 0.587, 0.114], np.float32))[..., None]
    sat = {"cine": 0.9, "warm": 0.88, "doa": 0.8, "cold": 0.35}[kind]
    x = l + (x - l) * sat
    x = x + 0.25 * (x * x * (3 - 2 * x) - x)           # gentle S-curve
    sh = (1 - l) ** 2; hi = l ** 2
    if kind == "cine":
        x += sh * np.array([-0.012, 0.010, 0.030], np.float32) + hi * np.array([0.03, 0.012, -0.02], np.float32)
    elif kind == "warm":
        x += sh * np.array([0.0, 0.005, 0.02], np.float32) + hi * np.array([0.05, 0.02, -0.03], np.float32)
    elif kind == "doa":
        x += 0.01 + hi * np.array([0.07, 0.035, -0.035], np.float32)
    elif kind == "cold":
        x = x * 0.62 + sh * np.array([0.0, 0.02, 0.04], np.float32)
    return np.clip(x * 255, 0, 255).astype(np.uint8)


def place(im, S, pcx, pcy, extra_shift=(0, 0)):
    h, w = im.shape[:2]
    ww, wh = W / S, H / S
    pcx = np.clip(pcx, ww / 2, w - ww / 2) if ww < w else w / 2
    pcy = np.clip(pcy, wh / 2, h - wh / 2) if wh < h else h / 2
    M = np.float32([[S, 0, W / 2 - S * pcx + extra_shift[0]], [0, S, H / 2 - S * pcy + extra_shift[1]]])
    return cv2.warpAffine(im, M, (W, H), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT)


# ------------------------------------------------------------------ static layers
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
r = np.sqrt(((xx - W / 2) / (W * 0.62)) ** 2 + ((yy - H * 0.47) / (H * 0.6)) ** 2)
VIG = (1 - 0.42 * ease(r - 0.35))[..., None].astype(np.float32)
GRAIN = [rng.normal(0, 4.0, (H // 2, W // 2, 1)).astype(np.float32) for _ in range(6)]
CARDS = {}
for c in CUES:
    if "icon" in c:
        CARDS[c["icon"]] = cv2.cvtColor(cv2.imread(f"{plan.S}/gfx/{c['icon']}.png", cv2.IMREAD_UNCHANGED), cv2.COLOR_BGRA2RGBA)
DOT = cv2.cvtColor(cv2.imread(f"{plan.S}/gfx/dot.png", cv2.IMREAD_UNCHANGED), cv2.COLOR_BGRA2RGBA)
PARTS = [dict(x=rng.uniform(0, W), y=rng.uniform(0, H), s=rng.uniform(0.3, 1.3),
              vy=rng.uniform(-40, -12), vx=rng.uniform(-10, 10), a=rng.uniform(0.15, 0.55),
              ph=rng.uniform(0, 6.28)) for _ in range(46)]


def over(dst, rgba, cx, cy, scale=1.0, alpha=1.0):
    if alpha <= 0.01 or scale <= 0.02: return
    if abs(scale - 1) > 1e-3:
        rgba = cv2.resize(rgba, None, fx=scale, fy=scale, interpolation=cv2.INTER_LINEAR)
    h, w = rgba.shape[:2]
    x0, y0 = int(round(cx - w / 2)), int(round(cy - h / 2))
    xa, ya, xb, yb = max(x0, 0), max(y0, 0), min(x0 + w, W), min(y0 + h, H)
    if xa >= xb or ya >= yb: return
    sp = rgba[ya - y0:yb - y0, xa - x0:xb - x0].astype(np.float32)
    a = sp[..., 3:4] / 255 * alpha
    d = dst[ya:yb, xa:xb]
    d[:] = d * (1 - a) + sp[..., :3] * a


def particles(fr, t, amt):
    if amt <= 0: return
    for p in PARTS:
        x = (p["x"] + p["vx"] * t + 30 * np.sin(t * 0.7 + p["ph"])) % W
        y = (p["y"] + p["vy"] * t) % H
        tw = 0.6 + 0.4 * np.sin(t * 2 + p["ph"])
        over(fr, DOT, x, y, p["s"], p["a"] * amt * tw)


def seg_at(t):
    cur = None
    for s in segs:
        if t >= s["v0"]: cur = s
    return cur


def zoom_of(s, ts):
    k = (ts - s["a0"]) / (s["a1"] - s["a0"])
    z = s["z"][0] + (s["z"][1] - s["z"][0]) * ease(k)
    shake = np.zeros(2)
    for pt, amt in s["punch"]:
        d = ts - pt
        if d > -0.1:
            z += amt * ease((d + 0.1) / 0.18) * (1 - 0.5 * ease((d - 1.6) / 1.2))
            if d < 0.3:
                shake += rng.normal(0, 5 * (1 - d / 0.3) * ease((d + 0.1) / 0.1), 2)
    return z, shake


def frame(n):
    t = n / FPS
    H_ = segs[-1]
    if t < plan.COLD:                                         # ---------- cold open
        k = t / plan.COLD
        ts = plan.COLD_SRC[0] + k * (plan.COLD_SRC[1] - plan.COLD_SRC[0])
        im = grade(get(ts), "cold")
        S0 = max(W / SW, H / SH)
        fr = place(im, S0 * (1.30 - 0.14 * ease(k)), 338, 520).astype(np.float32)
        fr = cv2.GaussianBlur(fr, (0, 0), 2.2 * (1 - k) + 0.6)
        fr *= 0.55 + 0.45 * ease(k / 0.25)                    # fade from black
        particles(fr, t, 0.6)
    else:
        s = seg_at(t)
        outro = t > H_["t1"]
        ts = s["a0"] + (t - s["t0"])
        ts = max(ts, s["vin"])
        if s["id"] == "H": ts = min(ts, 9.85)                  # hold before the source dip
        im = get(ts, s.get("crop"))
        im = grade(im, s["grade"])
        h, w = im.shape[:2]
        S0 = max(W / w, H / h)
        z, shake = zoom_of(s, ts)
        if outro:
            z += 0.06 * ease((t - H_["t1"]) / 3)
        # whip transition: zoom-blur around every cut except the hook cut
        idx = segs.index(s)
        dt_in = t - s["v0"]
        nxt = segs[idx + 1]["v0"] if idx + 1 < len(segs) else 1e9
        dt_out = nxt - t
        wk = 0.0
        if idx > 0 and dt_in < 0.13: wk = 1 - dt_in / 0.13
        if dt_out < 0.13: wk = max(wk, 1 - dt_out / 0.13)
        if s["id"] == "H" or (idx + 1 < len(segs) and segs[idx + 1]["id"] == "H" and dt_out < 0.13):
            wk *= 0.0                                          # doa enters with a soft dissolve instead
        z *= 1 + 0.12 * wk
        S = S0 * z
        cy = s["cy"] - s.get("crop", (0, 0))[1]
        pcy = cy + (0.5 - 0.37) * H / S
        fr = place(im, S, s["cx"], pcy, shake).astype(np.float32)
        if wk > 0:
            k = int(1 + 60 * wk) | 1
            fr = cv2.blur(fr, (1, k))
            fr = cv2.addWeighted(fr, 1, fr, 0, 25 * wk)
        # soft warm dissolve into the doa
        if s["id"] == "H" and dt_in < 0.6:
            g = s["t0"] - (segs[idx - 1]["t1"])
            prev = segs[idx - 1]
            pts = prev["a0"] + (t - prev["t0"])
            pim = place(grade(get(pts), prev["grade"]), max(W / SW, H / SH) * zoom_of(prev, pts)[0],
                        prev["cx"], prev["cy"] + 0.13 * H / (max(W / SW, H / SH))).astype(np.float32)
            a = ease(dt_in / 0.6)
            fr = pim * (1 - a) + fr * a + 22 * np.sin(np.pi * a) * np.array([1, 0.85, 0.6], np.float32)
        if s["id"] == "H":                                    # bloom + dust
            hl = cv2.GaussianBlur(np.clip(fr - 215, 0, 255), (0, 0), 30)
            fr += hl * 0.35
            particles(fr, t, 1.0)
        if outro:
            k = ease((t - H_["t1"]) / 1.2)
            fr = cv2.GaussianBlur(fr, (0, 0), 0.1 + 14 * k)
            fr *= 1 - 0.5 * k
            particles(fr, t, 1.0)
    # white flash on the hook cut
    if plan.COLD <= t < plan.COLD + 0.2:
        fr += 255 * 0.7 * (1 - (t - plan.COLD) / 0.2)
    # ------------------------------------------------------------- cards
    for c in CUES:
        if "icon" not in c: continue
        d = t - c["t"]
        if d < 0 or d > c["dur"] + 0.25: continue
        cy = 1150.0
        if c["icon"] == "cement":                              # slides up when BATA arrives
            b = [x for x in CUES if x.get("icon") == "brick"][0]
            cy -= 262 * back((t - b["t"]) / 0.3) if t > b["t"] else 0
        sc = 0.55 + 0.45 * back(d / 0.32)
        al = ease(d / 0.15)
        cy += 50 * (1 - ease(d / 0.3))
        if d > c["dur"]:
            e = (d - c["dur"]) / 0.25
            sc *= 1 - 0.12 * ease(e); al *= 1 - ease(e)
        over(fr, CARDS[c["icon"]], W / 2, cy, sc, al)
    # ------------------------------------------------------------- finishing
    fr *= VIG
    g = GRAIN[n % 6]
    fr += cv2.resize(g, (W, H), interpolation=cv2.INTER_NEAREST)[..., None]
    fr = np.clip(fr, 0, 255)
    # progress bar (retention cue)
    p = int(W * min(t / TOTAL, 1))
    fr[0:7, :p] = fr[0:7, :p] * 0.2 + np.array([245, 196, 66]) * 0.8
    return fr.astype(np.uint8)


if __name__ == "__main__":
    out = sys.argv[1]
    rng_frames = range(int(TOTAL * FPS))
    if len(sys.argv) > 2:   # preview stills: render.py out.jpg t1 t2 ...
        tiles = [cv2.resize(frame(int(float(a) * FPS)), (270, 480)) for a in sys.argv[2:]]
        cv2.imwrite(out, cv2.cvtColor(np.hstack(tiles), cv2.COLOR_RGB2BGR)); sys.exit()
    enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
                            "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset",
                            "medium", "-crf", "14", "-pix_fmt", "yuv420p", out], stdin=subprocess.PIPE)
    for n in rng_frames:
        enc.stdin.write(frame(n).tobytes())
        if n % 150 == 0: print(n, flush=True)
    enc.stdin.close(); enc.wait()
