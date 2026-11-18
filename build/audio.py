"""Builds the final stereo mix: cleaned speech + synthesized ambient score + SFX."""
import subprocess, numpy as np
from scipy import signal
import plan

SR = 48000
rng = np.random.default_rng(7)
segs, TOTAL = plan.timeline()
N = int(TOTAL * SR)


def load_speech():
    # light cleanup: highpass, gentle denoise, de-ess-ish lowpass, compression
    af = ("highpass=f=85,afftdn=nf=-28:nr=10,lowpass=f=15000,"
          "acompressor=threshold=-20dB:ratio=3:attack=8:release=120:makeup=4dB")
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", plan.SRC, "-af", af, "-ac", "1",
                          "-ar", str(SR), "-f", "f32le", "-"], capture_output=True).stdout
    return np.frombuffer(raw, np.float32)


def env(n, a, r):
    e = np.ones(n)
    a, r = min(a, n // 2), min(r, n // 2)
    if a: e[:a] = np.linspace(0, 1, a) ** 2
    if r: e[-r:] = np.linspace(1, 0, r) ** 2
    return e


def place(buf, x, t, gain=1.0, pan=0.0):
    i = int(t * SR)
    if i >= len(buf): return
    x = x[: len(buf) - i]
    l, r = np.cos((pan + 1) * np.pi / 4), np.sin((pan + 1) * np.pi / 4)
    if x.ndim == 1:
        buf[i:i + len(x), 0] += x * gain * l * 1.414
        buf[i:i + len(x), 1] += x * gain * r * 1.414
    else:
        buf[i:i + len(x)] += x * gain


def reverb(x, secs=2.8, wet=0.35, damp=3500):
    n = int(secs * SR)
    ir = rng.standard_normal((n, 2)) * np.exp(-np.linspace(0, 7, n))[:, None]
    b, a = signal.butter(2, damp / (SR / 2))
    ir = signal.lfilter(b, a, ir, axis=0)
    ir /= np.abs(ir).sum(0).max() / 6
    if x.ndim == 1: x = np.stack([x, x], 1)
    y = np.stack([signal.fftconvolve(x[:, c], ir[:, c])[: len(x)] for c in range(2)], 1)
    return x * (1 - wet) + y * wet


# ---------------------------------------------------------------- SFX
def whoosh(d=0.45, up=True):
    n = int(d * SR); t = np.linspace(0, 1, n)
    x = rng.standard_normal(n)
    f = np.linspace(400, 3500, n) if up else np.linspace(3500, 400, n)
    y = np.zeros(n); blk = 256
    for i in range(0, n, blk):   # time-varying bandpass
        b, a = signal.butter(2, [f[i] * 0.6 / (SR / 2), min(f[i] * 1.6, 20000) / (SR / 2)], "band")
        y[i:i + blk] = signal.lfilter(b, a, x[i:i + blk])
    e = np.sin(np.pi * t) ** 1.5
    return y * e / np.abs(y).max()


def boom(d=2.2, f0=58, f1=32):
    n = int(d * SR); t = np.arange(n) / SR
    ph = 2 * np.pi * np.cumsum(np.linspace(f0, f1, n)) / SR
    body = np.sin(ph) * np.exp(-t * 2.2)
    click = rng.standard_normal(n) * np.exp(-t * 60) * 0.5
    b, a = signal.butter(2, 900 / (SR / 2)); click = signal.lfilter(b, a, click)
    x = body + click
    return x / np.abs(x).max()


def riser(d=2.0):
    n = int(d * SR); t = np.arange(n) / SR
    x = rng.standard_normal(n)
    b, a = signal.butter(2, [800 / (SR / 2), 7000 / (SR / 2)], "band"); x = signal.lfilter(b, a, x)
    tone = np.sin(2 * np.pi * np.cumsum(np.linspace(110, 440, n)) / SR) * 0.4
    e = (t / d) ** 2.5
    y = (x * 0.6 + tone) * e
    return y / np.abs(y).max()


def pop():
    n = int(0.09 * SR); t = np.arange(n) / SR
    y = np.sin(2 * np.pi * np.cumsum(np.linspace(700, 1500, n)) / SR) * np.exp(-t * 45)
    return y


def tick():
    n = int(0.03 * SR); t = np.arange(n) / SR
    return np.sin(2 * np.pi * 2400 * t) * np.exp(-t * 200)


def bell(f=880, d=2.5):
    n = int(d * SR); t = np.arange(n) / SR
    y = sum(a * np.sin(2 * np.pi * f * m * t) * np.exp(-t * k)
            for m, a, k in [(1, 1, 1.6), (2.0, .35, 2.5), (2.76, .25, 3.5), (5.4, .1, 6)])
    y *= env(n, 30, 0)
    return y / np.abs(y).max()


# ---------------------------------------------------------------- score
def note(f): return 440 * 2 ** ((f - 69) / 12)


def pad(chord, d, bright=1.0):
    n = int(d * SR); t = np.arange(n) / SR
    y = np.zeros(n)
    for m in chord:
        for det in (-0.08, 0.0, 0.08):
            f = note(m + det)
            # soft saw (few harmonics) - warm string-like pad
            for h in range(1, 7):
                y += np.sin(2 * np.pi * f * h * t + rng.uniform(0, 6.28)) / h ** 1.6
    b, a = signal.butter(2, (900 + 1400 * bright) / (SR / 2)); y = signal.lfilter(b, a, y)
    y *= env(n, int(1.2 * SR), int(1.6 * SR))
    return y / np.abs(y).max()


def piano(f, d=4.0, vel=1.0):
    """Soft felt-piano tone: inharmonic partials, per-partial decay, gentle hammer."""
    n = int(d * SR); t = np.arange(n) / SR
    y = np.zeros(n)
    for h in range(1, 9):
        fh = f * h * np.sqrt(1 + 0.0004 * h * h)
        y += np.sin(2 * np.pi * fh * t) / h ** 1.4 * np.exp(-t * (0.9 + 0.55 * h) * (f / 440) ** 0.3)
    y += rng.standard_normal(n) * np.exp(-t * 90) * 0.02          # hammer felt
    b, a = signal.butter(2, min(2600 * vel + 600, 8000) / (SR / 2)); y = signal.lfilter(b, a, y)
    y *= env(n, int(0.006 * SR), int(0.3 * SR))
    return y / np.abs(y).max() * vel


def cello(f, d):
    n = int(d * SR); t = np.arange(n) / SR
    vib = 1 + 0.004 * np.sin(2 * np.pi * 5.2 * t) * np.clip(t - 0.5, 0, 1)
    ph = 2 * np.pi * np.cumsum(f * vib) / SR
    y = sum(np.sin(h * ph) / h ** 1.2 for h in range(1, 10))
    b, a = signal.butter(2, 1400 / (SR / 2)); y = signal.lfilter(b, a, y)
    y *= env(n, int(0.9 * SR), int(1.2 * SR))
    return y / np.abs(y).max()


def score():
    """Sad, emotional piano + strings in A minor, ~64 BPM."""
    mus = np.zeros((N, 2))
    beat = 60 / 64
    bar = 4 * beat
    # Am | F | C | G | Am | F | Dm | E   (harmonic-minor turn at the end of each phrase)
    prog = [(57, [57, 60, 64]), (53, [53, 57, 60]), (48, [48, 55, 60, 64]), (55, [55, 59, 62]),
            (57, [57, 60, 64]), (53, [53, 57, 60]), (50, [50, 53, 57]), (52, [52, 56, 59])]
    # melody: (beat offset in bar, midi, length in beats) per bar - a falling, sighing line
    mel = [[(0, 76, 2), (2, 74, 1), (3, 72, 1)], [(0, 72, 2), (2, 71, 1), (3, 69, 1)],
           [(0, 67, 2), (2, 76, 2)], [(0, 74, 4)],
           [(0, 76, 2), (2, 74, 1), (3, 72, 1)], [(0, 69, 2), (2, 72, 2)],
           [(0, 74, 1), (1, 77, 1), (2, 76, 2)], [(0, 76, 3), (3, 71, 1)]]
    doa_t = segs[-1]["t0"] - 0.6
    t, k = 0.0, 0
    while t < TOTAL:
        root, ch = prog[k % 8]
        intro = t < plan.COLD
        # strings pad (quiet, dark) + cello root
        place(mus, pad([m + 12 for m in ch], bar + 1.6, 0.15), t, 0.30, pan=0.0)
        place(mus, cello(note(root - 12), bar + 0.8), t, 0.30, pan=-0.3)
        # left hand: slow broken chord in 8ths (root-5th-octave-10th)
        lh = [root - 12, root - 5, root, ch[1] if len(ch) > 1 else root + 4]
        for e in range(8):
            if intro and e % 2: continue
            m = lh[[0, 1, 2, 3, 2, 1, 2, 3][e]]
            place(mus, piano(note(m), 2.6, 0.55 if e else 0.75), t + e * beat / 2 + rng.uniform(0, 0.012),
                  0.20, pan=-0.25)
        # right hand melody (sparser while he speaks, fuller in doa/outro, absent in cold open)
        if not intro:
            for off, m, ln in mel[k % 8]:
                tt = t + off * beat + rng.uniform(0, 0.02)
                g = 0.30 if tt >= doa_t else 0.22
                place(mus, piano(note(m), ln * beat + 2.0, 0.9), tt, g, pan=0.25)
                if tt >= doa_t:   # octave doubling for the doa - more heart
                    place(mus, piano(note(m - 12), ln * beat + 2.0, 0.6), tt + 0.01, 0.10, pan=0.1)
        t += bar; k += 1
    return reverb(mus, 4.0, 0.5, damp=3000)


def main():
    sp = load_speech()
    voice = np.zeros(N)
    fade = int(0.012 * SR)
    for s in segs:
        a, b = int(s["a0"] * SR), int(s["a1"] * SR)
        x = sp[a:b].copy() * env(b - a, fade, int(0.08 * SR))
        i = int(s["t0"] * SR)
        voice[i:i + len(x)] += x[: N - i]

    # speech-activity envelope from word timings -> music ducking
    act = np.zeros(N)
    for w in plan.words():
        act[int((w["s"] - 0.15) * SR): int((w["e"] + 0.25) * SR)] = 1
    k = int(0.25 * SR)
    act = np.convolve(act, np.ones(k) / k, "same")
    duck = 10 ** ((-9 * act) / 20)          # -9 dB under speech

    mus = score()
    # dynamics: swell in cold open & outro, softer inside body
    lvl = np.full(N, 2.8)
    tt = np.arange(N) / SR
    lvl = np.where(tt < plan.COLD, 3.6, lvl)
    lvl = np.where(tt > segs[-1]["t1"], 4.2, lvl)
    lvl = np.convolve(lvl, np.ones(SR) / SR, "same")
    mus *= (duck * lvl)[:, None]
    mus *= env(N, int(0.6 * SR), int(2.5 * SR))[:, None]

    fx = np.zeros((N, 2))
    place(fx, riser(2.1), 0.15, 0.30)
    place(fx, reverb(boom(), 2.5, 0.3), plan.COLD - 0.02, 0.85)
    place(fx, whoosh(0.4), plan.COLD - 0.22, 0.25)
    for s in segs[1:]:
        place(fx, whoosh(0.42, up=s["id"] != "H"), s["v0"] - 0.24, 0.22 if s["id"] != "H" else 0.14,
              pan=rng.uniform(-.5, .5))
    for c in plan.cues():
        if c["kind"] == "counter":
            for j in range(16):
                place(fx, tick(), c["t"] + j * 0.045, 0.12)
            place(fx, boom(1.2, 80, 45), c["t"] + 0.72, 0.35)
        else:
            place(fx, pop(), c["t"], 0.22)
            place(fx, whoosh(0.25), c["t"] - 0.08, 0.10)
    # shimmer on "Allah"/"Amin" in the doa, and outro hit
    for w in plan.words():
        if w["seg"] == "H" and w["text"].strip(".,").lower() in ("amin",):
            place(fx, reverb(bell(note(81), 3.0), 3, 0.5), w["s"], 0.12)
    place(fx, reverb(boom(2.5, 50, 30), 3, 0.4), segs[-1]["t1"] + 0.35, 0.45)
    place(fx, whoosh(0.6), segs[-1]["t1"] + 0.1, 0.18)

    mix = np.stack([voice, voice], 1) * 1.0 + mus * 0.42 + fx * 0.5
    np.stack([voice, voice], 1).astype(np.float32).tofile(f"{plan.S}/stem_voice.f32")
    (mus * 0.42).astype(np.float32).tofile(f"{plan.S}/stem_music.f32")
    mix /= max(1.0, np.abs(mix).max() / 0.95)
    mix.astype(np.float32).tofile(f"{plan.S}/mix.f32")
    # stems for checking
    print("done", TOTAL, "peak", np.abs(mix).max())


if __name__ == "__main__":
    main()
