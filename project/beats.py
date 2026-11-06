"""Motion-graphics + SFX beats, keyed to SOURCE times of the speaker's words.
Every visible word/label is either the speaker's own words or a neutral label
of what he is talking about (icons). Nothing adds new claims."""

# t3d anims: slam | fly_l | fly_r | fly_b | grow | drop
# colour styles: gold | green | white | coral | sky
def T(t, txt, style="gold", anim="slam", y=520, size=150, dur=2.2, sub="", sfx=(("cine_hit", 0, .45),), fx=()):
    return dict(type="t3d", t=t, txt=txt, style=style, anim=anim, y=y, size=size, dur=dur, sub=sub, sfx=list(sfx), fx=list(fx))


def I(t, icon, x, y, size=230, anim="pop", dur=2.4, sfx=(("pop2", 0, .45),), fx=(), ring=False):
    return dict(type="icon", t=t, icon=icon, x=x, y=y, size=size, anim=anim, dur=dur, sfx=list(sfx), fx=list(fx), ring=ring)


def C(t, txt, icon, side, y, dur=2.4, style="green", sfx=(("whoosh_s", -0.15, .35), ("pop2", 0.05, .3))):
    return dict(type="chip", t=t, txt=txt, icon=icon, side=side, y=y, dur=dur, style=style, sfx=list(sfx))


def A(t, txt, y=560, size=150, dur=2.6, sfx=(("chime", 0, .4),), fx=("rays",)):
    return dict(type="arabic", t=t, txt=txt, y=y, size=size, dur=dur, sfx=list(sfx), fx=list(fx))


def F(t, kind, **kw):
    return dict(type=kind, t=t, **kw)


BEATS = {
    "hook": [
        F(117.06, "burst", x=540, y=900, color="gold", n=40, sfx=[]),
        F(120.92, "flash", a=0.85, sfx=[("bass_drop", 0, .65), ("zap", 0, .3)]),
        F(120.92, "shake", amp=22, dur=0.6),
        F(120.92, "burst", x=540, y=900, color="gold", n=90, sfx=[("sparkle", 0.1, .5)]),
        F(120.92, "rays", dur=1.6),
    ],
    "salam": [
        A(2.45, "السَّلَامُ عَلَيْكُمْ", y=520, size=140, dur=3.6),
        I(2.6, "starcrescent", 880, 300, 170, "drop", 3.8, sfx=[("ding", 0.25, .3)]),
    ],
    "bism": [
        A(8.35, "بِسْمِ اللّٰهِ الرَّحْمٰنِ الرَّحِيْمِ", y=520, size=96, dur=1.75, sfx=[("sparkle", 0, .45)]),
    ],
    "lokasi": [
        I(33.10, "person", 190, 560, 170, "pop", 2.0),
        I(35.65, "pin", 540, 690, 250, "drop", 2.4, sfx=[("whoosh_s", -0.25, .3), ("pop2", 0, .5), ("ding", 0.05, .3)], ring=True),
        T(35.55, "MADRASAH ZAWIYAH AN NUR", "white", "fly_b", y=400, size=88, dur=2.6, sfx=[("whoosh_s", -0.1, .35)]),
        C(37.70, "GERIK", "map", "left", 1130, 2.0),
    ],
    "tanah": [
        T(41.46, "DI BELAKANG SAYA", "white", "fly_l", y=430, size=96, dur=1.6, sfx=[("whoosh_s", -0.1, .35)]),
        T(45.55, "TANAH WAKAF", "gold", "slam", y=470, size=160, dur=2.5, sfx=[("cine_hit", 0, .5), ("ding", 0.08, .25)],
          fx=["shake", "burst"]),
        I(45.75, "seedling", 880, 1110, 200, "pop", 2.2, sfx=[("pop_hi", 0, .35)]),
        I(46.66, "palms", 200, 1110, 200, "pop", 1.8, sfx=[("sparkle", 0, .35)]),
        F(49.90, "boundary", dur=3.0, sfx=[("swoosh", 0, .3)]),
        T(49.96, "± 1 HEKTAR", "green", "grow", y=470, size=170, dur=2.6, sfx=[("bell", 0.05, .35), ("cine_hit", 0, .35)],
          fx=["shake"]),
        I(50.10, "map", 880, 1120, 190, "pop", 2.2, sfx=[]),
        C(51.90, "BERKEMBAR DENGAN MADRASAH", "link", "right", 1130, 3.4, style="gold"),
    ],
    "syukur": [
        A(58.40, "اَلْحَمْدُ لِلّٰهِ", y=500, size=150, dur=3.0, sfx=[("chime", 0, .45)]),
        I(58.60, "sparkles", 860, 330, 170, "pop", 2.8, sfx=[]),
        I(58.70, "sparkles", 220, 700, 120, "pop", 2.6, sfx=[]),
    ],
    "rancangan": [
        I(63.86, "tools", 860, 560, 190, "pop", 2.2, sfx=[("pop2", 0, .4)]),
        T(64.96, "TANAH WAKAF INI", "gold", "fly_r", y=430, size=110, dur=1.9, sfx=[("whoosh_s", -0.1, .35)]),
        F(68.30, "iconrow", icons=["house", "hut", "house"], y=760, size=190, gap=0.18, dur=2.0,
          sfx=[("pop2", 0, .4), ("pop_hi", 0.18, .4), ("pop2", 0.36, .4)]),
        T(70.35, "PONDOK WARGA EMAS", "gold", "slam", y=470, size=128, dur=2.4, sfx=[("cine_hit", 0, .45), ("ding", 0.1, .3)],
          fx=["shake", "burst"]),
        I(70.50, "oldman", 300, 760, 210, "fly_l", 2.2, sfx=[("whoosh_s", -0.1, .3)]),
        I(70.65, "oldwoman", 780, 760, 210, "fly_r", 2.1, sfx=[]),
        C(72.00, "SINGLE", "person", "left", 1130, 1.6, style="sky"),
        C(73.20, "BERKELAMIN", "oldwoman", "right", 1130, 1.9, style="coral"),
    ],
    "raya": [
        I(76.30, "construction", 860, 520, 200, "pop", 1.9, sfx=[("pop2", 0, .4)]),
        T(77.90, "SELEPAS HARI RAYA", "green", "drop", y=470, size=128, dur=2.3, sfx=[("bell", 0.0, .4), ("cine_hit", 0, .3)],
          fx=["burst"]),
        I(78.05, "moon", 150, 250, 170, "drop", 2.1, sfx=[("sparkle", 0.1, .35)]),
        I(78.15, "starcrescent", 930, 250, 150, "pop", 2.0, sfx=[]),
    ],
    "rayuan": [
        I(83.96, "palms", 860, 560, 210, "pop", 1.6, sfx=[("pop2", 0, .4)]),
        T(84.70, "SUMBANGAN", "gold", "slam", y=470, size=170, dur=2.5, sfx=[("bass_drop", 0, .5), ("ding", 0.1, .3)],
          fx=["shake", "burst", "flash"]),
        I(84.90, "heart", 200, 760, 190, "pop", 2.0, sfx=[]),
        I(84.95, "coin", 880, 760, 170, "pop", 2.0, sfx=[("pop_hi", 0.05, .3)]),
        T(88.22, "PEMBINAAN", "white", "fly_l", y=430, size=120, dur=1.8, sfx=[("whoosh_s", -0.1, .35)]),
        I(88.40, "brick", 880, 680, 170, "drop", 2.0, sfx=[("pop2", 0, .35)]),
        I(88.65, "construction", 200, 680, 190, "drop", 1.8, sfx=[("pop2", 0, .35)]),
        F(91.26, "iconrow", icons=["house", "house", "house"], y=760, size=170, gap=0.16, dur=2.0,
          sfx=[("pop2", 0, .35), ("pop_hi", 0.16, .35), ("pop2", 0.32, .35)]),
        I(93.62, "oldman", 330, 1130, 170, "pop", 1.2, sfx=[]),
        I(93.72, "oldwoman", 750, 1130, 170, "pop", 1.1, sfx=[]),
    ],
    "ilmu": [
        C(100.42, "PENEMPATAN KOMPLEKS INI", "mosque", "left", 1130, 2.6, style="gold"),
        I(109.54, "oldman", 300, 1130, 200, "fly_l", 2.0, sfx=[("whoosh_s", -0.1, .3)]),
        I(109.70, "oldwoman", 780, 1130, 200, "fly_r", 1.9, sfx=[]),
        T(111.62, "MENUNTUT ILMU", "gold", "slam", y=470, size=150, dur=2.4, sfx=[("cine_hit", 0, .4), ("chime", 0.05, .3)],
          fx=["shake", "burst"]),
        I(111.80, "book", 880, 1120, 210, "pop", 2.2, sfx=[]),
        I(111.95, "gradcap", 200, 1120, 190, "pop", 2.1, sfx=[("sparkle", 0, .3)]),
        C(113.80, "MADRASAH ZAWIYAH AN NUR", "classical", "right", 1130, 2.4, style="green"),
    ],
    "akhirat": [
        I(117.90, "palms", 860, 560, 200, "pop", 1.6, sfx=[("pop2", 0, .4)]),
        T(119.55, "KEBAJIKAN", "gold", "slam", y=430, size=170, dur=1.4, sfx=[("cine_hit", 0, .45)], fx=["shake"]),
        T(120.90, "HINGGA KE AKHIRAT", "white", "grow", y=560, size=124, dur=2.3, sfx=[("bass_drop", 0, .6), ("chime", 0.1, .35)],
          fx=["shake", "burst", "flash", "rays"]),
        I(121.05, "star", 540, 300, 190, "pop", 2.0, sfx=[]),
    ],
    "sebar": [
        T(123.55, "SEBARKAN", "gold", "slam", y=470, size=170, dur=2.2, sfx=[("cine_hit", 0, .45), ("ding", 0.08, .3)],
          fx=["shake", "burst"]),
        I(123.70, "megaphone", 200, 760, 210, "fly_l", 2.0, sfx=[("whoosh_s", -0.1, .35)], ring=True),
        I(123.85, "phone", 880, 760, 190, "fly_r", 1.9, sfx=[]),
        I(126.44, "hourglass", 880, 520, 200, "pop", 2.4, sfx=[("pop2", 0, .4), ("tick", 0.3, .4), ("tick", 0.6, .4)]),
        T(126.44, "DALAM MASA YANG SINGKAT", "white", "fly_b", y=400, size=84, dur=2.4, sfx=[("whoosh_s", -0.1, .3)]),
        T(127.84, "BERJAYA", "green", "grow", y=1110, size=110, dur=1.2, sfx=[("ding", 0, .3)]),
        C(130.40, "MADRASAH", "classical", "left", 640, 3.4, style="gold", sfx=[("pop2", 0, .45)]),
        C(131.90, "ASRAMA", "bed", "right", 800, 2.1, style="green", sfx=[("pop_hi", 0, .45)]),
        C(132.90, "PONDOK", "house", "left", 960, 1.2, style="coral", sfx=[("pop2", 0, .45)]),
        T(134.84, "RUANG YANG LUAS", "gold", "grow", y=470, size=124, dur=2.0, sfx=[("swoosh", -0.1, .35), ("ding", 0.05, .25)]),
        I(136.96, "oldman", 300, 1130, 190, "pop", 1.7, sfx=[("pop2", 0, .3)]),
        I(137.10, "oldwoman", 780, 1130, 190, "pop", 1.6, sfx=[]),
        I(140.64, "bed", 540, 620, 230, "drop", 2.4, sfx=[("pop2", 0, .4), ("sparkle", 0.1, .3)]),
        T(140.64, "MENGINAP", "white", "fly_b", y=400, size=110, dur=2.2, sfx=[("whoosh_s", -0.1, .3)]),
    ],
    "penutup": [
        I(144.66, "speech", 870, 520, 200, "pop", 2.4, sfx=[("pop2", 0, .4)]),
        T(144.66, "RAYUAN", "gold", "fly_r", y=430, size=130, dur=1.9, sfx=[("whoosh_s", -0.1, .3)]),
        I(148.42, "thumbsup", 860, 560, 200, "pop", 2.0, sfx=[("pop_hi", 0, .4)]),
        I(148.60, "heart", 220, 560, 170, "pop", 1.9, sfx=[("sparkle", 0, .3)]),
        T(149.52, "RESPONS YANG BAIK", "green", "grow", y=400, size=104, dur=1.9, sfx=[("ding", 0, .3)]),
        I(151.40, "busts", 540, 560, 200, "pop", 2.2, sfx=[("pop2", 0, .3)]),
    ],
    "salam2": [
        I(154.70, "palms", 540, 520, 220, "pop", 1.9, sfx=[("sparkle", 0, .35)]),
        F(156.75, "rays", dur=6.0),
        F(156.75, "burst", x=540, y=760, color="gold", n=70, sfx=[("chime", 0, .45), ("cine_hit", 0, .3)]),
        F(156.75, "flash", a=0.6, sfx=[]),
    ],
}
