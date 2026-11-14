"""Builds the sound design: cleaned original voice (unaltered words), cinematic SFX,
soft ambient pad (optional) and outdoor ambience. Writes mix_music.wav and mix_nomusic.wav.

Usage: python3 audio.py SRC.mp4 OUT_DIR
"""
import sys, os, subprocess, math
import numpy as np
from scipy import signal
from scipy.io import wavfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import timeline as TL

SR = 48000
src, out = sys.argv[1], sys.argv[2]
os.makedirs(out, exist_ok=True)
rng = np.random.default_rng(3)

# 1. clean the voice (no content changes: denoise, rumble cut, gentle compression)
vpath = os.path.join(out, "voice_clean.wav")
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", src, "-ac", "1", "-ar", str(SR), "-af",
                "highpass=f=85,afftdn=nf=-30:nr=10,equalizer=f=3200:t=q:w=1.2:g=2.5,"
                "acompressor=threshold=-22dB:ratio=3:attack=8:release=180:makeup=4", vpath], check=True)
_, v = wavfile.read(vpath)
v = v.astype(np.float32) / 32768

N = int(SR * (TL.TOTAL + 0.5))
voice = np.zeros(N, np.float32)


def place(buf, clip, t, fade=0.015):
    clip = clip.copy(); f = int(fade * SR)
    if f and len(clip) > 2 * f:
        clip[:f] *= np.linspace(0, 1, f); clip[-f:] *= np.linspace(1, 0, f)
    i = int(t * SR); j = min(len(buf), i + len(clip))
    if j <= i:
        return
    buf[i:j] += clip[:j - i]


place(voice, v[int(TL.HOOK_SRC * SR):int((TL.HOOK_SRC + TL.HOOK_DUR) * SR)], 0.0)
place(voice, v[0:int(TL.SRC_END * SR)], TL.MAIN_OFFSET, fade=0.06)
voice *= 0.5 / (np.percentile(np.abs(voice), 99.5) + 1e-9)


def env(n, a, r):
    e = np.ones(n, np.float32)
    ia, ir = int(a * SR), int(r * SR)
    if ia: e[:ia] = np.linspace(0, 1, ia)
    if ir: e[-ir:] *= np.exp(-np.linspace(0, 6, ir))
    return e


def bandnoise(n, lo, hi, order=2):
    b, a = signal.butter(order, [lo / (SR / 2), hi / (SR / 2)], "band")
    return signal.lfilter(b, a, rng.normal(0, 1, n)).astype(np.float32)


def impact(gain=1.0, dur=1.8):
    n = int(dur * SR); t = np.arange(n) / SR
    f = 52 * np.exp(-t * 1.2) + 30
    sub = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 2.4)
    click = bandnoise(n, 80, 1800) * np.exp(-t * 35) * 0.35
    body = bandnoise(n, 40, 220) * np.exp(-t * 6) * 0.5
    x = (sub + click + body).astype(np.float32)
    return x / np.abs(x).max() * gain


def whoosh(dur=0.5, gain=0.35, rising=True):
    n = int(dur * SR); x = rng.normal(0, 1, n).astype(np.float32)
    out = np.zeros(n, np.float32); hop = 512
    for i in range(0, n, hop):  # time-varying band-pass via short blocks
        p = i / n; fc = (300 + 4200 * p) if rising else (4500 - 4000 * p)
        b, a = signal.butter(2, [max(60, fc * 0.5) / (SR / 2), min(20000, fc * 1.6) / (SR / 2)], "band")
        seg = x[max(0, i - 2048):i + hop]
        out[i:i + hop] = signal.lfilter(b, a, seg)[-len(out[i:i + hop]):]
    shape = np.sin(np.pi * np.linspace(0, 1, n)) ** 1.6
    out *= shape
    return out / (np.abs(out).max() + 1e-9) * gain


def riser(dur, gain=0.3):
    n = int(dur * SR); t = np.arange(n) / SR
    tone = np.sin(2 * np.pi * np.cumsum(180 + 520 * (t / dur) ** 2) / SR) * 0.3
    nz = bandnoise(n, 1500, 9000) * 0.4
    e = (t / dur) ** 2.2
    x = (tone + nz) * e
    return (x / np.abs(x).max() * gain).astype(np.float32)


def shimmer(gain=0.08, dur=1.6):
    n = int(dur * SR); t = np.arange(n) / SR
    x = sum(np.sin(2 * np.pi * f * t + rng.random() * 6) * w for f, w in ((1760, 1), (2349, 0.7), (2637, 0.6), (3520, 0.4)))
    x *= np.exp(-t * 2.8) * np.minimum(1, t / 0.01)
    return (x / np.abs(x).max() * gain).astype(np.float32)


sfx = np.zeros(N, np.float32)
place(sfx, impact(0.9), 0.0, 0)
place(sfx, riser(1.1, 0.22), TL.HOOK_DUR - 1.1, 0)
place(sfx, impact(0.75), TL.HOOK_DUR, 0)
place(sfx, shimmer(0.07), 1.37)
for t0, tr in TL.TRANSITION_TIMES:
    if tr in ("whipL", "whipR"):
        place(sfx, whoosh(0.42, 0.30), t0 - 0.21, 0)
    elif tr in ("slideU", "slideD"):
        place(sfx, whoosh(0.5, 0.26, rising=False), t0 - 0.25, 0)
    elif tr == "zoom":
        place(sfx, whoosh(0.6, 0.18), t0 - 0.4, 0)
    elif tr == "sweep":
        place(sfx, whoosh(0.8, 0.10), t0 - 0.4, 0)
    elif tr == "punch":
        place(sfx, impact(0.16, 0.6), t0, 0)
for kw in TL.KEYWORDS[3:]:
    if kw[3] in ("gold", "serif"):
        place(sfx, shimmer(0.045), kw[0])
place(sfx, impact(0.35, 2.5), TL.m(37.8), 0)          # emotional peak: low, soft
place(sfx, impact(0.4, 2.5), TL.OUTRO_T0 + 5.75, 0)  # end card

# 2. ambience: soft wind bed (title + outro louder)
amb = bandnoise(N, 120, 900, 1) * 0.02
amb = signal.lfilter(*signal.butter(1, 400 / (SR / 2)), amb).astype(np.float32) * 2.5
amb_gain = np.full(N, 0.35, np.float32)
amb_gain[int(TL.HOOK_DUR * SR):int(TL.MAIN_OFFSET * SR)] = 1.0
amb_gain[int(TL.OUTRO_T0 * SR):] = 1.0
amb *= signal.filtfilt(*signal.butter(1, 2 / (SR / 2)), amb_gain).astype(np.float32)

# 3. sad, emotional score: soft piano arpeggios + slow strings, A minor, 64 bpm
NOTE = lambda n: 440 * 2 ** ((n - 69) / 12)
BEAT = 60 / 64
# Am  F  C  G | Am  F  Dm  E   (root, chord tones as MIDI)
PROG = [(45, [57, 60, 64]), (41, [57, 60, 65]), (48, [55, 60, 64]), (43, [55, 59, 62]),
        (45, [57, 60, 64]), (41, [57, 60, 65]), (50, [57, 62, 65]), (40, [56, 59, 64])]
MEL = [[(76, 2), (72, 1), (71, 1)], [(69, 3), (72, 1)], [(67, 2), (76, 2)], [(74, 4)],
       [(72, 1.5), (71, 0.5), (69, 2)], [(69, 2), (72, 2)], [(74, 2), (77, 2)], [(76, 3), (71, 1)]]
music = np.zeros((N, 2), np.float32)
mel = np.zeros((N, 2), np.float32)


def piano(f, dur, vel=1.0):
    n = int(min(dur + 2.5, 6) * SR); t = np.arange(n) / SR
    x = np.zeros(n, np.float32)
    for k in range(1, 8):
        fk = f * k * (1 + 0.0004 * k * k)
        x += np.sin(2 * np.pi * fk * t) * (1 / k ** 1.6) * np.exp(-t * (0.9 + 0.55 * k) * (1 + f / 900))
    x *= np.minimum(1, t / 0.004)
    rel = int(min(n, (dur + 0.25) * SR))
    x[rel:] *= np.exp(-np.arange(n - rel) / SR * 9)
    return x * vel


def strings(notes, dur):
    n = int((dur + 2.5) * SR); t = np.arange(n) / SR
    out = np.zeros((n, 2), np.float32)
    for nn in notes:
        f = NOTE(nn)
        for c, det in enumerate((-0.0025, 0.0025)):
            ph = 2 * np.pi * np.cumsum(f * (1 + det + 0.003 * np.sin(2 * np.pi * 5.2 * t + c))) / SR
            out[:, c] += sum(np.sin(k * ph) / k for k in range(1, 7))
    e = np.minimum(1, t / 1.6) * np.clip((dur + 2.5 - t) / 2.5, 0, 1)
    out *= e[:, None] / len(notes)
    return signal.lfilter(*signal.butter(2, 1700 / (SR / 2)), out, axis=0).astype(np.float32)


bar = 4 * BEAT
nbars = int(TL.TOTAL / bar) + 1
for k in range(nbars):
    root, ch = PROG[k % 8]
    t0 = k * bar
    # arpeggio in eighths: low root, then chord tones rising and falling
    seq = [root, ch[0], ch[1], ch[2], ch[1] + 12 if ch[1] + 12 < 80 else ch[2], ch[2], ch[1], ch[0]]
    for i, nn in enumerate(seq):
        x = piano(NOTE(nn), BEAT / 2 * (3 if i == 0 else 1.5), 0.9 if i == 0 else 0.55)
        pan = 0.5 + 0.25 * math.sin(i)
        place(music[:, 0], x * (1 - pan) * 2, t0 + i * BEAT / 2, 0)
        place(music[:, 1], x * pan * 2, t0 + i * BEAT / 2, 0)
    st = strings([root + 12, ch[0], ch[2]], bar)
    i = int(t0 * SR); j = min(N, i + len(st))
    if j > i:
        music[i:j] += st[:j - i] * 0.9
    tm = t0
    for nn, beats in MEL[k % 8]:
        x = piano(NOTE(nn), beats * BEAT, 0.8)
        place(mel[:, 0], x, tm, 0); place(mel[:, 1], x, tm, 0)
        tm += beats * BEAT

ir_n = int(4.0 * SR)
ir = rng.normal(0, 1, (ir_n, 2)) * np.exp(-np.linspace(0, 6.5, ir_n))[:, None]
ir = signal.lfilter(*signal.butter(1, 4000 / (SR / 2)), ir, axis=0)


def verb(x, wet=0.55):
    w = np.stack([signal.fftconvolve(x[:, c], ir[:, c])[:N] for c in range(2)], 1)
    return x * (1 - wet) + w / (np.abs(w).max() + 1e-9) * np.abs(x).max() * wet


music = verb(music); mel = verb(mel, 0.6)
# the melody sings only where nobody is speaking (title, outro) and very softly under the hook
mgate = np.zeros(N, np.float32)
mgate[int(TL.HOOK_DUR * SR):int(TL.MAIN_OFFSET * SR)] = 1.0
mgate[int(TL.OUTRO_T0 * SR):] = 1.0
mgate = signal.filtfilt(*signal.butter(1, 1.2 / (SR / 2)), mgate)
pad = (music + mel * mgate[:, None] * 0.8).astype(np.float32)
pad /= np.abs(pad).max()

# ducking from voice envelope + scene dynamics
venv = signal.filtfilt(*signal.butter(1, 3 / (SR / 2)), np.abs(voice))
duck = 1 / (1 + (venv / 0.02) ** 1.5)
lvl = np.full(N, 0.30, np.float32)
lvl[:int(1.37 * SR)] = 0.0                                                  # hook opens dry: voice + impact
lvl[int(1.37 * SR):int(TL.HOOK_DUR * SR)] = 0.24
lvl[int(TL.HOOK_DUR * SR):int(TL.MAIN_OFFSET * SR)] = 0.36
lvl[int(TL.m(37.8) * SR):int(TL.m(47.2) * SR)] = 0.36                        # emotional peak: strings swell, still under the voice
lvl[int(TL.OUTRO_T0 * SR):] = 0.42
lvl = signal.filtfilt(*signal.butter(1, 1.5 / (SR / 2)), lvl).astype(np.float32)
pad *= (lvl * (0.45 + 0.55 * duck))[:, None]

fade = np.ones(N, np.float32)
fe = int((TL.TOTAL - 1.4) * SR)
fade[fe:] = np.clip(1 - np.arange(N - fe) / (1.4 * SR), 0, 1)


def mixdown(with_music, name):
    m = np.repeat((voice + sfx + amb)[:, None], 2, 1)
    if with_music:
        m = m + pad
    m *= fade[:, None]
    m = m / (np.abs(m).max() + 1e-9) * 0.9
    raw = os.path.join(out, name + "_raw.wav")
    wavfile.write(raw, SR, (m * 32767).astype(np.int16))
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", raw, "-af", "loudnorm=I=-14:TP=-1.5:LRA=11", "-ar", str(SR),
                    os.path.join(out, name + ".wav")], check=True)


mixdown(True, "mix_music")
mixdown(False, "mix_nomusic")
print("audio done", TL.TOTAL)
