"""
Edit plan v2 (director's cut, <2 min) for the Zawiyah An-Nur waqf appeal.

Times in SHOTS / overlays are SOURCE times (seconds in the original
recording).  The renderer maps them onto the tightened output timeline.

Only the speaker's own recorded words are used.  The Arabic opening
(mukadimah) and a few repeated sentences are left out for length; what
remains plays in its original order.
"""

SOURCE = "source/src.mov"
WORDS = "data/words.json"

# ---------------------------------------------------------------- timeline
HOOK = (156.10, 161.13)            # "sedekah jariah kita yang berkekalan ... alam kubur nanti"
BODY = [                           # kept source ranges, in order
    (43.10, 66.55),                # "Alhamdulillah saya sekarang ... 1 ekar."
    (77.95, 102.60),               # "Yang mana apabila siap ... 30 pintu ... musolla ... ibadat di dalamnya."
    (113.30, 137.80),              # "Jadi kita membuka wakaf ... RM50. ... nombor akaun ..."
    (148.30, 188.70),              # peak + final appeal, ending "... tanah air kita InsyaAllah."
]
MAX_PAUSE = 0.30
PEAK_PAUSE = (148.3, 161.9, 0.60)
HOOK_TAIL = 0.45
END_CARD = 6.5

# ---------------------------------------------------------------- donation info
ACCOUNT_NO = "558079530303"
ACCOUNT_NAME = "An Nur Resources"
BANK = "MAYBANK"
QR_IMAGE = "assets/qr_duitnow.jpg"
QR_CROP = (60, 60, 747, 872)        # x0, y0, x1, y1 of the white QR card

# ---------------------------------------------------------------- photos
# face_band: vertical range (0..1 of the photo) holding faces.  Text is never
# placed over it (checked by the renderer).
PHOTOS = {
    "ketibaan": dict(path="assets/ketibaan.jpg", face_band=(0.50, 0.62), z=(1.04, 1.16), focus=(0.47, 0.56), pan=(30, 0)),
    "banner":   dict(path="assets/banner_pelancaran.jpg", face_band=(0.42, 0.52), z=(1.14, 1.02), focus=(0.50, 0.48), pan=(0, -30)),
    "tanam":    dict(path="assets/tanam_pokok.jpg", face_band=(0.38, 0.58), z=(1.02, 1.14), focus=(0.50, 0.50), pan=(-30, 20)),
}

# ---------------------------------------------------------------- shots
# mode: full | card | broll | photo
# trans: transition INTO the shot: cut | whip_l | whip_r | slide_up | slide_down | zoom | light | fade
SHOTS = [
    # ---- HOOK
    dict(at="hook", mode="card", scene="dusk", trans="cut",
         card=dict(w=880, h=1130, cy=800), push=(1.22, 1.0), cam=(0, 260), sub_y=1500),

    # ---- CONNECTION: where / what
    dict(at=43.10, mode="full", trans="zoom", zoom=(1.06, 1.16), drift=(0, -20)),
    dict(at=45.90, mode="photo", photo="ketibaan", trans="whip_l",
         overlays=[dict(kind="lower3", t=46.1, dur=5.3, l1="PONDOK ZAWIYAH AN-NUR", l2="Gerik, Perak", y=1290)]),
    dict(at=51.90, mode="photo", photo="banner", trans="slide_up",
         overlays=[dict(kind="title", t=52.0, dur=4.0, text="MAJLIS PELANCARAN", size=64, y=200,
                        color="gold", anim="rise", sfx=True)]),
    dict(at=58.70, mode="card", scene="dawn", trans="whip_r",
         card=dict(w=820, h=1050, cy=860), cam=(300, 60),
         overlays=[dict(kind="title", t=59.5, dur=2.4, text="MUSOLLA", size=96, y=230, color="gold", anim="zoom", sfx=True)]),
    dict(at=61.40, mode="photo", photo="tanam", trans="slide_up",
         overlays=[dict(kind="title", t=65.2, dur=1.5, text="1 EKAR", size=170, y=470,
                        color="gold", anim="zoom", sfx=True)]),

    # ---- DEEP MESSAGE
    dict(at=77.95, mode="broll", scene="rooms", trans="whip_l", count=dict(t=83.13, n=30, t2=84.45)),
    dict(at=87.85, mode="broll", scene="mosque", trans="slide_down", cam=(520, 0),
         overlays=[
             dict(kind="title", t=91.7, dur=2.4, text="MUSOLLA", size=120, y=330, color="gold", anim="zoom", sfx=True),
             dict(kind="chip", t=92.98, dur=9.0, text="WARGA EMAS", y=330),
             dict(kind="chip", t=94.12, dur=7.9, text="WARGA PONDOK", y=430),
             dict(kind="chip", t=95.16, dur=6.9, text="WARGA TAHFIZ", y=530),
         ]),
    dict(at=113.30, mode="broll", scene="tiles", trans="whip_r", rm=dict(t=120.17, t_wakaf=115.95)),
    # "melalui skrin yang tertera, nombor akaun..."  -> QR + account
    dict(at=123.40, mode="broll", scene="gold", trans="zoom", cam=(0, 200), qr=True),

    # ---- EMOTIONAL PEAK
    dict(at=148.30, mode="full", trans="fade", zoom=(1.10, 1.40), drift=(0, 30), peak=True),

    # ---- FINAL IMPACT
    dict(at=161.85, mode="card", scene="village", trans="whip_l",
         card=dict(w=860, h=1100, cy=820), cam=(0, 160), slide=80),
    dict(at=168.40, mode="photo", photo="banner", trans="light",
         overlays=[dict(kind="title", t=168.6, dur=6.0, text="30 UNIT PINTU  ·  1 MUSOLLA", size=48, y=200,
                        color="white", anim="rise")]),
    dict(at=176.05, mode="broll", scene="bokeh", trans="slide_up", cam=(0, 380),
         overlays=[
             dict(kind="chip", t=177.2, dur=11.0, text="WARGA EMAS", y=420),
             dict(kind="chip", t=179.3, dur=8.9, text="MEMBACA AL-QURAN", y=520),
             dict(kind="chip", t=180.7, dur=7.5, text="MENGAJI AGAMA", y=620),
         ]),
    dict(at="end", mode="broll", scene="endcard", trans="fade", qr=True),
]

# Subtitle emphasis
KEY_GOLD = {"wakaf", "sedekah", "jariah", "berkekalan", "kubur", "alam", "rm50",
            "sekaki", "30", "pintu", "ekar", "1", "warga", "emas", "musolla",
            "tahfiz", "pondok", "quran", "islam", "merayu", "pembinaan", "solat",
            "berjamaah", "berkebajikan", "akaun", "skrin"}
KEY_ALLAH = {"allah", "insyaallah", "alhamdulillah", "alhamdulillahi"}
# Most important words: marker highlight + whoosh (source start time of the word)
IMPORTANT = [(53.68, 2), (56.98, 2), (65.26, 2), (83.13, 2), (91.74, 1), (115.95, 1), (120.17, 1),
             (121.89, 1), (134.19, 2), (150.19, 1), (156.18, 2), (160.22, 2), (163.20, 1),
             (177.20, 2), (179.84, 1)]
