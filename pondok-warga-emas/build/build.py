#!/usr/bin/env python3
"""Generates the HyperFrames composition for the Pondok Warga Emas appeal video.

Source of truth for the edit:
  build/edl.json   - cut list (source in/out -> edited timeline)
  CAPTIONS below   - corrected Malay captions per segment, timed from Whisper words
Run:  python3 build/build.py   (rewrites index.html and compositions/*.html)
After that, the HTML is normal HyperFrames source and can be edited in Studio directly.
"""
import json, html, os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EDL = json.load(open(os.path.join(ROOT, "build", "edl.json")))
W, H = 1080, 1920
TOTAL = 86.5  # speech ends 83.65; end card holds after it
SEG = {c["id"]: c for c in EDL}


def T(src):
    """Map a source-video time to the edited timeline."""
    for c in EDL:
        if c["in"] - 0.05 <= src <= c["out"] + 0.05:
            return round(c["at"] + min(max(src, c["in"]), c["out"]) - c["in"], 3)
    raise ValueError(f"source time {src} is not inside any kept segment")


def r(x):
    return round(x, 3)


# ---------------------------------------------------------------- grading
GRADE_TALK = {"preset": "skin-soft", "intensity": 0.66,
              "adjust": {"contrast": 0.07, "highlights": -0.16, "shadows": 0.1,
                         "temperature": 0.07, "tint": 0.01, "vibrance": 0.05, "saturation": 0.03},
              "details": {"vignette": 0.05}}
GRADE_PHOTO = {"intensity": 0.65,
               "adjust": {"contrast": 0.07, "highlights": -0.1, "shadows": 0.06,
                          "temperature": 0.05, "vibrance": 0.05, "saturation": 0.02},
               "details": {"vignette": 0.05}}


def grade(g):
    return html.escape(json.dumps(g, separators=(",", ":")), quote=True)


# ---------------------------------------------------------------- captions
# (segment, corrected text, source start, source end). Words wrapped in * are accent (gold).
CAPTIONS = [
    ("s01", "Di belakang saya ni,", 41.47, 42.54),
    ("s01", "tuan-tuan, ialah", 42.54, 43.56),
    ("s02", "*tanah* yang *diwakafkan*", 44.76, 46.56),
    ("s02", "oleh hamba Allah", 46.56, 47.58),
    ("s03", "keluasannya", 48.18, 49.24),
    ("s03", "lebih kurang *satu* *ekar*", 49.66, 50.84),
    ("s04", "Assalamualaikum", 2.40, 3.60),
    ("s04", "warahmatullahi wabarakatuh", 3.60, 6.48),
    ("s05", "Saya sekarang ni berada", 33.11, 35.36),
    ("s05", "di Madrasah Zawiyah", 35.49, 37.50),
    ("s05", "An-Nur, Gerik", 37.50, 38.13),
    ("s06", "Jadi, alhamdulillah,", 57.87, 59.16),
    ("s06", "syukur pada Allah Taala", 59.16, 60.34),
    ("s06", "di atas wakaf tersebut", 60.34, 61.56),
    ("s07", "InsyaAllah, kita akan", 62.82, 64.12),
    ("s07", "memanfaatkan tanah wakaf ini", 64.12, 66.31),
    ("s08", "untuk membina", 67.45, 68.55),
    ("s09", "*pondok* untuk *warga* *emas*", 69.69, 71.33),
    ("s10", "yang single", 71.96, 72.74),
    ("s10", "dan juga yang berkelamin", 72.74, 74.19),
    ("s11", "InsyaAllah, projek ni", 75.78, 77.16),
    ("s11", "akan berjalan", 77.16, 78.38),
    ("s11", "selepas *Hari* *Raya*", 78.38, 79.78),
    ("s12", "Jadi, kami amat mengharapkan", 83.14, 84.98),
    ("s12", "*sumbangan*", 84.98, 85.46),
    ("s12", "daripada tuan-tuan dan puan-puan", 85.56, 87.04),
    ("s13", "untuk menjayakan", 88.15, 90.10),
    ("s13", "pembinaan", 90.10, 91.33),
    ("s14", "pondok-pondok untuk *warga* *emas*", 92.66, 94.52),
    ("s15", "Mudah-mudahan,", 99.66, 100.66),
    ("s16", "dengan pendirian kompleks ini,", 105.51, 107.74),
    ("s16", "memudahkan", 107.74, 108.61),
    ("s17", "bagi warga-warga", 109.34, 110.84),
    ("s18", "*emas*", 111.70, 112.18),
    ("s19", "untuk menuntut *ilmu*", 112.83, 113.80),
    ("s19", "di Madrasah Zawiyah An-Nur ini", 113.80, 116.32),
    ("s20", "Mudah-mudahan sumbangan tuan-tuan sekalian", 117.36, 119.50),
    ("s20", "menjadi *kebajikan*", 119.50, 120.54),
    ("s20", "hingga ke *akhirat*", 120.54, 121.50),
    ("s21", "Dan tuan-tuan,", 122.88, 123.52),
    ("s21", "tolong *sebarkan* berita ini", 123.52, 125.08),
    ("s21", "InsyaAllah", 125.08, 125.74),
    ("s22", "dalam masa yang singkat", 126.37, 127.70),
    ("s22", "kita berjaya dan mampu", 127.70, 129.25),
    ("s23", "mendirikan asrama", 131.42, 132.84),
    ("s23", "atau pondok-pondok ini", 132.84, 134.09),
    ("s24", "untuk beri ruang yang luas", 134.77, 136.13),
    ("s25", "kepada *warga* *emas*", 136.85, 138.34),
    ("s25", "terutamanya", 138.34, 139.14),
    ("s26", "Itu sahaja rayuan daripada saya.", 144.29, 145.96),
    ("s26", "Mudah-mudahan", 145.96, 146.79),
    ("s27", "rayuan ini mendapat", 147.42, 148.88),
    ("s27", "respons yang baik", 148.88, 150.22),
    ("s27", "daripada tuan-tuan, puan-puan,", 150.22, 152.50),
    ("s27", "muslimin muslimat sekalian", 152.50, 153.74),
]


def caption_groups():
    groups = []
    for i, (seg, text, s0, s1) in enumerate(CAPTIONS):
        c = SEG[seg]
        a = r(c["at"] + max(s0, c["in"]) - c["in"])
        b = r(c["at"] + min(s1, c["out"]) - c["in"])
        words = text.split()
        weights = [len(w.strip("*")) + 2 for w in words]
        tot = sum(weights)
        t = a
        ws = []
        for w, k in zip(words, weights):
            ws.append((w, r(t)))
            t += (b - a) * k / tot
        groups.append({"i": i, "start": a, "end": b, "words": ws})
    # each group stays until the next one starts (or a short tail), never overlapping
    for g, n in zip(groups, groups[1:] + [None]):
        tail = g["end"] + 0.35
        g["hide"] = r(min(n["start"], tail) if n else tail)
    return groups


def captions_html():
    gs = caption_groups()
    parts, tl = [], []
    for g in gs:
        spans = []
        for j, (w, _) in enumerate(g["words"]):
            accent = w.startswith("*")
            spans.append(f'<span id="cw-{g["i"]}-{j}" class="cw{" acc" if accent else ""}">{html.escape(w.strip("*"))}</span>')
        parts.append(
            f'      <div id="cg-{g["i"]}" class="cg"><div class="pill">{" ".join(spans)}</div></div>')
        st, hide = g["start"] - 0.04, g["hide"]
        tl.append(f'tl.fromTo("#cg-{g["i"]}", {{opacity:0, y:14}}, {{opacity:1, y:0, duration:0.14, ease:"power3.out"}}, {r(st)});')
        for j, (w, wt) in enumerate(g["words"]):
            if not w.startswith("*"):
                tl.append(f'tl.fromTo("#cw-{g["i"]}-{j}", {{color:"rgba(255,255,255,0.55)"}}, {{color:"#ffffff", duration:0.08, ease:"none"}}, {r(max(st, wt - 0.04))});')
            else:
                tl.append(f'tl.fromTo("#cw-{g["i"]}-{j}", {{color:"rgba(242,201,120,0.55)"}}, {{color:"#f5cd7a", duration:0.08, ease:"none"}}, {r(max(st, wt - 0.04))});')
        tl.append(f'tl.to("#cg-{g["i"]}", {{opacity:0, duration:0.1, ease:"power2.in"}}, {r(hide - 0.1)});')
        tl.append(f'tl.set("#cg-{g["i"]}", {{opacity:0, visibility:"hidden"}}, {r(hide)});')
    return f"""<template>
  <style>
    #root {{ position:absolute; inset:0; pointer-events:none; }}
    .cg {{ position:absolute; left:0; top:1168px; width:1080px; height:190px; display:flex;
          align-items:center; justify-content:center; opacity:0; overflow:visible; }}
    .pill {{ max-width:900px; padding:14px 30px 16px; border-radius:22px; text-align:center;
            background:rgba(5,28,21,0.66); box-shadow:0 10px 30px rgba(0,0,0,0.25);
            font-family:"Montserrat", sans-serif; font-weight:800; font-size:54px; line-height:1.18;
            letter-spacing:-0.01em; color:#fff; text-wrap:balance; }}
    .cw {{ color:rgba(255,255,255,0.55); }}
    .cw.acc {{ color:#f5cd7a; }}
  </style>
  <div id="root" data-composition-id="captions" data-width="{W}" data-height="{H}" data-layout-allow-overlap>
{chr(10).join(parts)}
  </div>
  <script>
    const tl = gsap.timeline({{ paused: true }});
    {chr(10) + '    '.join(tl)}
    window.__timelines["captions"] = tl;
  </script>
</template>
"""


# ---------------------------------------------------------------- shared scene CSS
SCENE_CSS = """
    #root { position:absolute; inset:0; overflow:hidden; }
    .broll { position:absolute; left:0; top:0; width:1080px; height:1920px; overflow:hidden; }
    .kb { position:absolute; left:0; top:0; transform-origin:50% 50%; }
    .kb img { display:block; width:100%; height:100%; object-fit:cover; }
    .scrim-top { position:absolute; left:0; top:0; width:1080px; height:900px;
      background:linear-gradient(180deg, rgba(4,30,22,0.86) 0%, rgba(4,30,22,0.66) 50%, rgba(4,30,22,0) 100%); }
    .eyebrow { font-family:"Montserrat",sans-serif; font-weight:700; font-size:28px; letter-spacing:0.32em;
      text-transform:uppercase; color:#f2c978; }
    .serif { font-family:"Playfair Display",serif; font-weight:700; color:#fff; line-height:1.02; letter-spacing:-0.01em; }
    .gold { color:#f5cd7a; }
    .rule { height:3px; background:linear-gradient(90deg, rgba(245,205,122,0), #f5cd7a 20%, #f5cd7a 80%, rgba(245,205,122,0)); }
    .chip { display:inline-flex; align-items:center; gap:14px; padding:14px 28px; border-radius:999px;
      font-family:"Montserrat",sans-serif; font-weight:800; font-size:34px; letter-spacing:0.08em; text-transform:uppercase; }
    .tb { position:absolute; left:0; width:1080px; text-align:center; }
"""


def broll(id_, src, start, dur, iw, ih, x0, x1, s0, s1, y0=None, y1=None, ease="sine.inOut", z=1):
    """A full-frame photo with a Ken Burns move. (iw, ih) is the drawn size before scale;
    x/y are the wrapper offsets in px."""
    if y0 is None:
        y0 = -(ih - H) / 2
    if y1 is None:
        y1 = y0
    el = (f'    <div id="{id_}" class="clip broll" data-start="{r(start)}" data-duration="{r(dur)}" style="z-index:{z}">\n'
          f'      <div id="{id_}-kb" class="kb" style="width:{iw}px;height:{ih}px">'
          f'<img id="{id_}-img" src="{src}" alt="" data-color-grading="{grade(GRADE_PHOTO)}" /></div>\n'
          f'    </div>')
    js = (f'tl.fromTo("#{id_}-kb", {{x:{r(x0)}, y:{r(y0)}, scale:{s0}}}, '
          f'{{x:{r(x1)}, y:{r(y1)}, scale:{s1}, duration:{r(dur)}, ease:"{ease}"}}, {r(start)});')
    return el, js


def scene(cid, css, body, js):
    return f"""<template>
  <style>{SCENE_CSS}{css}
  </style>
  <div id="root" data-composition-id="{cid}" data-width="{W}" data-height="{H}">
{body}
  </div>
  <script>
    const tl = gsap.timeline({{ paused: true }});
    {(chr(10) + '    ').join(js)}
    window.__timelines["{cid}"] = tl;
  </script>
</template>
"""


def word_in(sel, t, blur=8, dur=0.2, y=0):
    return (f'tl.fromTo("{sel}", {{opacity:0, y:{y}, filter:"blur({blur}px)"}}, '
            f'{{opacity:1, y:0, filter:"blur(0px)", duration:{dur}, ease:"power4.out"}}, {r(t)});')


def out(sel, t, dur=0.2):
    return (f'tl.to("{sel}", {{opacity:0, filter:"blur(8px)", duration:{dur}, ease:"power3.in"}}, {r(t)});')


# ---------------------------------------------------------------- scene: hook (0 - 7.96)
def scene_hook():
    end = SEG["s03"]["end"]
    t_broll = SEG["s02"]["at"]
    t_ekar = T(50.12)
    # aerial: 1280x720 drawn at 1920 high -> 3413 wide
    iw, ih = 3413, 1920
    el = (f'    <div id="hk-aerial" class="clip broll" data-start="{t_broll}" data-duration="{r(end - t_broll)}" style="z-index:1">\n'
          f'      <div id="hk-kb" class="kb" style="width:{iw}px;height:{ih}px">\n'
          f'        <img id="hk-img" src="assets/photos/tanah-wakaf-aerial.jpg" alt="" data-color-grading="{grade(GRADE_PHOTO)}" />\n'
          f'        <svg id="hk-plot" viewBox="0 0 1280 720" preserveAspectRatio="none" style="position:absolute;left:0;top:0;width:100%;height:100%;overflow:visible">\n'
          f'          <polygon id="hk-plot-fill" points="{PLOT}" fill="rgba(245,205,122,0.20)" />\n'
          f'          <polygon id="hk-plot-line" points="{PLOT}" fill="none" stroke="#f5cd7a" stroke-width="3.2" stroke-linejoin="round" stroke-dasharray="4200" stroke-dashoffset="4200" />\n'
          f'        </svg>\n'
          f'      </div>\n'
          f'    </div>')
    body = f"""    <div id="hk-scrim" class="scrim-top" style="z-index:2"></div>
{el}
    <div id="hk-title" class="tb" style="top:236px;z-index:5">
      <div id="hk-eyebrow" class="eyebrow">Rayuan Wakaf &middot; Gerik</div>
      <div id="hk-l1" class="serif" style="font-size:132px;margin-top:22px">Tanah Wakaf</div>
      <div id="hk-l2" class="serif gold" style="font-size:76px;font-style:italic;font-weight:600;margin-top:6px">untuk Warga Emas</div>
    </div>
    <div id="hk-tag" class="tb" style="top:1010px;z-index:5">
      <span id="hk-chip" class="chip" style="background:rgba(5,28,21,0.78);color:#f5cd7a;border:2px solid rgba(245,205,122,0.7)">
        <svg width="30" height="30" viewBox="0 0 24 24"><path d="M12 2C8 2 5 5 5 9c0 5 7 13 7 13s7-8 7-13c0-4-3-7-7-7zm0 9.5A2.5 2.5 0 1 1 12 6.5a2.5 2.5 0 0 1 0 5z" fill="#f5cd7a"/></svg>
        Tanah Wakaf
      </span>
    </div>
    <div id="hk-ekar" class="tb" style="top:250px;z-index:6">
      <div id="hk-ekar-eb" class="eyebrow">Keluasan Lebih Kurang</div>
      <div style="display:flex;align-items:baseline;justify-content:center;gap:26px;margin-top:6px">
        <span id="hk-ekar-n" class="serif gold" style="font-size:300px;line-height:0.9">1</span>
        <span id="hk-ekar-u" class="serif" style="font-size:150px">Ekar</span>
      </div>
    </div>"""
    js = [
        # frame 0 is the thumbnail: the title is already landed at t=0
        'tl.set("#hk-scrim", {opacity:1}, 0);',
        'tl.set(["#hk-eyebrow","#hk-l1","#hk-l2"], {opacity:1}, 0);',
        out("#hk-eyebrow", t_broll - 0.22, 0.18), out("#hk-l1", t_broll - 0.18, 0.18), out("#hk-l2", t_broll - 0.14, 0.18),
        f'tl.to("#hk-scrim", {{opacity:0.0, duration:0.4, ease:"power2.inOut"}}, {r(t_broll - 0.1)});',
        f'tl.fromTo("#hk-kb", {{x:-60, y:0, scale:1.0}}, {{x:-520, y:0, scale:1.07, duration:{r(end - t_broll)}, ease:"sine.inOut"}}, {t_broll});',
        f'tl.to("#hk-plot-line", {{strokeDashoffset:0, duration:1.6, ease:"power2.inOut"}}, {r(t_broll + 0.35)});',
        f'tl.fromTo("#hk-plot-fill", {{opacity:0}}, {{opacity:1, duration:0.8, ease:"power2.out"}}, {r(t_broll + 1.3)});',
        f'tl.fromTo("#hk-chip", {{opacity:0, scale:0.6, y:20}}, {{opacity:1, scale:1, y:0, duration:0.55, ease:"back.out(1.6)"}}, {r(t_broll + 1.0)});',
        out("#hk-chip", t_ekar - 0.5, 0.2),
        f'tl.to("#hk-scrim", {{opacity:1, duration:0.4, ease:"power2.inOut"}}, {r(t_ekar - 0.45)});',
        word_in("#hk-ekar-eb", t_ekar - 0.3, 6, 0.2),
        f'tl.fromTo("#hk-ekar-n", {{opacity:0, scale:1.6, filter:"blur(14px)"}}, {{opacity:1, scale:1, filter:"blur(0px)", duration:0.42, ease:"expo.out"}}, {r(t_ekar)});',
        word_in("#hk-ekar-u", t_ekar + 0.14, 8, 0.24),
        f'tl.to("#hk-ekar", {{opacity:0, filter:"blur(10px)", duration:0.2, ease:"power3.in"}}, {r(end - 0.24)});',
        f'tl.to("#hk-scrim", {{opacity:0, duration:0.2}}, {r(end - 0.22)});',
    ]
    css = """
    #hk-ekar-eb, #hk-ekar-n, #hk-ekar-u, #hk-chip { opacity:0; }"""
    return scene("hook", css, body, js), end


# Wakaf plot outline in the aerial photo's own pixel space (1280x720)
PLOT = "352,186 470,184 598,196 636,238 650,340 666,452 698,560 756,650 792,720 0,720 0,466"


# ---------------------------------------------------------------- scene: lokasi (12.19 - 17.33)
def scene_lokasi():
    host = SEG["s05"]["at"]
    t_cut = T(35.40) - host
    dur = SEG["s05"]["end"] - host
    el, kb = broll("lk-aerial", "assets/photos/pondok-aerial.jpg", t_cut, dur - t_cut, 2882, 1920, -620, -980, 1.0, 1.06)
    body = f"""{el}
    <div id="lk-scrim" class="scrim-top" style="z-index:2"></div>
    <div id="lk-card" class="tb" style="top:250px;z-index:5">
      <svg id="lk-pin" width="64" height="64" viewBox="0 0 24 24"><path d="M12 2C8 2 5 5 5 9c0 5 7 13 7 13s7-8 7-13c0-4-3-7-7-7zm0 9.5A2.5 2.5 0 1 1 12 6.5a2.5 2.5 0 0 1 0 5z" fill="#f5cd7a"/></svg>
      <div id="lk-l1" class="serif" style="font-size:84px;margin-top:10px">Madrasah Zawiyah</div>
      <div id="lk-l2" class="serif gold" style="font-size:96px;font-style:italic">An-Nur</div>
      <div id="lk-rule" class="rule" style="width:360px;margin:26px auto 22px"></div>
      <div id="lk-l3" class="eyebrow" style="color:#fff">Gerik &middot; Perak</div>
    </div>"""
    t = t_cut + 0.15
    js = [kb,
          f'tl.fromTo("#lk-scrim", {{opacity:0}}, {{opacity:1, duration:0.4, ease:"power2.out"}}, {r(t_cut)});',
          f'tl.fromTo("#lk-pin", {{opacity:0, y:-40}}, {{opacity:1, y:0, duration:0.5, ease:"back.out(1.8)"}}, {r(t)});',
          word_in("#lk-l1", t + 0.18), word_in("#lk-l2", t + 0.32),
          f'tl.fromTo("#lk-rule", {{scaleX:0}}, {{scaleX:1, duration:0.5, ease:"expo.out"}}, {r(t + 0.45)});',
          word_in("#lk-l3", t + 0.55, 6),
          f'tl.to("#lk-card", {{opacity:0, filter:"blur(10px)", duration:0.22, ease:"power3.in"}}, {r(dur - 0.26)});',
          f'tl.to("#lk-scrim", {{opacity:0, duration:0.22}}, {r(dur - 0.24)});']
    css = "\n    #lk-pin, #lk-l1, #lk-l2, #lk-l3 { opacity:0; }"
    return scene("lokasi", css, body, js), host, dur


# ---------------------------------------------------------------- scene: reveal (24.69 - 29.95)
def scene_reveal():
    host = SEG["s08"]["at"]
    dur = SEG["s10"]["end"] - host
    t_rev = SEG["s09"]["at"] - host            # "pondok untuk warga emas"
    t_single = T(72.20) - host
    t_kelamin = T(73.54) - host
    el1, kb1 = broll("rv-land", "assets/photos/tanah-wakaf-aerial.jpg", 0, t_rev + 0.3, 3413, 1920, -380, -470, 1.08, 1.14)
    el2, kb2 = broll("rv-plan", "assets/photos/pelan-konsep.jpg", t_rev, dur - t_rev, 1359, 1920, -140, -140, 1.0, 1.06, z=2,
                     ease="power1.out")
    body = f"""{el1}
{el2}
    <div id="rv-flash" style="position:absolute;inset:0;z-index:3;background:radial-gradient(ellipse 70% 55% at 50% 40%, rgba(255,240,205,1), rgba(255,214,140,0.65) 45%, rgba(255,200,120,0) 75%);opacity:0;mix-blend-mode:screen"></div>
    <div id="rv-scrim" class="scrim-top" style="z-index:4"></div>
    <div id="rv-title" class="tb" style="top:228px;z-index:6">
      <div id="rv-eb" class="eyebrow">Projek Seterusnya</div>
      <div id="rv-l1" class="serif" style="font-size:98px;margin-top:18px">Kompleks Pondok</div>
      <div id="rv-l2" class="serif gold" style="font-size:118px;font-style:italic">Warga Emas</div>
      <div id="rv-rule" class="rule" style="width:420px;margin:24px auto 26px"></div>
      <div style="display:flex;gap:18px;justify-content:center">
        <span id="rv-c1" class="chip" style="background:#f5cd7a;color:#0b2e22">Bujang</span>
        <span id="rv-c2" class="chip" style="background:#f5cd7a;color:#0b2e22">Berkelamin</span>
      </div>
    </div>
    <div id="rv-note" style="position:absolute;right:56px;top:1010px;z-index:6;font-family:'Montserrat',sans-serif;font-weight:700;font-size:22px;letter-spacing:0.2em;color:rgba(255,255,255,0.92);background:rgba(0,0,0,0.42);padding:8px 16px;border-radius:8px">GAMBARAN KONSEP</div>"""
    t = t_rev + 0.12
    js = [kb1, kb2,
          # the plan arrives slightly large and settles, under a warm light flash
          f'tl.fromTo("#rv-plan", {{opacity:0}}, {{opacity:1, duration:0.3, ease:"power2.out"}}, {r(t_rev)});',
          f'tl.fromTo("#rv-flash", {{opacity:0}}, {{opacity:0.95, duration:0.22, ease:"power2.out"}}, {r(t_rev - 0.16)});',
          f'tl.to("#rv-flash", {{opacity:0, duration:0.7, ease:"power2.in"}}, {r(t_rev + 0.08)});',
          f'tl.fromTo("#rv-scrim", {{opacity:0}}, {{opacity:1, duration:0.5, ease:"power2.out"}}, {r(t)});',
          word_in("#rv-eb", t + 0.1, 6), word_in("#rv-l1", t + 0.22), word_in("#rv-l2", t + 0.36, 10, 0.24),
          f'tl.fromTo("#rv-rule", {{scaleX:0}}, {{scaleX:1, duration:0.5, ease:"expo.out"}}, {r(t + 0.5)});',
          f'tl.fromTo("#rv-note", {{opacity:0}}, {{opacity:1, duration:0.3}}, {r(t + 0.4)});',
          f'tl.fromTo("#rv-c1", {{opacity:0, scale:0.5}}, {{opacity:1, scale:1, duration:0.45, ease:"back.out(1.7)"}}, {r(t_single)});',
          f'tl.fromTo("#rv-c2", {{opacity:0, scale:0.5}}, {{opacity:1, scale:1, duration:0.45, ease:"back.out(1.7)"}}, {r(t_kelamin)});',
          f'tl.to(["#rv-title","#rv-note"], {{opacity:0, filter:"blur(10px)", duration:0.22, ease:"power3.in"}}, {r(dur - 0.26)});',
          f'tl.to("#rv-scrim", {{opacity:0, duration:0.22}}, {r(dur - 0.24)});']
    css = "\n    #rv-plan, #rv-eb, #rv-l1, #rv-l2, #rv-c1, #rv-c2, #rv-note { opacity:0; }\n    #rv-rule { transform-origin:50% 50%; }"
    return scene("reveal", css, body, js), host, dur


# ---------------------------------------------------------------- scene: tarikh (29.95 - 34.05)
def scene_tarikh():
    host = SEG["s11"]["at"]
    dur = SEG["s11"]["end"] - host
    t_sel = T(78.38) - host
    body = """    <div id="tk-scrim" class="scrim-top" style="z-index:1"></div>
    <div id="tk-card" class="tb" style="top:250px;z-index:5">
      <svg id="tk-moon" width="86" height="86" viewBox="0 0 64 64"><path d="M40 6a26 26 0 1 0 18 44A22 22 0 1 1 40 6z" fill="#f5cd7a"/><path d="M50 16l2 5 5 .4-4 3.2 1.4 5-4.4-2.8-4.4 2.8 1.4-5-4-3.2 5-.4z" fill="#f5cd7a"/></svg>
      <div id="tk-eb" class="eyebrow" style="margin-top:18px">Projek Bermula</div>
      <div id="tk-l1" class="serif" style="font-size:120px;margin-top:18px">Selepas</div>
      <div id="tk-l2" class="serif gold" style="font-size:132px;font-style:italic">Hari Raya</div>
      <div id="tk-rule" class="rule" style="width:420px;margin:26px auto 0"></div>
    </div>"""
    js = ['tl.fromTo("#tk-scrim", {opacity:0}, {opacity:1, duration:0.4, ease:"power2.out"}, 0.15);',
          'tl.fromTo("#tk-moon", {opacity:0, rotation:-25, scale:0.7}, {opacity:1, rotation:0, scale:1, duration:0.6, ease:"expo.out"}, 0.3);',
          word_in("#tk-eb", 0.5, 6),
          word_in("#tk-l1", t_sel - 0.05), word_in("#tk-l2", t_sel + 0.25, 10, 0.26),
          f'tl.fromTo("#tk-rule", {{scaleX:0}}, {{scaleX:1, duration:0.5, ease:"expo.out"}}, {r(t_sel + 0.4)});',
          f'tl.to("#tk-card", {{opacity:0, filter:"blur(10px)", duration:0.22, ease:"power3.in"}}, {r(dur - 0.26)});',
          f'tl.to("#tk-scrim", {{opacity:0, duration:0.22}}, {r(dur - 0.24)});']
    css = "\n    #tk-moon, #tk-eb, #tk-l1, #tk-l2 { opacity:0; }"
    return scene("tarikh", css, body, js), host, dur


# ---------------------------------------------------------------- scene: rayuan b-roll (38.03 - 43.25)
def scene_rayuan():
    host = SEG["s13"]["at"]
    dur = SEG["s14"]["end"] - host
    t2 = SEG["s14"]["at"] - host
    e1, k1 = broll("ry-a", "assets/photos/asrama-malam.jpg", 0, t2, 1080, 1920, 0, 0, 1.0, 1.08, ease="none")
    e2, k2 = broll("ry-b", "assets/photos/pondok-jalan.jpg", t2, dur - t2, 1080, 1920, 0, 0, 1.12, 1.04, y0=-40, y1=10, ease="power2.out")
    return scene("rayuan", "", f"{e1}\n{e2}", [k1, k2]), host, dur


# ---------------------------------------------------------------- scene: ilmu + pahala b-roll (47.49 - 57.45)
def scene_ilmu():
    host = SEG["s17"]["at"]
    dur = SEG["s20"]["end"] - host
    t_kul = SEG["s19"]["at"] - host
    t_ust = T(113.80) - host
    t_pah = SEG["s20"]["at"] - host
    t_keb = T(119.86) - host
    e1, k1 = broll("il-a", "assets/photos/jemaah-1.jpg", 0, t_kul, 2560, 1920, -820, -900, 1.04, 1.12, ease="none")
    e2, k2 = broll("il-b", "assets/photos/kuliah.jpg", t_kul, t_ust - t_kul, 2560, 1920, -1300, -900, 1.0, 1.0, ease="sine.inOut")
    e3, k3 = broll("il-c", "assets/photos/ustaz.jpg", t_ust, t_pah - t_ust, 1440, 1920, -260, -240, 1.0, 1.08, ease="none")
    e4, k4 = broll("il-d", "assets/photos/jemaah-2.jpg", t_pah, dur - t_pah, 2560, 1920, -640, -800, 1.06, 1.14, ease="none")
    body = f"""{e1}
{e2}
{e3}
{e4}
    <div id="il-scrim" class="scrim-top" style="z-index:3"></div>
    <div id="il-q" class="tb" style="top:250px;z-index:5">
      <div id="il-qm" class="serif gold" style="font-size:160px;line-height:0.6">&ldquo;</div>
      <div id="il-l1" class="serif gold" style="font-size:124px;font-style:italic;margin-top:10px">Kebajikan</div>
      <div id="il-l2" class="serif" style="font-size:84px;margin-top:4px">hingga ke akhirat</div>
    </div>"""
    js = [k1, k2, k3, k4,
          f'tl.fromTo("#il-scrim", {{opacity:0}}, {{opacity:1, duration:0.5, ease:"power2.out"}}, {r(t_keb - 0.4)});',
          word_in("#il-qm", t_keb - 0.2, 6), word_in("#il-l1", t_keb, 12, 0.28), word_in("#il-l2", T(120.54) - host, 8, 0.24),
          f'tl.to("#il-q", {{opacity:0, filter:"blur(10px)", duration:0.24, ease:"power3.in"}}, {r(dur - 0.28)});',
          f'tl.to("#il-scrim", {{opacity:0, duration:0.24}}, {r(dur - 0.26)});']
    css = "\n    #il-qm, #il-l1, #il-l2 { opacity:0; }"
    return scene("ilmu", css, body, js), host, dur


# ---------------------------------------------------------------- scene: sebar (57.45 - 60.39)
def scene_sebar():
    host = SEG["s21"]["at"]
    dur = SEG["s21"]["end"] - host
    t = T(123.60) - host
    body = """    <div id="sb-scrim" class="scrim-top" style="z-index:1;height:700px"></div>
    <div class="tb" style="top:300px;z-index:5">
      <span id="sb-chip" class="chip" style="background:#f5cd7a;color:#0b2e22;font-size:46px;padding:22px 44px">
        <svg width="46" height="46" viewBox="0 0 24 24"><circle cx="18" cy="5" r="3" fill="#0b2e22"/><circle cx="6" cy="12" r="3" fill="#0b2e22"/><circle cx="18" cy="19" r="3" fill="#0b2e22"/><path d="M8.6 13.5l6.8 4M15.4 6.5l-6.8 4" stroke="#0b2e22" stroke-width="2.2"/></svg>
        Sebarkan
      </span>
      <div id="sb-sub" class="serif" style="font-size:60px;font-style:italic;margin-top:30px">kepada sahabat &amp; keluarga</div>
    </div>"""
    js = [f'tl.fromTo("#sb-scrim", {{opacity:0}}, {{opacity:1, duration:0.35}}, {r(t - 0.2)});',
          f'tl.fromTo("#sb-chip", {{opacity:0, scale:0.4, y:30}}, {{opacity:1, scale:1, y:0, duration:0.55, ease:"back.out(1.8)"}}, {r(t)});',
          word_in("#sb-sub", t + 0.3, 8),
          f'tl.to(["#sb-chip","#sb-sub"], {{opacity:0, filter:"blur(10px)", duration:0.2, ease:"power3.in"}}, {r(dur - 0.24)});',
          f'tl.to("#sb-scrim", {{opacity:0, duration:0.2}}, {r(dur - 0.22)});']
    css = "\n    #sb-chip, #sb-sub { opacity:0; }"
    return scene("sebar", css, body, js), host, dur


# ---------------------------------------------------------------- scene: harapan b-roll (63.36 - 69.96)
def scene_harapan():
    host = SEG["s23"]["at"]
    dur = SEG["s25"]["end"] - host
    t2 = SEG["s25"]["at"] - host
    # concept plan, framed tighter on the rows of pondok (lower half of the render)
    e1, k1 = broll("hp-a", "assets/photos/pelan-konsep.jpg", 0, t2, 1359 * 1.55, 1920 * 1.55, -560, -500, 1.0, 1.05,
                   y0=-1060, y1=-1180, ease="sine.inOut")
    e2, k2 = broll("hp-b", "assets/photos/tuan-guru.jpg", t2, dur - t2, 1440, 1920, -180, -180, 1.0, 1.07, ease="none")
    body = f"""{e1}
{e2}
    <div id="hp-note" style="position:absolute;right:56px;top:1010px;z-index:6;font-family:'Montserrat',sans-serif;font-weight:700;font-size:22px;letter-spacing:0.2em;color:rgba(255,255,255,0.92);background:rgba(0,0,0,0.42);padding:8px 16px;border-radius:8px">GAMBARAN KONSEP</div>"""
    js = [k1, k2, 'tl.fromTo("#hp-note", {opacity:0}, {opacity:1, duration:0.3}, 0.2);',
          f'tl.to("#hp-note", {{opacity:0, duration:0.15}}, {r(t2 - 0.15)});']
    return scene("harapan", "", body, js), host, dur


# ---------------------------------------------------------------- scene: end card (78.95 - 86.5)
def scene_end():
    host = SEG["s28"]["at"]
    dur = TOTAL - host
    body = """    <div id="ec-bg" class="clip broll" data-start="0" data-duration="%s" style="z-index:1">
      <div id="ec-kb" class="kb" style="width:1080px;height:1920px"><img id="ec-img" src="assets/photos/pelan-konsep-blur.jpg" alt="" /></div>
    </div>
    <div id="ec-tint" style="position:absolute;inset:0;z-index:2;background:linear-gradient(180deg, rgba(4,34,25,0.86) 0%%, rgba(6,44,32,0.78) 55%%, rgba(3,24,18,0.94) 100%%)"></div>
    <div id="ec-glow" style="position:absolute;left:-200px;top:300px;width:1480px;height:900px;z-index:3;background:radial-gradient(ellipse 50%% 45%% at 50%% 50%%, rgba(245,205,122,0.28), rgba(245,205,122,0) 70%%);mix-blend-mode:screen"></div>
    <div class="tb" style="top:300px;z-index:5">
      <svg id="ec-orn" width="120" height="60" viewBox="0 0 120 60"><path d="M60 4c-8 10-8 22 0 30 8-8 8-20 0-30z" fill="#f5cd7a"/><path d="M4 44h44M72 44h44" stroke="#f5cd7a" stroke-width="2"/><circle cx="60" cy="44" r="5" fill="#f5cd7a"/></svg>
      <div id="ec-eb" class="eyebrow" style="margin-top:26px">Jom Bersama</div>
      <div id="ec-l1" class="serif" style="font-size:132px;margin-top:22px">Bina Pondok</div>
      <div id="ec-l2" class="serif gold" style="font-size:142px;font-style:italic">Warga Emas</div>
      <div id="ec-rule" class="rule" style="width:460px;margin:34px auto 30px"></div>
      <div id="ec-l3" style="font-family:'Montserrat',sans-serif;font-weight:600;font-size:36px;color:#fff;letter-spacing:0.04em">Madrasah Zawiyah An-Nur, Gerik</div>
      <div id="ec-cta" style="display:flex;gap:16px;justify-content:center;margin-top:58px">
        <span id="ec-c1" class="chip" style="background:#f5cd7a;color:#0b2e22">Sumbang</span>
        <span id="ec-c2" class="chip" style="border:2px solid #f5cd7a;color:#f5cd7a">Sebarkan</span>
        <span id="ec-c3" class="chip" style="border:2px solid #f5cd7a;color:#f5cd7a">Doakan</span>
      </div>
      <div id="ec-info" data-var-text="maklumat_sumbangan" style="font-family:'Montserrat',sans-serif;font-weight:600;font-size:32px;color:rgba(255,255,255,0.86);margin:44px auto 0;width:860px;line-height:1.35">Hubungi pihak Madrasah Zawiyah An-Nur Gerik untuk menyumbang</div>
      <div id="ec-q" class="serif" style="font-size:54px;font-style:italic;font-weight:600;color:#f5cd7a;margin-top:70px">&ldquo;Satu sumbangan, kebajikan<br/>hingga ke akhirat&rdquo;</div>
    </div>""" % r(dur)
    js = ['tl.fromTo("#ec-bg", {opacity:0}, {opacity:1, duration:0.6, ease:"power2.inOut"}, 0.1);',
          'tl.fromTo("#ec-kb", {scale:1.12}, {scale:1.0, duration:%s, ease:"power2.out"}, 0);' % r(dur),
          'tl.fromTo("#ec-tint", {opacity:0}, {opacity:1, duration:0.6, ease:"power2.inOut"}, 0.1);',
          'tl.fromTo("#ec-glow", {opacity:0, x:-120}, {opacity:1, x:120, duration:%s, ease:"sine.inOut"}, 0.3);' % r(dur - 0.3),
          'tl.fromTo("#ec-orn", {opacity:0, y:-20}, {opacity:1, y:0, duration:0.6, ease:"expo.out"}, 0.55);',
          word_in("#ec-eb", 0.7, 6), word_in("#ec-l1", 0.86, 10, 0.24), word_in("#ec-l2", 1.02, 12, 0.28),
          'tl.fromTo("#ec-rule", {scaleX:0}, {scaleX:1, duration:0.6, ease:"expo.out"}, 1.2);',
          word_in("#ec-l3", 1.35, 6),
          'tl.fromTo(["#ec-c1","#ec-c2","#ec-c3"], {opacity:0, y:24}, {opacity:1, y:0, duration:0.5, ease:"expo.out", stagger:0.08}, 1.75);',
          word_in("#ec-info", 2.3, 6),
          word_in("#ec-q", 3.2, 10, 0.3)]
    css = "\n    #ec-orn, #ec-eb, #ec-l1, #ec-l2, #ec-l3, #ec-c1, #ec-c2, #ec-c3, #ec-info, #ec-q { opacity:0; }"
    return scene("endcard", css, body, js), host, dur


# ---------------------------------------------------------------- speaker framing
# (segment ids, scale at cut, scale at end of run). Punch-ins alternate to hide jump cuts.
CAM = [
    (["s01"], 1.16, 1.20),
    (["s04"], 1.00, 1.04),
    (["s05"], 1.13, 1.16),
    (["s06"], 1.00, 1.05),
    (["s07"], 1.15, 1.18),
    (["s11"], 1.12, 1.15),
    (["s12"], 1.00, 1.03),          # punch to 1.18 on "sumbangan" (below)
    (["s15", "s16"], 1.13, 1.17),
    (["s21"], 1.22, 1.24),
    (["s22"], 1.00, 1.04),
    (["s26"], 1.00, 1.04),
    (["s27"], 1.12, 1.17),
    (["s28", "s29"], 1.17, 1.19),
]


def cam_js():
    js = []
    for ids, a, b in CAM:
        t0 = SEG[ids[0]]["at"]
        t1 = SEG[ids[-1]]["end"]
        js.append(f'tl.set("#cam", {{scale:{a}}}, {r(t0)});')
        if ids == ["s12"]:
            ts = T(84.98)
            js.append(f'tl.to("#cam", {{scale:1.03, duration:{r(ts - t0)}, ease:"none"}}, {r(t0)});')
            js.append(f'tl.set("#cam", {{scale:1.18}}, {r(ts)});')
            js.append(f'tl.to("#cam", {{scale:1.2, duration:{r(t1 - ts)}, ease:"none"}}, {r(ts)});')
            continue
        js.append(f'tl.to("#cam", {{scale:{b}, duration:{r(t1 - t0)}, ease:"none"}}, {r(t0)});')
    return js


# ---------------------------------------------------------------- sound effects
# (id, file, time the hit should land, peak offset inside the file, volume)
PEAK = {"whoosh-cinematic": 2.50, "whoosh": 0.16, "whoosh-short": 0.16, "impact-bass-1": 0.07,
        "impact-bass-2": 0.12, "pop": 0.11, "sparkle": 0.02}


SFX_DUR = {"whoosh-cinematic": 5.5, "whoosh": 0.55, "whoosh-short": 0.55, "impact-bass-1": 2.1,
           "impact-bass-2": 2.55, "pop": 0.7, "sparkle": 1.78}


def sfx_list():
    return [
        ("sfx-whoosh-aerial", "whoosh-cinematic", SEG["s02"]["at"], 0.42),
        ("sfx-pop-tag", "pop", SEG["s02"]["at"] + 1.0, 0.5),
        ("sfx-impact-ekar", "impact-bass-1", T(50.12), 0.55),
        ("sfx-whoosh-back", "whoosh", SEG["s04"]["at"], 0.4),
        ("sfx-whoosh-lokasi", "whoosh-short", T(35.40), 0.38),
        ("sfx-whoosh-land", "whoosh-short", SEG["s08"]["at"], 0.36),
        ("sfx-impact-reveal", "impact-bass-2", SEG["s09"]["at"], 0.55),
        ("sfx-sparkle-reveal", "sparkle", SEG["s09"]["at"] + 0.05, 0.4),
        ("sfx-pop-single", "pop", T(72.20), 0.45),
        ("sfx-pop-kelamin", "pop", T(73.54), 0.45),
        ("sfx-sparkle-raya", "sparkle", T(78.38) + 0.25, 0.32),
        ("sfx-whoosh-asrama", "whoosh", SEG["s13"]["at"], 0.36),
        ("sfx-whoosh-jemaah", "whoosh-short", SEG["s17"]["at"], 0.34),
        ("sfx-sparkle-akhirat", "sparkle", T(119.86), 0.36),
        ("sfx-pop-sebar", "pop", T(123.60), 0.5),
        ("sfx-whoosh-plan", "whoosh-cinematic", SEG["s23"]["at"], 0.36),
        ("sfx-whoosh-end", "whoosh-cinematic", SEG["s28"]["at"] + 0.1, 0.4),
        ("sfx-impact-end", "impact-bass-1", SEG["s28"]["at"] + 0.86, 0.45),
    ]


# ---------------------------------------------------------------- light leak
def leak_html(cid, d):
    """Warm gold light leak, adapted from the registry's organic-light-leak-overlay block."""
    return f"""<template>
  <style>
    #root {{ position:absolute; inset:0; overflow:hidden; pointer-events:none; }}
    .lk {{ position:absolute; inset:-16%; opacity:0; mix-blend-mode:screen; }}
    .lk .ly {{ position:absolute; inset:-20%; }}
    .lk .amber {{ background:radial-gradient(ellipse 52% 110% at 10% 58%, rgb(255 241 197 / 88%), transparent 45%),
                 radial-gradient(ellipse 72% 120% at 24% 54%, rgb(255 160 70 / 70%), transparent 66%); filter:blur(28px); }}
    .lk .warm {{ background:radial-gradient(ellipse 58% 105% at 78% 34%, rgb(255 190 90 / 60%), rgb(255 120 60 / 22%) 48%, transparent 76%); filter:blur(40px); }}
    .lk .gold {{ background:linear-gradient(104deg, transparent 24%, rgb(255 170 70 / 28%) 40%, rgb(255 247 210 / 70%) 51%, rgb(255 150 60 / 20%) 62%, transparent 78%); filter:blur(20px); }}
  </style>
  <div id="root" data-composition-id="{cid}" data-width="{W}" data-height="{H}" data-layout-ignore>
    <div id="{cid}-lk" class="lk"><div id="{cid}-a" class="ly amber"></div><div id="{cid}-w" class="ly warm"></div><div id="{cid}-g" class="ly gold"></div></div>
  </div>
  <script>
    const tl = gsap.timeline({{ paused: true }});
    const d = {d};
    tl.fromTo("#{cid}-lk", {{opacity:0}}, {{opacity:0.85, duration:d*0.26, ease:"sine.out"}}, d*0.06);
    tl.to("#{cid}-lk", {{opacity:0.4, duration:d*0.2, ease:"sine.inOut"}}, d*0.4);
    tl.to("#{cid}-lk", {{opacity:0, duration:d*0.3, ease:"sine.in"}}, d*0.66);
    tl.fromTo("#{cid}-a", {{xPercent:-20, scale:0.92, rotation:-4}}, {{xPercent:18, scale:1.1, rotation:2, duration:d, ease:"sine.inOut"}}, 0);
    tl.fromTo("#{cid}-w", {{xPercent:20, yPercent:-8, scale:1.08}}, {{xPercent:-16, yPercent:8, scale:0.94, duration:d, ease:"sine.inOut"}}, 0);
    tl.fromTo("#{cid}-g", {{xPercent:-28, rotation:-6}}, {{xPercent:24, rotation:4, duration:d, ease:"sine.inOut"}}, 0);
    window.__timelines["{cid}"] = tl;
  </script>
</template>
"""


# ---------------------------------------------------------------- root
def build():
    os.makedirs(os.path.join(ROOT, "compositions"), exist_ok=True)
    scenes = []
    s, end = scene_hook(); scenes.append(("hook", 0, end, s))
    for fn in (scene_lokasi, scene_reveal, scene_tarikh, scene_rayuan, scene_ilmu, scene_sebar, scene_harapan, scene_end):
        s, host, dur = fn()
        cid = re.search(r'data-composition-id="([^"]+)"', s).group(1)
        scenes.append((cid, host, dur, s))
    for cid, _, _, s in scenes:
        open(os.path.join(ROOT, "compositions", f"{cid}.html"), "w").write(s)
    open(os.path.join(ROOT, "compositions", "captions.html"), "w").write(captions_html())

    vids = []
    for i, c in enumerate(EDL):
        vids.append(
            f'        <video id="v-{c["id"]}" class="clip talk" src="assets/talk.mp4" playsinline data-has-audio="true" '
            f'data-start="{c["at"]}" data-duration="{r(c["end"] - c["at"])}" data-media-start="{c["in"]}" '
            f'data-fade-in="0.03" data-fade-out="0.03" data-volume="1" data-track-index="0" '
            f'data-color-grading="{grade(GRADE_TALK)}"></video>')

    hosts = []
    for k, (cid, host, dur, _) in enumerate(scenes):
        hosts.append(
            f'      <div id="{cid}" data-composition-id="{cid}" data-composition-src="compositions/{cid}.html" '
            f'data-start="{r(host)}" data-duration="{r(dur)}" data-track-index="{1 + (k % 2)}" data-track-kind="graphics" '
            f'data-width="{W}" data-height="{H}" style="z-index:{10 + k}"></div>')

    leaks = [(SEG["s02"]["at"] - 0.45, 1.3), (SEG["s04"]["at"] - 0.5, 1.2), (SEG["s09"]["at"] - 0.55, 1.8),
             (T(119.50), 2.2), (SEG["s28"]["at"] - 0.3, 2.4)]
    leak_hosts = []
    for k, (t, d) in enumerate(leaks):
        open(os.path.join(ROOT, "compositions", f"leak-{k + 1}.html"), "w").write(leak_html(f"leak-{k + 1}", d))
        leak_hosts.append(
            f'      <div id="leak-{k + 1}" data-composition-id="leak-{k + 1}" data-composition-src="compositions/leak-{k + 1}.html" '
            f'data-start="{r(t)}" data-duration="{d}" data-track-index="3" data-track-kind="graphics" '
            f'data-width="{W}" data-height="{H}" style="z-index:40"></div>')

    audio = []
    for id_, f, hit, vol in sfx_list():
        st = hit - PEAK[f] + 0.033
        ms = max(0.0, -st)
        st = max(0.0, st)
        dur = min(SFX_DUR[f] - ms, TOTAL - st)
        extra = f' data-media-start="{r(ms)}"' if ms else ""
        audio.append(f'      <audio id="{id_}" class="clip" src="assets/sfx/{f}.mp3" data-start="{r(st)}" data-duration="{r(dur)}"{extra} '
                     f'data-volume="{vol}" data-track-index="{5 + len(audio) % 3}"></audio>')

    variables = [{"id": "maklumat_sumbangan", "type": "string", "label": "Maklumat sumbangan (kad penutup)",
                  "default": "Hubungi pihak Madrasah Zawiyah An-Nur Gerik untuk menyumbang"}]
    page = f"""<!doctype html>
<html lang="ms" data-composition-variables='{json.dumps(variables, ensure_ascii=False)}'>
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width={W}, height={H}" />
    <script src="assets/vendor/gsap.min.js"></script>
    <style>
      :root {{ --ground:#04140f; --gold:#f5cd7a; --ink:#ffffff; }}
      * {{ margin:0; padding:0; box-sizing:border-box; }}
      html, body {{ margin:0; width:{W}px; height:{H}px; overflow:hidden; background:var(--ground); }}
      #root {{ position:relative; width:{W}px; height:{H}px; overflow:hidden; font-family:"Montserrat",sans-serif; }}
      #ground {{ position:absolute; inset:0; background:var(--ground); }}
      #cam {{ position:absolute; left:0; top:0; width:{W}px; height:{H}px; transform-origin:50% 44%; z-index:1; }}
      #cam video {{ position:absolute; left:0; top:0; width:{W}px; height:{H}px; object-fit:cover; }}
    </style>
  </head>
  <body>
    <div id="root" data-composition-id="main" data-start="0" data-duration="{TOTAL}" data-width="{W}" data-height="{H}">
      <div id="ground"></div>
      <div id="cam">
{chr(10).join(vids)}
      </div>
{chr(10).join(hosts)}
{chr(10).join(leak_hosts)}
      <div id="captions" data-composition-id="captions" data-composition-src="compositions/captions.html" data-start="0" data-duration="{SEG['s27']['end'] + 0.4:.2f}" data-track-index="4" data-track-kind="captions" data-width="{W}" data-height="{H}" style="z-index:60"></div>
{chr(10).join(audio)}
    </div>
    <script>
      const tl = gsap.timeline({{ paused: true }});
      {(chr(10) + '      ').join(cam_js())}
      window.__timelines["main"] = tl;
    </script>
  </body>
</html>
"""
    open(os.path.join(ROOT, "index.html"), "w").write(page)
    print("wrote index.html +", len(scenes) + 1, "scenes; total", TOTAL, "s")


if __name__ == "__main__":
    build()
