"""Edit decision list for the dakwah cut. All other build scripts import this."""
import json, os

S = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = f"{S}/src/in.mp4"
FPS = 30
W, H = 1080, 1920

# Words Whisper got wrong / spelling clean-up (meaning untouched)
FIX = {"bater.": "bata.", "bater": "bata", "seluahnya": "seluasnya", "-sama": "-sama"}

COLD = 2.4          # cold-open title length (visual)
JCUT = 0.5          # speech of first segment starts this much before the cut
GAP = 0.12          # breathing gap between segments
OUTRO = 4.2

# a0/a1: source audio in/out.  vin: first clean video frame (source has dips to black
# at shot changes; frames before vin freeze under the transition).
# crop: letterbox removal.  z: (zoom start, zoom end).  cx/cy: framing anchor (src px).
# punch: [(src_time, amount)] eased punch-in zooms on key words.  grade: look.
SEGS = [
    dict(id="A", a0=43.12, a1=48.12, vin=43.62, z=(1.00, 1.07), cx=420, cy=560,
         punch=[(44.36, 0.10), (46.84, 0.08)], grade="cine"),
    dict(id="B", a0=9.92, a1=16.56, vin=10.45, z=(1.00, 1.05), cx=320, cy=450,
         punch=[(12.42, 0.06)], grade="cine"),
    dict(id="C", a0=23.26, a1=32.22, vin=23.50, z=(1.06, 1.16), cx=338, cy=420,
         punch=[(27.14, 0.08), (29.38, 0.07)], grade="cine"),
    dict(id="D", a0=33.22, a1=37.96, vin=33.80, z=(1.00, 1.06), cx=320, cy=500,
         punch=[(34.60, 0.09)], grade="cine"),
    dict(id="E", a0=38.60, a1=42.06, vin=38.60, z=(1.00, 1.12), cx=325, cy=515,
         punch=[(39.74, 0.06)], grade="warm"),
    dict(id="F", a0=16.58, a1=22.12, vin=16.95, z=(1.00, 1.06), cx=344, cy=455,
         crop=(0, 32, 694, 1216), punch=[(21.00, 0.07)], grade="cine"),
    dict(id="G", a0=48.16, a1=53.26, vin=48.22, z=(1.00, 1.06), cx=380, cy=550,
         punch=[(51.90, 0.09)], grade="cine"),
    dict(id="H", a0=0.00, a1=9.36, vin=0.00, z=(1.00, 1.09), cx=330, cy=500,
         punch=[], grade="doa"),
]

# Cold open: slow-motion of the silent site shot (32.22-33.25, speaker not talking)
COLD_SRC = (32.24, 33.22)


# Graphic cues: (segment, source time, kind, args). Output time computed in cues().
CUES = [
    ("A", 44.36, "counter", dict(n=30, label="PINTU", dur=2.4)),
    ("A", 46.84, "card", dict(icon="pray", title="FOKUS IBADAH", sub="untuk warga emas", dur=1.5)),
    ("B", 12.42, "chip", dict(text="PEMBINAAN PONDOK WARGA EMAS", dur=4.0)),
    ("C", 27.10, "card", dict(icon="cement", title="SIMEN", sub="setiap beg membantu", dur=2.0)),
    ("C", 27.94, "card2", dict(icon="brick", title="BATA", sub="setiap biji bernilai", dur=3.6)),
    ("D", 34.55, "card", dict(icon="rebar", title="BESI BINAAN", sub="kukuhkan struktur pondok", dur=3.3)),
    ("E", 39.70, "card", dict(icon="heart", title="SEDIKIT / BANYAK", sub="amat dihargai", dur=2.3)),
    ("F", 19.25, "card", dict(icon="phone", title="HUBUNGI KAMI", sub="untuk menyumbang", dur=1.7)),
    ("G", 48.70, "card", dict(icon="key", title="30 PINTU", sub="PM segera untuk tempahan", dur=1.9)),
    ("G", 51.85, "card", dict(icon="share", title="SHARE", sub="seluas-luasnya", dur=1.5)),
]


def cues():
    segs = {s["id"]: s for s in timeline()[0]}
    return [dict(kind=k, t=src_to_out(segs[sid], ts), **a) for sid, ts, k, a in CUES]


def timeline():
    t = COLD - JCUT
    out = []
    for i, s in enumerate(SEGS):
        s = dict(s)
        s["t0"] = t                       # audio start on output timeline
        s["t1"] = t + (s["a1"] - s["a0"])
        # visual start: first segment cuts in after the cold open
        s["v0"] = COLD if i == 0 else t
        out.append(s)
        t = s["t1"] + (0.45 if s["id"] == "G" else GAP)   # longer breath before doa
    total = out[-1]["t1"] + OUTRO
    return out, total


def src_to_out(seg, ts):
    return seg["t0"] + (ts - seg["a0"])


def words():
    """Word list with output times, cleaned spelling, per segment."""
    tr = json.load(open(f"{S}/tr.json"))
    allw = [w for s in tr for w in s["words"]]
    segs, _ = timeline()
    out = []
    for sg in segs:
        ws = [w for w in allw if w["s"] >= sg["a0"] - 0.05 and w["e"] <= sg["a1"] + 0.05]
        for w in ws:
            txt = w["w"].strip()
            txt = FIX.get(txt, txt)
            if txt.startswith("-") and out:      # "sama" + "-sama" -> "sama-sama"
                out[-1]["text"] += txt
                out[-1]["e"] = src_to_out(sg, w["e"])
                continue
            out.append(dict(seg=sg["id"], text=txt, s=src_to_out(sg, w["s"]),
                            e=src_to_out(sg, w["e"])))
    return out


if __name__ == "__main__":
    segs, total = timeline()
    for s in segs:
        print(s["id"], f"{s['t0']:.2f}-{s['t1']:.2f}  v0={s['v0']:.2f}")
    print("total", round(total, 2))
    print(" ".join(w["text"] for w in words()))
