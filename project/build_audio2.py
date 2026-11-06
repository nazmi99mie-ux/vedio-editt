"""Stage 1 (v2): same voice cut + score, plus dense SFX design driven by beats.py.
Usage: python build_audio2.py <voice48.wav> <workdir>"""
import sys, json, subprocess
import numpy as np
import edl, audio, sfx2
from audio import SR
from beats import BEATS

src, work = sys.argv[1], sys.argv[2]
voice = audio.read_wav(src)
tl, words, _ = edl.build(voice, SR, verbose=False)
shots = edl.shots_out(tl)
end_card = [x for x in tl if x.get("card") == "end"][0]
total = end_card["out1"]
title = [x for x in tl if x.get("card") == "title"][0]
p_close = [p for p in edl.PIECES if p["id"] == "salam2"][0]
endcard_at = p_close["_s2o"](p_close["endcard_at"])
pieces = {p["id"]: p for p in edl.PIECES}

# ---- voice (identical processing to v1) -------------------------------------
n = int(total * SR) + SR
v = np.zeros((n, 2), np.float32)
fade = int(0.012 * SR)
for seg in tl:
    if "src0" not in seg:
        continue
    a, b = int(seg["src0"] * SR), int(seg["src1"] * SR)
    x = voice[a:b].copy()
    x[:fade] *= np.linspace(0, 1, fade)[:, None]
    x[-fade:] *= np.linspace(1, 0, fade)[:, None]
    o = int(seg["out0"] * SR)
    v[o: o + len(x)] += x[: n - o]
audio.write_wav(f"{work}/voice_cut.wav", v)
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", f"{work}/voice_cut.wav", "-af",
                "highpass=f=75,afftdn=nf=-28:nr=8,equalizer=f=180:t=q:w=1:g=-2,equalizer=f=3200:t=q:w=1.2:g=2.5,"
                "acompressor=threshold=-22dB:ratio=3:attack=8:release=180:makeup=3,loudnorm=I=-16:TP=-2:LRA=9",
                "-ar", str(SR), f"{work}/voice_proc.wav"], check=True)
vp = audio.read_wav(f"{work}/voice_proc.wav")[:n]
vp = np.pad(vp, ((0, n - len(vp)), (0, 0)))

mus = audio.music(total, dict(title_at=title["out0"], end_at=endcard_at))
mus = np.pad(mus, ((0, n - len(mus)), (0, 0)))
env, hop = edl.rms_env(vp.mean(1), SR, 0.05)
on = np.convolve((env > np.percentile(env, 60) * 0.25).astype(float), np.ones(8) / 8, "same")
duck = np.interp(np.arange(n) / SR, (np.arange(len(on)) + 0.5) * hop / SR, 1 - 0.55 * np.clip(on, 0, 1))
mus *= (duck * 0.8)[:, None]

# ---- events ------------------------------------------------------------------
fx = np.zeros((n, 2))
sfx_log = []


def place(name, at, g):
    s = audio.SFX[name]
    i = int(at * SR) - (len(s) if name in sfx2.PRE else 0)
    if i < 0:
        s, i = s[-i:], 0
    j = min(n, i + len(s))
    if j > i:
        fx[i:j] += s[: j - i] * g
    sfx_log.append((name, round(at, 3), g))


events = []
for pid, lst in BEATS.items():
    p = pieces[pid]
    for b in lst:
        e = dict(b)
        e["o"] = p["_s2o"](b["t"])
        events.append(e)
        for name, off, g in e.get("sfx", []):
            place(name, e["o"] + off, g)
        if e["type"] in ("t3d", "arabic") and not e.get("sfx"):
            place("pop2", e["o"], .35)
events.sort(key=lambda e: e["o"])

# hook words: pop + whoosh per word, ding for keywords
hook = [w for w in words if w["hook"]]
for k, w in enumerate(hook[:-1]):
    place("whoosh_s", w["s"] - 0.12, .22)
    place("pop2", w["s"], .32)
import render2
for w in hook:
    if render2.cap_style(w["w"]) and w is not hook[-1]:
        place("ding", w["s"] + 0.02, .18)
# title card
place("riser", title["out0"], .7)
place("cine_hit", title["out0"] + 0.27, .5)
place("whoosh_s", title["out0"] - 0.05, .3)
for k in range(4):
    place("pop_hi" if k % 2 else "pop2", title["out0"] + 1.2 + k * 0.15, .3)
place("chime", title["out0"] + 0.8, .3)
place("whoosh", title["out1"] - 0.35, .4)
# keyword pops (per-word ticks removed on request)
for w in words:
    if w["hook"]:
        continue
    if render2.cap_style(w["w"]):
        place("pop_hi", w["s"], .14)
# transitions
for i, sh in enumerate(shots):
    if i == 0:
        continue
    pr = shots[i - 1]
    if sh["pid"] == "title" or pr["pid"] == "title":
        continue
    if pr["spec"]["k"] == "spk" and sh["spec"]["k"] == "spk":
        place("whoosh_s", sh["o0"] - 0.1, .2)
        continue
    kind = render2.TR_KINDS[i % len(render2.TR_KINDS)]
    if kind in ("whip", "whip_up"):
        place("swoosh", sh["o0"] - 0.17, .45)
    elif kind == "zoom":
        place("riser_s", sh["o0"], .45)
        place("whoosh_s", sh["o0"] - 0.1, .3)
    else:
        place("zap", sh["o0"] - 0.02, .35)
        place("cine_hit", sh["o0"], .2)
place("shimmer", endcard_at, .3)

mix = vp + mus + fx * 0.55
audio.write_wav(f"{work}/v2_mix_raw.wav", mix[: int(total * SR)])
audio.write_wav(f"{work}/v2_nomusic_raw.wav", (vp + fx * 0.55)[: int(total * SR)])
for a, b in (("v2_mix_raw", "v2_mix"), ("v2_nomusic_raw", "v2_nomusic")):
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", f"{work}/{a}.wav", "-af",
                    "loudnorm=I=-14:TP=-1.5:LRA=10,alimiter=limit=0.89", "-ar", str(SR), f"{work}/{b}.wav"], check=True)

json.dump(dict(total=total, words=words, shots=[dict(o0=s["o0"], o1=s["o1"], spec=s["spec"], pid=s["pid"]) for s in shots],
               slams=[], endcard_at=endcard_at, title=[title["out0"], title["out1"]],
               segs=[dict(out0=x["out0"], out1=x["out1"], src0=x.get("src0"), card=x.get("card"), pid=x["piece"]["id"]) for x in tl],
               events_fx=events, sfx=sfx_log), open(f"{work}/plan2.json", "w"), ensure_ascii=False, indent=1)
print(f"total {total:.2f}s  events {len(events)}  sfx {len(sfx_log)}")
