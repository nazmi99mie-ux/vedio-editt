#!/usr/bin/env python3
"""Cinematic documentary render for Madrasah Zawiyah An Nur.

Takes the original talking-head video (narration) and the madrasah photos,
and renders a vertical 9:16 cinematic edit:

  * logo intro / outro cards
  * speaker footage: denoised, upscaled, slow push-in
  * photo b-roll with smooth sub-pixel camera moves (push-in, lateral
    tracking, elevated "drone" style zoom-outs, gentle rotation)
  * soft dissolves, a warm golden-hour glow with faint light rays
  * final warm grade, vignette, sharpening and fine grain (ffmpeg)

Nothing is generated or invented: every pixel comes from the original
footage and photos, only camera motion, light and colour are added.

Usage:
  python3 scripts/make_documentary.py ORIGINAL.mp4 OUTPUT.mp4 [--preview]
"""
import argparse
import math
import os
import subprocess
import sys

import cv2
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PHOTOS = os.path.join(ROOT, "assets", "photos")
FPS = 24
INTRO = 3.5      # seconds of logo before the narration starts
OUTRO = 4.5      # seconds of logo after the narration ends
FADE = 0.5       # dissolve length between shots

# ---------------------------------------------------------------------------
# Shot list.  Times are in seconds of the ORIGINAL narration.
# move: (zoom0, zoom1, cx0, cx1, cy0, cy1, rot0_deg, rot1_deg)
#   zoom 1.0 = photo just covers the frame; cx/cy = view centre (0..1)
# prep: None | ("crop", y0, y1) | ("card", y0, y1)  -- the latter for
#   landscape photos that arrived letterboxed with a blurred fill
# glow: strength of the warm light effect for this shot
# ---------------------------------------------------------------------------
SHOTS = [
    # opening: push-in up the campus road, then slide along the hostel block
    (0.0, 6.0, "campus_road.jpg", None, (1.00, 1.18, 0.52, 0.60, 0.52, 0.60, 0, 0), 1.0),
    (6.0, 11.5, "hostel_building.jpg", None, (1.16, 1.16, 0.40, 0.60, 0.50, 0.50, 0, 0), 1.0),
    # elevated slow zoom-out over the lecture
    (20.0, 25.5, "lecture_canopy.jpg", None, (1.30, 1.02, 0.55, 0.50, 0.42, 0.50, -1.2, 0), 0.8),
    (31.0, 36.0, "classroom.png", ("crop", 243, 1676), (1.02, 1.14, 0.45, 0.42, 0.50, 0.46, 0, 0), 0.6),
    (36.0, 41.0, "talaqqi.png", ("card", 555, 1364), (1.04, 1.12, 0.52, 0.48, 0.50, 0.50, 0, 0), 0.6),
    (48.0, 53.0, "students_seated.jpg", None, (1.14, 1.14, 0.42, 0.58, 0.52, 0.48, 0, 0), 0.7),
    (53.0, 57.5, "student_quran.png", None, (1.00, 1.14, 0.50, 0.50, 0.45, 0.38, 0, 0), 0.9),
    (64.0, 69.5, "night_prayer.jpg", None, (1.24, 1.02, 0.50, 0.50, 0.58, 0.52, 0.8, 0), 0.5),
    (69.5, 74.5, "maulid_night.png", ("card", 555, 1364), (1.10, 1.02, 0.50, 0.50, 0.50, 0.50, 0, 0), 0.4),
    (74.5, 78.5, "elders_banner.png", ("crop", 240, 1679), (1.02, 1.12, 0.48, 0.52, 0.45, 0.42, 0, 0), 0.6),
    (84.0, 89.0, "audience.jpg", None, (1.14, 1.14, 0.58, 0.42, 0.55, 0.52, 0, 0), 0.8),
    (89.0, 94.0, "women_doa.png", None, (1.02, 1.15, 0.50, 0.46, 0.58, 0.62, 0, 0.8), 1.0),
    (94.0, 98.0, "gathering.png", ("card", 555, 1364), (1.02, 1.10, 0.46, 0.54, 0.50, 0.50, 0, 0), 0.8),
    (101.0, 105.0, "podium.jpg", None, (1.00, 1.12, 0.52, 0.55, 0.50, 0.44, 0, 0), 0.7),
    (105.0, 109.0, "food_serving.jpg", None, (1.12, 1.12, 0.42, 0.56, 0.50, 0.50, 0, 0), 0.6),
    # closing: dignified zoom-out on the elder, dissolving into the logo
    (109.0, None, "elder_walk.jpg", None, (1.22, 1.00, 0.36, 0.50, 0.50, 0.52, 0, 0), 1.0),
]


def ease(p):
    p = min(max(p, 0.0), 1.0)
    return p * p * (3 - 2 * p)


def lerp(a, b, p):
    return a + (b - a) * p


# --------------------------------------------------------------------------- photos
def load_photo(name, prep):
    img = cv2.imread(os.path.join(PHOTOS, name), cv2.IMREAD_COLOR)
    if prep is None:
        return img
    kind, y0, y1 = prep
    content = img[y0:y1 + 1]
    if kind == "crop":
        return content
    # "card": landscape shot on a soft, blurred, darkened version of itself
    bw, bh = 1080, 1920
    ch, cw = content.shape[:2]
    s = bh / ch
    bg = cv2.resize(content, (int(cw * s) + 1, bh), interpolation=cv2.INTER_AREA)
    x = (bg.shape[1] - bw) // 2
    bg = bg[:, x:x + bw]
    bg = cv2.GaussianBlur(bg, (0, 0), 45)
    bg = cv2.convertScaleAbs(bg, alpha=0.62, beta=4)
    fw = bw
    fh = int(round(ch * fw / cw))
    fg = cv2.resize(content, (fw, fh), interpolation=cv2.INTER_CUBIC)
    y = (bh - fh) // 2
    # soft feathered edge so the photo floats instead of being a hard box
    mask = np.zeros((bh, bw), np.float32)
    mask[y:y + fh, :] = 1.0
    mask = cv2.GaussianBlur(mask, (0, 0), 6)[..., None]
    canvas = bg.astype(np.float32)
    full = canvas.copy()
    full[y:y + fh] = fg
    out = canvas * (1 - mask) + full * mask
    return np.clip(out, 0, 255).astype(np.uint8)


def render_move(img, W, H, zoom, cx, cy, rot):
    ih, iw = img.shape[:2]
    cover = max(W / iw, H / ih)
    s = cover * zoom
    # keep the view inside the photo (account for rotation margin)
    margin = 1.0 + abs(math.radians(rot)) * (max(W, H) / min(W, H)) * 0.5
    half_w = (W * margin / s) / 2 / iw
    half_h = (H * margin / s) / 2 / ih
    cx = min(max(cx, half_w), 1 - half_w) if half_w < 0.5 else 0.5
    cy = min(max(cy, half_h), 1 - half_h) if half_h < 0.5 else 0.5
    M = cv2.getRotationMatrix2D((cx * iw, cy * ih), rot, s)
    M[0, 2] += W / 2 - cx * iw
    M[1, 2] += H / 2 - cy * ih
    return cv2.warpAffine(img, M, (W, H), flags=cv2.INTER_CUBIC,
                          borderMode=cv2.BORDER_REFLECT_101)


# --------------------------------------------------------------------------- light
class Glow:
    """Warm sun glow with faint rays, computed small and upscaled."""

    def __init__(self, W, H):
        self.W, self.H = W, H
        self.w, self.h = 270, 480
        ys, xs = np.mgrid[0:self.h, 0:self.w].astype(np.float32)
        self.xs, self.ys = xs / self.w, ys / self.h
        self.color = np.array([95, 175, 255], np.float32) / 255.0  # BGR warm gold

    def frame(self, T, strength):
        if strength <= 0:
            return None
        sx = 0.15 + 0.25 * math.sin(T * 0.05)      # sun drifts slowly
        sy = -0.08
        dx = self.xs - sx
        dy = (self.ys - sy) * (self.h / self.w)
        r = np.sqrt(dx * dx + dy * dy)
        ang = np.arctan2(dy, dx)
        rays = 0.80 + 0.20 * np.sin(ang * 23 + T * 0.15) * np.sin(ang * 11 - T * 0.1)
        g = np.exp(-(r / 0.55) ** 2) * rays + 0.25 * np.exp(-(r / 0.12) ** 2)
        g = g * strength * 0.55
        g3 = (g[..., None] * self.color[None, None, :] * 255).clip(0, 255).astype(np.uint8)
        return cv2.resize(g3, (self.W, self.H), interpolation=cv2.INTER_LINEAR)


def screen(base, light):
    if light is None:
        return base
    inv = cv2.subtract(np.full_like(base, 255), base)
    return cv2.add(base, cv2.multiply(inv, light, scale=1 / 255.0))


def blend(a, b, alpha):
    if alpha >= 1:
        return b
    if alpha <= 0:
        return a
    return cv2.addWeighted(a, 1 - alpha, b, alpha, 0)


# --------------------------------------------------------------------------- cards
def logo_card(W, H):
    logo = cv2.imread(os.path.join(PHOTOS, "logo.jpg"))
    # soft warm-ivory vertical gradient so the white logo sits on a cinematic plate
    top = np.array([236, 244, 250], np.float32)
    bot = np.array([200, 222, 240], np.float32)
    t = np.linspace(0, 1, H, dtype=np.float32)[:, None, None]
    card = (top * (1 - t) + bot * t) * np.ones((1, W, 1), np.float32)
    lw = int(W * 0.92)
    lh = int(logo.shape[0] * lw / logo.shape[1])
    lg = cv2.resize(logo, (lw, lh), interpolation=cv2.INTER_CUBIC).astype(np.float32)
    # make the logo's white background transparent-ish (multiply blend)
    y, x = (H - lh) // 2, (W - lw) // 2
    card[y:y + lh, x:x + lw] = card[y:y + lh, x:x + lw] * (lg / 255.0)
    return np.clip(card, 0, 255).astype(np.uint8)


# --------------------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("original")
    ap.add_argument("output")
    ap.add_argument("--preview", action="store_true", help="540x960 quick render")
    ap.add_argument("--crf", type=int, default=18)
    args = ap.parse_args()

    W, H = (540, 960) if args.preview else (2160, 3840)

    dur = float(subprocess.check_output(
        ["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
         "stream=duration", "-of", "csv=p=0", args.original]).decode().strip())
    main_frames = int(round(dur * FPS))
    main_len = main_frames / FPS
    total_frames = int(round((INTRO + main_len + OUTRO) * FPS))

    shots = []
    for i, (s, e, name, prep, move, glow) in enumerate(SHOTS):
        e = main_len + OUTRO if e is None else e
        nxt = SHOTS[i + 1][0] if i + 1 < len(SHOTS) else None
        chained = nxt is not None and abs(nxt - e) < 1e-6
        shots.append(dict(s=s, e=e, img=load_photo(name, prep), move=move,
                          glow=glow, chained=chained))

    card = logo_card(W, H)
    glow = Glow(W, H)

    # speaker: denoise + 24 fps, decoded at source resolution
    dec = subprocess.Popen(
        ["ffmpeg", "-v", "error", "-i", args.original, "-an",
         "-vf", "hqdn3d=2:1.5:5:4,fps=24", "-f", "rawvideo", "-pix_fmt", "bgr24", "-"],
        stdout=subprocess.PIPE)
    sw, sh = 720, 1280
    spk_bytes = sw * sh * 3
    last_spk = np.zeros((sh, sw, 3), np.uint8)

    grade = ",".join([
        "eq=contrast=1.07:saturation=1.10:gamma=0.97",
        "colorbalance=rs=0.02:bs=-0.03:rm=0.03:gm=0.01:bm=-0.03:rh=0.04:gh=0.015:bh=-0.04",
        "curves=master='0/0.02 0.25/0.22 0.75/0.80 1/0.98'",
        "unsharp=5:5:0.55:5:5:0",
        "vignette=angle=PI/5.5",
        "noise=alls=1:allf=t",
        "format=yuv420p",
    ])
    a_fade_st = INTRO + main_len - 0.2
    enc = subprocess.Popen(
        ["ffmpeg", "-y", "-v", "error", "-stats",
         "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
         "-i", args.original,
         "-filter_complex",
         f"[0:v]{grade}[v];"
         f"[1:a]aresample=48000,adelay={int(INTRO*1000)}:all=1,"
         f"afade=t=in:st={INTRO}:d=0.3,afade=t=out:st={a_fade_st}:d={OUTRO-0.5},"
         f"apad,atrim=0:{total_frames/FPS}[a]",
         "-map", "[v]", "-map", "[a]",
         "-c:v", "libx264", "-preset", "fast" if args.preview else "medium",
         "-crf", str(args.crf), "-profile:v", "high",
         "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709",
         "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart",
         "-t", f"{total_frames/FPS}", args.output],
        stdin=subprocess.PIPE)

    for f in range(total_frames):
        T = f / FPS
        t = T - INTRO  # narration time

        # ---- main layer (speaker + b-roll), only needed from narration start
        frame = None
        if t >= 0:
            if f - int(INTRO * FPS) < main_frames:
                buf = dec.stdout.read(spk_bytes)
                if len(buf) == spk_bytes:
                    last_spk = np.frombuffer(buf, np.uint8).reshape(sh, sw, 3)
            p = min(t / main_len, 1.0)
            z = 1.0 + 0.06 * p
            frame = render_move(last_spk, W, H, z, 0.5, 0.47, 0)
            frame = screen(frame, glow.frame(T, 0.35))

            for sh_ in shots:
                if not (sh_["s"] <= t < sh_["e"] + (FADE if not sh_["chained"] else FADE)):
                    continue
                a_in = 1.0 if sh_["s"] == 0 else min((t - sh_["s"]) / FADE, 1.0)
                a_out = 1.0
                if not sh_["chained"] and t > sh_["e"]:
                    a_out = max(1.0 - (t - sh_["e"]) / FADE, 0.0)
                a = ease(a_in) * ease(a_out) if a_out < 1 else ease(a_in)
                if a <= 0:
                    continue
                span = sh_["e"] - sh_["s"] + FADE
                q = ease((t - sh_["s"]) / span)
                z0, z1, x0, x1, y0, y1, r0, r1 = sh_["move"]
                img = render_move(sh_["img"], W, H, lerp(z0, z1, q), lerp(x0, x1, q),
                                  lerp(y0, y1, q), lerp(r0, r1, q))
                img = screen(img, glow.frame(T, sh_["glow"]))
                frame = blend(frame, img, a)

        # ---- logo cards
        out_start = INTRO + main_len - 0.8
        if T < INTRO + 0.6:
            a_logo = 1.0 if T < INTRO else 1.0 - ease((T - INTRO) / 0.6)
            zl = 1.0 + 0.06 * (T / (INTRO + 0.6))
        elif T >= out_start:
            a_logo = ease((T - out_start) / 0.8)
            zl = 1.0 + 0.05 * ((T - out_start) / (OUTRO + 0.8))
        else:
            a_logo = 0.0
            zl = 1.0
        if a_logo > 0:
            lc = render_move(card, W, H, zl, 0.5, 0.5, 0)
            frame = lc if frame is None else blend(frame, lc, a_logo)

        # ---- fade from / to black
        k = 1.0
        if T < 1.0:
            k = ease(T / 1.0)
        elif T > total_frames / FPS - 1.2:
            k = ease((total_frames / FPS - T) / 1.2)
        if k < 1:
            frame = cv2.convertScaleAbs(frame, alpha=k)

        enc.stdin.write(np.ascontiguousarray(frame).tobytes())

    enc.stdin.close()
    enc.wait()
    dec.stdout.close()
    dec.wait()
    if enc.returncode != 0:
        sys.exit("encoder failed")


if __name__ == "__main__":
    main()
