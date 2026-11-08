"""Synthesize cinematic SFX and an ambient background pad (no external samples needed)."""
import numpy as np, wave, sys, os
SR = 48000
rng = np.random.default_rng(7)

def save(path, x):
    x = np.clip(x, -1, 1)
    if x.ndim == 1: x = np.stack([x, x], 1)
    with wave.open(path, "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((x * 32767).astype("<i2").tobytes())

def lp(x, a):  # one-pole lowpass, a in (0,1) (vectorised via cumulative trick is hard; loop in chunks)
    y = np.empty_like(x); s = 0.0
    for i in range(len(x)):
        s += a * (x[i] - s); y[i] = s
    return y

def reverb(x, secs=2.5, mix=0.35, seed=1):
    r = np.random.default_rng(seed)
    n = int(SR * secs); t = np.arange(n) / SR
    out = []
    for ch in range(2):
        ir = r.standard_normal(n) * np.exp(-t * 6.9 / secs)
        ir[:int(0.01*SR)] *= np.linspace(0, 1, int(0.01*SR))
        ir /= np.sqrt((ir**2).sum())
        wet = np.fft.irfft(np.fft.rfft(x, len(x)+n) * np.fft.rfft(ir, len(x)+n))[:len(x)+n]
        out.append(wet)
    dry = np.concatenate([x, np.zeros(n)])
    st = np.stack(out, 1) * mix + dry[:, None] * (1 - mix)
    return st

def norm(x, peak=0.9): return x / (np.abs(x).max() + 1e-9) * peak

def impact():
    d = 3.5; t = np.arange(int(SR*d)) / SR
    f = 30 + 70 * np.exp(-t * 9)                       # pitch-dropping sub boom
    boom = np.sin(2*np.pi*np.cumsum(f)/SR) * np.exp(-t * 2.2)
    click = rng.standard_normal(len(t)) * np.exp(-t * 60)
    body = lp(rng.standard_normal(len(t)), 0.05) * np.exp(-t * 7) * 3
    x = boom * 1.0 + click * 0.25 + body * 0.5
    return norm(reverb(x, 3.0, 0.3))

def whoosh(d=0.9, rev=False):
    n = int(SR*d); t = np.arange(n)/SR
    env = np.sin(np.pi * (t/d)**(0.6 if not rev else 1.6))**2
    noise = rng.standard_normal(n)
    # sweeping band: difference of two lowpasses with moving cutoff
    a = 0.02 + 0.25 * (t/d)
    y1 = np.empty(n); y2 = np.empty(n); s1 = s2 = 0.0
    for i in range(n):
        s1 += a[i] * (noise[i]-s1); s2 += a[i]*0.15*(noise[i]-s2); y1[i]=s1; y2[i]=s2
    x = (y1 - y2) * env
    pan = np.linspace(-0.7, 0.7, n)
    st = np.stack([x*(1-pan)/2, x*(1+pan)/2], 1)
    return norm(np.concatenate([st, np.zeros((int(SR*0.3),2))]), 0.8)

def riser(d=2.5):
    n = int(SR*d); t = np.arange(n)/SR
    f = 200 * (8 ** (t/d))
    tone = np.sin(2*np.pi*np.cumsum(f)/SR) * 0.15
    noise = lp(rng.standard_normal(n), 0.15) * 0.6
    x = (tone + noise) * (t/d)**2.5
    return norm(reverb(x, 1.5, 0.3), 0.7)

def chime():
    d = 4; t = np.arange(int(SR*d))/SR; x = np.zeros_like(t)
    for f, a in [(880, 1), (1318.5, .6), (1760, .4), (2637, .2)]:
        x += a*np.sin(2*np.pi*f*t)*np.exp(-t*1.6)
    x *= np.minimum(1, t/0.005)
    return norm(reverb(x, 3.5, 0.5), 0.6)

def pad(total):
    """Slow, warm ambient pad: Am - F - C - G (Dm) progression, 8 s per chord."""
    n = int(SR*total); t = np.arange(n)/SR
    chords = [[57,60,64,69],[53,57,60,65],[48,55,60,64],[55,59,62,67],[50,57,62,65],[53,57,60,64]]
    seg = 8.0
    L = np.zeros(n); R = np.zeros(n)
    for k in range(int(np.ceil(total/seg))+1):
        st = k*seg - 1.5; en = st + seg + 3.0
        i0 = max(0, int(st*SR)); i1 = min(n, int(en*SR))
        if i0 >= i1: continue
        tt = t[i0:i1] - st
        env = np.minimum(1, tt/2.5) * np.minimum(1, (en-st-tt)/2.5)
        for j, m in enumerate(chords[k % len(chords)]):
            f = 440*2**((m-69)/12)
            for det, pan in [(-0.12, 0.2), (0.12, 0.8)]:
                ph = rng.uniform(0, 6.28)
                v = (np.sin(2*np.pi*(f+det)*tt+ph) + 0.3*np.sin(2*np.pi*2*(f+det)*tt+ph)) * env * 0.08
                L[i0:i1] += v*(1-pan); R[i0:i1] += v*pan
        # soft bass
        f = 440*2**((chords[k % len(chords)][0]-12-69)/12)
        v = np.sin(2*np.pi*f*tt)*env*0.12
        L[i0:i1] += v; R[i0:i1] += v
    x = np.stack([L, R], 1)
    # gentle shimmer: sparse high bell notes
    for s in np.arange(4, total-4, 4.0):
        m = rng.choice([76, 79, 81, 84, 88]); f = 440*2**((m-69)/12)
        i0 = int(s*SR); tt = np.arange(int(3*SR))/SR
        v = np.sin(2*np.pi*f*tt)*np.exp(-tt*1.5)*0.035
        i1 = min(n, i0+len(v)); x[i0:i1] += v[:i1-i0, None]
    wet = reverb(x.mean(1), 4.0, 0.45)[:n]
    x = x*0.5 + wet*0.8
    x[:int(SR*2)] *= np.linspace(0, 1, int(SR*2))[:, None]
    x[-int(SR*4):] *= np.linspace(1, 0, int(SR*4))[:, None]
    return norm(x, 0.8)

if __name__ == "__main__":
    out = sys.argv[1]; total = float(sys.argv[2]); os.makedirs(out, exist_ok=True)
    save(f"{out}/impact.wav", impact())
    save(f"{out}/whoosh.wav", whoosh())
    save(f"{out}/whoosh_short.wav", whoosh(0.5))
    save(f"{out}/riser.wav", riser())
    save(f"{out}/chime.wav", chime())
    save(f"{out}/pad.wav", pad(total))
    print("ok")
