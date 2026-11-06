"""Builds the soundtrack: original voice (cut per EDL), synthesized ambient score and SFX.
Everything is generated here, so there are no licensing issues."""
import subprocess, sys, os
import numpy as np
from scipy.signal import fftconvolve, butter, sosfilt
from scipy.io import wavfile

SR = 48000
rng = np.random.default_rng(7)


def lp(x, f, o=2):
    return sosfilt(butter(o, f, "low", fs=SR, output="sos"), x, axis=0)


def hp(x, f, o=2):
    return sosfilt(butter(o, f, "high", fs=SR, output="sos"), x, axis=0)


def bp(x, f1, f2, o=2):
    return sosfilt(butter(o, [f1, f2], "band", fs=SR, output="sos"), x, axis=0)


def reverb_ir(dur=2.8, decay=2.2):
    n = int(dur * SR)
    t = np.arange(n) / SR
    ir = rng.standard_normal((n, 2)) * np.exp(-t * decay * 2.3)[:, None]
    ir = lp(ir, 6000)
    ir[:200] *= np.linspace(0, 1, 200)[:, None]
    return ir / np.abs(ir).sum(0).max() * 40


IR = reverb_ir()


def verb(x, wet=0.35):
    if x.ndim == 1:
        x = np.stack([x, x], 1)
    y = np.stack([fftconvolve(x[:, c], IR[:, c])[: len(x)] for c in range(2)], 1)
    return x * (1 - wet) + y * wet


def env_adsr(n, a, r):
    e = np.ones(n)
    na, nr = int(a * SR), int(r * SR)
    e[:na] = np.linspace(0, 1, na) ** 2
    e[-nr:] *= np.linspace(1, 0, nr) ** 2
    return e


def note_hz(m):
    return 440 * 2 ** ((m - 69) / 12)


# ---------------------------------------------------------------- music ----
def pad_note(m, dur, amp):
    n = int(dur * SR)
    t = np.arange(n) / SR
    out = np.zeros((n, 2))
    f = note_hz(m)
    for det, pan in ((-0.07, 0.2), (0.0, 0.5), (0.06, 0.8)):
        ff = f * 2 ** (det / 12)
        sig = np.zeros(n)
        for h in range(1, 7):
            sig += np.sin(2 * np.pi * ff * h * t + rng.uniform(0, 6)) / h ** 1.7
        out[:, 0] += sig * (1 - pan)
        out[:, 1] += sig * pan
    lfo = 1 + 0.15 * np.sin(2 * np.pi * 0.17 * t + rng.uniform(0, 6))
    return out * (env_adsr(n, min(2.5, dur / 2.5), min(2.5, dur / 2.5)) * lfo * amp)[:, None]


def pluck(m, amp, dur=3.5):
    n = int(dur * SR)
    t = np.arange(n) / SR
    f = note_hz(m)
    sig = sum(np.sin(2 * np.pi * f * h * t) * np.exp(-t * (1.6 + h * 1.1)) / h ** 1.3 for h in range(1, 6))
    sig *= np.minimum(1, t / 0.004)
    return np.stack([sig, sig], 1) * amp


def music(total, sections):
    """sections: dict with 'title_at','end_at' (output seconds)."""
    n = int(total * SR)
    mus = np.zeros((n + SR * 4, 2))
    # D minor: Dm - Bb - F - C   (slow, 5.6 s per chord)
    chords = [(50, 53, 57, 62), (46, 50, 53, 58), (45, 48, 53, 57), (48, 52, 55, 60)]
    arps = [(62, 65, 69, 74, 69, 65), (58, 62, 65, 70, 65, 62), (60, 65, 69, 72, 69, 65), (60, 64, 67, 72, 67, 64)]
    cd = 5.6
    t0 = 0.0
    k = 0
    while t0 < total + 2:
        ch = chords[k % 4]
        for m in ch:
            seg = pad_note(m, cd + 2.0, 0.050)
            i = int(t0 * SR)
            mus[i: i + len(seg)] += seg[: len(mus) - i]
        bass = pad_note(ch[0] - 12, cd + 2.0, 0.07)
        i = int(t0 * SR)
        mus[i: i + len(bass)] += bass[: len(mus) - i]
        # gentle arpeggio after the title card, thinning near the end
        if sections["title_at"] + 1.0 < t0 < sections["end_at"] + 2:
            for j, m in enumerate(arps[k % 4]):
                tt = t0 + j * cd / 6
                pl = pluck(m + 12, 0.035 if j % 2 == 0 else 0.022)
                i = int(tt * SR)
                mus[i: i + len(pl)] += pl[: len(mus) - i]
        t0 += cd
        k += 1
    mus = verb(lp(mus, 5000), 0.45)[:n]
    # arrangement envelope: quiet under the hook, swell on the title, settle, swell at end
    t = np.arange(n) / SR
    g = np.interp(t, [0, 3, sections["title_at"], sections["title_at"] + 1.2, sections["title_at"] + 4,
                      sections["end_at"] - 1, sections["end_at"] + 1.5, total - 2.5, total],
                  [0.35, 0.45, 0.9, 1.0, 0.75, 0.75, 1.0, 0.9, 0.0])
    return mus * g[:, None]


# ------------------------------------------------------------------ sfx ----
def impact():
    d = 3.0
    n = int(d * SR)
    t = np.arange(n) / SR
    f = 38 + 70 * np.exp(-t * 9)
    boom = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 1.6)
    noise = lp(rng.standard_normal(n), 900) * np.exp(-t * 22) * 0.9
    click = hp(rng.standard_normal(n), 3000) * np.exp(-t * 90) * 0.25
    x = boom * 0.9 + noise + click
    return verb(x, 0.4) * 0.9


def whoosh(d=0.75, up=True):
    n = int(d * SR)
    t = np.arange(n) / SR
    x = rng.standard_normal(n)
    # time-varying band: process in blocks
    out = np.zeros(n)
    blk = 1024
    for i in range(0, n, blk):
        p = i / n
        fc = 400 + 3200 * (np.sin(np.pi * p) ** 1.5)
        seg = x[max(0, i - 2048): i + blk]
        y = bp(seg, fc * 0.6, min(fc * 1.6, 20000))
        out[i: i + blk] = y[-len(out[i: i + blk]):]
    e = np.sin(np.pi * np.clip(t / d, 0, 1)) ** (2.2 if up else 1.6)
    out *= e
    pan = np.linspace(0.2, 0.8, n) if up else np.linspace(0.8, 0.2, n)
    st = np.stack([out * (1 - pan), out * pan], 1) * 1.6
    return verb(st, 0.25)


def riser(d=2.6):
    n = int(d * SR)
    t = np.arange(n) / SR
    p = t / d
    x = hp(rng.standard_normal(n), 1500) * p ** 2.5 * 0.35
    tone = np.sin(2 * np.pi * np.cumsum(180 + 520 * p ** 2) / SR) * p ** 2 * 0.12
    return verb(x + tone, 0.4)


def pop():
    d = 0.5
    n = int(d * SR)
    t = np.arange(n) / SR
    x = np.sin(2 * np.pi * np.cumsum(220 * np.exp(-t * 18) + 90) / SR) * np.exp(-t * 14) * 0.5
    x += hp(rng.standard_normal(n), 4000) * np.exp(-t * 120) * 0.12
    return verb(x, 0.3)


def shimmer():
    d = 4.0
    x = sum(pluck(m, 0.10, d) for m in (74, 81, 86, 90))
    return verb(x, 0.6)


SFX = dict(impact=impact(), whoosh=whoosh(), whoosh_dn=whoosh(0.6, False), riser=riser(), pop=pop(), shimmer=shimmer())


def place(buf, name, at, gain):
    s = SFX[name]
    i = int(at * SR)
    if name == "riser":
        i -= len(s)
    if i < 0:
        s = s[-i:]
        i = 0
    j = min(len(buf), i + len(s))
    buf[i:j] += s[: j - i] * gain


def read_wav(p):
    sr, x = wavfile.read(p)
    assert sr == SR
    return x.astype(np.float32) / 32768.0


def write_wav(p, x):
    wavfile.write(p, SR, (np.clip(x, -1, 1) * 32767).astype(np.int16))
