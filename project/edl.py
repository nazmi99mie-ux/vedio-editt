"""Edit decision list: which parts of the original talk are kept, in what order,
and what is shown on screen while each part plays.

All times in a piece are SOURCE times (seconds in the original video).
Only the speaker's own words are used; nothing is re-voiced or re-ordered
inside a sentence. Cuts are made only at pauses or to drop a repeated phrase.
"""
import json, os, re
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
FPS = 30
W, H = 1080, 1920
TITLE_DUR = 3.2
END_HOLD = 3.4

# --- spelling fixes for on-screen text only (audio is untouched) -------------
# Whisper mis-spellings of words the speaker clearly says.
FIX = {
    "perempuan": "puan-puan",      # "tuan-tuan, puan-puan" (only used right after "tuan-tuan")
    "hekar": "hektar",
    "memenafaatkan": "memanfaatkan",
    "komplek": "kompleks",
    "'alam": "a'lam",
    "bilai": "billahit",
    "taufiq": "taufiq",
    "respon": "respons",
}

PIECES = [
    # hook: the line that carries the whole message
    dict(id="hook", s=116.95, e=121.60, hook=True,
         shots=[(116.95, dict(k="img", img="jemaah_kuliah", a=(0.20, 0.62, 0.72), b=(0.42, 0.62, 0.60)))],
         slams=[]),
    dict(id="title", card="title"),
    dict(id="salam", s=2.25, e=6.55,
         shots=[(2.25, dict(k="spk", z=(1.00, 1.06)))]),
    dict(id="bism", s=8.25, e=9.85,
         shots=[(8.25, dict(k="spk", z=(1.22, 1.27)))]),
    dict(id="lokasi", s=32.55, e=38.30,
         shots=[(32.55, dict(k="spk", z=(1.10, 1.16))),
                (35.30, dict(k="img", img="madrasah_udara", a=(0.50, 0.50, 1.0), b=(0.56, 0.55, 0.80), tag="Madrasah Zawiyah An Nur, Gerik"))]),
    dict(id="tanah", s=40.45, e=56.30,
         shots=[(40.45, dict(k="spk", z=(1.00, 1.05))),
                (43.15, dict(k="wide", img="tanah_wakaf_udara", a=0.10, b=0.45, tag="Tanah wakaf · Gerik")),
                (51.15, dict(k="img", img="madrasah_udara", a=(0.30, 0.55, 0.85), b=(0.38, 0.48, 1.0)))],
         slams=[(45.55, "TANAH WAKAF", "diwakafkan oleh hamba Allah", 2.4),
                (49.90, "± 1 HEKTAR", "keluasan lebih kurang", 2.3)]),
    dict(id="syukur", s=57.65, e=61.65,
         shots=[(57.65, dict(k="spk", z=(1.30, 1.36)))]),
    dict(id="rancangan", s=62.40, e=74.35,
         shots=[(62.40, dict(k="spk", z=(1.06, 1.12))),
                (67.00, dict(k="img", img="konsep_kompleks", a=(0.50, 0.42, 1.0), b=(0.42, 0.62, 0.62), tag="Gambaran konsep"))],
         slams=[(70.35, "PONDOK WARGA EMAS", "single & berkelamin", 2.6)]),
    dict(id="raya", s=75.05, e=79.65,
         shots=[(75.05, dict(k="spk", z=(1.28, 1.35)))],
         slams=[(77.90, "SELEPAS HARI RAYA", "projek akan berjalan, insya-Allah", 2.2)]),
    dict(id="rayuan", s=80.45, e=94.40,
         shots=[(80.45, dict(k="spk", z=(1.00, 1.07))),
                (88.10, dict(k="img", img="konsep_kompleks", a=(0.30, 0.58, 0.55), b=(0.70, 0.62, 0.45), tag="Gambaran konsep"))],
         slams=[(84.70, "SUMBANGAN", "kami amat mengharapkan", 2.3)]),
    dict(id="ilmu", s=99.25, e=116.30, cuts=[(105.05, 107.50)],   # drops the repeated "dengan pendirian kompleks ini"
         shots=[(99.25, dict(k="img", img="konsep_kompleks", a=(0.50, 0.20, 0.55), b=(0.50, 0.28, 0.70), tag="Gambaran konsep")),
                (107.52, dict(k="img", img="jemaah_kuliah", a=(0.55, 0.60, 0.90), b=(0.52, 0.62, 0.66)))],
         slams=[(111.62, "MENUNTUT ILMU", "", 2.2)]),
    dict(id="akhirat", s=116.95, e=121.65,
         shots=[(116.95, dict(k="spk", z=(1.25, 1.40)))],
         slams=[(119.55, "KEBAJIKAN", "hingga ke akhirat", 2.4)]),
    dict(id="sebar", s=122.35, e=143.30,
         shots=[(122.35, dict(k="spk", z=(1.12, 1.18))),
                (125.40, dict(k="wide", img="tanah_wakaf_udara", a=0.55, b=0.20)),
                (129.05, dict(k="img", img="konsep_kompleks", a=(0.40, 0.45, 0.70), b=(0.50, 0.40, 0.95), tag="Gambaran konsep")),
                (133.85, dict(k="img", img="jemaah_kuliah", a=(0.78, 0.66, 0.62), b=(0.66, 0.64, 0.75))),
                (140.50, dict(k="img", img="bangunan_malam", a=(0.50, 0.55, 0.90), b=(0.50, 0.50, 1.0)))],
         slams=[(123.55, "SEBARKAN", "berita ini", 2.2)]),
    dict(id="penutup", s=143.75, e=153.85,
         shots=[(143.75, dict(k="spk", z=(1.02, 1.10))),
                (149.85, dict(k="spk", z=(1.26, 1.32)))]),
    dict(id="salam2", s=153.80, e=162.40, endcard_at=156.75,
         shots=[(153.80, dict(k="spk", z=(1.10, 1.20)))]),
    dict(id="end", card="end"),
]

KEYWORDS = {"akhirat", "kebajikan", "sumbangan", "wakaf", "diwakafkan", "hektar", "warga", "emas",
            "warga-warga", "pondok", "pondok-pondok", "ilmu", "sebarkan", "hari", "raya", "allah",
            "madrasah", "alhamdulillah", "syukur", "berkelamin", "single", "asrama", "kompleks"}


def load_words():
    segs = json.load(open(os.path.join(HERE, "transcript_raw.json")))
    words = []
    for s in segs:
        for w in s["words"]:
            t = w["w"].strip()
            if not t:
                continue
            if (t.startswith("-") or t.startswith("'")) and words and w["s"] - words[-1]["e"] < 0.6:
                words[-1]["w"] += t
                words[-1]["e"] = w["e"]
                continue
            words.append(dict(w=t, s=w["s"], e=w["e"]))
    # merge "tu sebut" -> "tersebut"
    out = []
    for w in words:
        if out and out[-1]["w"] == "tu" and w["w"].startswith("sebut"):
            out[-1] = dict(w="tersebut" + w["w"][5:], s=out[-1]["s"], e=w["e"])
            continue
        out.append(w)
    for i, w in enumerate(out):
        if abs(w["s"] - 84.76) < 0.05 and w["w"] == "semangat":
            w["w"] = "sumbangan"   # re-checked by a second transcription pass
            continue
        if w["w"].lower().startswith("perempuan") and not any(out[j]["w"].lower().startswith("tuan-tuan") for j in range(max(0, i - 2), i)):
            continue
        core = re.sub(r"[^\w'\-]", "", w["w"])
        tail = w["w"][len(w["w"].rstrip(".,!?")):]
        lw = core.lower()
        if lw in FIX:
            rep = FIX[lw]
            if core[:1].isupper():
                rep = rep[:1].upper() + rep[1:]
            w["w"] = rep + tail
    for w in out:
        w["w"] = (w["w"].replace("Wallahu'alam", "Wallahu a'lam,").replace("wassalamu'alaikum", "Wassalamu'alaikum")
                  .replace("Ta'ala", "Ta'ala"))
    return out


def rms_env(x, sr, win=0.02):
    n = int(sr * win)
    m = len(x) // n
    return np.sqrt((x[: m * n].reshape(m, n) ** 2).mean(1) + 1e-12), n


def build(voice, sr, verbose=True):
    """Returns (timeline, words_out). timeline: list of dicts with out0,out1 and either src0 or card."""
    words = load_words()
    mono = voice.mean(1) if voice.ndim == 2 else voice
    env, hop = rms_env(mono, sr)
    tl, wout, t = [], [], 0.0
    piece_spans = []
    for p in PIECES:
        if "card" in p:
            d = TITLE_DUR if p["card"] == "title" else END_HOLD
            tl.append(dict(out0=t, out1=t + d, card=p["card"], piece=p))
            piece_spans.append((p, t, t + d, []))
            t += d
            continue
        s, e = p["s"], p["e"]
        removes = list(p.get("cuts", []))
        pw = [w for w in words if w["s"] >= s - 0.05 and w["e"] <= e + 0.3]
        # compress long pauses: any silent run > 0.6 s is shortened to ~0.34 s (audio is clean lav-mic)
        i0, i1 = int(s * sr / hop), int(e * sr / hop)
        ref = np.percentile(env[i0:i1], 95)
        quiet = env[i0:i1] < ref * 0.035
        k = 0
        while k < len(quiet):
            if quiet[k]:
                j = k
                while j < len(quiet) and quiet[j]:
                    j += 1
                r0 = (i0 + k) * hop / sr + 0.17
                r1 = (i0 + j) * hop / sr - 0.17
                if k > 0 and j < len(quiet) and r1 - r0 > 0.26 and not any(r0 < c1 and r1 > c0 for c0, c1 in removes):
                    removes.append((r0, r1))
                k = j
            else:
                k += 1
        removes.sort()
        keep, cur = [], s
        for r0, r1 in removes:
            keep.append((cur, r0))
            cur = r1
        keep.append((cur, e))
        segs = []
        for a, b in keep:
            tl.append(dict(out0=t, out1=t + (b - a), src0=a, src1=b, piece=p))
            segs.append((a, b, t))
            t += b - a
        piece_spans.append((p, segs[0][2], t, segs))
        if verbose:
            cut = sum(r1 - r0 for r0, r1 in removes)
            print(f"{p['id']:10s} out {segs[0][2]:7.2f}-{t:7.2f}  removed {cut:5.2f}s in {len(removes)} cuts")

        def s2o(x, segs=segs):
            for a, b, o in segs:
                if a - 1e-6 <= x <= b + 1e-6:
                    return o + (x - a)
            # in a removed gap -> snap to next kept start
            for a, b, o in segs:
                if x < a:
                    return o
            return segs[-1][2] + segs[-1][1] - segs[-1][0]

        p["_s2o"] = s2o
        for w in pw:
            if any(r0 <= w["s"] and w["e"] <= r1 + 0.05 for r0, r1 in p.get("cuts", [])):
                continue
            wout.append(dict(w=w["w"], s=s2o(w["s"]), e=s2o(min(w["e"], e)), piece=p["id"], hook=p.get("hook", False)))
        t += 0.10  # breath between pieces
        tl.append(dict(out0=t - 0.10, out1=t, gap=True, piece=p))
    return tl, wout, t


def shots_out(tl):
    """Visual shots in output time."""
    shots = []
    for p in PIECES:
        if "card" in p:
            seg = [x for x in tl if x.get("card") and x["piece"] is p][0]
            shots.append(dict(o0=seg["out0"], o1=seg["out1"], spec=dict(k="card", card=p["card"]), pid=p["id"]))
            continue
        segs = [x for x in tl if x["piece"] is p and "src0" in x]
        pend = segs[-1]["out1"] + 0.10
        sh = p["shots"]
        for i, (st, spec) in enumerate(sh):
            o0 = p["_s2o"](st) if i else segs[0]["out0"]
            o1 = p["_s2o"](sh[i + 1][0]) if i + 1 < len(sh) else pend
            shots.append(dict(o0=o0, o1=o1, spec=spec, pid=p["id"]))
    return shots


def slams_out():
    out = []
    for p in PIECES:
        for st, txt, sub, d in p.get("slams", []):
            out.append(dict(o=p["_s2o"](st), d=d, txt=txt, sub=sub))
    return out
