"""Extended synthesized SFX library for the high-impact version."""
import numpy as np
from audio import SR, lp, hp, bp, verb, rng, SFX, impact, whoosh, riser, pop


def add(*xs):
    n = max(len(x) for x in xs)
    out = np.zeros((n, 2))
    for x in xs:
        out[: len(x)] += x
    return out


def _t(d):
    return np.arange(int(d * SR)) / SR


def bell(f0=1320, d=2.2, amp=0.5):
    t = _t(d)
    parts = [(1, 1.0, 2.2), (2.76, 0.55, 3.4), (5.40, 0.30, 5.0), (8.93, 0.16, 7.5), (0.5, 0.25, 1.5)]
    x = sum(a * np.sin(2 * np.pi * f0 * r * t + rng.uniform(0, 6)) * np.exp(-t * k) for r, a, k in parts)
    x *= np.minimum(1, t / 0.002)
    return verb(x * amp, 0.35)


def ding():
    return add(bell(1568, 2.0, 0.45), bell(2349, 1.6, 0.15) )


def pop2(f=520):
    t = _t(0.25)
    x = np.sin(2 * np.pi * np.cumsum(f * (1 + 1.5 * np.exp(-t * 60))) / SR) * np.exp(-t * 28)
    x += hp(rng.standard_normal(len(t)), 2500) * np.exp(-t * 200) * 0.25
    return verb(x * 0.6, 0.12)


def tick():
    t = _t(0.08)
    x = np.sin(2 * np.pi * 1800 * t) * np.exp(-t * 90) * 0.35 + hp(rng.standard_normal(len(t)), 5000) * np.exp(-t * 300) * 0.2
    return np.stack([x, x], 1)


def swoosh(d=0.35):
    t = _t(d)
    x = rng.standard_normal(len(t))
    out = np.zeros(len(t))
    blk = 512
    for i in range(0, len(t), blk):
        p = i / len(t)
        fc = 1500 + 5500 * p
        seg = x[max(0, i - 1024): i + blk]
        y = bp(seg, fc * 0.5, min(fc * 1.5, 22000))
        out[i: i + blk] = y[-len(out[i: i + blk]):]
    out *= np.sin(np.pi * t / d) ** 1.4
    pan = np.linspace(0.85, 0.15, len(t))
    return verb(np.stack([out * (1 - pan), out * pan], 1) * 1.5, 0.2)


def sparkle(d=1.4, n=14):
    out = np.zeros((int(d * SR), 2))
    for k in range(n):
        st = rng.uniform(0, d * 0.6)
        f = rng.uniform(2600, 6200)
        tt = _t(0.35)
        s = np.sin(2 * np.pi * f * tt) * np.exp(-tt * 18) * rng.uniform(0.05, 0.12)
        i = int(st * SR)
        pan = rng.uniform(0.1, 0.9)
        j = min(len(out), i + len(s))
        out[i:j, 0] += s[: j - i] * (1 - pan)
        out[i:j, 1] += s[: j - i] * pan
    return verb(out, 0.5)


def chime():
    notes = [74, 78, 81, 86, 90, 93]
    out = np.zeros((int(3.2 * SR), 2))
    for k, m in enumerate(notes):
        f = 440 * 2 ** ((m - 69) / 12)
        b = bell(f, 2.2, 0.16)
        i = int(k * 0.07 * SR)
        j = min(len(out), i + len(b))
        out[i:j] += b[: j - i]
    return add(out, sparkle(1.6, 10) * 0.8)


def bass_drop():
    t = _t(3.2)
    f = 30 + 90 * np.exp(-t * 3.5)
    x = np.sin(2 * np.pi * np.cumsum(f) / SR)
    x = np.tanh(x * 1.8) * np.exp(-t * 0.9)
    x += lp(rng.standard_normal(len(t)), 500) * np.exp(-t * 15) * 0.6
    return verb(x * 0.85, 0.3)


def cine_hit():
    t = _t(3.0)
    x = impact()[: len(t)] * 0.8
    metal = sum(np.sin(2 * np.pi * f * t) * np.exp(-t * k) for f, k in ((310, 4), (523, 5), (797, 6), (1187, 8))) * 0.12
    noise = bp(rng.standard_normal(len(t)), 800, 6000) * np.exp(-t * 10) * 0.35
    y = verb(metal + noise, 0.5)
    return add(x, y)


def riser_short(d=1.0):
    t = _t(d)
    p = t / d
    x = hp(rng.standard_normal(len(t)), 2000) * p ** 2.5 * 0.4
    tone = np.sin(2 * np.pi * np.cumsum(300 + 900 * p ** 2) / SR) * p ** 2 * 0.1
    return verb(x + tone, 0.3)


def flash_zap():
    t = _t(0.4)
    x = hp(rng.standard_normal(len(t)), 3000) * np.exp(-t * 18) * 0.4
    return verb(x, 0.4)


SFX.update(dict(ding=ding(), bell=bell(1046, 2.6, 0.5), pop2=pop2(), pop_hi=pop2(760), tick=tick(), swoosh=swoosh(),
                sparkle=sparkle(), chime=chime(), bass_drop=bass_drop(), cine_hit=cine_hit(),
                riser_s=riser_short(), zap=flash_zap(), whoosh_s=whoosh(0.45)))
PRE = {"riser": True, "riser_s": True}  # these end at the given time
