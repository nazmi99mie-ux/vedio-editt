"""Edit decision list for the 'Wakaf Masjid Pondok Zawiyah An-Nur' dakwah edit.

All `src` times are seconds in the ORIGINAL recording. Cut points are snapped to
real pauses using the voice energy envelope, so no word is clipped.
"""
import os, wave
import numpy as np

WORK = os.environ.get("EDIT_WORK", "")
_env = None
def _energy():
    global _env
    if _env is None:
        with wave.open(f"{WORK}/voice.wav") as w:
            x = np.frombuffer(w.readframes(w.getnframes()), "<i2").astype(np.float32).reshape(-1, w.getnchannels()).mean(1) / 32768
        hop = 480  # 10 ms
        n = len(x) // hop
        e = np.sqrt((x[:n * hop].reshape(n, hop) ** 2).mean(1) + 1e-10)
        db = 20 * np.log10(e)
        _env = (db > np.percentile(db, 10) + 12).astype(np.float32)
    return _env

def onset(t, look=1.2):
    """First voiced 10ms frame at/after t (within look), minus a small pre-roll."""
    e = _energy(); i = int(t * 100); end = min(len(e), i + int(look * 100))
    if e[i:i + 3].sum() > 0:
        # still inside the previous word: skip to the end of the next pause (>=100ms)
        k = i
        while k < end and e[k:k + 10].sum() > 0: k += 1
        if k >= end: return t
        i = k
    for k in range(i, end):
        if e[k:k + 4].sum() >= 3: return max(0, k / 100 - 0.07)
    return t

def word_onset(t, look=0.6):
    """For caption timing: if t sits in silence, move it to the first voiced frame."""
    e = _energy(); i = int(t * 100)
    for k in range(i, min(len(e), i + int(look * 100))):
        if e[k:k + 3].sum() >= 2: return k / 100
    return t

def offset(t, look=0.8):
    """End of speech at/after t: first 150ms of silence, plus a small tail."""
    e = _energy(); i = int(t * 100) - 15
    for k in range(i, min(len(e), i + int(look * 100))):
        if e[k:k + 15].sum() == 0: return k / 100 + 0.10
    return t

def S(a, b, exact_in=False, **kw):
    return dict(kind="speech", src=(a if exact_in else round(onset(a), 3), round(offset(b), 3)), **kw)

EMPHASIS = {"MASJID", "MASJID,", "BERWAKAF", "PAHALA", "ALLAH", "KUBUR", "SAHAM-SAHAM", "MENGALIR",
            "SUBHANALLAH", "INFAK", "AKHIRAT", "BERKAT", "AL-QURAN", "SOLAT", "SEMBAHYANG",
            "BERIBADAH", "REZEKI", "FI SABILILLAH", "WAKAF", "MEMBINA", "BINA", "AN-NUR",
            "ALHAMDULILLAH", "INSYAALLAH", "HARTA", "PELAJAR", "WARGA", "EMAS", "TANAH", "TAPAK"}

FACE = (0.5, 0.30)

def build():
    T = []
    # 1. HOOK (cold open): strongest line of the talk
    T.append(S(33.78, 37.44, exact_in=True, hook=True, zoom=(1.08, 1.14), focus=(0.45, 0.38), punch=[34.4], flash=False))
    T.append(S(42.00, 47.08, hook=True, zoom=(1.0, 1.04),
               broll=[dict(img="grave_a", at=(43.4, 48.0), motion="in", particles=True)]))
    # 2. TITLE
    T.append(dict(kind="title", dur=3.2, bg="light_sky_a", flash=True,
                  line1="SAHAM", line2="YANG TERUS MENGALIR",
                  line3="Wakaf Masjid  •  Pondok Zawiyah An-Nur, Gerik"))
    # 3. CONTEXT: the land, the plan
    T.append(S(2.28, 8.24, zoom=(1.0, 1.07), focus=(0.5, 0.45), flash=True,
               lower=("PONDOK ZAWIYAH AN-NUR", "Gerik, Perak  •  Tapak cadangan masjid")))
    T.append(S(10.52, 16.94, zoom=(1.1, 1.14), focus=FACE,
               broll=[dict(img="mosque_a", at=(13.75, 17.5), motion="up")]))
    T.append(S(17.82, 21.24,
               broll=[dict(img="students_a", at=(17.0, 19.6), motion="left"),
                      dict(img="elderly_a", at=(19.6, 22.0), motion="in")]))
    T.append(S(21.24, 23.28, zoom=(1.0, 1.05), focus=(0.5, 0.45)))
    # 4. THE CALL
    T.append(S(23.28, 30.38, zoom=(1.12, 1.2), focus=FACE, punch=[26.6],
               broll=[dict(img="donate_a", at=(28.6, 31.0), motion="in")]))
    # 5. WHY: the reward
    T.append(S(30.38, 47.08, zoom=(1.0, 1.06), focus=FACE, punch=[32.95], flash=True,
               broll=[dict(img="light_sky_b", at=(34.4, 37.5), motion="down"),
                      dict(img="interior_a", at=(37.5, 39.75), motion="right"),
                      dict(img="sujud_a", at=(39.75, 41.5), motion="in"),
                      dict(img="quran_a", at=(41.5, 43.4), motion="in"),
                      dict(img="grave_b", at=(44.6, 48.0), motion="out", particles=True)]))
    # 6. HADITH: sedekah jariah (supports 'saham mengalir dalam kubur')
    T.append(dict(kind="hadith", key="h1", dur=9.5, bg="night_a", flash=True,
                  head="SABDA RASULULLAH SAW",
                  arabic="إِذَا مَاتَ الإِنْسَانُ انْقَطَعَ عَنْهُ عَمَلُهُ إِلَّا مِنْ ثَلَاثَةٍ: إِلَّا مِنْ صَدَقَةٍ جَارِيَةٍ، أَوْ عِلْمٍ يُنْتَفَعُ بِهِ، أَوْ وَلَدٍ صَالِحٍ يَدْعُو لَهُ",
                  malay="“Apabila seseorang manusia meninggal dunia, terputuslah amalannya kecuali tiga perkara: sedekah jariah, ilmu yang dimanfaatkan, atau anak soleh yang mendoakannya.”",
                  source="— HR Muslim, no. 1631"))
    # 7. INVITATION
    T.append(S(47.08, 53.50, zoom=(1.0, 1.08), focus=(0.5, 0.42), flash=True,
               broll=[dict(img="elderly_b", at=(52.7, 54.0), motion="in")]))
    T.append(S(53.50, 56.88, zoom=(1.14, 1.2), focus=FACE,
               broll=[dict(img="dua_a", at=(54.9, 57.5), motion="up")]))
    # 8. CTA
    T.append(S(57.20, 64.28, zoom=(1.0, 1.06), focus=FACE,
               broll=[dict(img="village_a", at=(57.0, 59.0), motion="down")],
               badge=("FACEBOOK  •  TIKTOK", 4.2)))
    T.append(S(65.24, 71.58, zoom=(1.12, 1.18), focus=FACE,
               broll=[dict(img="mosque_b", at=(67.4, 69.2), motion="in"),
                      dict(img="elderly_a", at=(69.2, 70.2), motion="left"),
                      dict(img="students_b", at=(70.2, 72.0), motion="right")]))
    T.append(S(71.58, 74.88, zoom=(1.0, 1.05), focus=FACE))
    # 9. OUTRO: hadith on building a masjid + where to find the pondok
    T.append(dict(kind="hadith", key="h2", dur=8.5, bg="path_a", motion="in", flash=True, fade_in=True,
                  head="SABDA RASULULLAH SAW",
                  arabic="مَنْ بَنَى مَسْجِدًا لِلَّهِ بَنَى اللَّهُ لَهُ فِي الْجَنَّةِ مِثْلَهُ",
                  malay="“Sesiapa yang membina masjid kerana Allah, Allah akan membina untuknya seumpamanya di syurga.”",
                  source="— HR Muslim, no. 533"))
    T.append(dict(kind="end", dur=5.0, bg="mosque_c",
                  line1="PONDOK ZAWIYAH AN-NUR", line2="Gerik, Perak",
                  line3="Hubungi mudir madrasah untuk berwakaf. Ikuti kami di Facebook & TikTok.",
                  line4="SAMA-SAMA KITA INFAK DI JALAN ALLAH"))
    return T

TIMELINE = build() if WORK else []

def out_times():
    t, res = 0.0, []
    for c in TIMELINE:
        d = c["src"][1] - c["src"][0] if c["kind"] == "speech" else c["dur"]
        res.append((t, t + d)); t += d
    return res

def sfx():
    o = out_times(); ev = [("impact", 0.0, -4)]
    for c, (a, b) in zip(TIMELINE, o):
        if c["kind"] == "title": ev += [("whoosh", a - 0.35, -6), ("impact", a, -3), ("riser", b - 2.5, -14)]
        elif c["kind"] == "hadith": ev += [("riser", a - 2.5, -12), ("impact", a, -8), ("chime", a + 0.6, -10)]
        elif c["kind"] == "end": ev += [("chime", a + 0.1, -10)]
        elif c.get("flash"): ev += [("whoosh_short", a - 0.2, -10)]
        for br in c.get("broll", []):
            s = a + br["at"][0] - c["src"][0]
            if s > a + 0.1: ev.append(("whoosh_short", s - 0.15, -16))
        for pt in c.get("punch", []):
            ev.append(("impact", a + pt - c["src"][0], -16))
    return ev

SFX = sfx() if WORK else []
