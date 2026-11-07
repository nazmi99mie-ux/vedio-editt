"""Build the final soundtrack: cleaned original voice + synthesized score + SFX.

usage: python3 audio.py SOURCE.mp4 SFX_CUES.txt OUT.wav [--no-music]
Everything (music and sound effects) is synthesized here, so there are no
third-party licensing issues.
"""
import os, sys, subprocess, math
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import edit_plan as P

SR = 48000
rng = np.random.default_rng(1)


def db(x):
    return 10 ** (x / 20)


# ------------------------------------------------------------------ voice
def integrated_lufs(path, start=0.0, dur=None):
    cmd = ["ffmpeg", "-hide_banner", "-ss", str(start), "-i", path]
    if dur:
        cmd += ["-t", str(dur)]
    r = subprocess.run(cmd + ["-af", "highpass=f=75,ebur128", "-f", "null", "-"], capture_output=True, text=True)
    line = [l for l in r.stderr.splitlines() if l.strip().startswith("I:")][-1]
    return float(line.split()[1])


DEMO_CLIP = os.path.join(P.HERE, "assets", "demo_infaqpay.mp4")


def build_voice(src, tmp):
    parts, labels = [], []
    # match the demo voice-over to the speaker's level before the shared chain
    gain = integrated_lufs(src, 0, 50) - integrated_lufs(DEMO_CLIP, 0, 12.4)
    for i, L in enumerate(P.LAID):
        d = (L["f1"] - L["f0"]) / P.FPS
        if L["kind"] == "src":
            parts.append(f"[0:a]atrim={L['s']:.3f}:{L['s'] + d:.3f},asetpts=PTS-STARTPTS,"
                         f"afade=t=in:d=0.012,afade=t=out:st={d - 0.03:.3f}:d=0.03,"
                         f"aformat=sample_rates={SR}:channel_layouts=mono[p{i}]")
        elif L["kind"] == "demo":
            parts.append(f"[1:a]atrim={L['s']:.3f}:{L['s'] + d:.3f},asetpts=PTS-STARTPTS,"
                         f"highpass=f=90,afftdn=nf=-25,volume={gain:.2f}dB,"
                         f"afade=t=in:d=0.02,afade=t=out:st={d - 0.08:.3f}:d=0.08,"
                         f"aformat=sample_rates={SR}:channel_layouts=mono[p{i}]")
        else:
            parts.append(f"anullsrc=r={SR}:cl=mono,atrim=0:{d:.3f}[p{i}]")
        labels.append(f"[p{i}]")
    fc = ";".join(parts) + ";" + "".join(labels) + f"concat=n={len(labels)}:v=0:a=1," \
        "highpass=f=75,afftdn=nf=-30,equalizer=f=180:t=q:w=1:g=-1.5,equalizer=f=3500:t=q:w=1.2:g=2.5," \
        "acompressor=threshold=-20dB:ratio=3:attack=8:release=120:makeup=2," \
        "loudnorm=I=-15:TP=-2:LRA=7[v]"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", src, "-i", DEMO_CLIP, "-filter_complex", fc, "-map", "[v]",
                    "-ar", str(SR), "-ac", "1", tmp], check=True)
    import wave
    w = wave.open(tmp)
    a = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
    return a


# ------------------------------------------------------------------ dsp helpers
def onepole_lp(x, fc):
    """Time-varying one-pole lowpass. fc may be scalar or array."""
    fc = np.broadcast_to(np.asarray(fc, np.float32), x.shape)
    a = np.exp(-2 * np.pi * fc / SR)
    y = np.empty_like(x)
    z = 0.0
    for i in range(len(x)):
        z = (1 - a[i]) * x[i] + a[i] * z
        y[i] = z
    return y


def fft_conv(x, ir):
    n = len(x) + len(ir) - 1
    N = 1 << (n - 1).bit_length()
    y = np.fft.irfft(np.fft.rfft(x, N) * np.fft.rfft(ir, N), N)[:n]
    return y.astype(np.float32)


def reverb_ir(sec=2.8, seed=0):
    r = np.random.default_rng(seed)
    n = int(sec * SR)
    t = np.arange(n) / SR
    ir = r.normal(0, 1, n) * np.exp(-t * 6.9 / sec)
    # darken the tail
    ir = np.convolve(ir, np.ones(6) / 6, mode="same")
    ir[0] = 0
    return (ir / np.sqrt(np.sum(ir ** 2))).astype(np.float32)


IR_L, IR_R = reverb_ir(seed=1), reverb_ir(seed=2)


def stereo_verb(mono, wet=0.35):
    l = fft_conv(mono, IR_L)[:len(mono)]
    r = fft_conv(mono, IR_R)[:len(mono)]
    return np.stack([mono + wet * l, mono + wet * r], 1)


def midi(n):
    return 440 * 2 ** ((n - 69) / 12)


# ------------------------------------------------------------------ score
def score(total, voice_env):
    n = int(total * SR)
    t = np.arange(n) / SR
    # vi - IV - I - V in C  (Am F C G), warm and hopeful
    chords = [[57, 60, 64, 69], [53, 57, 60, 65], [48, 55, 60, 64], [55, 59, 62, 67]]
    bass = [45, 41, 48, 43]
    cl = 4.0   # seconds per chord
    pad = np.zeros(n, np.float32)
    lowb = np.zeros(n, np.float32)
    arp = np.zeros(n, np.float32)
    nch = int(math.ceil(total / cl)) + 1
    for c in range(nch):
        t0 = c * cl
        notes = chords[c % 4]
        i0 = int(max(t0 - 0.8, 0) * SR)
        i1 = min(int((t0 + cl + 1.2) * SR), n)
        if i0 >= n:
            break
        tt = t[i0:i1] - (t0 - 0.8)
        seg_len = cl + 2.0
        env = np.clip(tt / 1.2, 0, 1) * np.clip((seg_len - tt) / 1.4, 0, 1)
        env = env ** 1.5
        s = np.zeros(i1 - i0, np.float32)
        for nn in notes:
            f = midi(nn)
            for det in (-0.12, 0.0, 0.11):
                ff = f * 2 ** (det / 12)
                ph = rng.random() * 6.28
                for h, amp in ((1, 1.0), (2, 0.28), (3, 0.12), (4, 0.05)):
                    s += amp * np.sin(2 * np.pi * ff * h * tt + ph * h)
        pad[i0:i1] += s * env * 0.045
        fb = midi(bass[c % 4])
        lowb[i0:i1] += (np.sin(2 * np.pi * fb * tt) + 0.3 * np.sin(4 * np.pi * fb * tt)) * env * 0.12
        # gentle piano-like arpeggio, eighth notes at 75 bpm
        step = 0.4
        pattern = [notes[0] + 12, notes[2] + 12, notes[1] + 24, notes[2] + 12, notes[3] + 12, notes[1] + 12,
                   notes[0] + 24, notes[2] + 12, notes[1] + 12, notes[3] + 12]
        for k in range(int(cl / step)):
            ts = t0 + k * step
            j0 = int(ts * SR)
            if j0 >= n:
                break
            ln = min(int(2.2 * SR), n - j0)
            tk = np.arange(ln) / SR
            f = midi(pattern[k % len(pattern)])
            v = 0.6 + 0.4 * (k % 4 == 0)
            note = (np.sin(2 * np.pi * f * tk) + 0.25 * np.sin(4 * np.pi * f * tk) * np.exp(-tk * 6)
                    + 0.08 * np.sin(6 * np.pi * f * tk) * np.exp(-tk * 9))
            note *= np.exp(-tk * 2.4) * np.clip(tk / 0.004, 0, 1) * v
            arp[j0:j0 + ln] += note.astype(np.float32) * 0.05
    pad = onepole_lp(pad, 1800.0)

    # arrangement: sparse in the hook, arp enters with the story, bass from the call-to-action
    def ramp(a, b):
        return np.clip((t - a) / max(b - a, 1e-3), 0, 1)
    title = P.LAID[1]["o"]
    cta = P.m(51.58)
    end = P.LAID[-1]["o"]
    pad_g = 0.55 + 0.45 * ramp(title - 0.5, title + 0.5)
    arp_g = ramp(title + 1.0, title + 4.0) * (1 - 0.3 * ramp(P.m(83.0), P.m(84.0))) + 0.3 * ramp(P.m(89.7), P.m(91))
    bass_g = ramp(title - 0.2, title + 0.3) * 0.6 + 0.4 * ramp(cta, cta + 3)
    mix = pad * pad_g + arp * arp_g + lowb * bass_g
    st = stereo_verb(mix, 0.55)
    # final fade
    fade = np.clip((total - t) / 3.0, 0, 1)[:, None]
    fin = np.clip(t / 1.0, 0, 1)[:, None]
    st *= fade * (0.5 + 0.5 * fin)
    # ducking under voice
    duck = 1.0 - 0.72 * voice_env
    st *= duck[:, None]
    return st


# ------------------------------------------------------------------ sfx
def env_exp(n, k):
    return np.exp(-np.arange(n) / SR * k)


def sfx_impact(strength=1.0):
    n = int(2.5 * SR)
    tt = np.arange(n) / SR
    f = 34 + 46 * np.exp(-tt * 9)
    ph = 2 * np.pi * np.cumsum(f) / SR
    sub = np.sin(ph) * np.exp(-tt * 2.6)
    noise = rng.normal(0, 1, n).astype(np.float32) * np.exp(-tt * 18)
    noise = onepole_lp(noise, 2500.0)
    body = sub * 0.9 + noise * 0.55
    st = stereo_verb(body.astype(np.float32), 0.6)
    return st * 0.24 * strength


def sfx_hit():
    n = int(1.2 * SR)
    tt = np.arange(n) / SR
    f = 60 + 80 * np.exp(-tt * 14)
    sub = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt * 6)
    noise = onepole_lp(rng.normal(0, 1, n).astype(np.float32) * np.exp(-tt * 30), 4000.0)
    return stereo_verb((sub * 0.7 + noise * 0.4).astype(np.float32), 0.4) * 0.3


def sfx_whoosh(soft=False):
    d = 0.42 if soft else 0.6
    n = int(d * SR)
    tt = np.arange(n) / SR
    x = tt / d
    env = np.sin(np.pi * np.clip(x, 0, 1)) ** 2.2
    cut = 300 + 5200 * np.sin(np.pi * x) ** 2
    noise = rng.normal(0, 1, n).astype(np.float32)
    s = onepole_lp(noise, cut) - 0.6 * onepole_lp(noise, cut * 0.25)
    s *= env
    pan = x
    st = np.stack([s * (1 - 0.6 * pan), s * (0.4 + 0.6 * pan)], 1)
    return st * (0.10 if soft else 0.18)


def sfx_riser(d):
    n = int(d * SR)
    tt = np.arange(n) / SR
    x = tt / d
    noise = rng.normal(0, 1, n).astype(np.float32)
    s = onepole_lp(noise, 200 + 6000 * x ** 2) * x ** 2.5
    tone = np.sin(2 * np.pi * np.cumsum(110 + 330 * x ** 2) / SR) * x ** 3 * 0.25
    return stereo_verb((s * 0.5 + tone).astype(np.float32), 0.4) * 0.22


def sfx_tick():
    n = int(0.35 * SR)
    tt = np.arange(n) / SR
    s = (np.sin(2 * np.pi * 1760 * tt) + 0.5 * np.sin(2 * np.pi * 2640 * tt)) * np.exp(-tt * 28)
    return stereo_verb(s.astype(np.float32), 0.3) * 0.07


def sfx_shimmer():
    n = int(2.6 * SR)
    tt = np.arange(n) / SR
    s = np.zeros(n, np.float32)
    for k, f in enumerate([1568, 2093, 2637, 3136, 4186]):
        off = int(k * 0.07 * SR)
        e = np.exp(-tt[:n - off] * 2.2)
        s[off:] += (np.sin(2 * np.pi * f * tt[:n - off]) * e).astype(np.float32)
    return stereo_verb(s, 0.7) * 0.03


def place(buf, clip, t):
    i = int(t * SR)
    if i < 0:
        clip = clip[-i:]
        i = 0
    j = min(len(buf), i + len(clip))
    if j > i:
        buf[i:j] += clip[:j - i]


def main():
    src, cues, out = sys.argv[1:4]
    no_music = "--no-music" in sys.argv
    tmp = out + ".voice.wav"
    voice = build_voice(src, tmp)
    total = P.LAID[-1]["f1"] / P.FPS
    n = int(total * SR)
    voice = np.pad(voice, (0, max(0, n - len(voice))))[:n]

    # voice activity envelope for ducking
    blk = 480
    rms = np.sqrt(np.convolve(voice ** 2, np.ones(blk) / blk, mode="same"))
    act = (rms > db(-42)).astype(np.float32)
    # attack 60 ms / release 450 ms smoothing
    envv = np.zeros_like(act)
    z = 0.0
    a_up, a_dn = math.exp(-1 / (0.06 * SR)), math.exp(-1 / (0.45 * SR))
    step = 48
    for i in range(0, n, step):
        tgt = act[i]
        a = a_up if tgt > z else a_dn
        z = tgt + (z - tgt) * a ** step
        envv[i:i + step] = z

    mixbuf = np.zeros((n, 2), np.float32)
    if not no_music:
        mixbuf += score(total, envv) * db(-12.5)

    sfx = np.zeros((n, 2), np.float32)
    lib = {}
    for line in open(cues):
        t, kind = line.split()
        t = float(t)
        if kind == "impact":
            c = sfx_impact()
        elif kind == "impact_soft":
            c = sfx_impact(0.6)
        elif kind == "hit":
            c = sfx_hit()
        elif kind == "whoosh":
            c = sfx_whoosh()
            t -= 0.12
        elif kind == "whoosh_soft":
            c = sfx_whoosh(True)
        elif kind == "riser_short":
            d = P.LAID[1]["o"]
            c = sfx_riser(d)
        elif kind == "tick":
            c = sfx_tick()
        elif kind == "shimmer":
            c = sfx_shimmer()
        else:
            continue
        place(sfx, c, t)
    # keep sfx under voice a little too
    sfx *= (1 - 0.35 * envv)[:, None]

    mix = mixbuf + sfx + voice[:, None] * 1.0
    # soft limiter
    peak = np.max(np.abs(mix))
    mix = np.tanh(mix * 1.05) / np.tanh(1.05) if peak > 0.98 else mix
    mix = np.clip(mix, -0.99, 0.99)
    import wave
    w = wave.open(out, "w")
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes((mix * 32767).astype(np.int16).tobytes())
    w.close()
    os.remove(tmp)
    print("peak", float(peak), "dur", total)


if __name__ == "__main__":
    main()
