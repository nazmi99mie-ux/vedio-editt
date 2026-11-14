"""Edit decision list for 'Masjid Warga Emas — Pondok Zawiyah An-Nur'.

Times in SHOTS/KEYWORDS etc. are OUTPUT timeline seconds. Helper m(x) converts a
source-recording time to output time (main body plays the recording unaltered, in order).
"""
import json, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORDS = json.load(open(os.path.join(ROOT, "data", "words_final.json")))

# Hook: real quote from the recording (src 33.55-37.62):
# "Siapa membina masjid, pahala sangat besar dari sisi Allah SWT."
HOOK_SRC = 33.55
HOOK_DUR = 4.07
TITLE_DUR = 1.40
MAIN_OFFSET = HOOK_DUR + TITLE_DUR      # main body starts here
SRC_END = 74.98                          # end of closing salam
OUTRO_DUR = 11.5
OUTRO_T0 = MAIN_OFFSET + SRC_END
TOTAL = OUTRO_T0 + OUTRO_DUR


def m(src):
    return src + MAIN_OFFSET


def wt(word, after=0.0):
    """Source start time of first word containing `word` after `after`."""
    for w in WORDS:
        if w["s"] >= after and word.lower() in w["w"].lower():
            return w["s"]
    raise KeyError(word)


def we(word, after=0.0):
    for w in WORDS:
        if w["s"] >= after and word.lower() in w["w"].lower():
            return w["e"]
    raise KeyError(word)


P1, P2, P3, P4, P5 = ("01_banner_pelancaran.jpg", "02_pecah_tanah.jpg", "03_warga_emas.jpg",
                      "04_tapak_tiang.jpg", "05_lori_kerunai.jpg")


def S(kind, a, b, **k):
    k.update(kind=kind, t0=a, t1=b)
    return k


SHOTS = [
    # ACT 1 — HOOK: punch-in on the speaker, camera drifting vertically
    S("spk", 0.0, HOOK_DUR, z=(1.40, 1.52), punch=True, drift=((0, 60), (0, -60)), mood="neutral"),
    S("title", HOOK_DUR, MAIN_OFFSET, img=P2, tr="zoom", trd=0.40, mood="golden"),
    # ACT 2 — CONNECTION
    S("spk", m(0.0), m(3.0), z=(1.04, 1.12), tr="zoom", trd=0.45),
    S("spk", m(3.0), m(8.36), z=(1.20, 1.22), drift=((95, 0), (-95, 0)), punch=True),        # side tracking across the land
    S("fill", m(8.36), m(11.0), img=P5, zoom=(1.0, 1.12), path=((0.66, 0.5), (0.40, 0.5)), tr="whipL", trd=0.34, pdrift=(-1, -0.3)),
    S("spk", m(11.0), m(15.94), z=(1.22, 1.32), tr="whipL", trd=0.34),
    S("card", m(15.94), m(17.9), img=P1, bgpath=(0.15, 0.6), cardx=(0, 0), cardy=(60, -10), cz=(1.0, 1.10), cw=860, tr="sweep", trd=0.45),
    S("fill", m(17.9), m(21.35), img=P3, zoom=(1.05, 1.10), path=((0.30, 0.5), (0.64, 0.5)), tr="whipR", trd=0.34, pdrift=(1, -0.3)),
    # ACT 3 — DEEP MESSAGE
    S("spk", m(21.35), m(23.6), z=(1.34, 1.02), tr="zoom", trd=0.40),                          # reveal: "ni tanah dia"
    S("spk", m(23.6), m(27.8), z=(1.12, 1.20), punch=True),
    S("split", m(27.8), m(30.65), img=P4, z=1.35),
    S("spk", m(30.65), m(33.5), z=(1.30, 1.38), punch=True),
    S("fill", m(33.5), m(37.8), img=P2, zoom=(1.18, 1.25), path=((0.5, 0.85), (0.45, 0.28)), tr="sweep", trd=0.45, pdrift=(0, 1)),  # vertical reveal upward
    # ACT 4 — EMOTIONAL PEAK: minimal, close, slow push, quieter grade
    S("spk", m(37.8), m(47.2), z=(1.32, 1.56), mood="somber", parts=False, tr="zoom", trd=0.6),
    # ACT 5 — CALL & FINAL IMPACT
    S("fill", m(47.2), m(51.0), img=P4, zoom=(1.10, 1.24), path=((0.5, 0.78), (0.5, 0.35)), tr="slideU", trd=0.40, pdrift=(0, 1)),
    S("spk", m(51.0), m(53.55), z=(1.05, 1.12), tr="whipL", trd=0.34),
    S("spk", m(53.55), m(57.15), z=(1.25, 1.32), punch=True),
    S("fill", m(57.15), m(60.45), img=P1, zoom=(1.10, 1.28), path=((0.35, 0.40), (0.60, 0.62)), tr="whipR", trd=0.34),
    S("spk", m(60.45), m(65.2), z=(1.08, 1.15), tr="sweep", trd=0.45),
    S("spk", m(65.2), m(68.3), z=(1.30, 1.34), punch=True),
    S("card", m(68.3), m(71.65), img=P3, bgpath=(0.7, 0.3), cardx=(110, -70), cardy=(0, 0), cz=(1.02, 1.10), cw=980, tr="zoom", trd=0.45),
    S("spk", m(71.65), m(SRC_END), z=(1.25, 1.02), tr="sweep", trd=0.45),
    # OUTRO — visual breathing room + end card
    S("fill", OUTRO_T0, OUTRO_T0 + 2.95, img=P4, zoom=(1.0, 1.15), path=((0.3, 0.5), (0.58, 0.42)), tr="sweep", trd=0.8, mood="golden", pdrift=(1, -0.3)),
    S("fill", OUTRO_T0 + 2.95, OUTRO_T0 + 5.75, img=P2, zoom=(1.22, 1.06), path=((0.5, 0.3), (0.5, 0.6)), tr="whipL", trd=0.40, mood="golden"),
    S("title", OUTRO_T0 + 5.75, TOTAL + 1, img=P3, tr="fade", trd=0.8, mood="golden"),
]

KY_SPK, KY_BROLL = 1120, 760
# (t0, t1, text, style, y_center, direction)
KEYWORDS = [
    (0.02, 1.30, "SIAPA MEMBINA\nMASJID", "hook", 1230, "Z"),
    (1.37, 2.60, "PAHALA\nSANGAT BESAR", "hookgold", 1230, "U"),
    (2.65, 4.00, "DARI SISI\nALLAH SWT", "serif", 1230, "Z"),
    (HOOK_DUR + 0.08, MAIN_OFFSET - 0.05, "MEMBINA\nMASJID", "serif", 840, "Z"),
    (m(wt("Kampung", 8)), m(10.6), "KAMPUNG\nKERUNAI", "white", KY_BROLL, "L"),
    (m(wt("masjid", 15)), m(16.95), "MASJID", "gold", KY_SPK, "Z"),
    (m(wt("warga", 19)), m(21.25), "WARGA EMAS", "gold", KY_BROLL, "R"),
    (m(wt("berwakaf", 24)), m(27.6), "WAKAF", "gold", KY_SPK, "Z"),
    (m(wt("pahala", 34)), m(36.5), "PAHALA", "gold", KY_BROLL, "U"),
    (m(wt("mengalir", 42)), m(47.0), "MENGALIR", "white", KY_SPK, "D"),
    (m(wt("bina", 51)), m(53.4), "BINA MASJID", "gold", KY_SPK, "L"),
    (m(wt("infaq", 53)), m(55.4), "INFAQ", "gold", KY_SPK, "Z"),
    (m(wt("sabilillah", 55) - 0.2), m(57.0), "FI SABILILLAH", "serif", KY_SPK, "Z"),
    (m(wt("berkat", 57)), m(60.2), "BERKAT\nDUNIA AKHIRAT", "gold", KY_BROLL, "R"),
]

# lower-third pills: (t0, t1, line1, line2, y)
PILLS = [
    (m(0.4), m(5.2), "Pondok Zawiyah An-Nur", "Kg. Kerunai, Gerik, Perak", 190),
    (m(60.8), m(67.9), "Ikuti di Facebook & TikTok", "Pondok Zawiyah An-Nur", 190),
]

O = OUTRO_T0 + 5.75
# small text: (t0, font_key, size, colour_key, y, text)
TEXTCARDS = [
    (HOOK_DUR + 0.30, "bold", 44, "cream", 1070, "UNTUK WARGA EMAS & PELAJAR PONDOK"),
    (HOOK_DUR + 0.45, "semi", 38, "gold", 1140, "Pondok Zawiyah An-Nur · Gerik, Perak"),
    (O + 0.50, "serif", 64, "cream", 600, "“Sama-sama kita infaq harta kita"),
    (O + 0.70, "serif", 64, "cream", 680, "pada jalan Allah.”"),
    (O + 1.60, "black", 72, "gold", 930, "PONDOK ZAWIYAH AN-NUR"),
    (O + 1.80, "semi", 40, "cream", 1010, "Kg. Kerunai, Gerik, Perak"),
    (O + 2.20, "bold", 38, "cream", 1120, "PEMBINAAN MASJID & PONDOK WARGA EMAS"),
    (O + 2.40, "bold", 46, "gold", 1190, "30 Unit Pintu  ·  1 Sebiji Masjid"),
]
TEXT_END = {0: MAIN_OFFSET - 0.05, 1: MAIN_OFFSET - 0.05}   # title lines disappear with the title

# (t0, t1, exposure0, exposure1) — dramatic light change in the hook
EXPOSURE = [
    (0.0, 1.30, 0.80, 0.86),
    (1.30, 1.75, 0.86, 1.06),
    (1.75, HOOK_DUR, 1.06, 1.0),
    (m(37.8), m(38.6), 1.0, 0.94),
    (m(38.6), m(47.2), 0.94, 0.94),
]
SWEEPS = [(1.25, 2.1), (HOOK_DUR + 0.1, HOOK_DUR + 1.1), (m(wt("berkat", 57)) - 0.1, m(wt("berkat", 57)) + 0.9), (O + 1.4, O + 2.6)]


def sub_y(t):
    for s in SHOTS:
        if s["t0"] <= t < s["t1"] and s["kind"] == "split":
            return 1460
    return 1420


# ---- audio cue sheet (output times) used by audio.py
TRANSITION_TIMES = [(s["t0"], s.get("tr", "cut")) for s in SHOTS]
