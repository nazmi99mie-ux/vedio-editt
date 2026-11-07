"""Edit decision list, transcript corrections and visual plan for the dakwah video.

All `src` times refer to the original recording (VID_20261106_100640_100.mp4).
"""
import json, os

HERE = os.path.dirname(os.path.abspath(__file__))
FPS = 30

# --- Pieces of the output timeline -------------------------------------------
# ("src", start, end) plays the original footage + voice
# ("card", name, duration) is a full-screen motion graphic with no voice
PIECES = [
    ("src", 98.92, 102.36),   # HOOK: "Kita mungkin tak mampu jadi orang yang mengajar ilmu agama kan?"
    ("card", "title", 2.0),
    ("src", 0.00, 50.58),     # main story (drops the throwaway "Semua dalam tu.")
    ("src", 51.58, 97.50),
    ("demo", 0.00, 12.40),    # INSERT: real infaqpay.my sign-up walkthrough (stabilised screen)
    ("src", 97.50, 110.88),
    ("src", 111.25, 111.98),  # "InsyaAllah." (drops "Tak gitu.")
    ("card", "end", 5.0),
]

# --- Transcript spelling fixes (ASR heard dialect; meaning unchanged) ---------
# key: (original word as transcribed, approx src start) -> corrected display text
FIXES = {
    ("ayak", 32.36): "air",
    ("menyambut", 41.20): "menyambung",
    ("Fardun", 46.24): "Fardu",
    ("mengajak,", 75.12): "mengajar,",
    ("mengajak", 101.16): "mengajar",
    ("kuraikan.", 86.46): "kurniakan",
    ("Murniakan", 86.78): "kepada",
    ("infak", 93.50): "InfakPay",
    ("pay", 94.00): None,      # merged into previous word
    ("RM150", 25.16): "RM150",
}

# fixes for the demo clip's voice-over (transcript_demo.json)
DEMO_FIXES = {
    ("bank,", 0.70): "bang,",
    ("nama", 4.30): "nama,",
    ("nombor,", 4.58): "nombor",
    ("IC", 4.96): "IC,",
    ("tetap", 11.16): "tetap.",
    ("mudah", 11.64): "Mudah",
}

KEYWORDS = {
    "link", "nama", "ic", "fon", "email", "sumbangan", "jumlah", "amount", "join",
    "allah", "pondok", "agama", "madrasah", "zawiyah", "ilmu", "warga", "emas",
    "rm150", "makan", "minum", "elektrik", "air", "penyelenggaraan", "guru-guru",
    "yaman", "fardu", "ain", "majlis", "dakwah", "penginfak", "tetap", "bulanan",
    "ikhlas", "istiqamah", "rezeki", "pahala", "mudah", "pautan", "infakpay",
    "daftar", "insyaallah", "membantu", "disampaikan", "diajarkan", "beban",
    "bantu", "guru", "berkembang", "beribadah", "belajar", "tiga", "masyarakat",
    "kurniakan", "amalkan", "sebulan",
}


def load_words(fname="transcript_raw.json", fixes=None):
    """Return transcript words [(text, src_start, src_end)] with fixes applied."""
    fixes = FIXES if fixes is None else fixes
    segs = json.load(open(os.path.join(HERE, fname)))
    raw = [(w["w"].strip(), w["s"], w["e"]) for s in segs for w in s["words"]]
    out = []
    for t, s, e in raw:
        fixed = t
        for (ow, os_), nw in fixes.items():
            if ow == t and abs(os_ - s) < 0.05:
                fixed = nw
                break
        if fixed is None:  # merge into previous
            pt, ps, pe = out[-1]
            out[-1] = (pt, ps, e)
            continue
        # glue hyphen-split words ("anak" + "-anak")
        if fixed.startswith("-") and out:
            pt, ps, pe = out[-1]
            out[-1] = (pt + fixed, ps, e)
            continue
        out.append((fixed, s, e))
    return out


def build_timeline():
    """Compute output start for every piece and a src->out mapper for main pieces."""
    t = 0.0
    laid = []
    for p in PIECES:
        if p[0] in ("src", "demo"):
            d = p[2] - p[1]
            laid.append(dict(kind=p[0], s=p[1], e=p[2], o=t, d=d))
        else:
            d = p[2]
            laid.append(dict(kind="card", name=p[1], o=t, d=d))
        t += d
    # snap to frame grid
    for L in laid:
        L["f0"] = round(L["o"] * FPS)
    for i, L in enumerate(laid):
        L["f1"] = laid[i + 1]["f0"] if i + 1 < len(laid) else round(t * FPS)
    return laid, t


LAID, TOTAL = build_timeline()
MAIN = [L for L in LAID[2:] if L["kind"] == "src"]


def m(src):
    """Map a source time inside the main story to output time."""
    for L in MAIN:
        if src < L["s"]:
            return L["o"]           # inside a cut gap -> next piece start
        if src <= L["e"]:
            return L["o"] + (src - L["s"])
    return MAIN[-1]["o"] + MAIN[-1]["d"]


def out_words():
    """Words placed on the output timeline (hook words appear twice)."""
    words = load_words()
    res = []
    demo_words = load_words("transcript_demo.json", DEMO_FIXES)
    for L in LAID:
        if L["kind"] not in ("src", "demo"):
            continue
        for t, s, e in (words if L["kind"] == "src" else demo_words):
            if s >= L["s"] - 0.03 and e <= L["e"] + 0.08:
                res.append(dict(text=t, t0=L["o"] + s - L["s"], t1=L["o"] + min(e, L["e"]) - L["s"],
                                hook=(L is LAID[0]), demo=(L["kind"] == "demo"),
                                src=s if L["kind"] == "src" else -1))
    return res


DEMO = next(L for L in LAID if L["kind"] == "demo")

# Step chips over the demo (demo-local times), aligned with the 3 steps the speaker gives
DEMO_STEPS = [
    (0.85, 3.25, "1", "Tekan pautan"),
    (3.25, 9.10, "2", "Isi maklumat & pilih sumbangan"),
    (9.10, 12.40, "3", "Daftar penginfak tetap"),
]


# --- Visual plan (src times of the main story) --------------------------------
# kind spk: speaker. z0->z1 zoom, a = anchor y in source px (face ~300)
# kind img: B-roll photo. mode cover|card, z0->z1, f0->f1 focus points
SHOTS = [
    (0.00, "spk", dict(z0=1.00, z1=1.07)),
    (2.62, "img", dict(img="huts", z0=1.04, z1=1.16, f0=(0.5, 0.55), f1=(0.6, 0.55))),
    (5.50, "img", dict(img="solat", z0=1.18, z1=1.05, f0=(0.5, 0.72), f1=(0.5, 0.62))),
    (7.30, "spk", dict(z0=1.22, z1=1.28)),
    (11.60, "img", dict(img="building", z0=1.00, z1=1.12, f0=(0.5, 0.5), f1=(0.45, 0.5))),
    (13.34, "img", dict(img="class", z0=1.02, z1=1.12, f0=(0.35, 0.5), f1=(0.45, 0.55))),
    (16.72, "img", dict(img="elders", z0=1.05, z1=1.16, f0=(0.5, 0.5), f1=(0.62, 0.48))),
    (19.72, "img", dict(img="doa", z0=1.12, z1=1.02, f0=(0.45, 0.6), f1=(0.5, 0.55))),
    (23.00, "spk", dict(z0=1.04, z1=1.10)),
    (26.78, "spk", dict(z0=1.24, z1=1.30)),
    (30.45, "img", dict(img="food", z0=1.10, z1=1.24, f0=(0.5, 0.72), f1=(0.48, 0.74))),
    (31.40, "img", dict(img="elec", z0=1.15, z1=1.30, f0=(0.45, 0.40), f1=(0.47, 0.36))),
    (32.32, "img", dict(img="water", z0=1.10, z1=1.24, f0=(0.5, 0.55), f1=(0.5, 0.58))),
    (33.34, "img", dict(img="building", z0=1.35, z1=1.25, f0=(0.35, 0.68), f1=(0.45, 0.66))),
    (34.32, "img", dict(img="tasmik", mode="card", z0=1.02, z1=1.12, f0=(0.6, 0.5), f1=(0.5, 0.5))),
    (35.56, "spk", dict(z0=1.00, z1=1.06)),
    (38.84, "yaman", dict()),
    (43.46, "img", dict(img="nightmajlis", mode="card", z0=1.0, z1=1.1, f0=(0.5, 0.5), f1=(0.5, 0.45))),
    (45.80, "img", dict(img="tahiyat", z0=1.02, z1=1.12, f0=(0.6, 0.55), f1=(0.5, 0.6))),
    (47.12, "img", dict(img="kuliah", z0=1.10, z1=1.20, f0=(0.75, 0.45), f1=(0.72, 0.42))),
    (48.32, "img", dict(img="crowd", mode="card", z0=1.0, z1=1.1, f0=(0.4, 0.5), f1=(0.5, 0.5))),
    (51.58, "spk", dict(z0=1.04, z1=1.10)),
    (54.74, "spk", dict(z0=1.00, z1=1.03, dim=0.45)),
    (57.95, "spk", dict(z0=1.22, z1=1.27)),
    (62.18, "spk", dict(z0=1.02, z1=1.09)),
    (68.70, "spk", dict(z0=1.20, z1=1.30)),
    (72.60, "img", dict(img="food", z0=1.00, z1=1.10, f0=(0.5, 0.6), f1=(0.5, 0.66))),
    (73.95, "img", dict(img="class", z0=1.15, z1=1.05, f0=(0.25, 0.45), f1=(0.3, 0.5))),
    (75.96, "img", dict(img="quran", z0=1.02, z1=1.14, f0=(0.5, 0.55), f1=(0.5, 0.58))),
    (78.72, "spk", dict(z0=1.28, z1=1.30)),
    (79.38, "img", dict(img="solat", z0=1.02, z1=1.12, f0=(0.4, 0.65), f1=(0.6, 0.65))),
    (83.20, "spk", dict(z0=1.06, z1=1.16, glow=True)),
    (87.80, "spk", dict(z0=1.22, z1=1.26)),
    (89.74, "steps", dict()),
    (97.52, "spk", dict(z0=1.00, z1=1.08)),
    (102.38, "img", dict(img="tahiyat", z0=1.12, z1=1.02, f0=(0.4, 0.5), f1=(0.5, 0.55))),
    (106.12, "img", dict(img="quran", z0=1.00, z1=1.12, f0=(0.5, 0.45), f1=(0.5, 0.38))),
    (108.50, "img", dict(img="kuliah", z0=1.20, z1=1.05, f0=(0.6, 0.5), f1=(0.5, 0.55))),
    (111.25, "spk", dict(z0=1.12, z1=1.16, glow=True)),
]

# Top labels (src start, src end, text)
PILLS = [
    (11.62, 13.30, "MADRASAH ZAWIYAH AN NUR"),
    (16.75, 19.70, "WARGA EMAS TURUT BELAJAR"),
    (30.47, 31.38, "MAKAN MINUM"),
    (31.42, 32.30, "BIL ELEKTRIK"),
    (32.34, 33.32, "AIR"),
    (33.36, 34.30, "PENYELENGGARAAN"),
    (34.34, 35.52, "ALLOWANCE GURU"),
    (45.82, 47.10, "KELAS FARDU AIN"),
    (47.14, 48.30, "MAJLIS ILMU"),
    (48.34, 50.58, "PROGRAM DAKWAH"),
]

# Big kinetic words (src start, src end, [(line, spoken word that triggers it)]);
# the trigger words (and the rest of the window's words that appear in a line) are hidden from subtitles
BIG = [
    (25.12, 26.80, [("RM150", "RM150"), ("SEBULAN", "sebulan.")]),
    (37.18, 38.84, [("RM150", "RM150"), ("SEBULAN", "sebulan.")]),
    (55.04, 57.95, [("PENGINFAK", "penginfak"), ("TETAP", "tetap"), ("BULANAN", "bulanan.")]),
    (65.56, 66.30, [("IKHLAS", "ikhlas,")]),
    (67.10, 68.68, [("ISTIQAMAH", "istiqamah."), ("TIAP-TIAP BULAN", "Tiap-tiap")]),
]

# Light-leak / flash accents (src times)
LEAKS = [7.30, 23.00, 38.84, 51.58, 68.70, 89.74, 102.38]
