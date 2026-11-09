"""
Edit plan (director's cut) for the Zawiyah An-Nur waqf appeal.

All times in `SHOTS` / overlays are SOURCE times (seconds in the original
recording).  The renderer maps them onto the tightened output timeline.

Nothing here adds words to the speaker's mouth: the audio is only the
original recording (pauses shortened), and every subtitle comes from
data/words.json (the transcript of that recording).
"""

SOURCE = "source/src.mov"          # original upload (not committed: large)
WORDS = "data/words.json"

# ---------------------------------------------------------------- timeline
# Hook = the speaker's own strongest line, used as a cold-open teaser.
# It is heard again, in full context, at the emotional peak.
HOOK = (156.10, 161.13)            # "sedekah jariah kita yang berkekalan ... alam kubur nanti"
BODY = (22.35, 197.70)             # salam -> closing salam
MAX_PAUSE = 0.42                   # long pauses are shortened to this
PEAK_PAUSE = (148.3, 161.9, 0.75)  # ...but breathe more at the emotional peak
HOOK_TAIL = 0.55                   # beat of silence after the hook
END_CARD = 4.2                     # seconds of end card after the last word

# ---------------------------------------------------------------- end card
# The speaker says the account number is "on screen".  We do not have it, so
# fill these in and re-render.  Empty strings are simply not shown.
INFO = {
    "title": "MAKLUMAT WAKAF",
    "lines": [
        "Pondok Zawiyah An-Nur",
        "Gerik, Perak",
        "Wakaf sekaki: RM50",
    ],
    "account": "",                 # e.g. "Bank Islam  08xxx xxxxxxx"
    "account_name": "",            # e.g. "Madrasah Zawiyah An-Nur"
    "contact": "",                 # e.g. "Tel: 01x-xxx xxxx"
}

# ---------------------------------------------------------------- shots
# mode:  full  = speaker full frame (graded, camera moves)
#        card  = speaker in a floating card over a living background scene
#        broll = full-screen cinematic scene / motion graphic, voice continues
# trans: transition INTO this shot: cut | whip_l | whip_r | slide_up |
#        slide_down | zoom | light | fade
SHOTS = [
    # ---- BABAK 1: HOOK
    dict(at="hook", mode="card", scene="dusk", trans="cut",
         card=dict(w=880, h=1130, cy=800), push=(1.22, 1.0), cam=(0, 260),
         sub_style="big", sub_y=1500),

    # ---- BABAK 2: CONNECTION
    dict(at=22.35, mode="card", scene="dawn", trans="zoom",
         card=dict(w=780, h=1000, cy=900), cam=(380, 0),
         overlays=[
             dict(kind="title", t=22.9, dur=8.5, text="PONDOK WARGA EMAS", size=74,
                  y=190, color="gold", anim="track"),
             dict(kind="title", t=23.6, dur=7.8, text="& MUSOLLA", size=58, y=285,
                  color="white", anim="rise"),
         ]),
    dict(at=43.10, mode="full", trans="light", zoom=(1.04, 1.16), drift=(0, -20),
         punches=[(47.0, 0.10)],
         overlays=[dict(kind="lower3", t=46.0, dur=5.0, l1="PONDOK ZAWIYAH AN-NUR",
                        l2="Gerik, Perak")]),
    dict(at=53.55, mode="broll", scene="blueprint", trans="whip_l",
         overlays=[
             dict(kind="title", t=53.7, dur=3.6, text="MAJLIS PELANCARAN", size=64, y=300,
                  color="white", anim="rise"),
             dict(kind="title", t=54.3, dur=3.1, text="PEMBINAAN", size=96, y=400,
                  color="gold", anim="zoom"),
         ]),

    # ---- BABAK 3: DEEP MESSAGE
    dict(at=61.35, mode="broll", scene="land", trans="slide_up",
         overlays=[dict(kind="title", t=65.2, dur=1.3, text="1 EKAR", size=170, y=520,
                        color="gold", anim="zoom", sfx="impact")]),
    dict(at=66.60, mode="card", scene="village", trans="zoom",
         card=dict(w=860, h=1100, cy=820), cam=(120, 120), slide=-70),
    dict(at=78.00, mode="broll", scene="rooms", trans="whip_r",
         count=dict(t=83.13, n=30, t2=84.45)),
    dict(at=87.85, mode="broll", scene="mosque", trans="slide_down", cam=(520, 0),
         overlays=[
             dict(kind="title", t=91.7, dur=2.3, text="MUSOLLA", size=120, y=330,
                  color="gold", anim="zoom"),
             dict(kind="chip", t=92.98, dur=9.3, text="WARGA EMAS", y=330),
             dict(kind="chip", t=94.12, dur=8.2, text="WARGA PONDOK", y=430),
             dict(kind="chip", t=95.16, dur=7.2, text="WARGA TAHFIZ", y=530),
         ]),
    dict(at=103.00, mode="full", trans="light", zoom=(1.12, 1.22), drift=(10, -10),
         punches=[(107.27, 0.10), (109.03, 0.08)]),
    dict(at=113.30, mode="broll", scene="tiles", trans="whip_l",
         rm=dict(t=120.17, t_wakaf=115.95)),
    dict(at=123.40, mode="card", scene="gold", trans="zoom",
         card=dict(w=660, h=820, cy=580), cam=(0, 200),
         overlays=[dict(kind="panel", t=125.4, dur=12.0, y=1080)]),
    dict(at=137.85, mode="broll", scene="rays", trans="light", cam=(0, 420),
         overlays=[dict(kind="title", t=143.75, dur=2.6, text="ALLAH", size=150, y=640,
                        color="allah", anim="glow")]),

    # ---- BABAK 4: EMOTIONAL PEAK  (minimal visuals, close on the speaker)
    dict(at=148.30, mode="full", trans="fade", zoom=(1.10, 1.42), drift=(0, 30),
         peak=True),

    # ---- BABAK 5: FINAL IMPACT
    dict(at=161.85, mode="card", scene="village", trans="whip_r",
         card=dict(w=860, h=1100, cy=820), cam=(0, 160), slide=80),
    dict(at=176.05, mode="broll", scene="bokeh", trans="slide_up", cam=(0, 380),
         overlays=[
             dict(kind="chip", t=179.3, dur=8.4, text="MEMBACA AL-QURAN", y=420),
             dict(kind="chip", t=180.7, dur=7.0, text="MENGAJI AGAMA", y=520),
         ]),
    dict(at=189.30, mode="full", trans="fade", zoom=(1.22, 1.02), drift=(0, 0)),
    dict(at="end", mode="broll", scene="endcard", trans="fade"),
]

# Words shown with special emphasis in the subtitles (lower-case, stripped).
KEY_GOLD = {"wakaf", "sedekah", "jariah", "berkekalan", "kubur", "alam", "rm50",
            "sekaki", "30", "pintu", "ekar", "1", "warga", "emas", "musolla",
            "tahfiz", "pondok", "quran", "islam", "merayu", "pembinaan", "solat",
            "berjamaah", "kebajikan", "berkebajikan", "menginfak"}
KEY_ALLAH = {"allah", "insyaallah", "alhamdulillah", "alhamdulillahi"}
