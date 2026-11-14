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
MAIN_START = 3.0                         # skip the opening salam: go straight from the hook into the message
MAIN_OFFSET = HOOK_DUR + TITLE_DUR - MAIN_START   # out = src + MAIN_OFFSET
SRC_END = 74.98                          # end of closing salam
OUTRO_DUR = 8.0
OUTRO_T0 = MAIN_OFFSET + SRC_END
BODY_T0 = HOOK_DUR + TITLE_DUR
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
P12 = "12_qr_akaun.jpg"
P6, P7, P8, P9, P10, P11 = ("06_udara_tanah_kosong.jpg", "07_ilustrasi_cadangan.jpg", "08_udara_pondok.jpg",
                            "09_asrama.jpg", "10_chalet.jpg", "11_wakaf_infak.jpg")
# boundary of the empty land in 06_udara_tanah_kosong.jpg (pixel coords, 1280x720)
LAND = [(330, 196), (470, 188), (600, 196), (632, 222), (642, 300), (652, 420), (676, 515), (716, 598), (770, 662), (812, 720),
        (0, 720), (0, 480), (118, 392), (232, 292)]


def S(kind, t0_, t1_, **k):
    k.update(kind=kind, t0=t0_, t1=t1_)
    return k


SHOTS = [
    # ACT 1 — HOOK: punch-in on the speaker, camera drifting vertically
    S("spk", 0.0, HOOK_DUR, z=(1.40, 1.52), punch=True, drift=((0, 60), (0, -60)), mood="neutral"),
    S("title", HOOK_DUR, BODY_T0, img=P2, tr="zoom", trd=0.40, mood="golden"),
    # ACT 2 — CONNECTION
    S("spk", m(3.0), m(4.40), z=(1.16, 1.22), tr="zoom", trd=0.40),
    # "kawasan tanah lapang" -> drone view, gold boundary traced around the whole empty land
    S("land", m(4.40), m(8.36), img=P6, poly=LAND, zoom=(1.30, 1.42), path=((0.30, 0.5), (0.36, 0.5)), draw=(0.25, 2.0), tr="whipL", trd=0.34),
    S("fill", m(8.36), m(11.0), img=P5, zoom=(1.0, 1.12), path=((0.66, 0.5), (0.40, 0.5)), tr="whipL", trd=0.34, pdrift=(-1, -0.3)),
    S("fill", m(11.0), m(13.4), img=P8, zoom=(1.0, 1.18), path=((0.45, 0.55), (0.55, 0.40)), tr="slideU", trd=0.38, pdrift=(0, 1)),   # drone push over the pondok
    S("spk", m(13.4), m(15.94), z=(1.24, 1.32), tr="whipL", trd=0.34),
    S("card", m(15.94), m(17.9), img=P1, bgpath=(0.15, 0.6), cardx=(0, 0), cardy=(60, -10), cz=(1.0, 1.10), cw=860, tr="sweep", trd=0.45),
    S("fill", m(17.9), m(21.35), img=P3, zoom=(1.05, 1.10), path=((0.30, 0.5), (0.64, 0.5)), tr="whipR", trd=0.34, pdrift=(1, -0.3)),
    # ACT 3 — DEEP MESSAGE
    # "ni lah tanah dia" -> back to the land: pull-back reveal, boundary traced fast
    S("land", m(21.35), m(23.6), img=P6, poly=LAND, zoom=(1.50, 1.34), path=((0.32, 0.5), (0.34, 0.5)), draw=(0.05, 0.9), tr="zoom", trd=0.40),
    S("spk", m(23.6), m(27.8), z=(1.12, 1.20), tr="zoom", trd=0.35),
    # "bolehlah berwakaf untuk buat masjid" -> empty land transforms into the development illustration
    S("reveal", m(27.8), m(30.65), a=dict(kind="land", img=P6, poly=LAND, zoom=(1.34, 1.30), path=((0.34, 0.5), (0.34, 0.5)), draw=(-3, 0.5)),
      b=dict(kind="fill", img=P7, zoom=(1.12, 1.0), path=((0.45, 0.45), (0.45, 0.5))), wipe=(0.55, 1.1), tr="sweep", trd=0.4),
    S("spk", m(30.65), m(33.5), z=(1.30, 1.38), tr="whipR", trd=0.34),
    S("fill", m(33.5), m(37.8), img=P2, zoom=(1.18, 1.25), path=((0.5, 0.85), (0.45, 0.28)), tr="sweep", trd=0.45, pdrift=(0, 1)),  # vertical reveal upward
    # ACT 4 — EMOTIONAL PEAK: minimal, close, slow push, quieter grade
    S("spk", m(37.8), m(47.2), z=(1.32, 1.56), mood="somber", parts=False, tr="zoom", trd=0.6),
    # ACT 5 — CALL & FINAL IMPACT
    S("fill", m(47.2), m(49.4), img=P10, zoom=(1.05, 1.12), path=((0.5, 0.25), (0.5, 0.7)), tr="slideU", trd=0.40, pdrift=(0, 1)),   # "datang sini"
    S("fill", m(49.4), m(51.0), img=P9, zoom=(1.10, 1.02), path=((0.4, 0.5), (0.6, 0.5)), tr="whipL", trd=0.34),                      # "Pondok Zawiyah An-Nur ni"
    S("fill", m(51.0), m(53.55), img=P7, zoom=(1.0, 1.32), path=((0.45, 0.55), (0.38, 0.24)), tr="zoom", trd=0.40),                  # "tapak dia untuk bina masjid" -> push to the dome
    S("spk", m(53.55), m(57.15), z=(1.25, 1.32), tr="whipR", trd=0.34),
    S("fill", m(57.15), m(60.45), img=P1, zoom=(1.10, 1.28), path=((0.35, 0.40), (0.60, 0.62)), tr="whipR", trd=0.34),
    S("spk", m(60.45), m(65.2), z=(1.08, 1.15), tr="sweep", trd=0.45),
    S("spk", m(65.2), m(68.3), z=(1.30, 1.34), punch=True),
    S("card", m(68.3), m(71.65), img=P3, bgpath=(0.7, 0.3), cardx=(110, -70), cardy=(0, 0), cz=(1.02, 1.10), cw=980, tr="zoom", trd=0.45),
    S("spk", m(71.65), m(SRC_END), z=(1.25, 1.02), tr="sweep", trd=0.45),
    # OUTRO — straight to the wakaf/infak QR + account (cropped from the official poster, never retyped)
    S("card", OUTRO_T0, TOTAL + 1, img=P12, bgpath=(0.3, 0.6), cardx=(0, 0), cardy=(150, 150), cz=(1.0, 1.03), cw=1000, parts=0.15, tr="sweep", trd=0.6, mood="neutral"),
]

KY_SPK, KY_BROLL = 1150, 330   # speaker: on the chest, well below the face; photos: top band (sky/roof)
# (t0, t1, text, style, y_center, direction)
KEYWORDS = [
    (0.02, 1.30, "SIAPA MEMBINA\nMASJID", "hook", 1230, "Z"),
    (1.37, 2.60, "PAHALA\nSANGAT BESAR", "hookgold", 1230, "U"),
    (2.65, 4.00, "DARI SISI\nALLAH SWT", "serif", 1230, "Z"),
    (HOOK_DUR + 0.08, BODY_T0 - 0.55, "MEMBINA\nMASJID", "serif", 840, "Z"),
    (m(wt("Kampung", 8)), m(10.6), "KAMPUNG\nKERUNAI", "white", KY_BROLL, "L"),
    (m(wt("tanah", 4)) + 1.2, m(8.3), "KELUASAN\nTAPAK", "gold", 300, "Z"),
    (m(wt("masjid", 15)), m(16.95), "MASJID", "gold", KY_SPK, "Z"),
    (m(21.6), m(23.5), "TAPAK MASJID &\nPONDOK WARGA EMAS", "whitesm", 300, "D"),
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
    (m(28.9), m(30.5), "Gambaran Ilustrasi", "Cadangan Masjid & Pondok Warga Emas", 190),
    (m(51.1), m(53.4), "Gambaran Ilustrasi", "Cadangan Masjid & Pondok Warga Emas", 190),
    (m(60.8), m(67.9), "Ikuti di Facebook & TikTok", "Pondok Zawiyah An-Nur", 190),
]

O = OUTRO_T0 + 5.75
# small text: (t0, font_key, size, colour_key, y, text)
TEXTCARDS = [
    (HOOK_DUR + 0.30, "bold", 44, "cream", 1070, "UNTUK WARGA EMAS & PELAJAR PONDOK"),
    (HOOK_DUR + 0.45, "semi", 38, "gold", 1140, "Pondok Zawiyah An-Nur · Gerik, Perak"),
    (OUTRO_T0 + 0.30, "black", 66, "gold", 420, "SALURKAN WAKAF / INFAK"),
    (OUTRO_T0 + 0.50, "semi", 40, "cream", 1480, "Madrasah Zawiyah An Nur \u00b7 Gerik, Perak"),
]
TEXT_END = {0: BODY_T0 - 0.5, 1: BODY_T0 - 0.5, }   # title lines disappear with the title

# (t0, t1, exposure0, exposure1) — dramatic light change in the hook
EXPOSURE = [
    (0.0, 1.30, 0.80, 0.86),
    (1.30, 1.75, 0.86, 1.06),
    (1.75, HOOK_DUR, 1.06, 1.0),
    (m(37.8), m(38.6), 1.0, 0.94),
    (m(38.6), m(47.2), 0.94, 0.94),
]
SWEEPS = [(1.25, 2.1), (HOOK_DUR + 0.1, HOOK_DUR + 1.1), (m(wt("berkat", 57)) - 0.1, m(wt("berkat", 57)) + 0.9)]


def sub_y(t):
    for s in SHOTS:
        if s["t0"] <= t < s["t1"] and s["kind"] == "split":
            return 1460
    return 1420


# ---- audio cue sheet (output times) used by audio.py
TRANSITION_TIMES = [(s["t0"], s.get("tr", "cut")) for s in SHOTS]
