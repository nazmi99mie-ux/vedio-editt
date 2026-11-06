"""Stage 1: assemble voice per EDL, generate score + SFX, mix and master.
Usage: python build_audio.py <voice48.wav> <workdir>"""
import sys, os, json, subprocess
import numpy as np
import edl, audio
from audio import SR

src, work = sys.argv[1], sys.argv[2]
voice = audio.read_wav(src)
tl, words, total = edl.build(voice, SR)
shots = edl.shots_out(tl)
slams = edl.slams_out()
end_card = [x for x in tl if x.get("card") == "end"][0]
total = end_card["out1"]
title = [x for x in tl if x.get("card") == "title"][0]
p_close = [p for p in edl.PIECES if p["id"] == "salam2"][0]
endcard_at = p_close["_s2o"](p_close["endcard_at"])
print(f"TOTAL {total:.2f}s  title@{title['out0']:.2f}  endcard@{endcard_at:.2f}")

# ---- voice ----------------------------------------------------------------
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

# ---- music with ducking -----------------------------------------------------
mus = audio.music(total, dict(title_at=title["out0"], end_at=endcard_at))
mus = np.pad(mus, ((0, n - len(mus)), (0, 0)))
env, hop = edl.rms_env(vp.mean(1), SR, 0.05)
on = (env > np.percentile(env, 60) * 0.25).astype(float)
# smooth attack/release
k = np.ones(8) / 8
on = np.convolve(on, k, "same")
duck = np.interp(np.arange(n) / SR, (np.arange(len(on)) + 0.5) * hop / SR, 1 - 0.55 * np.clip(on, 0, 1))
mus *= (duck * 0.85)[:, None]

# ---- sfx -------------------------------------------------------------------
fx = np.zeros((n, 2))
events = []
def ev(name, t, g):
    audio.place(fx, name, t, g)
    events.append((name, round(t, 3)))

hook_last = [w for w in words if w["hook"]][-1]
ev("impact", hook_last["s"], 0.55)
ev("riser", title["out0"], 0.7)
ev("impact", title["out0"] + 0.05, 0.45)
ev("whoosh_dn", title["out1"] - 0.3, 0.5)
prev = None
for sh in shots:
    k_ = sh["spec"]["k"]
    if prev is not None and sh["pid"] not in ("title", "end") and prev["pid"] != "title":
        if (k_ != "spk" or prev["spec"]["k"] != "spk"):
            ev("whoosh", sh["o0"] - 0.38, 0.38)
    prev = sh
for s in slams:
    big = s["txt"] in ("KEBAJIKAN", "± 1 HEKTAR", "SEBARKAN", "SUMBANGAN")
    ev("impact" if big else "pop", s["o"], 0.38 if big else 0.5)
ev("shimmer", endcard_at, 0.35)
ev("impact", endcard_at, 0.3)

mix = vp * 1.0 + mus + fx * 0.8
audio.write_wav(f"{work}/mix_raw.wav", mix[: int(total * SR)])
audio.write_wav(f"{work}/mix_nomusic_raw.wav", (vp + fx * 0.8)[: int(total * SR)])
for a, b in (("mix_raw", "mix"), ("mix_nomusic_raw", "mix_nomusic")):
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", f"{work}/{a}.wav", "-af",
                    "loudnorm=I=-14:TP=-1.5:LRA=10,alimiter=limit=0.89", "-ar", str(SR), f"{work}/{b}.wav"], check=True)

json.dump(dict(total=total, words=words, shots=[dict(o0=s["o0"], o1=s["o1"], spec=s["spec"], pid=s["pid"]) for s in shots],
               slams=slams, endcard_at=endcard_at, title=[title["out0"], title["out1"]],
               segs=[dict(out0=x["out0"], out1=x["out1"], src0=x.get("src0"), card=x.get("card"), pid=x["piece"]["id"]) for x in tl],
               events=events), open(f"{work}/plan.json", "w"), ensure_ascii=False, indent=1)
print("events", len(events))
